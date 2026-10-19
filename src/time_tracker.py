"""Time tracking logic, kept separate from the UI.

A session is one block of work (Session 1, Session 2...). Each stretch between
a start/resume and a pause/stop is a segment. A sessions total is the sum of
its segments, minus any idle time the user chose to remove."""
import time

import database

HEARTBEAT_SECONDS = 1

class TimeTracker:
    def __init__(self, conn=None):
        self.conn = conn if conn is not None else database.connect()
        self.session_id = None
        self.segment_id = None
        self.segment_start = None
        self.banked = 0.0
        self.removed = 0.0
        self.idle_id = None
        self.idle_start = None
        self.recovered = False
        self._load_open_session()

    @property
    def is_running(self):
        return self.segment_id is not None

    @property
    def is_paused(self):
        return self.session_id is not None and self.segment_id is None

    @property
    def is_idle(self):
        return self.idle_id is not None

    def elapsed(self):
        """Counted seconds in the current session, including the running segment."""
        total = self.banked - self.removed
        if self.is_running:
            total += time.time() - self.segment_start
        return max(total, 0.0)

    def start(self):
        if self.session_id is not None:
            return
        now = time.time()
        cur = self.conn.execute("INSERT INTO sessions (started_at) VALUES (?)", (now,))
        self.session_id = cur.lastrowid
        self.banked = 0.0
        self.removed = 0.0
        self._open_segment(now)

    def pause(self):
        if self.is_running:
            now = time.time()
            self._close_idle(now)
            self._close_segment(now)

    def resume(self):
        if self.is_paused:
            self._open_segment(time.time())

    def stop(self):
        if self.session_id is None:
            return
        now = time.time()
        if self.is_running:
            self._close_idle(now)
            self._close_segment(now)
        self.conn.execute(
            "UPDATE sessions SET ended_at = ? WHERE id = ?", (now, self.session_id)
        )
        self.session_id = None
        self.banked = 0.0
        self.removed = 0.0

    def heartbeat(self):
        """Record that the timer is still running, for crash recovery."""
        if self.is_running:
            self.conn.execute(
                "UPDATE segments SET last_seen = ? WHERE id = ?",
                (time.time(), self.segment_id),
            )

    def begin_idle(self, started_at):
        """The user went idle at started_at. The timer keeps running."""
        if not self.is_running or self.is_idle:
            return
        started_at = max(started_at, self.segment_start)
        cur = self.conn.execute(
            "INSERT INTO idle_periods (session_id, started_at) VALUES (?, ?)",
            (self.session_id, started_at),
        )
        self.idle_id = cur.lastrowid
        self.idle_start = started_at

    def end_idle(self, ended_at):
        """The user is back. Returns the idle period's id so it can be reviewed."""
        idle_id = self.idle_id
        self._close_idle(ended_at)
        return idle_id

    def add_gap(self, started_at, ended_at):
        """Record time the app couldn't watch, e.g. while the PC was asleep."""
        if not self.is_running:
            return None
        started_at = max(started_at, self.segment_start)
        if ended_at <= started_at:
            return None
        cur = self.conn.execute(
            "INSERT INTO idle_periods (session_id, started_at, ended_at) VALUES (?, ?, ?)",
            (self.session_id, started_at, ended_at),
        )
        return cur.lastrowid

    def get_idle_period(self, idle_id):
        """Returns (started_at, ended_at) for one idle period."""
        return self.conn.execute(
            "SELECT started_at, ended_at FROM idle_periods WHERE id = ?", (idle_id,)
        ).fetchone()

    def resolve_idle(self, idle_id, kept_seconds):
        """Save how much of an idle period counted as work."""
        self.conn.execute(
            "UPDATE idle_periods SET kept_seconds = ? WHERE id = ?",
            (kept_seconds, idle_id),
        )
        self._recalculate_removed()

    def _open_segment(self, now):
        cur = self.conn.execute(
            "INSERT INTO segments (session_id, started_at, last_seen) VALUES (?, ?, ?)",
            (self.session_id, now, now),
        )
        self.segment_id = cur.lastrowid
        self.segment_start = now

    def _close_segment(self, now):
        self.conn.execute(
            "UPDATE segments SET ended_at = ?, last_seen = ? WHERE id = ?",
            (now, now, self.segment_id),
        )
        self.banked += now - self.segment_start
        self.segment_id = None
        self.segment_start = None

    def _close_idle(self, ended_at):
        if self.is_idle:
            self.conn.execute(
                "UPDATE idle_periods SET ended_at = ? WHERE id = ?",
                (ended_at, self.idle_id),
            )
            self.idle_id = None
            self.idle_start = None

    def _recalculate_removed(self):
        if self.session_id is None:
            self.removed = 0.0
            return
        (self.removed,) = self.conn.execute(
            "SELECT COALESCE(SUM((ended_at - started_at) - kept_seconds), 0) "
            "FROM idle_periods WHERE session_id = ? "
            "AND ended_at IS NOT NULL AND kept_seconds IS NOT NULL",
            (self.session_id,),
        ).fetchone()

    def _load_open_session(self):
        """Pick up a session that wasn't stopped, e.g. after a crash or restart."""
        row = self.conn.execute(
            "SELECT id FROM sessions WHERE ended_at IS NULL ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if row is None:
            return
        self.session_id = row[0]

        open_segments = self.conn.execute(
            "SELECT id, last_seen, started_at FROM segments "
            "WHERE session_id = ? AND ended_at IS NULL",
            (self.session_id,),
        ).fetchall()
        for seg_id, last_seen, started_at in open_segments:
            self.conn.execute(
                "UPDATE segments SET ended_at = ? WHERE id = ?",
                (last_seen or started_at, seg_id),
            )
            self.recovered = True

        self.conn.execute(
            "UPDATE idle_periods SET ended_at = "
            "(SELECT MAX(ended_at) FROM segments WHERE session_id = ?) "
            "WHERE session_id = ? AND ended_at IS NULL",
            (self.session_id, self.session_id),
        )

        (self.banked,) = self.conn.execute(
            "SELECT COALESCE(SUM(ended_at - started_at), 0) FROM segments WHERE session_id = ?",
            (self.session_id,),
        ).fetchone()
        self._recalculate_removed()