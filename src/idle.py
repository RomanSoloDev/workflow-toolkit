"""Detects when the user has stopped using the mouse and keyboard."""

import ctypes
import time
from ctypes import wintypes

from PySide6.QtCore import QObject, QTimer, Signal

IDLE_THRESHOLD_SECONDS = 60 * 5
CHECK_EVERY_MS = 1000
SLEEP_GAP_SECONDS = 60
class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]

_user32 = ctypes.windll.user32
_kernel32 = ctypes.windll.kernel32
_kernel32.GetTickCount.restype = wintypes.DWORD


def read_last_input():
    """Returns (seconds since last input, Windows' tick count at that input)."""
    info = LASTINPUTINFO()
    info.cbSize = ctypes.sizeof(info)
    if not _user32.GetLastInputInfo(ctypes.byref(info)):
        return 0.0, None
    millis = (_kernel32.GetTickCount() - info.dwTime) & 0xFFFFFFFF
    return millis / 1000.0, info.dwTime

class IdleMonitor(QObject):
    user_returned = Signal(int)

    def __init__(self, tracker, parent=None):
        super().__init__(parent)
        self.tracker = tracker
        self.last_check = time.time()
        self.idle_input_tick = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check)
        self.timer.start(CHECK_EVERY_MS)

    def check(self):
        now = time.time()
        gap = now - self.last_check
        self.last_check = now

        if not self.tracker.is_running:
            return

        idle_for, input_tick = read_last_input()
        last_input_at = now - idle_for

        if self.tracker.is_idle:
            if input_tick != self.idle_input_tick:
                idle_id = self.tracker.end_idle(last_input_at)
                self.user_returned.emit(idle_id)
            return

        if gap > SLEEP_GAP_SECONDS:
            asleep_from = now - gap
            if last_input_at > asleep_from:
                idle_id = self.tracker.add_gap(asleep_from, last_input_at)
                if idle_id is not None:
                    self.user_returned.emit(idle_id)
            else:
                self.start_idle(last_input_at, input_tick)
            return

        if idle_for >= IDLE_THRESHOLD_SECONDS:
            self.start_idle(last_input_at, input_tick)

    def start_idle(self, started_at, input_tick):
        self.tracker.begin_idle(started_at)
        self.idle_input_tick = input_tick