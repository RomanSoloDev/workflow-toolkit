"""Session history: worked time per session, daily and weekly totals, CSV export.

A session's worked time is the total of its segments minus any idle time the
user chose to remove.
"""

import csv
import time
from dataclasses import dataclass
from datetime import datetime, timedelta

SESSION_QUERY = """
SELECT
    s.id,
    s.started_at,
    s.ended_at,
    COALESCE((
        SELECT SUM(COALESCE(g.ended_at, :now) - g.started_at)
        FROM segments g WHERE g.session_id = s.id
    ), 0) AS segment_total,
    COALESCE((
        SELECT SUM((i.ended_at - i.started_at) - i.kept_seconds)
        FROM idle_periods i
        WHERE i.session_id = s.id
          AND i.ended_at IS NOT NULL AND i.kept_seconds IS NOT NULL
    ), 0) AS removed,
    (
        SELECT COUNT(*) FROM idle_periods i
        WHERE i.session_id = s.id
          AND i.ended_at IS NOT NULL AND i.kept_seconds IS NULL
    ) AS undecided
FROM sessions s
WHERE s.started_at >= :since
ORDER BY s.id DESC
"""

@dataclass
class SessionSummary:
    number: int
    started_at: float
    ended_at: float | None
    worked: float
    removed: float
    undecided: int

def format_hms(seconds):
    seconds = int(seconds)
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    return f"{hours:02}:{minutes:02}:{secs:02}"

def get_sessions(conn, since=0.0):
    """All sessions started since the given timestamp, newest first."""
    rows = conn.execute(SESSION_QUERY, {"now": time.time(), "since": since}).fetchall()
    return [
        SessionSummary(number, started, ended, max(segments - removed, 0.0), removed, undecided)
        for number, started, ended, segments, removed, undecided in rows
    ]


def start_of_today():
    return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

def today_total(conn):
    since = start_of_today().timestamp()
    return sum(s.worked for s in get_sessions(conn, since))

def week_total(conn):
    today = start_of_today()
    monday = today - timedelta(days=today.weekday())
    return sum(s.worked for s in get_sessions(conn, monday.timestamp()))

def undecided_idle_periods(conn):
    """Idle periods where the popup was closed without choosing, oldest first."""
    return conn.execute(
        "SELECT id, session_id, started_at, ended_at FROM idle_periods "
        "WHERE ended_at IS NOT NULL AND kept_seconds IS NULL ORDER BY started_at"
    ).fetchall()

def export_csv(conn, path):
    """Save every session to a CSV file, oldest first."""
    sessions = list(reversed(get_sessions(conn)))
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Session", "Date", "Start", "End", "Worked",
            "Worked (seconds)", "Idle removed (seconds)", "Idle to review",
        ])
        for s in sessions:
            start = datetime.fromtimestamp(s.started_at)
            if s.ended_at:
                end = datetime.fromtimestamp(s.ended_at).strftime("%Y-%m-%d %H:%M:%S")
            else:
                end = "running"
            writer.writerow([
                s.number,
                start.strftime("%Y-%m-%d"),
                start.strftime("%Y-%m-%d %H:%M:%S"),
                end,
                format_hms(s.worked),
                round(s.worked, 2),
                round(s.removed, 2),
                s.undecided,
            ])