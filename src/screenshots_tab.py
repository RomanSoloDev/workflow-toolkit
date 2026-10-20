import os

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from screenshot_capture import (
    RegionSelector,
    Toast,
    grab_screen,
    save_screenshot,
    screen_under_cursor,
    session_folder,
)

HIDE_DELAY_MS = 250

class ScreenshotsTab(QWidget):
    def __init__(self, tracker):
        super().__init__()
        self.tracker = tracker
        self.selector = None
        self.toast = None
        self.window_was_visible = False

        full_button = QPushButton("Full screen")
        region_button = QPushButton("Region")
        open_button = QPushButton("Open folder")
        full_button.clicked.connect(lambda: self.capture(region=False))
        region_button.clicked.connect(lambda: self.capture(region=True))
        open_button.clicked.connect(self.open_folder)

        buttons = QHBoxLayout()
        buttons.addWidget(full_button)
        buttons.addWidget(region_button)
        buttons.addWidget(open_button)

        self.folder_label = QLabel()
        self.last_label = QLabel("No screenshots yet")
        self.last_label.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.addLayout(buttons)
        layout.addWidget(self.folder_label)
        layout.addWidget(self.last_label)
        layout.addStretch()

    def showEvent(self, event):
        super().showEvent(event)
        self.update_folder_label()

    def current_folder(self):
        return session_folder(self.tracker.session_id)

    def update_folder_label(self):
        self.folder_label.setText(f"Saving to: {self.current_folder().name}")

    def capture(self, region):
        window = self.window()
        self.window_was_visible = window.isVisible()
        window.hide()
        QTimer.singleShot(HIDE_DELAY_MS, lambda: self.grab(region))

    def grab(self, region):
        screen = screen_under_cursor()
        if region:
            self.selector = RegionSelector(screen)
            self.selector.selected.connect(lambda pixmap: self.finish(pixmap, screen))
            self.selector.cancelled.connect(lambda: self.finish(None, screen))
        else:
            self.finish(grab_screen(screen), screen)

    def finish(self, pixmap, screen):
        if self.window_was_visible:
            self.window().show()
        if pixmap is None:
            return
        path = save_screenshot(pixmap, self.tracker.session_id)
        self.last_label.setText(f"Last saved: {path.name}")
        self.update_folder_label()
        self.toast = Toast("Screenshot saved and copied", screen)

    def open_folder(self):
        os.startfile(self.current_folder())