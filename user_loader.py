import os
import json

DATA_PATH = "data/users"

DEFAULT_USER = {
    "owned_cards": [],
    "active_card": None
}

def get_user_path(user_id):
    return os.path.join(DATA_PATH, f"{user_id}.json")

def load_user(user_id):
    path = get_user_path(user_id)

    # If user file doesn't exist, create it with default structure
    if not os.path.exists(path):
        user_data = {
            "user_id": user_id,
            **DEFAULT_USER
        }
        save_user(user_data)
        return user_data

    try:
        with open(path, "r", encoding="utf8") as f:
            user_data = json.load(f)

        # Ensure all required fields are present
        for key, value in DEFAULT_USER.items():
            if key not in user_data:
                user_data[key] = value

        return user_data

    except json.JSONDecodeError as e:
        print(f"[ERROR] Malformed JSON for user {user_id}: {e}")
        return {
            "user_id": user_id,
            **DEFAULT_USER
        }

    except Exception as e:
        print(f"[ERROR] Could not load user {user_id}: {e}")
        return {
            "user_id": user_id,
            **DEFAULT_USER
        }

def save_user(user_data):
    path = get_user_path(user_data["user_id"])
    try:
        with open(path, "w", encoding="utf8") as f:
            json.dump(user_data, f, indent=2)
    except Exception as e:
        print(f"[ERROR] Failed to save user {user_data['user_id']}: {e}")