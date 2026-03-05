"""Interactive canvas for drawing, editing, dragging, and merging two polygons."""

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
        self.setStyleSheet("background: white;")
        self.setMouseTracking(True)

        self.polygon1_points = []
        self.polygon2_points = []
        self.merged_polygon_points = []

        self.current_polygon = 1
        self.polygon1_closed = False
        self.polygon2_closed = False
        self.merged = False

        self.close_threshold = 14
        self.vertex_pick_radius = 10
        self.vertex_radius = 5

        self.dragging_polygon = None
        self.dragging_vertex = None
        self.drag_start_pos = None

    def set_current_polygon(self, polygon_num):
        self.current_polygon = polygon_num

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
        self.drag_start_pos = None
        self.setCursor(Qt.ArrowCursor)
        self.update()

    def mousePressEvent(self, event):
        pos = event.pos()

        vertex_hit = self.find_vertex_hit(pos)
        if vertex_hit is not None:
            self.dragging_vertex = vertex_hit
            self.setCursor(Qt.CrossCursor)
            if vertex_hit[0] in ("poly1", "poly2"):
                self.clear_merge_result()
            return

        polygon_hit = self.find_polygon_hit(pos)
        if polygon_hit is not None:
            self.dragging_polygon = polygon_hit
            self.drag_start_pos = pos
            self.setCursor(Qt.ClosedHandCursor)
            if polygon_hit in ("poly1", "poly2"):
                self.clear_merge_result()
            return

        self.handle_draw_click(pos)

    def mouseMoveEvent(self, event):
        pos = event.pos()

        if self.dragging_vertex is not None:
            polygon_name, index = self.dragging_vertex
            points = self.get_points_ref(polygon_name)
            if points is not None and 0 <= index < len(points):
                points[index] = pos
                self.geometry_changed.emit()
                self.update()
            return

        if self.dragging_polygon is not None and self.drag_start_pos is not None:
            dx = pos.x() - self.drag_start_pos.x()
            dy = pos.y() - self.drag_start_pos.y()
            self.translate_polygon(self.dragging_polygon, dx, dy)
            self.drag_start_pos = pos
            self.geometry_changed.emit()
            self.update()
            return

        self.update_hover_cursor(pos)

    def mouseReleaseEvent(self, event):
        self.dragging_vertex = None
        self.dragging_polygon = None
        self.drag_start_pos = None
        self.update_hover_cursor(event.pos())

    def handle_draw_click(self, pos):
        if self.merged:
            return

        if self.current_polygon == 1:
            points = self.polygon1_points
            closed = self.polygon1_closed
        else:
            points = self.polygon2_points
            closed = self.polygon2_closed

        if closed:
            return

        if len(points) >= 3 and self.distance(pos, points[0]) <= self.close_threshold:
            if self.current_polygon == 1:
                self.polygon1_closed = True
                self.polygon_completed.emit(1)
            else:
                self.polygon2_closed = True
                self.polygon_completed.emit(2)
            self.geometry_changed.emit()
            self.update()
            return

        points.append(pos)
        self.geometry_changed.emit()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        self.draw_polygon(
            painter,
            self.polygon1_points,
            QColor(80, 130, 255, 90),
            QColor(30, 90, 220),
            self.polygon1_closed,
        )
        self.draw_polygon(
            painter,
            self.polygon2_points,
            QColor(255, 95, 95, 90),
            QColor(215, 45, 45),
            self.polygon2_closed,
        )

        if self.merged and self.merged_polygon_points:
            self.draw_polygon(
                painter,
                self.merged_polygon_points,
                QColor(90, 220, 120, 90),
                QColor(30, 160, 70),
                True,
            )

    def draw_polygon(self, painter, points, fill_color, stroke_color, is_closed):
        if not points:
            return

        painter.setPen(QPen(stroke_color, 2))
        painter.setBrush(QBrush(fill_color if is_closed else Qt.NoBrush))

        if is_closed:
            painter.drawPolygon(QPolygon(points))
        else:
            for i in range(len(points) - 1):
                painter.drawLine(points[i], points[i + 1])

        painter.setPen(QPen(stroke_color, 2))
        painter.setBrush(QBrush(stroke_color))
        for i, point in enumerate(points):
            radius = self.vertex_radius + 1 if i == 0 else self.vertex_radius
            painter.drawEllipse(point, radius, radius)

    def merge_polygons(self):
        if not self.polygon1_closed or not self.polygon2_closed:
            return False

        poly1 = [(p.x(), p.y()) for p in self.polygon1_points]
        poly2 = [(p.x(), p.y()) for p in self.polygon2_points]

        try:
            from shapely.geometry import MultiPolygon, Polygon
            from shapely.ops import unary_union

            merged_geom = unary_union([Polygon(poly1), Polygon(poly2)])
            if merged_geom.is_empty:
                return False

            if isinstance(merged_geom, Polygon):
                coords = list(merged_geom.exterior.coords)
            elif isinstance(merged_geom, MultiPolygon):
                largest = max(merged_geom.geoms, key=lambda g: g.area)
                coords = list(largest.exterior.coords)
            else:
                hull = merged_geom.convex_hull
                coords = list(hull.exterior.coords)

            self.merged_polygon_points = [QPoint(int(x), int(y)) for x, y in coords[:-1]]
        except ImportError:
            hull = self.convex_hull(poly1 + poly2)
            self.merged_polygon_points = [QPoint(int(x), int(y)) for x, y in hull]
        except Exception:
            return False

        self.merged = True
        self.update()
        return True

    def clear_merge_result(self):
        if self.merged:
            self.merged = False
            self.merged_polygon_points = []

    def get_points_ref(self, polygon_name):
        if polygon_name == "poly1":
            return self.polygon1_points
        if polygon_name == "poly2":
            return self.polygon2_points
        if polygon_name == "merged":
            return self.merged_polygon_points
        return None

    def find_polygon_hit(self, pos):
        if self.merged and self.point_in_polygon(pos, self.merged_polygon_points):
            return "merged"
        if self.polygon2_closed and self.point_in_polygon(pos, self.polygon2_points):
            return "poly2"
        if self.polygon1_closed and self.point_in_polygon(pos, self.polygon1_points):
            return "poly1"
        return None

    def find_vertex_hit(self, pos):
        for name, points, closed in (
            ("merged", self.merged_polygon_points, self.merged),
            ("poly2", self.polygon2_points, self.polygon2_closed),
            ("poly1", self.polygon1_points, self.polygon1_closed),
        ):
            if not closed:
                continue
            for index, point in enumerate(points):
                if self.distance(pos, point) <= self.vertex_pick_radius:
                    return name, index
        return None

    def translate_polygon(self, polygon_name, dx, dy):
        points = self.get_points_ref(polygon_name)
        if points is None:
            return
        for i, point in enumerate(points):
            points[i] = QPoint(point.x() + dx, point.y() + dy)

    def update_hover_cursor(self, pos):
        if self.find_vertex_hit(pos) is not None:
            self.setCursor(Qt.CrossCursor)
            return
        if self.find_polygon_hit(pos) is not None:
            self.setCursor(Qt.OpenHandCursor)
            return
        self.setCursor(Qt.ArrowCursor)

    @staticmethod
    def point_in_polygon(point, polygon_points):
        if len(polygon_points) < 3:
            return False

        x, y = point.x(), point.y()
        inside = False
        p1x, p1y = polygon_points[0].x(), polygon_points[0].y()

        for i in range(1, len(polygon_points) + 1):
            p2x, p2y = polygon_points[i % len(polygon_points)].x(), polygon_points[i % len(polygon_points)].y()
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
    def distance(p1, p2):
        return math.hypot(p1.x() - p2.x(), p1.y() - p2.y())

    @staticmethod
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    def convex_hull(self, points):
        if len(points) <= 1:
            return points

        pts = sorted(set(points))
        if len(pts) <= 2:
            return pts

        lower = []
        for point in pts:
            while len(lower) >= 2 and self.cross(lower[-2], lower[-1], point) <= 0:
                lower.pop()
            lower.append(point)

        upper = []
        for point in reversed(pts):
            while len(upper) >= 2 and self.cross(upper[-2], upper[-1], point) <= 0:
                upper.pop()
            upper.append(point)

        return lower[:-1] + upper[:-1]
