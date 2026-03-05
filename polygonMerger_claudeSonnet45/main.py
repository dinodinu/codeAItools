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
