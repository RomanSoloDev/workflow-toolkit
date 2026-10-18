"""Where the app keeps its data.

Everything is stored in AppData, to avoid NDA breaches"""
import os
from pathlib import Path

DATA_DIR = Path(os.environ.get("APPDATA", Path.home())) / "WorkflowToolkit"
SCREENSHOTS_DIR = DATA_DIR / "screenshots"
NOTES_DIR = DATA_DIR / "notes"
DB_PATH = DATA_DIR / "toolkit.db"

def ensure_data_dirs():
    """Create the data folders if they dont exist yet."""
    for folder in (DATA_DIR, SCREENSHOTS_DIR, NOTES_DIR):
        folder.mkdir(parents=True, exist_ok=True)