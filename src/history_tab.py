from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import history
from idle_dialog import IdleDialog

COLUMNS = ["Session", "Date", "Time", "Worked"]

class HistoryTab(QWidget):
    def __init__(self, tracker):
        super().__init__()
        self.tracker = tracker
        self.conn = tracker.conn

        self.today_label = QLabel()
        self.week_label = QLabel()
        totals = QHBoxLayout()
        totals.addWidget(self.today_label)
        totals.addStretch()
        totals.addWidget(self.week_label)

        self.review_button = QPushButton()
        self.review_button.clicked.connect(self.review_idle)
        export_button = QPushButton("Export CSV")
        export_button.clicked.connect(self.export)
        actions = QHBoxLayout()
        actions.addWidget(self.review_button)
        actions.addWidget(export_button)

        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(True)

        layout = QVBoxLayout(self)
        layout.addLayout(totals)
        layout.addLayout(actions)
        layout.addWidget(self.table)

        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_if_visible)
        self.refresh_timer.start(1000)

    def showEvent(self, event):
        super().showEvent(event)
        self.reload()

    def refresh_if_visible(self):
        if self.isVisible():
            self.reload()

    def reload(self):
        today = history.format_hms(history.today_total(self.conn))
        week = history.format_hms(history.week_total(self.conn))
        self.today_label.setText(f"Today: <b>{today}</b>")
        self.week_label.setText(f"This week: <b>{week}</b>")

        count = len(history.undecided_idle_periods(self.conn))
        self.review_button.setText(f"Review idle time ({count})")
        self.review_button.setEnabled(count > 0)

        sessions = history.get_sessions(self.conn)
        self.table.setRowCount(len(sessions))
        for row, s in enumerate(sessions):
            start = datetime.fromtimestamp(s.started_at)
            if s.ended_at:
                ended = datetime.fromtimestamp(s.ended_at)
                # Show the day too if the session finished on a different day
                if ended.date() != start.date():
                    end = ended.strftime("%a %H:%M")
                else:
                    end = ended.strftime("%H:%M")
            else:
                end = "now"
            worked = history.format_hms(s.worked)
            if s.undecided:
                worked += " *"
            values = [
                str(s.number),
                start.strftime("%a %d %b"),
                f"{start:%H:%M} to {end}",
                worked,
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                if s.undecided:
                    item.setToolTip("Has idle time waiting for review")
                self.table.setItem(row, col, item)

    def review_idle(self):
        for idle_id, session_id, started_at, ended_at in history.undecided_idle_periods(self.conn):
            dialog = IdleDialog(started_at, ended_at)
            dialog.setWindowTitle(f"Review idle time (Session {session_id})")
            if not dialog.exec():
                break
            self.tracker.resolve_idle(idle_id, dialog.kept)
        self.reload()

    def export(self):
        default_path = Path.home() / "Documents" / f"timesheet-{datetime.now():%Y-%m-%d}.csv"
        path, _ = QFileDialog.getSaveFileName(
            self, "Export sessions", str(default_path), "CSV files (*.csv)"
        )
        if not path:
            return
        history.export_csv(self.conn, path)
        QMessageBox.information(self, "Exported", f"Saved to:\n{path}")