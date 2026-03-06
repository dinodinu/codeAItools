#!/usr/bin/env python3
"""Generate a calendar .icns icon for macOS using the current date."""
import datetime
import os
import subprocess
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap, QPainter, QFont, QColor, QPen
from PySide6.QtCore import Qt, QRect


def draw_calendar(sz, month_str, day_str, dark=False):
    pm = QPixmap(sz, sz)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)

    m = int(sz * 0.04)
    r = int(sz * 0.08)
    body = QRect(m, m, sz - 2 * m, sz - 2 * m)

    # Shadow
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(0, 0, 0, 80 if dark else 40))
    p.drawRoundedRect(body.adjusted(2, 2, 2, 2), r, r)

    # Body
    p.setBrush(QColor(44, 44, 46) if dark else QColor(255, 255, 255))
    p.setPen(QPen(QColor(68, 68, 70) if dark else QColor(200, 200, 200),
                  max(1, sz // 128)))
    p.drawRoundedRect(body, r, r)

    # Red header
    hh = int(sz * 0.28)
    header = QRect(body.x(), body.y(), body.width(), hh)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(200, 40, 40) if dark else QColor(220, 50, 50))
    p.drawRoundedRect(header.adjusted(0, 0, 0, r), r, r)
    p.drawRect(header.adjusted(0, r, 0, 0))

    # Month text
    p.setFont(QFont("Helvetica", max(1, int(sz * 0.11)), QFont.Bold))
    p.setPen(QColor(255, 255, 255))
    p.drawText(header, Qt.AlignCenter, month_str)

    # Day number
    p.setFont(QFont("Helvetica", max(1, int(sz * 0.35)), QFont.Bold))
    p.setPen(QColor(230, 230, 230) if dark else QColor(50, 50, 50))
    day_rect = QRect(body.x(), body.y() + hh, body.width(), body.height() - hh)
    p.drawText(day_rect, Qt.AlignCenter, day_str)

    p.end()
    return pm


def detect_dark_mode():
    try:
        result = subprocess.run(
            ["defaults", "read", "-g", "AppleInterfaceStyle"],
            capture_output=True, text=True)
        return result.stdout.strip().lower() == "dark"
    except Exception:
        return False


def main():
    app = QApplication(sys.argv)
    today = datetime.date.today()
    month_str = today.strftime("%b").upper()
    day_str = str(today.day)
    dark = detect_dark_mode()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    iconset = os.path.join(script_dir, "DailyCalendar.iconset")
    os.makedirs(iconset, exist_ok=True)

    for sz in [16, 32, 64, 128, 256, 512, 1024]:
        draw_calendar(sz, month_str, day_str, dark).save(
            os.path.join(iconset, f"icon_{sz}x{sz}.png"))
        if sz <= 512:
            draw_calendar(sz * 2, month_str, day_str, dark).save(
                os.path.join(iconset, f"icon_{sz}x{sz}@2x.png"))

    icns_path = os.path.join(script_dir, "DailyCalendar.icns")
    subprocess.run(["iconutil", "-c", "icns", iconset, "-o", icns_path],
                   check=True)
    print(f"Generated {icns_path}  ({month_str} {day_str}, "
          f"{'dark' if dark else 'light'})")


if __name__ == "__main__":
    main()
