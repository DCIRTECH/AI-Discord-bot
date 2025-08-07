# AI-Discord-bot
I made this as a bot for discord kinda like a waifu trading card type, where you can actually talk to the cards. I don't really care to take this project much further so have fun who ever finds this.
# What you need
Ollama set and running
a LLM picked out, go to hugging face and just snoop around I recommend mistral:7b personally, It's easy and a good allrounder. When you pick out your model, and have it in your ollama models folder, go to the config file and change the OLLAMA_MODEL to your model. The OLLAMA_URL should work for you off the rip.
you need a discord token for you bot, slap it into your ENV file, label it DISCORD_TOKEN
# packages needed:
- discord(ofcourse)
- random
- difflap
- datetime
- textblob
- requests
# File structure looks like this
Echosend
 - data
   - cards
   - memory
   - users
 - prompts
 - utils
  - __init__.py
  - card_loader.py
  - config.py
  - llm_bridge.py
  - memory.py
  - sanitize.py
  - user_loader.py

#IF YOU HAVE ANY QUESTIONS OR THINK IF THERE IS A WAY I CAN MAKE THIS AN EASIER SET UP, DROP ME A LINE.
