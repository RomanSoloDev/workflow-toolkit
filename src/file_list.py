"""A list of files you can drag out into other apps."""

import os
import subprocess

from PySide6.QtCore import QMimeData, Qt, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QAbstractItemView, QListWidget, QMenu

PATH_ROLE = Qt.ItemDataRole.UserRole

class DraggableFileList(QListWidget):
    def __init__(self):
        super().__init__()
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragOnly)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_menu)
        self.itemDoubleClicked.connect(lambda item: os.startfile(item.data(PATH_ROLE)))

    def mimeData(self, items):
        mime = QMimeData()
        mime.setUrls([QUrl.fromLocalFile(item.data(PATH_ROLE)) for item in items])
        return mime

    def supportedDropActions(self):
        return Qt.DropAction.CopyAction

    def show_menu(self, position):
        item = self.itemAt(position)
        if item is None:
            return
        path = item.data(PATH_ROLE)
        menu = QMenu(self)
        menu.addAction("Open", lambda: os.startfile(path))
        menu.addAction("Show in folder", lambda: subprocess.Popen(f'explorer /select,"{path}"'))
        menu.addAction("Copy path", lambda: QGuiApplication.clipboard().setText(path))
        menu.exec(self.viewport().mapToGlobal(position))