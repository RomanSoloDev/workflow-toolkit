import os

from PySide6.QtCore import QMimeData, QSize, Qt, QTimer, QUrl
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QListView,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from screenshot_capture import (
    RegionSelector,
    Toast,
    grab_screen,
    save_screenshot,
    screen_under_cursor,
    session_folder,
)
from settings import get_setting

HIDE_DELAY_MS = 250

class ScreenshotList(QListWidget):
    def __init__(self):
        super().__init__()
        self.setViewMode(QListView.ViewMode.IconMode)
        self.setIconSize(QSize(120, 80))
        self.setResizeMode(QListView.ResizeMode.Adjust)
        self.setMovement(QListView.Movement.Static)
        self.setSpacing(6)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragOnly)
        self.itemDoubleClicked.connect(self.open_item)

    def load(self, folder):
        self.clear()
        for path in sorted(folder.glob("*.png"), reverse=True):
            time_text = path.stem[11:19].replace("-", ":")
            item = QListWidgetItem(QIcon(str(path)), time_text)
            item.setData(Qt.ItemDataRole.UserRole, str(path))
            item.setToolTip(path.name)
            self.addItem(item)

    def mimeData(self, items):
        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile(item.data(Qt.ItemDataRole.UserRole)) for item in items])
        return mime

    def supportedDropActions(self):
        return Qt.DropAction.CopyAction

    def open_item(self, item):
        os.startfile(item.data(Qt.ItemDataRole.UserRole))

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
        self.screenshot_list = ScreenshotList()

        full_key = get_setting("full_screen_key", "F")
        region_key = get_setting("region_key", "R")
        shortcuts_text = f"Shortcuts: Ctrl+Alt+{full_key} full screen, Ctrl+Alt+{region_key} region"

        layout = QVBoxLayout(self)
        layout.addLayout(buttons)
        layout.addWidget(QLabel(shortcuts_text))
        layout.addWidget(self.folder_label)
        layout.addWidget(self.screenshot_list)
        layout.addWidget(QLabel("Drag a screenshot out to upload it. Double-click to open."))

    def showEvent(self, event):
        super().showEvent(event)
        self.reload()

    def current_folder(self):
        return session_folder(self.tracker.session_id)

    def reload(self):
        folder = self.current_folder()
        self.folder_label.setText(f"Saving to: {folder.name}")
        self.screenshot_list.load(folder)

    def capture(self, region):
        # Ignore a second press while a region is still being picked
        if self.selector is not None and self.selector.isVisible():
            return
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
        save_screenshot(pixmap, self.tracker.session_id)
        self.reload()
        self.toast = Toast("Screenshot saved and copied", screen)

    def open_folder(self):
        os.startfile(self.current_folder())