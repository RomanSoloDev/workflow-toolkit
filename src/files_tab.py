"""Recent files from Downloads and any other folders you add, newest first.
"""

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QFileInfo, QFileSystemWatcher, QStandardPaths, QTimer
from PySide6.QtWidgets import (
    QFileDialog,
    QFileIconProvider,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from file_list import PATH_ROLE, DraggableFileList
from settings import get_setting, set_setting

MAX_FILES = 50
UNFINISHED = {".crdownload", ".part", ".partial", ".download", ".tmp"}

def downloads_folder():
    return QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation)

def is_unfinished(path):
    if path.suffix.lower() in UNFINISHED or path.name.startswith(("~$", ".")):
        return True
    return any(path.with_name(path.name + ext).exists() for ext in (".part", ".crdownload"))

def arrived_at(path):
    info = path.stat()
    created = getattr(info, "st_birthtime", info.st_ctime)
    return max(info.st_mtime, created)

def recent_files(folders):
    found = []
    for folder in folders:
        try:
            entries = list(Path(folder).iterdir())
        except OSError:
            continue
        for path in entries:
            try:
                if path.is_file() and not is_unfinished(path):
                    found.append((arrived_at(path), path))
            except OSError:
                continue
    found.sort(reverse=True)
    return found[:MAX_FILES]

def friendly_time(timestamp):
    when = datetime.fromtimestamp(timestamp)
    days_ago = (datetime.now().date() - when.date()).days
    if days_ago == 0:
        return f"Today {when:%H:%M}"
    if days_ago == 1:
        return f"Yesterday {when:%H:%M}"
    if days_ago < 7:
        return f"{when:%a %H:%M}"
    return f"{when:%d %b %H:%M}"

class FilesTab(QWidget):
    def __init__(self):
        super().__init__()
        self.icons = QFileIconProvider()
        self.folders = get_setting("watched_folders", [downloads_folder()])

        add_button = QPushButton("Add folder")
        remove_button = QPushButton("Remove folder")
        add_button.clicked.connect(self.add_folder)
        remove_button.clicked.connect(self.remove_folder)
        buttons = QHBoxLayout()
        buttons.addWidget(add_button)
        buttons.addWidget(remove_button)

        self.folders_label = QLabel()
        self.folders_label.setWordWrap(True)
        self.file_list = DraggableFileList()

        layout = QVBoxLayout(self)
        layout.addLayout(buttons)
        layout.addWidget(self.folders_label)
        layout.addWidget(self.file_list)
        layout.addWidget(QLabel("Drag a file out to upload it. Right-click for more options."))

        self.rescan_timer = QTimer(self)
        self.rescan_timer.setSingleShot(True)
        self.rescan_timer.setInterval(500)
        self.rescan_timer.timeout.connect(self.reload)

        self.watcher = QFileSystemWatcher(self)
        self.watcher.directoryChanged.connect(lambda _folder: self.rescan_timer.start())

        self.watch_folders()
        self.reload()

    def showEvent(self, event):
        super().showEvent(event)
        self.reload()

    def watch_folders(self):
        if self.watcher.directories():
            self.watcher.removePaths(self.watcher.directories())
        existing = [folder for folder in self.folders if Path(folder).is_dir()]
        if existing:
            self.watcher.addPaths(existing)
        if self.folders:
            names = ", ".join(Path(folder).name or folder for folder in self.folders)
            self.folders_label.setText(f"Watching: {names}")
        else:
            self.folders_label.setText("Not watching any folders")

    def reload(self):
        self.file_list.clear()
        for arrived, path in recent_files(self.folders):
            when = friendly_time(arrived)
            icon = self.icons.icon(QFileInfo(str(path)))
            item = QListWidgetItem(icon, f"{path.name}\n{path.parent.name}, {when}")
            item.setData(PATH_ROLE, str(path))
            item.setToolTip(str(path))
            self.file_list.addItem(item)

    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Watch a folder")
        if folder and folder not in self.folders:
            self.folders.append(folder)
            self.save_folders()

    def remove_folder(self):
        if not self.folders:
            return
        folder, ok = QInputDialog.getItem(
            self, "Stop watching", "Folder:", self.folders, 0, False
        )
        if ok:
            self.folders.remove(folder)
            self.save_folders()

    def save_folders(self):
        set_setting("watched_folders", self.folders)
        self.watch_folders()
        self.reload()