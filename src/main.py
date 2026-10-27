import sys

from PySide6.QtWidgets import QApplication

from dock import DockController
from hotkeys import MOD_ALT, MOD_CONTROL, HotkeyManager
from main_window import MainWindow
from paths import ensure_data_dirs
from settings import get_setting
from tray import TrayIcon

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Workflow Toolkit")
    # Keep running in the tray when the window is hidden
    app.setQuitOnLastWindowClosed(False)

    ensure_data_dirs()

    window = MainWindow()
    dock = DockController(window, window.timer_tab.tracker)
    tray = TrayIcon(window, dock)
    tray.show()

    hotkeys = HotkeyManager(app)
    shots = window.screenshots_tab
    full_key = get_setting("full_screen_key", "F")
    region_key = get_setting("region_key", "R")
    full_ok = hotkeys.register(MOD_CONTROL | MOD_ALT, full_key, lambda: shots.capture(region=False))
    region_ok = hotkeys.register(MOD_CONTROL | MOD_ALT, region_key, lambda: shots.capture(region=True))
    if not (full_ok and region_ok):
        tray.showMessage("Workflow Toolkit", "A screenshot shortcut is already in use by another app.")
    app.aboutToQuit.connect(hotkeys.unregister_all)

    if get_setting("docked_mode", False):
        dock.set_enabled(True)
    elif "--tray" not in sys.argv:
        window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()