import re

def clean_input(msg: str) -> str:
    msg = msg.replace("@", "")
    msg = re.sub(r"[`_~|<>]", "", msg)
    msg = re.sub(r"https?://\S+", "[link]", msg)
    return msg.strip()

def sanitize_output(text: str) -> str:
    text = text.replace("@", "")
    text = text.replace("<@", "[user]")
    text = text.replace("@everyone", "[everyone]")
    text = text.replace("@here", "[here]")
    text = re.sub(r"[`_~|<>]", "", text)
    return text