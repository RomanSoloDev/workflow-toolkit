"""System-wide keyboard shortcuts using Windows' RegisterHotKey.
"""

import ctypes
from ctypes import wintypes

from PySide6.QtCore import QAbstractNativeEventFilter

WM_HOTKEY = 0x0312
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_NOREPEAT = 0x4000  # holding the keys down doesn't fire it over and over

_user32 = ctypes.windll.user32


class HotkeyManager(QAbstractNativeEventFilter):
    def __init__(self, app):
        super().__init__()
        self.callbacks = {}
        self.next_id = 1
        app.installNativeEventFilter(self)

    def register(self, modifiers, key, callback):
        hotkey_id = self.next_id
        self.next_id += 1
        ok = _user32.RegisterHotKey(None, hotkey_id, modifiers | MOD_NOREPEAT, ord(key.upper()))
        if ok:
            self.callbacks[hotkey_id] = callback
        return bool(ok)

    def unregister_all(self):
        for hotkey_id in self.callbacks:
            _user32.UnregisterHotKey(None, hotkey_id)
        self.callbacks.clear()

    def nativeEventFilter(self, event_type, message):
        if bytes(event_type) in (b"windows_generic_MSG", b"windows_dispatcher_MSG"):
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == WM_HOTKEY and msg.wParam in self.callbacks:
                self.callbacks[msg.wParam]()
                return True, 0
        return False, 0