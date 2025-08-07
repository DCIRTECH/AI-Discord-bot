import json
from pathlib import Path

# Directory where memory files are stored
MEMORY_DIR = Path("data/memory")
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

# How many past user-agent exchanges to keep
MAX_TURNS = 6

def _memory_path(agent_name: str, user_id: str) -> Path:
    """Build path to memory file for this agent/user."""
    filename = f"{agent_name}_{user_id}.json"
    return MEMORY_DIR / filename

def load_memory(agent_name: str, user_id: str) -> list:
    """Load the recent memory history for this user/agent."""
    path = _memory_path(agent_name, user_id)
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_turn(agent_name: str, user_id: str, user_message: str, agent_response: str):
    """Append a new turn and prune old ones if necessary."""
    history = load_memory(agent_name, user_id)
    history.append({
        "user": user_message.strip(),
        "agent": agent_response.strip()
    })
    history = history[-MAX_TURNS:]  # trim old history
    with open(_memory_path(agent_name, user_id), "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

def get_recent_turns(agent_name: str, user_id: str) -> list:
    """Get only recent turn data (same as load)."""
    return load_memory(agent_name, user_id)