import os
import sys
from pathlib import Path

DATA_DIR = Path(os.environ.get("APPDATA", Path.home())) / "WorkflowToolkit"
SCREENSHOTS_DIR = DATA_DIR / "screenshots"
NOTES_DIR = DATA_DIR / "notes"
DB_PATH = DATA_DIR / "toolkit.db"

APP_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
ICON_PATH = APP_DIR / "assets" / "icon.png"

def ensure_data_dirs():
    for folder in (DATA_DIR, SCREENSHOTS_DIR, NOTES_DIR):
        folder.mkdir(parents=True, exist_ok=True)