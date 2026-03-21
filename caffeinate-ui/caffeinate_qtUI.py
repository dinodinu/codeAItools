#!/usr/bin/env python3
"""
Caffeinate UI — Native macOS process viewer (PyQt5).
Select a running process and caffeinate it to keep the Mac awake.
"""

import signal
import subprocess
import sys

from PyQt5.QtCore import Qt, QTimer, QSortFilterProxyModel
from PyQt5.QtGui import QIcon, QStandardItemModel, QStandardItem, QKeySequence
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTreeView, QLabel, QHeaderView, QMessageBox,
    QAbstractItemView, QShortcut,
)

HEADERS = ["PID", "PPID", "Command"]
COL_PID, COL_PPID, COL_CMD = range(len(HEADERS))
_RIGHT = Qt.AlignRight | Qt.AlignVCenter

STYLESHEET = """
    QMainWindow { background: #1e1e1e; }
    QWidget { background: #1e1e1e; color: #e5e5e5; font-size: 13px; }
    QLineEdit {
        background: #2a2a2a; border: 1px solid #3d3d3d; border-radius: 6px;
        padding: 5px 8px; color: #e5e5e5;
    }
    QLineEdit:focus { border-color: #0a84ff; }
    QPushButton {
        background: #323232; color: #e5e5e5; border: 1px solid #3d3d3d;
        border-radius: 6px; padding: 6px 14px; font-weight: 600;
    }
    QPushButton:hover { background: #3a3a3a; }
    QPushButton:disabled { background: #282828; color: #5a5a5a; }
    QTreeView {
        background: #252525; alternate-background-color: #2a2a2a;
        border: 1px solid #3d3d3d; border-radius: 6px;
        selection-background-color: rgba(10,132,255,0.3);
        selection-color: #e5e5e5;
    }
    QTreeView::item { padding: 2px 0; }
    QHeaderView::section {
        background: #1e1e1e; color: #98989d; border: none;
        border-bottom: 1px solid #3d3d3d; padding: 6px 8px; font-weight: 600;
    }
    QScrollBar:vertical {
        background: transparent; width: 8px; margin: 0;
    }
    QScrollBar::handle:vertical {
        background: rgba(255,255,255,0.25); border-radius: 4px; min-height: 20px;
    }
    QScrollBar::handle:vertical:hover { background: rgba(255,255,255,0.4); }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        background: transparent; height: 0; width: 0;
    }
    QScrollBar:horizontal {
        background: transparent; height: 8px; margin: 0;
    }
    QScrollBar::handle:horizontal {
        background: rgba(255,255,255,0.25); border-radius: 4px; min-width: 20px;
    }
    QScrollBar::handle:horizontal:hover { background: rgba(255,255,255,0.4); }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
        background: transparent; height: 0; width: 0;
    }
    QLabel { color: #98989d; }
"""


def _parse_ps():
    """Run ps and return [(pid, ppid, command)] for /Applications/ processes."""
    result = subprocess.run(
        ["ps", "-eo", "pid,ppid,command"], capture_output=True, text=True,
    )
    procs = []
    for line in result.stdout.strip().splitlines()[1:]:
        parts = line.split(None, 2)
        if len(parts) >= 3 and parts[2].startswith("/Applications/"):
            procs.append((int(parts[0]), int(parts[1]), parts[2]))
    return procs


def _num_item(value):
    """Create a right-aligned QStandardItem for a numeric value."""
    item = QStandardItem(str(value))
    item.setData(value, Qt.UserRole)
    item.setTextAlignment(_RIGHT)
    return item


class CaffeinateUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mini Process Viewer")
        self.resize(900, 580)
        self.setMinimumSize(640, 360)
        self.setStyleSheet(STYLESHEET)

        self.caffeinate_proc = None
        self.tracked_pid = None
        self.tracked_cmd = None

        self._build_ui()
        self._refresh()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll_caffeinate)
        self._timer.start(2000)

        QShortcut(QKeySequence(Qt.Key_Escape), self, activated=self.close)

    # -- UI ---------------------------------------------------------------

    @staticmethod
    def _make_button(text, callback, *, enabled=True, tooltip=None):
        btn = QPushButton(text)
        btn.setEnabled(enabled)
        btn.clicked.connect(callback)
        if tooltip:
            btn.setToolTip(tooltip)
        return btn

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 6)

        # Toolbar
        toolbar = QHBoxLayout()

        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Filter processes\u2026")
        self.filter_edit.setClearButtonEnabled(True)
        self.filter_edit.textChanged.connect(self._apply_filter)
        toolbar.addWidget(self.filter_edit, 1)

        self.btn_refresh = self._make_button("\u21bb Refresh", self._refresh)
        self.btn_caff = self._make_button(
            "\u2615 Caffeinate", self._caffeinate_selected, enabled=False,
        )
        self.btn_kill = self._make_button(
            "\u2715 Kill Process", self._kill_selected, enabled=False,
        )
        self.btn_retry = self._make_button(
            "\u21ba Retry", self._retry_caffeinate,
            enabled=False, tooltip="Retry caffeinating the last tracked process",
        )
        for btn in (self.btn_refresh, self.btn_caff, self.btn_kill, self.btn_retry):
            toolbar.addWidget(btn)

        layout.addLayout(toolbar)

        # Model / proxy
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(HEADERS)

        self.proxy = QSortFilterProxyModel()
        self.proxy.setSourceModel(self.model)
        self.proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy.setFilterKeyColumn(-1)
        self.proxy.setRecursiveFilteringEnabled(True)

        # Tree view
        self.tree = QTreeView()
        self.tree.setModel(self.proxy)
        self.tree.setRootIsDecorated(True)
        self.tree.setAlternatingRowColors(True)
        self.tree.setSortingEnabled(True)
        self.tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tree.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tree.selectionModel().selectionChanged.connect(self._on_selection)
        self.tree.selectionModel().currentChanged.connect(self._pin_current_column)
        self.tree.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tree.header().setStretchLastSection(True)
        self.tree.header().setSectionResizeMode(QHeaderView.Interactive)
        self.tree.header().setSectionResizeMode(COL_CMD, QHeaderView.Stretch)

        layout.addWidget(self.tree, 1)

        # Status bar
        self.status_label = QLabel("No process being caffeinated.")
        layout.addWidget(self.status_label)

    # -- Process loading --------------------------------------------------

    def _refresh(self):
        parsed = _parse_ps()

        self.tree.setSortingEnabled(False)
        self.model.clear()
        self.model.setHorizontalHeaderLabels(HEADERS)

        rows = {}
        for pid, ppid, cmd in parsed:
            rows[pid] = (ppid, [_num_item(pid), _num_item(ppid), QStandardItem(cmd)])

        for pid, (ppid, row) in rows.items():
            parent = rows.get(ppid)
            (parent[1][0] if parent else self.model).appendRow(row)

        self.tree.setSortingEnabled(True)
        self.proxy.sort(COL_CMD, Qt.AscendingOrder)
        self.tree.collapseAll()
        if self.proxy.rowCount():
            self.tree.expand(self.proxy.index(0, 0))
        for col in (COL_PID, COL_PPID):
            self.tree.resizeColumnToContents(col)

    def _apply_filter(self, text):
        self.proxy.setFilterFixedString(text)

    def _on_selection(self):
        count = len(self.tree.selectionModel().selectedRows())
        self.btn_caff.setEnabled(count == 1)
        self.btn_kill.setEnabled(count >= 1)

    def _pin_current_column(self, current, _previous):
        if current.isValid() and current.column() != 0:
            self.tree.selectionModel().setCurrentIndex(
                current.sibling(current.row(), 0),
                self.tree.selectionModel().NoUpdate,
            )

    # -- Helpers ----------------------------------------------------------

    def _selected_rows(self):
        """Return list of (pid_str, cmd_str) for all selected rows."""
        result = []
        for idx in self.tree.selectionModel().selectedRows():
            src = self.proxy.mapToSource(idx)
            pid_item = self.model.itemFromIndex(src)
            cmd_item = self.model.itemFromIndex(src.sibling(src.row(), COL_CMD))
            if pid_item and cmd_item:
                result.append((str(pid_item.data(Qt.UserRole)), cmd_item.text()))
        return result

    def _set_status(self, text, color="#98989d"):
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {color};")

    def _caffeinate_stderr(self):
        """Read and return stderr from the caffeinate process, or None."""
        if self.caffeinate_proc and self.caffeinate_proc.stderr:
            return self.caffeinate_proc.stderr.read().decode().strip() or None
        return None

    # -- Caffeinate control -----------------------------------------------

    def _caffeinate_selected(self):
        rows = self._selected_rows()
        if rows:
            self._start_caffeinate(*rows[0])

    def _start_caffeinate(self, pid, cmd):
        self._stop_caffeinate(clear_tracked=False)
        self.tracked_pid, self.tracked_cmd = pid, cmd
        self.caffeinate_proc = subprocess.Popen(
            ["caffeinate", "-w", pid],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        )
        self._set_status(
            f"\u2615 Caffeinating PID {pid} "
            f"(caffeinate PID {self.caffeinate_proc.pid})  \u2014  {cmd}",
            "#248c46",
        )
        self.btn_retry.setEnabled(False)
        QTimer.singleShot(500, self._check_caffeinate_start)

    def _check_caffeinate_start(self):
        if self.caffeinate_proc is None:
            return
        rc = self.caffeinate_proc.poll()
        if rc is not None and rc != 0:
            err = self._caffeinate_stderr() or f"exit code {rc}"
            self._set_status(
                f"Caffeinate failed for PID {self.tracked_pid}: {err}", "#ff3b30",
            )
            self.caffeinate_proc = None
            self.btn_retry.setEnabled(True)
        elif rc is None:
            self._refresh()

    def _retry_caffeinate(self):
        if self.tracked_pid and self.tracked_cmd:
            self._start_caffeinate(self.tracked_pid, self.tracked_cmd)

    def _kill_selected(self):
        rows = self._selected_rows()
        if not rows:
            return

        summary = "\n".join(f"PID {pid}: {cmd}" for pid, cmd in rows)
        if QMessageBox.question(
            self, "Kill Process",
            f"Kill {len(rows)} process(es)?\n\n{summary}",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        ) != QMessageBox.Yes:
            return

        killed, failed = [], []
        for pid, _ in rows:
            try:
                subprocess.run(["kill", pid], check=True)
                killed.append(pid)
            except subprocess.CalledProcessError:
                failed.append(pid)

        parts = []
        if killed:
            parts.append(f"Killed: {', '.join(killed)}")
        if failed:
            parts.append(f"Failed: {', '.join(failed)}")
        self._set_status("  |  ".join(parts), "#ff3b30")

        QTimer.singleShot(500, self._refresh)

    def _stop_caffeinate(self, clear_tracked=True):
        if self.caffeinate_proc is not None:
            if self.caffeinate_proc.poll() is None:
                self.caffeinate_proc.send_signal(signal.SIGTERM)
                try:
                    self.caffeinate_proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self.caffeinate_proc.kill()
                    self.caffeinate_proc.wait()
            self.caffeinate_proc = None
        if clear_tracked:
            self.tracked_pid = self.tracked_cmd = None
            self.btn_retry.setEnabled(False)
        self._set_status("No process being caffeinated.")

    def _poll_caffeinate(self):
        if not self.caffeinate_proc or self.caffeinate_proc.poll() is None:
            return
        rc = self.caffeinate_proc.returncode
        err = self._caffeinate_stderr()
        if rc != 0 and err:
            self._set_status(
                f"Caffeinate failed for PID {self.tracked_pid}: {err}", "#ff3b30",
            )
            self.btn_retry.setEnabled(True)
        else:
            self._set_status(
                f"Caffeinate ended \u2014 PID {self.tracked_pid} exited (code {rc}).",
                "#ff9500",
            )
        self.caffeinate_proc = None
        self.tracked_pid = self.tracked_cmd = None

    # -- Cleanup ----------------------------------------------------------

    def closeEvent(self, event):
        self._stop_caffeinate()
        event.accept()


_ACTIVITY_MONITOR_ICON = (
    "/System/Applications/Utilities/Activity Monitor.app"
    "/Contents/Resources/AppIcon.icns"
)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Mini Process Viewer")
    app.setWindowIcon(QIcon(_ACTIVITY_MONITOR_ICON))
    window = CaffeinateUI()
    window.show()
    sys.exit(app.exec_())
