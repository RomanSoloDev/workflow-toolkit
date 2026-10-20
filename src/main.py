import sys

from PySide6.QtWidgets import QApplication

from hotkeys import MOD_ALT, MOD_CONTROL, HotkeyManager
from main_window import MainWindow
from paths import ensure_data_dirs
from tray import TrayIcon

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Workflow Toolkit")
    # Keep running in the tray when the window is hidden
    app.setQuitOnLastWindowClosed(False)

    ensure_data_dirs()

    window = MainWindow()
    tray = TrayIcon(window)
    tray.show()

    hotkeys = HotkeyManager(app)
    shots = window.screenshots_tab
    full_ok = hotkeys.register(MOD_CONTROL | MOD_ALT, "F", lambda: shots.capture(region=False))
    region_ok = hotkeys.register(MOD_CONTROL | MOD_ALT, "R", lambda: shots.capture(region=True))
    if not (full_ok and region_ok):
        tray.showMessage("Workflow Toolkit", "A screenshot shortcut is already in use by another app.")
    app.aboutToQuit.connect(hotkeys.unregister_all)

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()