"""Time tracking logic"""
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
        self.recovered = False
        self._load_open_session()

    @property
    def is_running(self):
        return self.segment_id is not None

    @property
    def is_paused(self):
        return self.session_id is not None and self.segment_id is None

    def elapsed(self):
        total = self.banked
        if self.is_running:
            total += time.time() - self.segment_start
        return total

    def start(self):
        if self.session_id is not None:
            return
        now = time.time()
        cur = self.conn.execute("INSERT INTO sessions (started_at) VALUES (?)", (now,))
        self.session_id = cur.lastrowid
        self.banked = 0.0
        self._open_segment(now)

    def pause(self):
        if self.is_running:
            self._close_segment(time.time())

    def resume(self):
        if self.is_paused:
            self._open_segment(time.time())

    def stop(self):
        if self.session_id is None:
            return
        now = time.time()
        if self.is_running:
            self._close_segment(now)
        self.conn.execute(
            "UPDATE sessions SET ended_at = ? WHERE id = ?", (now, self.session_id)
        )
        self.session_id = None
        self.banked = 0.0

    def heartbeat(self):
        """Record that the timer is still running, for crash recovery."""
        if self.is_running:
            self.conn.execute(
                "UPDATE segments SET last_seen = ? WHERE id = ?",
                (time.time(), self.segment_id),
            )

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

    def _load_open_session(self):
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

        (self.banked,) = self.conn.execute(
            "SELECT COALESCE(SUM(ended_at - started_at), 0) FROM segments WHERE session_id = ?",
            (self.session_id,),
        ).fetchone()