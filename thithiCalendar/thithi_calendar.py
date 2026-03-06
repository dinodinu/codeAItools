#!/usr/bin/env python3
"""
Thithi Calendar Application
Displays the thithi (tithi) for a user-selected date.
Uses calendar images from srirangaminfo.com and astronomical calculations via PyEphem.
"""

import sys
import math
import datetime
import argparse

import ephem


# ─── Constants ────────────────────────────────────────────────────────────────

_TITHI = [
    ("Prathama",    "பிரதமை"),
    ("Dvitiya",     "த்விதீயை"),
    ("Tritiya",     "திரிதீயை"),
    ("Chaturthi",   "சதுர்த்தி"),
    ("Panchami",    "பஞ்சமி"),
    ("Shashthi",    "சஷ்டி"),
    ("Saptami",     "சப்தமி"),
    ("Ashtami",     "அஷ்டமி"),
    ("Navami",      "நவமி"),
    ("Dashami",     "தசமி"),
    ("Ekadashi",    "ஏகாதசி"),
    ("Dvadashi",    "த்வாதசி"),
    ("Trayodashi",  "த்ரயோதசி"),
    ("Chaturdashi", "சதுர்த்தசி"),
]

_CAL_URL = "https://www.srirangaminfo.com/cal/{year}/{dd}{mm}.jpg"

_STYLE_DATE_EDIT = (
    "QDateEdit { background-color: #fff; color: #222; "
    "border: 2px solid #b08050; border-radius: 4px; padding: 4px 8px; }"
    "QDateEdit::drop-down { subcontrol-origin: padding; "
    "subcontrol-position: right center; width: 24px; }"
    "QDateEdit QAbstractItemView { background-color: #fff; color: #222; "
    "selection-background-color: #d35400; selection-color: #fff; }"
)

_STYLE_FETCH_BTN = (
    "QPushButton { background-color: #d35400; color: white; "
    "border-radius: 6px; padding: 6px 20px; }"
    "QPushButton:hover { background-color: #e67e22; }"
    "QPushButton:pressed { background-color: #a04000; }"
)

_STYLE_ICS_BTN = (
    "QPushButton { background-color: #27ae60; color: white; "
    "border-radius: 6px; padding: 6px 16px; }"
    "QPushButton:hover { background-color: #2ecc71; }"
    "QPushButton:pressed { background-color: #1e8449; }"
)

_PALETTE_COLORS = {
    "Window":          "#fdf6e3",
    "WindowText":      "#222",
    "Base":            "#fff",
    "AlternateBase":   "#f7f0e0",
    "Text":            "#222",
    "ButtonText":      "#222",
    "Button":          "#f0e6d2",
    "Highlight":       "#d35400",
    "HighlightedText": "#fff",
    "ToolTipBase":     "#fff",
    "ToolTipText":     "#222",
}


# ─── Tithi Calculation ───────────────────────────────────────────────────────

_IST_REF = datetime.time(0, 30)  # 6:00 AM IST = 00:30 UTC


def _elongation_at(dt_utc: datetime.datetime) -> float:
    """Moon\u2013Sun ecliptic elongation in degrees at a UTC datetime."""
    ed = ephem.Date(dt_utc)
    s = ephem.Sun(ed)
    m = ephem.Moon(ed)
    return (math.degrees(float(ephem.Ecliptic(m).lon))
            - math.degrees(float(ephem.Ecliptic(s).lon))) % 360.0


def _tithi_num_at(dt_utc: datetime.datetime) -> int:
    """Tithi index (0\u201329) at the given UTC datetime."""
    return int(_elongation_at(dt_utc) / 12.0)


def _find_tithi_boundary(t1: datetime.datetime, t2: datetime.datetime) -> datetime.datetime:
    """Binary-search for the tithi transition between t1 and t2 (UTC)."""
    n1 = _tithi_num_at(t1)
    for _ in range(30):
        mid = t1 + (t2 - t1) / 2
        if _tithi_num_at(mid) == n1:
            t1 = mid
        else:
            t2 = mid
    return t2


def find_tithi_window(date: datetime.date) -> tuple:
    """Return (start_utc, end_utc) for the tithi on *date* (at 6 AM IST)."""
    ref = datetime.datetime.combine(date, _IST_REF)
    cur = _tithi_num_at(ref)
    step = datetime.timedelta(hours=1)

    t = ref
    for _ in range(48):
        if _tithi_num_at(t - step) != cur:
            break
        t -= step
    start = _find_tithi_boundary(t - step, t)

    t = ref
    for _ in range(48):
        if _tithi_num_at(t + step) != cur:
            break
        t += step
    end = _find_tithi_boundary(t, t + step)

    return start, end


def compute_tithi(date: datetime.date) -> dict:
    """Compute the tithi for a given date at 6:00 AM IST (00:30 UTC)."""
    elongation = _elongation_at(datetime.datetime.combine(date, _IST_REF))
    tithi_num = int(elongation / 12.0)  # 0-29
    is_shukla = tithi_num < 15
    tithi_index = tithi_num if is_shukla else tithi_num - 15

    if tithi_index == 14:
        tithi_name = "Purnima (Full Moon)" if is_shukla else "Amavasya (New Moon)"
        tithi_tamil = "பூர்ணிமை (பௌர்ணமி)" if is_shukla else "அமாவாசை"
    else:
        tithi_name, tithi_tamil = _TITHI[tithi_index]

    return {
        "tithi_name": tithi_name,
        "tithi_tamil": tithi_tamil,
        "tithi_number": tithi_index + 1,
        "paksha_en": "Shukla Paksha (Waxing Moon)" if is_shukla else "Krishna Paksha (Waning Moon)",
        "elongation": round(elongation, 2),
        "moon_phase": round(elongation / 3.6, 1),
    }


# ─── CLI Mode ─────────────────────────────────────────────────────────────────

def _cli_show_tithi(date: datetime.date):
    """Print tithi details for a date to stdout."""
    info = compute_tithi(date)
    start_utc, end_utc = find_tithi_window(date)
    local_tz = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
    start_local = start_utc.replace(tzinfo=datetime.timezone.utc).astimezone(local_tz)
    end_local = end_utc.replace(tzinfo=datetime.timezone.utc).astimezone(local_tz)
    tz_name = start_local.strftime("%Z")
    cal_url = _CAL_URL.format(year=date.year, mm=f"{date.month:02d}", dd=f"{date.day:02d}")

    print(f"\n{'─' * 50}")
    print(f"  🙏  Thithi Calendar")
    print(f"{'─' * 50}")
    print(f"  Date           : {date.strftime('%A, %d %B %Y')}")
    print(f"  Thithi         : {info['tithi_name']}  ({info['tithi_tamil']})")
    print(f"  Paksha         : {info['paksha_en']}")
    print(f"  Tithi Number   : {info['tithi_number']} of 15")
    print(f"  Thithi Start   : {start_local.strftime('%d %b %Y, %I:%M %p')} {tz_name}")
    print(f"  Thithi End     : {end_local.strftime('%d %b %Y, %I:%M %p')} {tz_name}")
    print(f"  Elongation     : {info['elongation']}°")
    print(f"  Lunar Phase    : {info['moon_phase']}%")
    print(f"  Calendar Image : {cal_url}")
    print(f"{'─' * 50}\n")


def _find_chaturthi_events(start_y: int, end_y: int) -> list:
    """Return list of (date, paksha) tuples for all Chaturthi dates in range."""
    events = []
    d = datetime.date(start_y, 1, 1)
    end = datetime.date(end_y, 12, 31)
    while d <= end:
        elong = _elongation_at(datetime.datetime.combine(d, _IST_REF))
        tnum = int(elong / 12.0)
        tithi_in_paksha = tnum if tnum < 15 else tnum - 15
        if tithi_in_paksha == 3:  # Chaturthi
            events.append((d, "Shukla" if tnum < 15 else "Krishna"))
            d += datetime.timedelta(days=13)  # next Chaturthi is ~14-15 days away
        else:
            # estimate days until next Chaturthi (tithi 3 or 18)
            target = 3 if tnum < 3 else (18 if tnum < 18 else 33)
            skip = max(1, target - tnum - 1)
            d += datetime.timedelta(days=skip)
    return events


def _write_chaturthi_ics(events: list, path: str):
    """Write Chaturthi events to an .ics file."""
    one_day = datetime.timedelta(days=1)
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//ThithiCalendar//Chaturthi//EN",
        "CALSCALE:GREGORIAN",
    ]
    for date, paksha in events:
        ds = date.strftime("%Y%m%d")
        next_ds = (date + one_day).strftime("%Y%m%d")
        lines += [
            "BEGIN:VEVENT",
            f"DTSTART;VALUE=DATE:{ds}",
            f"DTEND;VALUE=DATE:{next_ds}",
            f"SUMMARY:{paksha} Chaturthi",
            f"DESCRIPTION:{paksha} Paksha ({'Waxing' if paksha == 'Shukla' else 'Waning'} Moon)",
            f"UID:chaturthi-{ds}-{paksha.lower()}@thithicalendar",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\r\n".join(lines) + "\r\n")


def _cli_export_chaturthi_ics(start_y: int, end_y: int, path: str):
    """Export Chaturthi dates to an .ics file from the CLI."""
    if start_y > end_y:
        start_y, end_y = end_y, start_y
    events = _find_chaturthi_events(start_y, end_y)
    _write_chaturthi_ics(events, path)
    print(f"✅ Exported {len(events)} Chaturthi dates ({start_y}–{end_y}) to: {path}")


def _run_cli(args):
    """Handle CLI mode."""
    if args.date:
        sel = datetime.datetime.strptime(args.date, "%Y-%m-%d").date()
    else:
        sel = datetime.date.today()

    _cli_show_tithi(sel)

    if args.export_ics:
        parts = args.export_ics.split(":")
        if len(parts) != 3:
            print("Error: --export-ics format must be START_YEAR:END_YEAR:FILEPATH")
            print("  Example: --export-ics 2026:2030:chaturthi.ics")
            sys.exit(1)
        start_y, end_y, path = int(parts[0]), int(parts[1]), parts[2]
        _cli_export_chaturthi_ics(start_y, end_y, path)


# ─── GUI Mode ─────────────────────────────────────────────────────────────────

def _run_gui():
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QDateEdit, QPushButton, QGroupBox, QFileDialog, QSpinBox,
    )
    from PyQt6.QtCore import Qt, QDate
    from PyQt6.QtGui import QFont, QPalette, QColor

    class ThithiCalendarApp(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Thithi Calendar — srirangaminfo.com")
            self._init_ui()
            self._on_fetch_clicked()
            self.adjustSize()

        # ── UI Setup ──

        def _init_ui(self):
            central = QWidget()
            self.setCentralWidget(central)
            root = QVBoxLayout(central)
            root.setSpacing(12)
            root.setContentsMargins(16, 16, 16, 16)

            self._add_header(root)
            self._add_date_picker(root)
            self._add_tithi_panel(root)
            self._add_ics_section(root)
            self._add_footer(root)

        def _add_header(self, layout):
            title = QLabel("🙏 Thithi Calendar")
            title.setFont(QFont("Arial", 22, QFont.Weight.Bold))
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(title)

            subtitle = QLabel("Panchangam data sourced from srirangaminfo.com")
            subtitle.setFont(QFont("Arial", 10))
            subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
            subtitle.setStyleSheet("color: #666;")
            layout.addWidget(subtitle)

        def _add_date_picker(self, layout):
            group = QGroupBox("Select Date")
            row = QHBoxLayout(group)

            self.date_edit = QDateEdit()
            self.date_edit.setCalendarPopup(True)
            self.date_edit.setDate(QDate.currentDate())
            self.date_edit.setDisplayFormat("dd MMMM yyyy, dddd")
            self.date_edit.setFont(QFont("Arial", 13))
            self.date_edit.setMinimumWidth(300)
            self.date_edit.setStyleSheet(_STYLE_DATE_EDIT)
            row.addWidget(self.date_edit)

            self.fetch_btn = QPushButton("Get Thithi")
            self.fetch_btn.setFont(QFont("Arial", 13, QFont.Weight.Bold))
            self.fetch_btn.setMinimumHeight(38)
            self.fetch_btn.setStyleSheet(_STYLE_FETCH_BTN)
            self.fetch_btn.clicked.connect(self._on_fetch_clicked)
            row.addWidget(self.fetch_btn)

            row.addStretch()
            layout.addWidget(group)

        def _add_tithi_panel(self, layout):
            info_group = QGroupBox("Thithi Details (Astronomical Calculation)")
            info_inner = QVBoxLayout(info_group)

            self.tithi_label = QLabel()
            self.tithi_label.setFont(QFont("Arial", 14))
            self.tithi_label.setWordWrap(True)
            self.tithi_label.setTextFormat(Qt.TextFormat.RichText)
            self.tithi_label.setOpenExternalLinks(True)
            info_inner.addWidget(self.tithi_label)

            layout.addWidget(info_group)

        def _add_ics_section(self, layout):
            group = QGroupBox("Export Chaturthi Dates")
            row = QHBoxLayout(group)

            row.addWidget(QLabel("From:"))
            self.ics_start_year = QSpinBox()
            self.ics_start_year.setRange(1900, 2100)
            self.ics_start_year.setValue(2026)
            self.ics_start_year.setFont(QFont("Arial", 12))
            row.addWidget(self.ics_start_year)

            row.addWidget(QLabel("To:"))
            self.ics_end_year = QSpinBox()
            self.ics_end_year.setRange(1900, 2100)
            self.ics_end_year.setValue(2030)
            self.ics_end_year.setFont(QFont("Arial", 12))
            row.addWidget(self.ics_end_year)

            ics_btn = QPushButton("Export .ics")
            ics_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            ics_btn.setMinimumHeight(36)
            ics_btn.setStyleSheet(_STYLE_ICS_BTN)
            ics_btn.clicked.connect(self._export_chaturthi_ics)
            row.addWidget(ics_btn)
            row.addStretch()

            layout.addWidget(group)

        def _add_footer(self, layout):
            footer = QLabel("Data & Calendar: srirangaminfo.com  |  Tithi calc: PyEphem (astronomical)")
            footer.setFont(QFont("Arial", 9))
            footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
            footer.setStyleSheet("color: #888;")
            layout.addWidget(footer)

        # ── Helpers ──

        def _selected_date(self) -> datetime.date:
            q = self.date_edit.date()
            return datetime.date(q.year(), q.month(), q.day())

        # ── Slots ──

        def _on_fetch_clicked(self):
            sel = self._selected_date()
            try:
                info = compute_tithi(sel)
                start_utc, end_utc = find_tithi_window(sel)
                local_tz = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
                start_local = start_utc.replace(tzinfo=datetime.timezone.utc).astimezone(local_tz)
                end_local = end_utc.replace(tzinfo=datetime.timezone.utc).astimezone(local_tz)
                tz_name = start_local.strftime("%Z")
                cal_url = _CAL_URL.format(year=sel.year, mm=f"{sel.month:02d}", dd=f"{sel.day:02d}")
                self.tithi_label.setText(
                    f"<b>Date:</b> {sel.strftime('%A, %d %B %Y')}<br>"
                    f"<b>Thithi:</b> {info['tithi_name']}  ({info['tithi_tamil']})<br>"
                    f"<b>Paksha:</b> {info['paksha_en']}<br>"
                    f"<b>Tithi Number:</b> {info['tithi_number']} of 15<br>"
                    f"<b>Thithi Start:</b> {start_local.strftime('%d %b %Y, %I:%M %p')} {tz_name}<br>"
                    f"<b>Thithi End:</b> {end_local.strftime('%d %b %Y, %I:%M %p')} {tz_name}<br>"
                    f"<b>Moon–Sun Elongation:</b> {info['elongation']}°<br>"
                    f"<b>Lunar Phase:</b> {info['moon_phase']}%<br><br>"
                    f'📅 <a href="{cal_url}" style="color: #d35400;">'
                    f"View Daily Tamil Calendar Image (srirangaminfo.com)</a>"
                )
            except Exception as e:
                self.tithi_label.setText(f"<span style='color:red;'>Calculation error: {e}</span>")

        def _export_chaturthi_ics(self):
            start_y = self.ics_start_year.value()
            end_y = self.ics_end_year.value()
            if start_y > end_y:
                start_y, end_y = end_y, start_y

            path, _ = QFileDialog.getSaveFileName(
                self, "Save Chaturthi Calendar",
                f"chaturthi_{start_y}_{end_y}.ics",
                "iCalendar Files (*.ics)"
            )
            if not path:
                return

            events = _find_chaturthi_events(start_y, end_y)
            _write_chaturthi_ics(events, path)

            self.tithi_label.setText(
                self.tithi_label.text()
                + f"<br><br>✅ Exported <b>{len(events)}</b> Chaturthi dates to:<br>"
                + f"<i>{path}</i>"
            )

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    palette = app.palette()
    for role_name, color in _PALETTE_COLORS.items():
        palette.setColor(getattr(QPalette.ColorRole, role_name), QColor(color))
    app.setPalette(palette)

    window = ThithiCalendarApp()
    window.show()
    sys.exit(app.exec())


# ─── Entry Point ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Thithi Calendar — display tithi for any date",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python thithi_calendar.py --cli                    # today's tithi\n"
            "  python thithi_calendar.py --cli --date 2026-03-06  # specific date\n"
            "  python thithi_calendar.py --cli --export-ics 2026:2030:chaturthi.ics\n"
            "  python thithi_calendar.py                          # launch GUI (default)"
        ),
    )
    parser.add_argument(
        "--cli", action="store_true",
        help="Run in CLI mode (no GUI, no PyQt6 required)",
    )
    parser.add_argument(
        "--date", type=str, default=None,
        help="Date in YYYY-MM-DD format (default: today)",
    )
    parser.add_argument(
        "--export-ics", type=str, default=None,
        help="Export Chaturthi dates as START_YEAR:END_YEAR:FILEPATH (e.g. 2026:2030:chaturthi.ics)",
    )
    args = parser.parse_args()

    if args.cli or args.date or args.export_ics:
        _run_cli(args)
    else:
        _run_gui()


if __name__ == "__main__":
    main()
