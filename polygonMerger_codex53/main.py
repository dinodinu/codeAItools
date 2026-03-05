#!/usr/bin/env python3
"""Polygon merger desktop app using PyQt5."""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel

from canvas_widget import CanvasWidget


class PolygonMergerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.canvas = None
        self.status_label = None
        self.switch_btn = None
        self.merge_btn = None
        self.clear_btn = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Polygon Merger")
        self.setGeometry(100, 100, 1100, 760)

        container = QWidget()
        self.setCentralWidget(container)

        root_layout = QVBoxLayout()
        container.setLayout(root_layout)

        self.canvas = CanvasWidget()
        root_layout.addWidget(self.canvas)

        controls = QHBoxLayout()
        root_layout.addLayout(controls)

        self.status_label = QLabel(
            "Draw Polygon 1 (blue): click to add points, click near first point to close."
        )
        self.status_label.setStyleSheet("font-size: 12pt; padding: 6px;")
        controls.addWidget(self.status_label)

        self.switch_btn = QPushButton("Switch to Polygon 2")
        self.switch_btn.setEnabled(False)
        self.switch_btn.clicked.connect(self.switch_to_polygon_2)
        controls.addWidget(self.switch_btn)

        self.merge_btn = QPushButton("Merge Polygons")
        self.merge_btn.setEnabled(False)
        self.merge_btn.clicked.connect(self.merge_polygons)
        controls.addWidget(self.merge_btn)

        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.clicked.connect(self.clear_all)
        controls.addWidget(self.clear_btn)

        self.canvas.polygon_completed.connect(self.on_polygon_completed)
        self.canvas.geometry_changed.connect(self.on_geometry_changed)

    def switch_to_polygon_2(self):
        self.canvas.set_current_polygon(2)
        self.status_label.setText(
            "Draw Polygon 2 (red): click to add points, click near first point to close."
        )
        self.switch_btn.setEnabled(False)

    def on_polygon_completed(self, polygon_num):
        if polygon_num == 1:
            self.status_label.setText(
                "Polygon 1 complete. You can drag its body/vertices. Click 'Switch to Polygon 2'."
            )
            self.switch_btn.setEnabled(True)
            return

        self.status_label.setText(
            "Both polygons complete. Drag bodies/vertices anytime, then click 'Merge Polygons'."
        )
        self.merge_btn.setEnabled(True)

    def on_geometry_changed(self):
        if self.canvas.polygon1_closed and self.canvas.polygon2_closed:
            self.merge_btn.setEnabled(True)

    def merge_polygons(self):
        merged_ok = self.canvas.merge_polygons()
        if merged_ok:
            self.status_label.setText(
                "Merged outline shown in green. Drag polygons/vertices and click 'Merge Polygons' again to recompute."
            )
        else:
            self.status_label.setText("Unable to merge polygons. Ensure both are valid and closed.")

    def clear_all(self):
        self.canvas.clear_all()
        self.status_label.setText(
            "Draw Polygon 1 (blue): click to add points, click near first point to close."
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
#!/usr/bin/env python3
"""
Qt Application for Polygon Drawing and Merging
Allows drawing two polygons and merges them into a single outline
"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt
from canvas_widget import CanvasWidget


class PolygonMergerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('Polygon Merger - Draw and Merge Polygons')
        self.setGeometry(100, 100, 1000, 700)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Canvas widget
        self.canvas = CanvasWidget()
        main_layout.addWidget(self.canvas)
        
        # Control panel
        control_layout = QHBoxLayout()
        
        # Status label
        self.status_label = QLabel('Click to draw Polygon 1 (blue). Close polygon by clicking near first point.')
        self.status_label.setStyleSheet('font-size: 12pt; padding: 5px;')
        control_layout.addWidget(self.status_label)
        
        # Buttons
        self.switch_btn = QPushButton('Switch to Polygon 2')
        self.switch_btn.clicked.connect(self.switch_polygon)
        self.switch_btn.setEnabled(False)
        control_layout.addWidget(self.switch_btn)
        
        self.merge_btn = QPushButton('Merge Polygons')
        self.merge_btn.clicked.connect(self.merge_polygons)
        self.merge_btn.setEnabled(False)
        control_layout.addWidget(self.merge_btn)
        
        self.clear_btn = QPushButton('Clear All')
        self.clear_btn.clicked.connect(self.clear_all)
        control_layout.addWidget(self.clear_btn)
        
        main_layout.addLayout(control_layout)
        
        # Connect canvas signals
        self.canvas.polygon_completed.connect(self.on_polygon_completed)
        
    def switch_polygon(self):
        self.canvas.set_current_polygon(2)
        self.status_label.setText('Click to draw Polygon 2 (red). Close polygon by clicking near first point.')
        self.switch_btn.setEnabled(False)
        
    def on_polygon_completed(self, polygon_num):
        if polygon_num == 1:
            self.status_label.setText('Polygon 1 completed! Drag polygon to move or drag vertices to adjust. Click "Switch to Polygon 2".')
            self.switch_btn.setEnabled(True)
        elif polygon_num == 2:
            self.status_label.setText('Both polygons completed! Drag polygons/vertices to adjust. Click "Merge Polygons" to combine.')
            self.merge_btn.setEnabled(True)
            
    def merge_polygons(self):
        self.canvas.merge_polygons()
        self.status_label.setText('Merged! Drag any polygon/vertex to adjust. Re-click "Merge" after editing to update.')
        # Keep merge button enabled so users can re-merge after moving polygons
        
    def clear_all(self):
        self.canvas.clear_all()
        self.status_label.setText('Click to draw Polygon 1 (blue). Close polygon by clicking near first point.')
        self.switch_btn.setEnabled(False)
        self.merge_btn.setEnabled(False)


def main():
    app = QApplication(sys.argv)
    window = PolygonMergerApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
