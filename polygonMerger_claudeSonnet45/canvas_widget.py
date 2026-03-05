"""
Canvas Widget for drawing and merging polygons
"""

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QPoint, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QPolygon
import math


class CanvasWidget(QWidget):
    polygon_completed = pyqtSignal(int)  # Signal emitted when a polygon is completed
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(800, 500)
        self.setStyleSheet('background-color: white;')
        
        # Polygon data
        self.polygon1_points = []
        self.polygon2_points = []
        self.merged_polygon_points = []
        
        # Drawing state
        self.current_polygon = 1
        self.is_drawing = True
        self.polygon1_closed = False
        self.polygon2_closed = False
        self.merged = False
        
        # Drag state for polygons
        self.is_dragging = False
        self.drag_start_pos = None
        self.dragged_polygon = None  # Track which polygon is being dragged ('poly1', 'poly2', or 'merged')
        
        # Vertex dragging state
        self.is_dragging_vertex = False
        self.dragged_vertex_polygon = None  # Which polygon the vertex belongs to
        self.dragged_vertex_index = None  # Index of the vertex being dragged
        
        # Styling
        self.point_radius = 5
        self.close_threshold = 15  # Distance to close polygon
        self.vertex_grab_threshold = 10  # Distance to grab a vertex
        
    def set_current_polygon(self, polygon_num):
        """Switch to drawing a different polygon"""
        self.current_polygon = polygon_num
        self.is_drawing = True
        
    def clear_all(self):
        """Clear all polygons and reset state"""
        self.polygon1_points = []
        self.polygon2_points = []
        self.merged_polygon_points = []
        self.current_polygon = 1
        self.is_drawing = True
        self.polygon1_closed = False
        self.polygon2_closed = False
        self.merged = False
        self.is_dragging = False
        self.drag_start_pos = None
        self.dragged_polygon = None
        self.is_dragging_vertex = False
        self.dragged_vertex_polygon = None
        self.dragged_vertex_index = None
        self.update()
        
    def find_vertex_near_point(self, pos):
        """Find if there's a vertex near the given point. Returns (polygon_name, vertex_index) or (None, None)"""
        # Check vertices in order: merged, poly2, poly1
        if self.merged:
            for i, point in enumerate(self.merged_polygon_points):
                distance = math.sqrt((pos.x() - point.x())**2 + (pos.y() - point.y())**2)
                if distance <= self.vertex_grab_threshold:
                    return ('merged', i)
        
        if self.polygon2_closed:
            for i, point in enumerate(self.polygon2_points):
                distance = math.sqrt((pos.x() - point.x())**2 + (pos.y() - point.y())**2)
                if distance <= self.vertex_grab_threshold:
                    return ('poly2', i)
        
        if self.polygon1_closed:
            for i, point in enumerate(self.polygon1_points):
                distance = math.sqrt((pos.x() - point.x())**2 + (pos.y() - point.y())**2)
                if distance <= self.vertex_grab_threshold:
                    return ('poly1', i)
        
        return (None, None)
    
    def mousePressEvent(self, event):
        """Handle mouse clicks for adding polygon vertices or starting drag"""
        pos = event.pos()
        
        # Check if we're clicking on a vertex to drag it (highest priority)
        vertex_polygon, vertex_index = self.find_vertex_near_point(pos)
        if vertex_polygon is not None:
            self.is_dragging_vertex = True
            self.dragged_vertex_polygon = vertex_polygon
            self.dragged_vertex_index = vertex_index
            self.setCursor(Qt.CrossCursor)
            # Clear merged polygon when editing individual polygon vertices
            if vertex_polygon in ['poly1', 'poly2'] and self.merged:
                self.merged = False
                self.merged_polygon_points = []
            return
        
        # Check if we're clicking on any polygon to drag it (check in reverse order of drawing)
        # Check merged polygon first
        if self.merged and self.is_point_inside_polygon(pos, self.merged_polygon_points):
            self.is_dragging = True
            self.drag_start_pos = pos
            self.dragged_polygon = 'merged'
            self.setCursor(Qt.ClosedHandCursor)
            return
        
        # Check polygon 2
        if self.polygon2_closed and self.is_point_inside_polygon(pos, self.polygon2_points):
            self.is_dragging = True
            self.drag_start_pos = pos
            self.dragged_polygon = 'poly2'
            self.setCursor(Qt.ClosedHandCursor)
            # Clear merged polygon when moving individual polygons
            if self.merged:
                self.merged = False
                self.merged_polygon_points = []
            return
        
        # Check polygon 1
        if self.polygon1_closed and self.is_point_inside_polygon(pos, self.polygon1_points):
            self.is_dragging = True
            self.drag_start_pos = pos
            self.dragged_polygon = 'poly1'
            self.setCursor(Qt.ClosedHandCursor)
            # Clear merged polygon when moving individual polygons
            if self.merged:
                self.merged = False
                self.merged_polygon_points = []
            return
        
        # Handle polygon drawing
        if not self.is_drawing or self.merged:
            return
        
        if self.current_polygon == 1:
            points = self.polygon1_points
        else:
            points = self.polygon2_points
            
        # Check if we should close the polygon
        if len(points) >= 3:
            first_point = points[0]
            distance = math.sqrt((pos.x() - first_point.x())**2 + (pos.y() - first_point.y())**2)
            
            if distance < self.close_threshold:
                # Close the polygon
                if self.current_polygon == 1:
                    self.polygon1_closed = True
                else:
                    self.polygon2_closed = True
                    
                self.is_drawing = False
                self.polygon_completed.emit(self.current_polygon)
                self.update()
                return
        
        # Add new point
        points.append(pos)
        self.update()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging polygons/vertices or cursor feedback"""
        pos = event.pos()
        
        # Handle vertex dragging
        if self.is_dragging_vertex and self.dragged_vertex_polygon is not None:
            # Update the vertex position
            if self.dragged_vertex_polygon == 'merged':
                self.merged_polygon_points[self.dragged_vertex_index] = pos
            elif self.dragged_vertex_polygon == 'poly1':
                self.polygon1_points[self.dragged_vertex_index] = pos
            elif self.dragged_vertex_polygon == 'poly2':
                self.polygon2_points[self.dragged_vertex_index] = pos
            
            self.update()
            return
        
        # Handle polygon dragging
        if self.is_dragging and self.drag_start_pos and self.dragged_polygon:
            # Calculate the offset
            dx = pos.x() - self.drag_start_pos.x()
            dy = pos.y() - self.drag_start_pos.y()
            
            # Move all points in the appropriate polygon
            if self.dragged_polygon == 'merged':
                self.merged_polygon_points = [
                    QPoint(p.x() + dx, p.y() + dy) 
                    for p in self.merged_polygon_points
                ]
            elif self.dragged_polygon == 'poly1':
                self.polygon1_points = [
                    QPoint(p.x() + dx, p.y() + dy) 
                    for p in self.polygon1_points
                ]
            elif self.dragged_polygon == 'poly2':
                self.polygon2_points = [
                    QPoint(p.x() + dx, p.y() + dy) 
                    for p in self.polygon2_points
                ]
            
            # Update drag start position for next move
            self.drag_start_pos = pos
            self.update()
            return
        
        # Change cursor based on what's under the mouse (priority: vertex > polygon)
        vertex_polygon, _ = self.find_vertex_near_point(pos)
        if vertex_polygon is not None:
            self.setCursor(Qt.CrossCursor)
        elif self.merged and self.is_point_inside_polygon(pos, self.merged_polygon_points):
            self.setCursor(Qt.OpenHandCursor)
        elif self.polygon2_closed and self.is_point_inside_polygon(pos, self.polygon2_points):
            self.setCursor(Qt.OpenHandCursor)
        elif self.polygon1_closed and self.is_point_inside_polygon(pos, self.polygon1_points):
            self.setCursor(Qt.OpenHandCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release to stop dragging"""
        if self.is_dragging_vertex:
            self.is_dragging_vertex = False
            self.dragged_vertex_polygon = None
            self.dragged_vertex_index = None
            self.setCursor(Qt.ArrowCursor)
        elif self.is_dragging:
            self.is_dragging = False
            self.drag_start_pos = None
            self.dragged_polygon = None
            self.setCursor(Qt.ArrowCursor)
    
    def is_point_inside_polygon(self, point, polygon_points):
        """Check if a point is inside a polygon using ray casting algorithm"""
        if not polygon_points or len(polygon_points) < 3:
            return False
        
        x, y = point.x(), point.y()
        n = len(polygon_points)
        inside = False
        
        p1x, p1y = polygon_points[0].x(), polygon_points[0].y()
        for i in range(n + 1):
            p2x, p2y = polygon_points[i % n].x(), polygon_points[i % n].y()
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
        
    def paintEvent(self, event):
        """Draw the polygons on the canvas"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw Polygon 1
        if self.polygon1_points:
            self.draw_polygon(painter, self.polygon1_points, 
                            QColor(100, 150, 255, 100), 
                            QColor(0, 100, 255),
                            self.polygon1_closed)
        
        # Draw Polygon 2
        if self.polygon2_points:
            self.draw_polygon(painter, self.polygon2_points, 
                            QColor(255, 100, 100, 100), 
                            QColor(255, 0, 0),
                            self.polygon2_closed)
        
        # Draw merged polygon
        if self.merged and self.merged_polygon_points:
            pen = QPen(QColor(0, 180, 0), 3)
            painter.setPen(pen)
            brush = QBrush(QColor(100, 255, 100, 80))
            painter.setBrush(brush)
            
            # Draw the merged polygon
            qpolygon = QPolygon(self.merged_polygon_points)
            painter.drawPolygon(qpolygon)
            
    def draw_polygon(self, painter, points, fill_color, line_color, closed):
        """Draw a single polygon with given styling"""
        if not points:
            return
            
        # Draw filled polygon if closed
        if closed:
            pen = QPen(line_color, 2)
            painter.setPen(pen)
            brush = QBrush(fill_color)
            painter.setBrush(brush)
            
            qpolygon = QPolygon(points)
            painter.drawPolygon(qpolygon)
        else:
            # Draw lines between points
            pen = QPen(line_color, 2)
            painter.setPen(pen)
            
            for i in range(len(points) - 1):
                painter.drawLine(points[i], points[i + 1])
        
        # Draw vertices
        pen = QPen(line_color, 2)
        painter.setPen(pen)
        brush = QBrush(line_color)
        painter.setBrush(brush)
        
        for i, point in enumerate(points):
            if i == 0:
                # Draw first point larger
                painter.drawEllipse(point, self.point_radius + 2, self.point_radius + 2)
            else:
                painter.drawEllipse(point, self.point_radius, self.point_radius)
                
    def merge_polygons(self):
        """Merge the two polygons using polygon union algorithm"""
        if not self.polygon1_closed or not self.polygon2_closed:
            return
            
        # Convert QPoint lists to coordinate tuples
        poly1_coords = [(p.x(), p.y()) for p in self.polygon1_points]
        poly2_coords = [(p.x(), p.y()) for p in self.polygon2_points]
        
        try:
            # Try using Shapely for robust polygon operations
            from shapely.geometry import Polygon
            from shapely.ops import unary_union
            
            poly1 = Polygon(poly1_coords)
            poly2 = Polygon(poly2_coords)
            
            # Merge polygons using union
            merged = unary_union([poly1, poly2])
            
            # Extract exterior coordinates
            if hasattr(merged, 'exterior'):
                # Single polygon result
                coords = list(merged.exterior.coords)
            elif hasattr(merged, 'geoms'):
                # Multiple polygons - take the convex hull or largest
                coords = list(merged.convex_hull.exterior.coords)
            else:
                coords = []
                
            # Convert back to QPoints
            self.merged_polygon_points = [QPoint(int(x), int(y)) for x, y in coords[:-1]]
            
        except ImportError:
            # Fallback to simple convex hull if Shapely is not available
            print("Shapely not available, using convex hull fallback")
            all_points = poly1_coords + poly2_coords
            hull = self.convex_hull(all_points)
            self.merged_polygon_points = [QPoint(int(x), int(y)) for x, y in hull]
        
        self.merged = True
        self.update()
        
    def convex_hull(self, points):
        """Compute convex hull using Graham scan algorithm"""
        if len(points) < 3:
            return points
            
        # Find the bottommost point (or leftmost if tie)
        start = min(points, key=lambda p: (p[1], p[0]))
        
        # Sort points by polar angle with respect to start point
        def polar_angle(p):
            dx = p[0] - start[0]
            dy = p[1] - start[1]
            return math.atan2(dy, dx)
            
        sorted_points = sorted([p for p in points if p != start], key=polar_angle)
        
        # Graham scan
        hull = [start, sorted_points[0]]
        
        for point in sorted_points[1:]:
            while len(hull) > 1 and self.cross_product(hull[-2], hull[-1], point) <= 0:
                hull.pop()
            hull.append(point)
            
        return hull
        
    def cross_product(self, o, a, b):
        """Calculate cross product of vectors OA and OB"""
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
