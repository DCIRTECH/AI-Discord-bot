import os
import json

CARDS_PATH = "data/cards"
REQUIRED_FIELDS = ["id", "name", "description", "rarity", "prompt_file"]

def load_all_cards():
    cards = []
    for filename in os.listdir(CARDS_PATH):
        if not filename.endswith(".json"):
            continue

        path = os.path.join(CARDS_PATH, filename)

        try:
            with open(path, "r", encoding="utf8") as f:
                card = json.load(f)

            # Field validation
            for field in REQUIRED_FIELDS:
                if field not in card:
                    raise ValueError(f"Missing field '{field}' in {filename}")

            # Prompt file existence check
            if not os.path.exists(card["prompt_file"]):
                raise FileNotFoundError(f"Prompt file not found: {card['prompt_file']}")

            cards.append(card)

        except json.JSONDecodeError as e:
            print(f"[ERROR] Malformed JSON in {filename}: {e}")
        except Exception as e:
            print(f"[ERROR] Failed to load card {filename}: {e}")

    return cards


def get_card_by_id(card_id):
    path = os.path.join(CARDS_PATH, f"{card_id}.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[ERROR] Could not read card {card_id}: {e}")
    return None
