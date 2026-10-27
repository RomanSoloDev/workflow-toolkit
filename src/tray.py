from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QMenu, QStyle, QSystemTrayIcon

from settings import get_setting

class TrayIcon(QSystemTrayIcon):
    def __init__(self, main_window, dock):
        icon = QApplication.windowIcon()
        if icon.isNull():
            icon = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        super().__init__(icon)
        self.main_window = main_window
        self.setToolTip("Workflow Toolkit")

        self.menu = QMenu()

        show_action = QAction("Show / Hide", self.menu)
        show_action.triggered.connect(self.toggle_window)
        self.menu.addAction(show_action)

        on_top_action = QAction("Always on top", self.menu)
        on_top_action.setCheckable(True)
        on_top_action.setChecked(True)
        on_top_action.toggled.connect(main_window.set_always_on_top)
        self.menu.addAction(on_top_action)

        dock_action = QAction("Docked mode", self.menu)
        dock_action.setCheckable(True)
        dock_action.setChecked(get_setting("docked_mode", False))
        dock_action.toggled.connect(dock.set_enabled)
        self.menu.addAction(dock_action)

        self.menu.addSeparator()

        quit_action = QAction("Quit", self.menu)
        quit_action.triggered.connect(QApplication.instance().quit)
        self.menu.addAction(quit_action)

        self.setContextMenu(self.menu)
        self.activated.connect(self.on_click)

    def toggle_window(self):
        if self.main_window.isVisible():
            self.main_window.hide()
        else:
            self.main_window.show()
            self.main_window.raise_()
            self.main_window.activateWindow()

    def on_click(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.toggle_window()