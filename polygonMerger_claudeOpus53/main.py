#!/usr/bin/env python3
"""
Polygon Merger - Qt Application
Draw two polygons, edit vertices, drag to move, and merge into one outline.
"""

import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel
)
from canvas_widget import CanvasWidget


class PolygonMergerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.canvas = None
        self.status_label = None
        self.switch_btn = None
        self.merge_btn = None
        self.clear_btn = None
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("Polygon Merger")
        self.setGeometry(100, 100, 1000, 700)

        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout()
        central.setLayout(layout)

        # Canvas
        self.canvas = CanvasWidget()
        layout.addWidget(self.canvas)

        # Controls
        controls = QHBoxLayout()
        layout.addLayout(controls)

        self.status_label = QLabel(
            "Draw Polygon 1 (blue): click to add vertices, click near first point to close."
        )
        self.status_label.setStyleSheet("font-size: 12pt; padding: 5px;")
        controls.addWidget(self.status_label)

        self.switch_btn = QPushButton("Switch to Polygon 2")
        self.switch_btn.setEnabled(False)
        self.switch_btn.clicked.connect(self._switch_to_poly2)
        controls.addWidget(self.switch_btn)

        self.merge_btn = QPushButton("Merge Polygons")
        self.merge_btn.setEnabled(False)
        self.merge_btn.clicked.connect(self._merge)
        controls.addWidget(self.merge_btn)

        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.clicked.connect(self._clear)
        controls.addWidget(self.clear_btn)

        # Connect signals
        self.canvas.polygon_completed.connect(self._on_polygon_done)
        self.canvas.geometry_changed.connect(self._on_geometry_changed)

    def _switch_to_poly2(self):
        self.canvas.set_current_polygon(2)
        self.status_label.setText(
            "Draw Polygon 2 (red): click to add vertices, click near first point to close."
        )
        self.switch_btn.setEnabled(False)

    def _on_polygon_done(self, num):
        if num == 1:
            self.status_label.setText(
                "Polygon 1 done! Drag body or vertices to edit. Click 'Switch to Polygon 2'."
            )
            self.switch_btn.setEnabled(True)
        else:
            self.status_label.setText(
                "Both polygons done! Drag to edit anytime. Click 'Merge Polygons'."
            )
            self.merge_btn.setEnabled(True)

    def _on_geometry_changed(self):
        # Re-enable merge if both closed
        if self.canvas.polygon1_closed and self.canvas.polygon2_closed:
            self.merge_btn.setEnabled(True)

    def _merge(self):
        ok = self.canvas.merge_polygons()
        if ok:
            self.status_label.setText(
                "Merged! Green outline shown. Drag polygons/vertices, then 'Merge' again to update."
            )
        else:
            self.status_label.setText("Merge failed. Ensure both polygons are valid and closed.")

    def _clear(self):
        self.canvas.clear_all()
        self.status_label.setText(
            "Draw Polygon 1 (blue): click to add vertices, click near first point to close."
        )
        self.switch_btn.setEnabled(False)
        self.merge_btn.setEnabled(False)


def main():
    app = QApplication(sys.argv)
    window = PolygonMergerApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
