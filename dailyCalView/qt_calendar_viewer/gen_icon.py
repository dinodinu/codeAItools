#!/usr/bin/env python3
"""Generate a calendar .icns icon for macOS."""
import os
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap, QPainter, QFont, QColor, QPen
from PySide6.QtCore import Qt, QRect

def draw_calendar(sz):
    pm = QPixmap(sz, sz)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)

    m = int(sz * 0.04)
    r = int(sz * 0.08)
    body = QRect(m, m, sz - 2 * m, sz - 2 * m)

    # Shadow
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(0, 0, 0, 40))
    p.drawRoundedRect(body.adjusted(2, 2, 2, 2), r, r)

    # White body
    p.setBrush(QColor(255, 255, 255))
    p.setPen(QPen(QColor(200, 200, 200), max(1, sz // 128)))
    p.drawRoundedRect(body, r, r)

    # Red header
    hh = int(sz * 0.28)
    header = QRect(body.x(), body.y(), body.width(), hh)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(220, 50, 50))
    p.drawRoundedRect(header.adjusted(0, 0, 0, r), r, r)
    p.drawRect(header.adjusted(0, r, 0, 0))

    # Month text
    p.setFont(QFont("Helvetica", max(1, int(sz * 0.11)), QFont.Bold))
    p.setPen(QColor(255, 255, 255))
    p.drawText(header, Qt.AlignCenter, "MAR")

    # Day number
    p.setFont(QFont("Helvetica", max(1, int(sz * 0.35)), QFont.Bold))
    p.setPen(QColor(50, 50, 50))
    day_rect = QRect(body.x(), body.y() + hh, body.width(), body.height() - hh)
    p.drawText(day_rect, Qt.AlignCenter, "5")

    p.end()
    return pm

def main():
    app = QApplication(sys.argv)
    iconset = os.path.join(os.path.dirname(__file__), "DailyCalendar.iconset")
    os.makedirs(iconset, exist_ok=True)

    for sz in [16, 32, 64, 128, 256, 512, 1024]:
        draw_calendar(sz).save(os.path.join(iconset, f"icon_{sz}x{sz}.png"))
        if sz <= 512:
            draw_calendar(sz * 2).save(os.path.join(iconset, f"icon_{sz}x{sz}@2x.png"))

    print("Icon PNGs generated in", iconset)

if __name__ == "__main__":
    main()
