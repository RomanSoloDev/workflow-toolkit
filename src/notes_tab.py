"""Notepads for each session, saved automatically as you type.

Notes live in the local database in AppData."""

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from notes_store import (
    create_note,
    delete_note,
    notes_for_session,
    session_ids_with_notes,
    update_note,
)

SAVE_DELAY_MS = 800
NOT_LOADED = "not loaded"
NO_SESSION = -1  # stands in for "no session" in the picker

class NoteEditor(QPlainTextEdit):
    def __init__(self, note_id, title, body):
        super().__init__()
        self.note_id = note_id
        self.title = title
        self.setPlainText(body)

class NotesTab(QWidget):
    def __init__(self, tracker):
        super().__init__()
        self.tracker = tracker
        self.conn = tracker.conn
        self.loaded_session = NOT_LOADED  # the session whose notes are showing
        self.known_current = NOT_LOADED  # the timer's session last time we looked
        self.unsaved = set()

        self.picker = QComboBox()
        self.picker.currentIndexChanged.connect(self.on_picked)
        new_button = QPushButton("New note")
        delete_button = QPushButton("Delete note")
        new_button.clicked.connect(self.new_note)
        delete_button.clicked.connect(self.delete_current)

        top = QHBoxLayout()
        top.addWidget(self.picker)
        top.addStretch()
        top.addWidget(new_button)
        top.addWidget(delete_button)

        self.notepads = QTabWidget()
        self.notepads.setDocumentMode(True)
        self.notepads.tabBarDoubleClicked.connect(self.rename)

        layout = QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(self.notepads)
        layout.addWidget(QLabel("Saved automatically. Double-click a note's name to rename it."))

        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.setInterval(SAVE_DELAY_MS)
        self.save_timer.timeout.connect(self.save_unsaved)

        # Don't lose the last few keystrokes when quitting
        QApplication.instance().aboutToQuit.connect(self.save_unsaved)

    def showEvent(self, event):
        super().showEvent(event)
        current = self.tracker.session_id
        if current != self.known_current:
            self.known_current = current
            self.show_session(current)
        else:
            self.fill_picker(self.loaded_session)

    def fill_picker(self, select):
        current = self.tracker.session_id
        ids = set(session_ids_with_notes(self.conn))
        if current is not None:
            ids.add(current)
        if select not in (None, NOT_LOADED):
            ids.add(select)

        self.picker.blockSignals(True)
        self.picker.clear()
        for session_id in sorted(ids, reverse=True):
            label = f"Session {session_id}"
            if session_id == current:
                label += " (current)"
            self.picker.addItem(label, session_id)
        label = "No session"
        if current is None:
            label += " (current)"
        self.picker.addItem(label, NO_SESSION)

        wanted = NO_SESSION if select is None else select
        for i in range(self.picker.count()):
            if self.picker.itemData(i) == wanted:
                self.picker.setCurrentIndex(i)
                break
        self.picker.blockSignals(False)

    def show_session(self, session_id):
        self.save_unsaved()
        self.fill_picker(session_id)
        self.load(session_id)

    def on_picked(self, index):
        if index < 0:
            return
        data = self.picker.itemData(index)
        session_id = None if data == NO_SESSION else data
        if session_id != self.loaded_session:
            self.save_unsaved()
            self.load(session_id)

    def load(self, session_id):
        old_editors = [self.notepads.widget(i) for i in range(self.notepads.count())]
        self.notepads.clear()
        for editor in old_editors:
            editor.deleteLater()

        self.loaded_session = session_id
        notes = notes_for_session(self.conn, session_id)
        for note_id, title, body in notes:
            self.add_notepad(note_id, title, body)
        if not notes:
            self.add_notepad(None, "Note 1", "")

    def add_notepad(self, note_id, title, body):
        editor = NoteEditor(note_id, title, body)
        editor.textChanged.connect(lambda: self.mark_unsaved(editor))
        return self.notepads.addTab(editor, title)

    def mark_unsaved(self, editor):
        self.unsaved.add(editor)
        self.save_timer.start()

    def save_unsaved(self):
        for editor in self.unsaved:
            body = editor.toPlainText()
            if editor.note_id is None:
                # Only create a note once there's something in it
                if body.strip():
                    editor.note_id = create_note(self.conn, self.loaded_session, editor.title, body)
            else:
                update_note(self.conn, editor.note_id, editor.title, body)
        self.unsaved.clear()

    def new_note(self):
        index = self.add_notepad(None, f"Note {self.notepads.count() + 1}", "")
        self.notepads.setCurrentIndex(index)
        self.notepads.widget(index).setFocus()

    def rename(self, index):
        if index < 0:
            return
        editor = self.notepads.widget(index)
        title, ok = QInputDialog.getText(
            self, "Rename note", "Name:", QLineEdit.EchoMode.Normal, editor.title
        )
        if ok and title.strip():
            editor.title = title.strip()
            self.notepads.setTabText(index, editor.title)
            self.mark_unsaved(editor)

    def delete_current(self):
        index = self.notepads.currentIndex()
        if index < 0:
            return
        editor = self.notepads.widget(index)
        if editor.toPlainText().strip():
            answer = QMessageBox.question(
                self, "Delete note", f"Delete '{editor.title}'? This can't be undone."
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        if editor.note_id is not None:
            delete_note(self.conn, editor.note_id)
        self.unsaved.discard(editor)
        self.notepads.removeTab(index)
        editor.deleteLater()
        if self.notepads.count() == 0:
            self.add_notepad(None, "Note 1", "")