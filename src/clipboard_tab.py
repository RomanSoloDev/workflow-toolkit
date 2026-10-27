"""Recent clipboard text, kept in memory only.

Nothing is written to disk: the history disappears when the app quits, and
Clear empties it straight away.
"""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

MAX_ITEMS = 30
PREVIEW_LENGTH = 80
DEFAULT_STATUS = "Click an item to copy it again. Kept in memory only."

def is_private(mime):
    for fmt in mime.formats():
        if "ExcludeClipboardContentFromMonitorProcessing" in fmt:
            return True
        if "CanIncludeInClipboardHistory" in fmt:
            if not any(bytes(mime.data(fmt))):
                return True
    return False

def preview(text):
    lines = text.strip().splitlines()
    first = lines[0]
    if len(first) > PREVIEW_LENGTH:
        first = first[:PREVIEW_LENGTH] + "..."
    if len(lines) > 1:
        first += f"   (+{len(lines) - 1} more lines)"
    return first

class ClipboardTab(QWidget):
    def __init__(self):
        super().__init__()
        self.clipboard = QGuiApplication.clipboard()
        self.clipboard.dataChanged.connect(self.on_clipboard_changed)

        self.pause_box = QCheckBox("Pause recording")
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.clear)

        top = QHBoxLayout()
        top.addWidget(self.pause_box)
        top.addStretch()
        top.addWidget(clear_button)

        self.history = QListWidget()
        self.history.itemClicked.connect(self.copy_item)
        self.status = QLabel(DEFAULT_STATUS)

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(self.history)
        layout.addWidget(self.status)

    def on_clipboard_changed(self):
        if self.pause_box.isChecked():
            return
        mime = self.clipboard.mimeData()
        if mime is None or not mime.hasText() or is_private(mime):
            return
        text = mime.text()
        if text.strip():
            self.add(text)

    def add(self, text):
        for row in range(self.history.count()):
            if self.history.item(row).data(Qt.ItemDataRole.UserRole) == text:
                self.history.takeItem(row)
                break
        item = QListWidgetItem(preview(text))
        item.setData(Qt.ItemDataRole.UserRole, text)
        item.setToolTip(text[:500])
        self.history.insertItem(0, item)
        while self.history.count() > MAX_ITEMS:
            self.history.takeItem(self.history.count() - 1)

    def copy_item(self, item):
        self.clipboard.setText(item.data(Qt.ItemDataRole.UserRole))
        self.status.setText("Copied. Paste it with Ctrl+V.")
        QTimer.singleShot(2000, lambda: self.status.setText(DEFAULT_STATUS))

    def clear(self):
        self.history.clear()