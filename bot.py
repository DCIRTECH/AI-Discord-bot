import discord
from discord.ext import commands
import os
import time
from dotenv import load_dotenv
from collections import defaultdict, deque
import random
import difflib
from datetime import datetime, UTC, timedelta
from textblob import TextBlob

from utils.memory import get_recent_turns, save_turn
from utils.llm_bridge import build_context, get_response
from utils.user_loader import load_user, save_user
from utils.card_loader import load_all_cards, get_card_by_id
from utils.sanitize import clean_input, sanitize_output
import utils.config as config

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix=">>", intents=intents, help_command=None)
cards = load_all_cards()
#TODO ADD MORE CARDS
#Ollama fails or offline, give fallback message
#preview command, gives a greeting from that character
#Set up analytics >most talked to cards >longest convos >active users
#admin only commands??? grant/revoke/forceequip
#chatlogs? delete? encrypt? WANT MAXIMUM SECURITY, MINIMIZE ANY AVAILIBILITY TO IT.stremio sing a bit of harmony
#get user ID to send personalized messages
def analyze_sentiment(message):

    blob = TextBlob(message)
    polarity = blob.sentiment.polarity
    subjectivity = blob.sentiment.subjectivity

    if polarity > 0.5:
        mood = "happy"
    elif polarity > 0.1:
        mood = "content"
    elif polarity < -0.5:
        mood = "upset"
    elif polarity < -0.1:
        mood = "sad"
    else:
        mood = "neutral"

    energy = "high" if subjectivity > 0.6 else "low"
    engagement = "engaged" if len(message.split()) > 6 else "brief"

    return {
        "mood": mood,
        "energy": energy,
        "emotion": mood,
        "engagement": engagement
    }

@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="📖 Bot Commands",
        description="Here's a list of commands you can use:",
        color=0x00ffcc
    )

    embed.add_field(
        name=">>roll",
        value="🎲 Roll a random card once per day. Bonus rolls can be earned by chatting.\n**Usage:** `>>roll`",
        inline=False
    )

    embed.add_field(
        name=">>inventory",
        value="🎒 View your collected companion cards.\n**Usage:** `>>inventory`",
        inline=False
    )

    embed.add_field(
        name=">>equip",
        value="🗡️ Equip a companion card to interact with.\n**Usage:** `>>equip <card_id>`",
        inline=False
    )

    embed.add_field(
        name=">>talk",
        value="💬 Chat with your active companion.\n**Usage:** `>>talk <message>`",
        inline=False
    )

    embed.add_field(
        name=">>listcards",
        value="📋 List available companion cards, filtered by rarity and page.\n**Usage:** `>>listcards [rarity] [page]`\n*Example:* `>>listcards rare 2`",
        inline=False
    )

    embed.add_field(
        name=">>cardinfo",
        value="🔍 Works as a search function, search by name, ID or their tags.\n**Usage:** `>>cardinfo <card_id>`",
        inline=False
    )

    embed.add_field(
        name="feedback?",
        value="If you have feedback or any questions please come to https://discord.gg/jkFkNmjrSS and leave it in our forums.",
        inline=False
    )

    await ctx.send(embed=embed)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.command()
async def listcards(ctx, rarity: str = "all", page: int = 1):
    rarity = rarity.lower()
    per_page = 10

    valid_rarities = ["common", "uncommon", "rare", "epic", "legendary", "mythic", "all"]
    if rarity not in valid_rarities:
        await ctx.send(f"Invalid rarity! Please choose from: {', '.join(valid_rarities)}")
        return

    # Filter cards by visibility and rarity
    filtered_cards = [
        card for card in cards
        if not card.get("hidden", False) and (rarity == "all" or card["rarity"].lower() == rarity)
    ]

    if not filtered_cards:
        await ctx.send(f"No cards available for rarity '{rarity}'.")
        return

    total_cards = len(filtered_cards)
    total_pages = (total_cards + per_page - 1) // per_page

    # Page boundary check
    if page < 1 or page > total_pages:
        await ctx.send(f"Page {page} doesn't exist. Please choose a page between 1 and {total_pages}.")
        return

    # Get page slice
    start = (page - 1) * per_page
    end = start + per_page
    cards_page = filtered_cards[start:end]

    # Generate response
    response = f"**Available Cards [{rarity.title()}] (Page {page}/{total_pages}):**\n"
    for card in cards_page:
        response += f"- **{card['name']}** ({card['rarity'].title()}) — ID: `{card['id']}`\n"

    # Inform user about navigating
    response += f"\nUse `>>listcards {rarity} {page + 1}` for next page." if page < total_pages else "\nYou're on the last page."

    await ctx.send(response)

@bot.command()
async def cardinfo(ctx, *, query: str):
    query_parts = query.strip().rsplit(" ", 1)
    page = 1
    if len(query_parts) == 2 and query_parts[1].isdigit():
        query, page = query_parts[0], int(query_parts[1])
    
    query = query.lower()
    per_page = 10

    search_pool = []
    for card in cards:
        combined_fields = f"{card['id']} {card['name']} {' '.join(card.get('tags', []))}".lower()
        search_pool.append((combined_fields, card))

    # CUT OFF BIGGER NUMBER = LESS RESULTS, SMALLER NUMBER = MORE RESULTS
    query_length = len(query)
    if query_length <= 3:
        cutoff = 0.078
    elif 4 <= query_length <= 6:
        cutoff = 0.14
    else:
        cutoff = 0.18

    all_matches = difflib.get_close_matches(
        query, 
        [item[0] for item in search_pool],
        n=len(search_pool), 
        cutoff=cutoff
    )

    matched_cards = [item[1] for item in search_pool if item[0] in all_matches]

    if not matched_cards:
        await ctx.send(f"No matches found for '{query}'.")
        return

    total_matches = len(matched_cards)
    total_pages = (total_matches + per_page - 1) // per_page

    if page < 1 or page > total_pages:
        await ctx.send(f"Page {page} is out of range. Please choose between 1 and {total_pages}.")
        return

    exact_matches = [card for card in matched_cards if query in (card['id'].lower(), card['name'].lower())]
    if exact_matches:
        card = exact_matches[0]
        response = (
            f"**{card['name']}** (🆔 `{card['id']}`)\n"
            f"**Rarity:** {card['rarity'].title()}\n"
            f"**Description:** {card['description']}\n"
        )
        if "event_rarity" in card:
            response += f"**Event Rarity:** {card['event_rarity'].title()}\n"
        if "tags" in card:
            response += f"**Tags:** {', '.join(card['tags'])}\n"
        await ctx.send(response)
        return

    start = (page - 1) * per_page
    end = start + per_page
    page_matches = matched_cards[start:end]

    response = f"**Matches for '{query}' (Page {page}/{total_pages}):**\n"
    for card in page_matches:
        response += f"- **{card['name']}** ({card['rarity'].title()}) — 🆔 `{card['id']}`\n"

    if page < total_pages:
        response += f"\nView next page: `/cardinfo \"{query}\" {page + 1}`"
    else:
        response += "\n*End of results.*"

    await ctx.send(response)

@bot.command()
async def roll(ctx):
    user_id = str(ctx.author.id)
    user = load_user(user_id)
    today = datetime.now(UTC).date()

    last_roll_str = user.get("last_roll_date")
    last_roll_date = None
    if last_roll_str:
        try:
            last_roll_date = datetime.strptime(last_roll_str, "%Y-%m-%d").date()
        except ValueError:
            last_roll_date = None

    # === Check Daily Roll Availability ===
    used_daily_roll = last_roll_date == today
    has_bonus_roll = user.get("bonus_roll_available", False)

    if used_daily_roll and not has_bonus_roll:
        await ctx.send("🛑 You've already used your daily roll. Try again tomorrow or earn a bonus roll!")
        return

    # === Determine which roll we're using ===
    using_bonus = False
    if used_daily_roll and has_bonus_roll:
        using_bonus = True
        user["bonus_roll_available"] = False
        save_user(user)

    # === Update streak and metadata (if using daily roll) ===
    if not used_daily_roll:
        if last_roll_date == today - timedelta(days=1):
            user["daily_streak"] = user.get("daily_streak", 0) + 1
        else:
            user["daily_streak"] = 1
        user["last_roll_date"] = today.strftime("%Y-%m-%d")
        save_user(user)

    # === Gacha Roll ===
    card_pool = defaultdict(list)
    for card in cards:
        rarity = card.get("rarity", "common")
        card_pool[rarity].append(card)

    rarity = random.choices(
        population=list(config.RARITY_WEIGHTS.keys()),
        weights=list(config.RARITY_WEIGHTS.values()),
        k=1
    )[0]

    if not card_pool[rarity]:
        await ctx.send("⚠️ No cards available for that rarity.")
        return

    pulled_card = random.choice(card_pool[rarity])
    already_owned = pulled_card["id"] in user["owned_cards"]

    if not already_owned:
        user["owned_cards"].append(pulled_card["id"])
        save_user(user)

    roll_type = "🎁 **Bonus Roll!**" if using_bonus else "🎉 **Daily Roll!**"

    await ctx.send(
        f"{roll_type}\n"
        f"You rolled a **{rarity.title()}**: **{pulled_card['name']}** (🆔 `{pulled_card['id']}`)\n"
        f"*{pulled_card['description']}*\n"
        f"{'✅ New companion added!' if not already_owned else '⚠️ Already owned!'}"
    )

@bot.command()
async def inventory(ctx):
    user_id = str(ctx.author.id)
    user = load_user(user_id)

    if not user["owned_cards"]:
        await ctx.send("You have no companions yet. Use `/roll` to summon one!")
        return

    response = "**Your Companions:**\n"
    for card_id in user["owned_cards"]:
        card = get_card_by_id(card_id)
        if card:
            response += f"- {card['name']} ({card['rarity']}) — 🆔: `{card['id']}`\n"
    await ctx.send(response)

@bot.command()
async def equip(ctx, card_id: str):
    user_id = str(ctx.author.id)
    user = load_user(user_id)

    if card_id not in user["owned_cards"]:
        await ctx.send("You don’t own that companion.")
        return

    user["active_card"] = card_id
    save_user(user)
    card = get_card_by_id(card_id)
    await ctx.send(f"Equipped **{card['name']}**.")

TALK_COOLDOWN_SECONDS = 5
TALK_BURST_WINDOW = 60  # seconds
TALK_MAX_BURST = 5

# Track user message history
user_message_timestamps = defaultdict(lambda: deque(maxlen=TALK_MAX_BURST))
last_message_time = defaultdict(float)
@bot.command()
async def talk(ctx, *, message: str):
    user_id = str(ctx.author.id)
    user = load_user(user_id)

    now = time.time()

    # Check 5 second cooldown
    if now - last_message_time[user_id] < TALK_COOLDOWN_SECONDS:
        await ctx.send("⏳ You're talking too fast. Please wait a few seconds.")
        return

    # Check burst limit (5 per 60 seconds)
    recent_msgs = user_message_timestamps[user_id]
    # Remove timestamps older than 60 seconds
    while recent_msgs and now - recent_msgs[0] > TALK_BURST_WINDOW:
        recent_msgs.popleft()

    if len(recent_msgs) >= TALK_MAX_BURST:
        await ctx.send("🚫 You've reached your message limit. Try again in a minute.")
        return

    # Update records
    recent_msgs.append(now)
    last_message_time[user_id] = now
    
    if not user["active_card"]:
        await ctx.send("You must equip a companion first using `/equip [card_id]`.")
        return

    card = get_card_by_id(user["active_card"])
    if not card:
        await ctx.send("Active companion not found.")
        return

    try:
        with open(card["prompt_file"], "r", encoding="utf8") as f:
            prompt_template = f.read()
    except FileNotFoundError:
        await ctx.send(f"Prompt file for **{card['name']}** is missing.")
        return
    except Exception as e:
        await ctx.send(f"Error loading prompt for **{card['name']}**: {e}")
        return

    sanitized_input = clean_input(message)
    sentiment = analyze_sentiment(sanitized_input)
    sentiment_string = f"(User mood: {sentiment['mood']}, energy: {sentiment['energy']}, style: {sentiment['engagement']})"
    

    # Load memory history
    history = get_recent_turns(card["id"], user_id)

    # Build full context with recent turns
    prompt = build_context(prompt_template, sanitized_input, history)
    prompt = prompt_template.replace("{{user_input}}", f'"""\n{sanitized_input}\n{sentiment_string}\n"""')

    try:
        raw_output = get_response(prompt)
        output = sanitize_output(raw_output)
        if not output:
            output = "(No response generated.)"
        await ctx.send(f"**{card['name']}**: {output}")
        save_turn(card["id"], user_id, sanitized_input, output)
    except Exception as e:
        await ctx.send(f"Error talking to model: {e}")

    today = datetime.now(UTC).date()
    last_talk_str = user.get("last_talk_date")
    last_talk_date = datetime.strptime(last_talk_str, "%Y-%m-%d").date() if last_talk_str else None
    last_bonus_roll_str = user.get("last_bonus_roll_date")
    last_bonus_roll_date = datetime.strptime(last_bonus_roll_str, "%Y-%m-%d").date() if last_bonus_roll_str else None

# Only one bonus roll attempt per day
    chance = 0.6
    if last_talk_date != today:
        streak = user.get("daily_streak", 0)
        chance = 1/(10 + streak)
    if random.random() < chance and last_bonus_roll_date != today:
        user["bonus_roll_available"] = True
        user["last_bonus_roll_date"] = today.strftime("%Y-%m-%d")
        await ctx.send("🎉 You earned a bonus roll for chatting with your companion today!")
    user["last_talk_date"] = today.strftime("%Y-%m-%d")
    save_user(user)

@bot.command()
async def guide(ctx):
    message = (
        "**🌟 Welcome to The Echosend Companion Network!**\n"
        "Here, you’ll collect and connect with personal companions — each with their own voice, personality, and story to share.\n\n"
        "**Getting started is easy:**\n"
        "1. Use `>>roll` to meet your first companion.\n"
        "2. Use `>>equip [card_id]` to choose who you want by your side.\n"
        "3. Use `>>talk [message]` to start a conversation.\n\n"
        "You can see your collection with `>>inventory`, or browse others with `>>listcards`.\n"
        "Type `>>help` anytime to learn what else you can do.\n\n"
        "Have questions or feedback? head to `https://discord.gg/jkFkNmjrSS` and let us know in the forum!\n"
        "✨ Every companion is here to make your day a little more interesting. Go say hi."
    )
    await ctx.send(message)

bot.run(TOKEN)
