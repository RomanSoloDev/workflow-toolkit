"""Local SQLite database for time tracking. Lives in AppData."""
import sqlite3

from paths import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at REAL NOT NULL,
    ended_at REAL
);

CREATE TABLE IF NOT EXISTS segments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES sessions(id),
    started_at REAL NOT NULL,
    ended_at REAL,
    last_seen REAL
);
"""


def connect():
    #saves every change immediately, so nothing is lost in a crash
    conn = sqlite3.connect(DB_PATH, isolation_level=None)
    conn.executescript(SCHEMA)
    return conn