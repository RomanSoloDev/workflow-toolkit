"""Small app settings, saved as JSON in AppData."""

import json

from paths import DATA_DIR

SETTINGS_PATH = DATA_DIR / "settings.json"

def load_settings():
    try:
        return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def get_setting(key, default=None):
    return load_settings().get(key, default)

def set_setting(key, value):
    current = load_settings()
    current[key] = value
    SETTINGS_PATH.write_text(json.dumps(current, indent=2), encoding="utf-8")