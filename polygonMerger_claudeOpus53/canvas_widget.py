"""
Canvas widget for drawing, editing, and merging polygons.
Supports: drawing polygons, dragging polygon bodies, dragging vertices, merging.
"""

import math
from PyQt5.QtCore import QPoint, Qt, pyqtSignal
from PyQt5.QtGui import QBrush, QColor, QPainter, QPen, QPolygon
from PyQt5.QtWidgets import QWidget


class CanvasWidget(QWidget):
    polygon_completed = pyqtSignal(int)
    geometry_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setMinimumSize(900, 560)
        self.setStyleSheet("background-color: white;")
        self.setMouseTracking(True)

        # Polygon data
        self.polygon1_points = []
        self.polygon2_points = []
        self.merged_polygon_points = []

        # State
        self.current_polygon = 1
        self.polygon1_closed = False
        self.polygon2_closed = False
        self.merged = False

        # Thresholds
        self.close_threshold = 15
        self.vertex_grab_radius = 12
        self.vertex_draw_radius = 6

        # Drag state
        self.dragging_polygon = None
        self.dragging_vertex = None
        self.drag_start = None

    def set_current_polygon(self, num):
        self.current_polygon = num

    def clear_all(self):
        self.polygon1_points = []
        self.polygon2_points = []
        self.merged_polygon_points = []
        self.current_polygon = 1
        self.polygon1_closed = False
        self.polygon2_closed = False
        self.merged = False
        self.dragging_polygon = None
        self.dragging_vertex = None
        self.drag_start = None
        self.setCursor(Qt.ArrowCursor)
        self.update()

    def mousePressEvent(self, event):
        pos = event.pos()

        # Priority 1: Check vertex hit
        vertex = self._find_vertex_at(pos)
        if vertex:
            self.dragging_vertex = vertex
            self.setCursor(Qt.CrossCursor)
            if vertex[0] in ("poly1", "poly2"):
                self._clear_merge()
            return

        # Priority 2: Check polygon body hit
        poly = self._find_polygon_at(pos)
        if poly:
            self.dragging_polygon = poly
            self.drag_start = pos
            self.setCursor(Qt.ClosedHandCursor)
            if poly in ("poly1", "poly2"):
                self._clear_merge()
            return

        # Priority 3: Drawing new points
        self._handle_draw(pos)

    def mouseMoveEvent(self, event):
        pos = event.pos()

        # Dragging vertex
        if self.dragging_vertex:
            name, idx = self.dragging_vertex
            pts = self._get_points(name)
            if pts and 0 <= idx < len(pts):
                pts[idx] = pos
                self.geometry_changed.emit()
                self.update()
            return

        # Dragging polygon
        if self.dragging_polygon and self.drag_start:
            dx = pos.x() - self.drag_start.x()
            dy = pos.y() - self.drag_start.y()
            self._translate_polygon(self.dragging_polygon, dx, dy)
            self.drag_start = pos
            self.geometry_changed.emit()
            self.update()
            return

        # Hover cursor
        self._update_cursor(pos)

    def mouseReleaseEvent(self, event):
        self.dragging_vertex = None
        self.dragging_polygon = None
        self.drag_start = None
        self._update_cursor(event.pos())

    def _handle_draw(self, pos):
        if self.merged:
            return

        if self.current_polygon == 1:
            pts = self.polygon1_points
            closed = self.polygon1_closed
        else:
            pts = self.polygon2_points
            closed = self.polygon2_closed

        if closed:
            return

        # Check if closing polygon
        if len(pts) >= 3:
            dist = self._distance(pos, pts[0])
            if dist <= self.close_threshold:
                if self.current_polygon == 1:
                    self.polygon1_closed = True
                    self.polygon_completed.emit(1)
                else:
                    self.polygon2_closed = True
                    self.polygon_completed.emit(2)
                self.geometry_changed.emit()
                self.update()
                return

        pts.append(pos)
        self.geometry_changed.emit()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw polygon 1 (blue)
        self._draw_polygon(
            painter,
            self.polygon1_points,
            QColor(100, 150, 255, 100),
            QColor(0, 100, 255),
            self.polygon1_closed
        )

        # Draw polygon 2 (red)
        self._draw_polygon(
            painter,
            self.polygon2_points,
            QColor(255, 100, 100, 100),
            QColor(255, 0, 0),
            self.polygon2_closed
        )

        # Draw merged polygon (green)
        if self.merged and self.merged_polygon_points:
            self._draw_polygon(
                painter,
                self.merged_polygon_points,
                QColor(100, 255, 100, 100),
                QColor(0, 180, 0),
                True
            )

    def _draw_polygon(self, painter, points, fill, stroke, closed):
        if not points:
            return

        pen = QPen(stroke, 2)
        painter.setPen(pen)

        if closed:
            painter.setBrush(QBrush(fill))
            painter.drawPolygon(QPolygon(points))
        else:
            painter.setBrush(Qt.NoBrush)
            for i in range(len(points) - 1):
                painter.drawLine(points[i], points[i + 1])

        # Draw vertices
        painter.setBrush(QBrush(stroke))
        for i, pt in enumerate(points):
            r = self.vertex_draw_radius + 2 if i == 0 else self.vertex_draw_radius
            painter.drawEllipse(pt, r, r)

    def merge_polygons(self):
        if not self.polygon1_closed or not self.polygon2_closed:
            return False

        p1 = [(p.x(), p.y()) for p in self.polygon1_points]
        p2 = [(p.x(), p.y()) for p in self.polygon2_points]

        try:
            from shapely.geometry import Polygon, MultiPolygon
            from shapely.ops import unary_union

            geom = unary_union([Polygon(p1), Polygon(p2)])

            if geom.is_empty:
                return False

            if isinstance(geom, Polygon):
                coords = list(geom.exterior.coords)
            elif isinstance(geom, MultiPolygon):
                largest = max(geom.geoms, key=lambda g: g.area)
                coords = list(largest.exterior.coords)
            else:
                coords = list(geom.convex_hull.exterior.coords)

            self.merged_polygon_points = [QPoint(int(x), int(y)) for x, y in coords[:-1]]

        except ImportError:
            # Fallback: convex hull
            hull = self._convex_hull(p1 + p2)
            self.merged_polygon_points = [QPoint(int(x), int(y)) for x, y in hull]
        except Exception:
            return False

        self.merged = True
        self.update()
        return True

    def _clear_merge(self):
        if self.merged:
            self.merged = False
            self.merged_polygon_points = []

    def _get_points(self, name):
        if name == "poly1":
            return self.polygon1_points
        if name == "poly2":
            return self.polygon2_points
        if name == "merged":
            return self.merged_polygon_points
        return None

    def _find_polygon_at(self, pos):
        if self.merged and self._point_in_polygon(pos, self.merged_polygon_points):
            return "merged"
        if self.polygon2_closed and self._point_in_polygon(pos, self.polygon2_points):
            return "poly2"
        if self.polygon1_closed and self._point_in_polygon(pos, self.polygon1_points):
            return "poly1"
        return None

    def _find_vertex_at(self, pos):
        for name, pts, closed in [
            ("merged", self.merged_polygon_points, self.merged),
            ("poly2", self.polygon2_points, self.polygon2_closed),
            ("poly1", self.polygon1_points, self.polygon1_closed),
        ]:
            if not closed:
                continue
            for i, pt in enumerate(pts):
                if self._distance(pos, pt) <= self.vertex_grab_radius:
                    return (name, i)
        return None

    def _translate_polygon(self, name, dx, dy):
        pts = self._get_points(name)
        if not pts:
            return
        for i, pt in enumerate(pts):
            pts[i] = QPoint(pt.x() + dx, pt.y() + dy)

    def _update_cursor(self, pos):
        if self._find_vertex_at(pos):
            self.setCursor(Qt.CrossCursor)
        elif self._find_polygon_at(pos):
            self.setCursor(Qt.OpenHandCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    @staticmethod
    def _point_in_polygon(point, polygon):
        if len(polygon) < 3:
            return False

        x, y = point.x(), point.y()
        inside = False
        p1x, p1y = polygon[0].x(), polygon[0].y()

        for i in range(1, len(polygon) + 1):
            p2x, p2y = polygon[i % len(polygon)].x(), polygon[i % len(polygon)].y()
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y) and x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    else:
                        xinters = p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
            p1x, p1y = p2x, p2y

        return inside

    @staticmethod
    def _distance(p1, p2):
        return math.hypot(p1.x() - p2.x(), p1.y() - p2.y())

    def _convex_hull(self, points):
        if len(points) <= 1:
            return points

        pts = sorted(set(points))
        if len(pts) <= 2:
            return pts

        def cross(o, a, b):
            return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

        lower = []
        for p in pts:
            while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
                lower.pop()
            lower.append(p)

        upper = []
        for p in reversed(pts):
            while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
                upper.pop()
            upper.append(p)

        return lower[:-1] + upper[:-1]
