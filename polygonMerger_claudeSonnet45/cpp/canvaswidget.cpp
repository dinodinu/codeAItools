#include "canvaswidget.h"
#include <QPen>
#include <QBrush>
#include <QPolygon>
#include <cmath>
#include <algorithm>

CanvasWidget::CanvasWidget(QWidget *parent)
    : QWidget(parent)
    , m_currentPolygon(1)
    , m_isDrawing(true)
    , m_polygon1Closed(false)
    , m_polygon2Closed(false)
    , m_merged(false)
    , m_isDragging(false)
    , m_isDraggingVertex(false)
    , m_draggedVertexIndex(-1)
{
    setMinimumSize(800, 500);
    setStyleSheet("background-color: white;");
}

void CanvasWidget::setCurrentPolygon(int polygonNum)
{
    m_currentPolygon = polygonNum;
    m_isDrawing = true;
}

void CanvasWidget::clearAll()
{
    m_polygon1Points.clear();
    m_polygon2Points.clear();
    m_mergedPolygonPoints.clear();
    m_currentPolygon = 1;
    m_isDrawing = true;
    m_polygon1Closed = false;
    m_polygon2Closed = false;
    m_merged = false;
    m_isDragging = false;
    m_dragStartPos = QPoint();
    m_draggedPolygon.clear();
    m_isDraggingVertex = false;
    m_draggedVertexPolygon.clear();
    m_draggedVertexIndex = -1;
    update();
}

QPair<QString, int> CanvasWidget::findVertexNearPoint(const QPoint &pos)
{
    // Check vertices in order: merged, poly2, poly1
    if (m_merged) {
        for (int i = 0; i < m_mergedPolygonPoints.size(); ++i) {
            const QPoint &point = m_mergedPolygonPoints[i];
            double distance = std::sqrt(std::pow(pos.x() - point.x(), 2) + 
                                        std::pow(pos.y() - point.y(), 2));
            if (distance <= VERTEX_GRAB_THRESHOLD) {
                return qMakePair(QString("merged"), i);
            }
        }
    }

    if (m_polygon2Closed) {
        for (int i = 0; i < m_polygon2Points.size(); ++i) {
            const QPoint &point = m_polygon2Points[i];
            double distance = std::sqrt(std::pow(pos.x() - point.x(), 2) + 
                                        std::pow(pos.y() - point.y(), 2));
            if (distance <= VERTEX_GRAB_THRESHOLD) {
                return qMakePair(QString("poly2"), i);
            }
        }
    }

    if (m_polygon1Closed) {
        for (int i = 0; i < m_polygon1Points.size(); ++i) {
            const QPoint &point = m_polygon1Points[i];
            double distance = std::sqrt(std::pow(pos.x() - point.x(), 2) + 
                                        std::pow(pos.y() - point.y(), 2));
            if (distance <= VERTEX_GRAB_THRESHOLD) {
                return qMakePair(QString("poly1"), i);
            }
        }
    }

    return qMakePair(QString(), -1);
}

void CanvasWidget::mousePressEvent(QMouseEvent *event)
{
    QPoint pos = event->pos();

    // Check if we're clicking on a vertex to drag it (highest priority)
    auto [vertexPolygon, vertexIndex] = findVertexNearPoint(pos);
    if (!vertexPolygon.isEmpty()) {
        m_isDraggingVertex = true;
        m_draggedVertexPolygon = vertexPolygon;
        m_draggedVertexIndex = vertexIndex;
        setCursor(Qt::CrossCursor);
        // Clear merged polygon when editing individual polygon vertices
        if ((vertexPolygon == "poly1" || vertexPolygon == "poly2") && m_merged) {
            m_merged = false;
            m_mergedPolygonPoints.clear();
        }
        return;
    }

    // Check if we're clicking on any polygon to drag it
    // Check merged polygon first
    if (m_merged && isPointInsidePolygon(pos, m_mergedPolygonPoints)) {
        m_isDragging = true;
        m_dragStartPos = pos;
        m_draggedPolygon = "merged";
        setCursor(Qt::ClosedHandCursor);
        return;
    }

    // Check polygon 2
    if (m_polygon2Closed && isPointInsidePolygon(pos, m_polygon2Points)) {
        m_isDragging = true;
        m_dragStartPos = pos;
        m_draggedPolygon = "poly2";
        setCursor(Qt::ClosedHandCursor);
        // Clear merged polygon when moving individual polygons
        if (m_merged) {
            m_merged = false;
            m_mergedPolygonPoints.clear();
        }
        return;
    }

    // Check polygon 1
    if (m_polygon1Closed && isPointInsidePolygon(pos, m_polygon1Points)) {
        m_isDragging = true;
        m_dragStartPos = pos;
        m_draggedPolygon = "poly1";
        setCursor(Qt::ClosedHandCursor);
        // Clear merged polygon when moving individual polygons
        if (m_merged) {
            m_merged = false;
            m_mergedPolygonPoints.clear();
        }
        return;
    }

    // Handle polygon drawing
    if (!m_isDrawing || m_merged) {
        return;
    }

    QVector<QPoint> &points = (m_currentPolygon == 1) ? m_polygon1Points : m_polygon2Points;

    // Check if we should close the polygon
    if (points.size() >= 3) {
        const QPoint &firstPoint = points[0];
        double distance = std::sqrt(std::pow(pos.x() - firstPoint.x(), 2) + 
                                    std::pow(pos.y() - firstPoint.y(), 2));

        if (distance < CLOSE_THRESHOLD) {
            // Close the polygon
            if (m_currentPolygon == 1) {
                m_polygon1Closed = true;
            } else {
                m_polygon2Closed = true;
            }

            m_isDrawing = false;
            emit polygonCompleted(m_currentPolygon);
            update();
            return;
        }
    }

    // Add new point
    points.append(pos);
    update();
}

void CanvasWidget::mouseMoveEvent(QMouseEvent *event)
{
    QPoint pos = event->pos();

    // Handle vertex dragging
    if (m_isDraggingVertex && !m_draggedVertexPolygon.isEmpty()) {
        // Update the vertex position
        if (m_draggedVertexPolygon == "merged") {
            m_mergedPolygonPoints[m_draggedVertexIndex] = pos;
        } else if (m_draggedVertexPolygon == "poly1") {
            m_polygon1Points[m_draggedVertexIndex] = pos;
        } else if (m_draggedVertexPolygon == "poly2") {
            m_polygon2Points[m_draggedVertexIndex] = pos;
        }
        update();
        return;
    }

    // Handle polygon dragging
    if (m_isDragging && !m_draggedPolygon.isEmpty()) {
        // Calculate the offset
        int dx = pos.x() - m_dragStartPos.x();
        int dy = pos.y() - m_dragStartPos.y();

        // Move all points in the appropriate polygon
        if (m_draggedPolygon == "merged") {
            for (QPoint &p : m_mergedPolygonPoints) {
                p.setX(p.x() + dx);
                p.setY(p.y() + dy);
            }
        } else if (m_draggedPolygon == "poly1") {
            for (QPoint &p : m_polygon1Points) {
                p.setX(p.x() + dx);
                p.setY(p.y() + dy);
            }
        } else if (m_draggedPolygon == "poly2") {
            for (QPoint &p : m_polygon2Points) {
                p.setX(p.x() + dx);
                p.setY(p.y() + dy);
            }
        }

        // Update drag start position for next move
        m_dragStartPos = pos;
        update();
        return;
    }

    // Change cursor based on what's under the mouse (priority: vertex > polygon)
    auto [vertexPolygon, vertexIndex] = findVertexNearPoint(pos);
    Q_UNUSED(vertexIndex);
    
    if (!vertexPolygon.isEmpty()) {
        setCursor(Qt::CrossCursor);
    } else if (m_merged && isPointInsidePolygon(pos, m_mergedPolygonPoints)) {
        setCursor(Qt::OpenHandCursor);
    } else if (m_polygon2Closed && isPointInsidePolygon(pos, m_polygon2Points)) {
        setCursor(Qt::OpenHandCursor);
    } else if (m_polygon1Closed && isPointInsidePolygon(pos, m_polygon1Points)) {
        setCursor(Qt::OpenHandCursor);
    } else {
        setCursor(Qt::ArrowCursor);
    }
}

void CanvasWidget::mouseReleaseEvent(QMouseEvent *event)
{
    Q_UNUSED(event);
    
    if (m_isDraggingVertex) {
        m_isDraggingVertex = false;
        m_draggedVertexPolygon.clear();
        m_draggedVertexIndex = -1;
        setCursor(Qt::ArrowCursor);
    } else if (m_isDragging) {
        m_isDragging = false;
        m_dragStartPos = QPoint();
        m_draggedPolygon.clear();
        setCursor(Qt::ArrowCursor);
    }
}

bool CanvasWidget::isPointInsidePolygon(const QPoint &point, const QVector<QPoint> &polygonPoints)
{
    if (polygonPoints.isEmpty() || polygonPoints.size() < 3) {
        return false;
    }

    int x = point.x();
    int y = point.y();
    int n = polygonPoints.size();
    bool inside = false;

    int p1x = polygonPoints[0].x();
    int p1y = polygonPoints[0].y();
    
    for (int i = 0; i <= n; ++i) {
        int p2x = polygonPoints[i % n].x();
        int p2y = polygonPoints[i % n].y();
        
        if (y > std::min(p1y, p2y)) {
            if (y <= std::max(p1y, p2y)) {
                if (x <= std::max(p1x, p2x)) {
                    if (p1y != p2y) {
                        double xinters = static_cast<double>(y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x;
                        if (p1x == p2x || x <= xinters) {
                            inside = !inside;
                        }
                    }
                }
            }
        }
        p1x = p2x;
        p1y = p2y;
    }

    return inside;
}

void CanvasWidget::paintEvent(QPaintEvent *event)
{
    Q_UNUSED(event);
    
    QPainter painter(this);
    painter.setRenderHint(QPainter::Antialiasing);

    // Draw Polygon 1
    if (!m_polygon1Points.isEmpty()) {
        drawPolygon(painter, m_polygon1Points, 
                    QColor(100, 150, 255, 100), 
                    QColor(0, 100, 255),
                    m_polygon1Closed);
    }

    // Draw Polygon 2
    if (!m_polygon2Points.isEmpty()) {
        drawPolygon(painter, m_polygon2Points, 
                    QColor(255, 100, 100, 100), 
                    QColor(255, 0, 0),
                    m_polygon2Closed);
    }

    // Draw merged polygon
    if (m_merged && !m_mergedPolygonPoints.isEmpty()) {
        QPen pen(QColor(0, 180, 0), 3);
        painter.setPen(pen);
        QBrush brush(QColor(100, 255, 100, 80));
        painter.setBrush(brush);

        // Draw the merged polygon
        QPolygon qpolygon(m_mergedPolygonPoints);
        painter.drawPolygon(qpolygon);
    }
}

void CanvasWidget::drawPolygon(QPainter &painter, const QVector<QPoint> &points,
                                const QColor &fillColor, const QColor &lineColor, bool closed)
{
    if (points.isEmpty()) {
        return;
    }

    // Draw filled polygon if closed
    if (closed) {
        QPen pen(lineColor, 2);
        painter.setPen(pen);
        QBrush brush(fillColor);
        painter.setBrush(brush);

        QPolygon qpolygon(points);
        painter.drawPolygon(qpolygon);
    } else {
        // Draw lines between points
        QPen pen(lineColor, 2);
        painter.setPen(pen);

        for (int i = 0; i < points.size() - 1; ++i) {
            painter.drawLine(points[i], points[i + 1]);
        }
    }

    // Draw vertices
    QPen pen(lineColor, 2);
    painter.setPen(pen);
    QBrush brush(lineColor);
    painter.setBrush(brush);

    for (int i = 0; i < points.size(); ++i) {
        const QPoint &point = points[i];
        if (i == 0) {
            // Draw first point larger
            painter.drawEllipse(point, POINT_RADIUS + 2, POINT_RADIUS + 2);
        } else {
            painter.drawEllipse(point, POINT_RADIUS, POINT_RADIUS);
        }
    }
}

void CanvasWidget::mergePolygons()
{
    if (!m_polygon1Closed || !m_polygon2Closed) {
        return;
    }

    // Convert QPoint lists to coordinate tuples
    QVector<QPair<double, double>> poly1Coords;
    for (const QPoint &p : m_polygon1Points) {
        poly1Coords.append(qMakePair(static_cast<double>(p.x()), static_cast<double>(p.y())));
    }

    QVector<QPair<double, double>> poly2Coords;
    for (const QPoint &p : m_polygon2Points) {
        poly2Coords.append(qMakePair(static_cast<double>(p.x()), static_cast<double>(p.y())));
    }

    // Fallback to convex hull (for a proper polygon union, you'd use a library like CGAL or Clipper)
    QVector<QPair<double, double>> allPoints = poly1Coords + poly2Coords;
    QVector<QPair<double, double>> hull = convexHull(allPoints);
    
    m_mergedPolygonPoints.clear();
    for (const auto &coord : hull) {
        m_mergedPolygonPoints.append(QPoint(static_cast<int>(coord.first), 
                                            static_cast<int>(coord.second)));
    }

    m_merged = true;
    update();
}

QVector<QPair<double, double>> CanvasWidget::convexHull(const QVector<QPair<double, double>> &points)
{
    if (points.size() < 3) {
        return points;
    }

    // Find the bottommost point (or leftmost if tie)
    auto start = *std::min_element(points.begin(), points.end(), 
        [](const auto &a, const auto &b) {
            return (a.second < b.second) || (a.second == b.second && a.first < b.first);
        });

    // Sort points by polar angle with respect to start point
    QVector<QPair<double, double>> sortedPoints;
    for (const auto &p : points) {
        if (p != start) {
            sortedPoints.append(p);
        }
    }

    std::sort(sortedPoints.begin(), sortedPoints.end(), 
        [&start](const auto &a, const auto &b) {
            double angleA = std::atan2(a.second - start.second, a.first - start.first);
            double angleB = std::atan2(b.second - start.second, b.first - start.first);
            return angleA < angleB;
        });

    // Graham scan
    QVector<QPair<double, double>> hull;
    hull.append(start);
    if (!sortedPoints.isEmpty()) {
        hull.append(sortedPoints[0]);
    }

    for (int i = 1; i < sortedPoints.size(); ++i) {
        while (hull.size() > 1 && crossProduct(hull[hull.size() - 2], hull.back(), sortedPoints[i]) <= 0) {
            hull.pop_back();
        }
        hull.append(sortedPoints[i]);
    }

    return hull;
}

double CanvasWidget::crossProduct(const QPair<double, double> &o, 
                                   const QPair<double, double> &a, 
                                   const QPair<double, double> &b)
{
    return (a.first - o.first) * (b.second - o.second) - 
           (a.second - o.second) * (b.first - o.first);
}
