import requests
import utils.config as config  # Replace with your actual config import

def build_context(prompt_template: str, user_input: str, history: list) -> str:
    """
    Builds the full prompt by injecting previous conversation history and user input.
    
    Args:
        prompt_template (str): Template string with a `{{user_input}}` placeholder.
        user_input (str): The latest user input.
        history (list): List of dicts containing past turns. Each dict should have:
                        {"user": str, "bot": str}
    
    Returns:
        str: Prompt with conversation history and current user input.
    """
    history_text = ""
    for turn in history:
        history_text += f'User: "{turn["user"]}"\nBot: "{turn["bot"]}"\n'

    # Insert the new user input into the prompt template
    return prompt_template.replace("{{user_input}}", f'{history_text}User: """\n{user_input}\n"""')


def get_response(prompt: str) -> str:
    """
    Sends a prompt to the configured model endpoint and returns the response.
    
    Args:
        prompt (str): The prompt string to send to the model.
    
    Returns:
        str: The model's response text.
    """
    response = requests.post(config.OLLAMA_URL, json={
        "model": config.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    })
    response.raise_for_status()
    result = response.json()
    return result.get("response", "").strip()