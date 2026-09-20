import os
import keyring

SERVICE = "GPTImageStudio"

def get_api_key():
    return os.getenv("OPENAI_API_KEY") or keyring.get_password(SERVICE, "openai_api_key")

def save_api_key(value: str):
    value = value.strip()
    if value:
        keyring.set_password(SERVICE, "openai_api_key", value)

def delete_api_key():
    try:
        keyring.delete_password(SERVICE, "openai_api_key")
    except Exception:
        pass
