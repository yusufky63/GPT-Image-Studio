from pathlib import Path
import os

APP_NAME = "GPT Image Studio"
APP_VERSION = "1.0.2"
APP_DIR = Path(os.getenv("LOCALAPPDATA", Path.home())) / "GPTImageStudio"
DATA_DIR = APP_DIR / "data"
IMAGE_DIR = Path.home() / "Pictures" / "GPT Image Studio"
DB_PATH = DATA_DIR / "history.db"
SETTINGS_PATH = DATA_DIR / "settings.json"
LOG_PATH = DATA_DIR / "app.log"

API_BASE = "https://api.openai.com/v1"
MODELS = ["gpt-image-2.5-sunburst", "gpt-image-2.5-flare", "gpt-image-2"]
QUALITIES = ["auto", "low", "medium", "high", "xhigh", "max"]
FORMATS = ["png", "jpeg", "webp"]
BACKGROUNDS = ["opaque", "transparent", "auto"]
MODERATION = ["auto", "low"]
ORIENTATIONS = ["Landscape", "Portrait", "Square", "Custom"]
ASPECTS = ["16:9", "21:9", "3:2", "4:3", "1:1", "3:4", "2:3", "9:16", "Custom"]
RESOLUTION_PRESETS = {
    ("Landscape","16:9"): ["3840x2160","2560x1440","2048x1152","1536x864"],
    ("Portrait","9:16"): ["2160x3840","1440x2560","1152x2048","864x1536"],
    ("Landscape","3:2"): ["3072x2048","1536x1024"],
    ("Portrait","2:3"): ["2048x3072","1024x1536"],
    ("Landscape","4:3"): ["3072x2304","2048x1536"],
    ("Portrait","3:4"): ["2304x3072","1536x2048"],
    ("Square","1:1"): ["2048x2048","1024x1024"],
    ("Landscape","21:9"): ["3360x1440","2560x1104"],
}
for p in (APP_DIR, DATA_DIR, IMAGE_DIR): p.mkdir(parents=True, exist_ok=True)
