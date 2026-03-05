#!/usr/bin/env python3
"""Qt calendar image viewer for month-folder/day-image structure.

Expected structure:
- jan'26/0101.jpg
- feb'26/0202.jpg
- ...

File naming convention: DDMM.<ext>
"""

from __future__ import annotations

import bisect
from functools import partial
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Dict, List, Tuple

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QImageReader, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCalendarWidget,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

MONTH_MAP = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}


class CalendarRepository:
    FOLDER_RE = re.compile(r"^([a-zA-Z]{3})'(\d{2})$")
    FILE_RE = re.compile(r"^(\d{2})(\d{2}).*\.(jpg|jpeg|png|bmp|webp|gif)$", re.IGNORECASE)

    def __init__(self, root: Path) -> None:
        self.root = root
        self.by_date: Dict[date, List[Path]] = {}
        self._sorted_dates: List[date] = []
        self._load()

    def _load(self) -> None:
        for child in sorted(self.root.iterdir()):
            if not child.is_dir():
                continue

            folder_match = self.FOLDER_RE.match(child.name)
            if not folder_match:
                continue

            month_token = folder_match.group(1).lower()
            if month_token not in MONTH_MAP:
                continue

            month = MONTH_MAP[month_token]
            year = 2000 + int(folder_match.group(2))

            for file_path in sorted(child.iterdir()):
                if not file_path.is_file():
                    continue

                file_match = self.FILE_RE.match(file_path.name)
                if not file_match:
                    continue

                day = int(file_match.group(1))
                month_in_file = int(file_match.group(2))
                if month_in_file != month:
                    # Skip mismatched files if any exist.
                    continue

                try:
                    file_date = date(year, month, day)
                except ValueError:
                    continue

                self.by_date.setdefault(file_date, []).append(file_path)
        self._sorted_dates = sorted(self.by_date)

    @property
    def available_dates(self) -> List[date]:
        return self._sorted_dates

    def has_data(self) -> bool:
        return bool(self.by_date)


class MainWindow(QMainWindow):
    MIN_ZOOM = 0.25
    MAX_ZOOM = 6.0
    ZOOMIN_STEP = 1.25
    ZOOMOUT_STEP = 1/ZOOMIN_STEP


    def __init__(self, repository: CalendarRepository) -> None:
        super().__init__()
        self.repo = repository
        self.dates = repository.available_dates
        self.date_to_index = {d: i for i, d in enumerate(self.dates)}
        self.month_order = sorted({(d.year, d.month) for d in self.dates})
        self.month_to_date_indices: Dict[Tuple[int, int], List[int]] = {}
        # day -> index lookup per month for O(1) same-day match in _move_month
        self.month_day_to_index: Dict[Tuple[int, int], Dict[int, int]] = {}
        for idx, d in enumerate(self.dates):
            key = (d.year, d.month)
            self.month_to_date_indices.setdefault(key, []).append(idx)
            self.month_day_to_index.setdefault(key, {})[d.day] = idx
        self.month_to_order_index = {m: i for i, m in enumerate(self.month_order)}

        self.current_index = self._pick_initial_index()
        self.current_pixmap = QPixmap()
        self.current_image_path: Path | None = None
        self._initial_show_refresh_done = False
        self.zoom_factor = 1.0

        self.resize(1200, 800)

        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #bbb; font-size: 12px;")
        self.status_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        self.status_label.setMinimumWidth(40)

        self.image_label = QLabel("No image")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background: #111; color: #ddd;")
        self.image_label.setMinimumSize(1, 1)

        self.image_scroll = QScrollArea()
        self.image_scroll.setWidget(self.image_label)
        self.image_scroll.setWidgetResizable(False)
        self.image_scroll.setAlignment(Qt.AlignCenter)
        self.image_scroll.setStyleSheet("background: #111;")

        # Navigation buttons (moved to overlay)
        prev_month_btn = QPushButton("\u23ee")
        prev_month_btn.setToolTip("Previous Month")
        prev_day_btn = QPushButton("\u25c0")
        prev_day_btn.setToolTip("Previous Day")
        next_day_btn = QPushButton("\u25b6")
        next_day_btn.setToolTip("Next Day")
        next_month_btn = QPushButton("\u23ed")
        next_month_btn.setToolTip("Next Month")

        prev_day_btn.clicked.connect(partial(self._navigate, -1, "day"))
        next_day_btn.clicked.connect(partial(self._navigate, 1, "day"))
        prev_month_btn.clicked.connect(partial(self._navigate, -1, "month"))
        next_month_btn.clicked.connect(partial(self._navigate, 1, "month"))

        # Overlay toolbar buttons
        overlay_btn_style = (
            "QPushButton { color: #ddd; background: rgba(50,50,50,200); "
            "border: 1px solid #444; border-radius: 4px; padding: 5px 12px; font-size: 12px; } "
            "QPushButton:hover { background: rgba(80,80,80,230); color: #fff; }"
        )
        today_btn = QPushButton("Today")
        goto_btn = QPushButton("Go To Date")
        zoom_out_btn = QPushButton("\u2212")
        fit_btn = QPushButton("Fit")
        zoom_in_btn = QPushButton("+")
        quit_btn = QPushButton("Quit")
        for btn in (prev_month_btn, prev_day_btn, next_day_btn, next_month_btn,
                     today_btn, goto_btn, zoom_out_btn, fit_btn, zoom_in_btn, quit_btn):
            btn.setStyleSheet(overlay_btn_style)
            btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        today_btn.clicked.connect(self._go_to_today)
        goto_btn.clicked.connect(self._go_to_specific_date)
        zoom_out_btn.clicked.connect(partial(self._zoom, self.ZOOMOUT_STEP))
        fit_btn.clicked.connect(partial(self._zoom, 0))
        zoom_in_btn.clicked.connect(partial(self._zoom, self.ZOOMIN_STEP))
        quit_btn.clicked.connect(self.close)

        # Overlay widget pinned to bottom of image area
        self.overlay = QWidget(self.image_scroll)
        self.overlay.setStyleSheet(
            "background: rgba(0, 0, 0, 150); border-radius: 8px;"
        )
        overlay_layout = QHBoxLayout(self.overlay)
        overlay_layout.setContentsMargins(10, 6, 10, 6)
        overlay_layout.addWidget(prev_month_btn)
        overlay_layout.addWidget(prev_day_btn)
        overlay_layout.addSpacing(8)
        overlay_layout.addWidget(today_btn)
        overlay_layout.addWidget(goto_btn)
        overlay_layout.addSpacing(8)
        overlay_layout.addWidget(next_day_btn)
        overlay_layout.addWidget(next_month_btn)
        overlay_layout.addStretch(1)
        overlay_layout.addWidget(zoom_out_btn)
        overlay_layout.addWidget(fit_btn)
        overlay_layout.addWidget(zoom_in_btn)
        overlay_layout.addSpacing(8)
        overlay_layout.addWidget(self.status_label)
        overlay_layout.addSpacing(8)
        overlay_layout.addWidget(quit_btn)

        # Main layout: [image]
        central = QWidget()
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.image_scroll, stretch=1)
        self.setCentralWidget(central)

        self._add_shortcuts()
        # Defer image load to showEvent — viewport has no size yet.

    def showEvent(self, event) -> None:  # type: ignore[override]
        super().showEvent(event)
        self._position_overlay()
        if self._initial_show_refresh_done:
            return
        self._initial_show_refresh_done = True
        self._show_current_date()

    def _position_overlay(self) -> None:
        vp = self.image_scroll.viewport()
        vp_geo = vp.geometry()
        hint = self.overlay.sizeHint()
        ow = min(hint.width(), vp_geo.width() - 20)
        oh = hint.height()
        x = vp_geo.x() + vp_geo.width() - ow - 10
        y = vp_geo.y() + vp_geo.height() - oh - 10
        self.overlay.setGeometry(x, y, ow, oh)
        self.overlay.raise_()

    def _add_shortcuts(self) -> None:
        shortcuts = {
            "Right": partial(self._navigate, 1, "day"),
            "Left": partial(self._navigate, -1, "day"),
            "Up": partial(self._navigate, 1, "month"),
            "Down": partial(self._navigate, -1, "month"),
            "T": self._go_to_today,
            "G": self._go_to_specific_date,
            "Ctrl+=": partial(self._zoom, self.ZOOMIN_STEP),
            "Ctrl+-": partial(self._zoom, self.ZOOMOUT_STEP),
            "Ctrl+0": partial(self._zoom, 0),
            "Ctrl+Q": self.close,
        }
        for key, handler in shortcuts.items():
            action = QAction(self)
            action.setShortcut(key)
            action.triggered.connect(handler)
            self.addAction(action)

    def _nearest_available_index(self, target: date) -> int:
        pos = bisect.bisect_left(self.dates, target)
        if pos == 0:
            return 0
        if pos >= len(self.dates):
            return len(self.dates) - 1

        before = self.dates[pos - 1]
        after = self.dates[pos]
        return pos - 1 if (target - before) <= (after - target) else pos

    def _pick_initial_index(self) -> int:
        return self._nearest_available_index(date.today())

    def _navigate(self, step: int, unit: str) -> None:
        if unit == "day":
            self.current_index = (self.current_index + step) % len(self.dates)
        else:
            cur = self.dates[self.current_index]
            mi = self.month_to_order_index[(cur.year, cur.month)]
            target_month = self.month_order[(mi + step) % len(self.month_order)]
            indices = self.month_to_date_indices[target_month]
            same_day = self.month_day_to_index[target_month].get(cur.day)
            if same_day is not None:
                self.current_index = same_day
            else:
                self.current_index = indices[-1] if step > 0 else indices[0]
        self._show_current_date()

    def _go_to_today(self) -> None:
        self.current_index = self._nearest_available_index(date.today())
        self._show_current_date()

    def _go_to_specific_date(self) -> None:
        current = self.dates[self.current_index]
        dialog = QDialog(self)
        dialog.setWindowTitle("Go To Date")

        dialog_layout = QVBoxLayout(dialog)
        calendar = QCalendarWidget(dialog)
        calendar.setSelectedDate(current)
        calendar.setGridVisible(True)
        dialog_layout.addWidget(calendar)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        dialog_layout.addWidget(buttons)

        if dialog.exec() != QDialog.Accepted:
            return

        qdate = calendar.selectedDate()
        target = date(qdate.year(), qdate.month(), qdate.day())

        target_index = self.date_to_index.get(target)
        if target_index is None:
            target_index = self._nearest_available_index(target)
        self.current_index = target_index
        self._show_current_date()

        shown = self.dates[self.current_index]
        if shown != target:
            self.status_label.setText(
                f"No exact image for {target.isoformat()}. Showing nearest: {shown.isoformat()}"
            )

    def _zoom(self, multiplier: float) -> None:
        if multiplier:
            self.zoom_factor = max(self.MIN_ZOOM, min(self.MAX_ZOOM, self.zoom_factor * multiplier))
        else:
            self.zoom_factor = 1.0
        self._refresh_scaled_pixmap()

    def _show_current_date(self) -> None:
        target_date = self.dates[self.current_index]
        images = self.repo.by_date.get(target_date, [])
        self.setWindowTitle(target_date.strftime("%A, %d %B %Y  —  Daily Calendar Viewer"))

        if images:
            self.zoom_factor = 1.0
            self._load_image(images[0])
            if len(images) == 1:
                self.status_label.setText(f"Showing {images[0].name}")
            else:
                self.status_label.setText(
                    f"Showing first of {len(images)} images: {images[0].name}"
                )
        else:
            self.status_label.setText("No images found for this date")
            self.current_image_path = None
            self.current_pixmap = QPixmap()
            self.image_label.setText("No image")
            self.image_label.setPixmap(QPixmap())
            self.image_label.adjustSize()
        self._position_overlay()

    def _load_image(self, path: Path) -> None:
        self.current_image_path = path

        reader = QImageReader(str(path))
        reader.setAutoTransform(True)

        target_size = self.image_scroll.viewport().size()
        source_size = reader.size()
        if (
            target_size.width() > 0
            and target_size.height() > 0
            and source_size.width() > 0
            and source_size.height() > 0
        ):
            reader.setScaledSize(source_size.scaled(target_size, Qt.KeepAspectRatio))

        image = reader.read()
        if image.isNull():
            self.status_label.setText(f"Failed to load: {path.name}")
            return

        self.current_pixmap = QPixmap.fromImage(image)
        self._refresh_scaled_pixmap()

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self._position_overlay()
        if self.current_image_path is not None:
            self._load_image(self.current_image_path)
        else:
            self._refresh_scaled_pixmap()

    def _refresh_scaled_pixmap(self) -> None:
        if self.current_pixmap.isNull():
            return

        viewport = self.image_scroll.viewport().size()
        if viewport.width() <= 0 or viewport.height() <= 0:
            return

        fit_size = self.current_pixmap.size().scaled(viewport, Qt.KeepAspectRatio)
        zoomed_size = fit_size * self.zoom_factor
        scaled = self.current_pixmap.scaled(
            zoomed_size,
            Qt.KeepAspectRatio,
            Qt.FastTransformation,
        )
        self.image_label.setPixmap(scaled)
        self.image_label.resize(scaled.size())


def _find_image_root() -> Path:
    """Locate the folder containing month directories.

    Search order:
    1. Directory next to the script / frozen executable.
    2. If running as a macOS .app, the directory containing the .app bundle.
    """
    if getattr(sys, "frozen", False):
        # PyInstaller sets sys._MEIPASS; the .app lives inside
        # DailyCalendar.app/Contents/MacOS/calendar_viewer
        exe = Path(sys.executable).resolve()
        # Walk up to the .app's parent directory
        for parent in exe.parents:
            if parent.suffix == ".app":
                return parent.parent
        return exe.parent
    return Path(__file__).resolve().parent


def _load_config() -> Path:
    config_path = Path(_find_image_root()) / "config.json"
    if config_path.is_file():
        with open(config_path, encoding="utf-8") as f:
            cfg = json.load(f)
        images_dir = cfg.get("images_dir", "")
        if images_dir:
            p = Path(images_dir)
            if not p.is_absolute():
                p = config_path.parent / p
            return p
    return _find_image_root()


def main() -> int:
    root = _load_config()
    repo = CalendarRepository(root)

    if not repo.has_data():
        app = QApplication(sys.argv)
        QMessageBox.critical(
            None,
            "No Images Found",
            "No valid calendar images were found.\n\n"
            "Expected folders like jan'26 with files such as 0101.jpg",
        )
        return 1

    app = QApplication(sys.argv)
    window = MainWindow(repo)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
