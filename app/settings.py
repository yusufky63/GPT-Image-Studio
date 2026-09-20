import json
from .config import SETTINGS_PATH
DEFAULTS = {
 "model":"gpt-image-2.5-sunburst","quality":"high","size":"3840x2160","format":"png",
 "background":"opaque","moderation":"auto","partial_images":2,"timeout_seconds":900,
 "cost_limit_usd":0.0,"orientation":"Landscape","aspect":"16:9","compression":90,"output_folder":"",
}
def load_settings():
    if not SETTINGS_PATH.exists(): return DEFAULTS.copy()
    try: return {**DEFAULTS, **json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))}
    except Exception: return DEFAULTS.copy()
def save_settings(data):
    SETTINGS_PATH.parent.mkdir(parents=True,exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(data,indent=2),encoding="utf-8")
