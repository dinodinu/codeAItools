#ifndef CANVASWIDGET_H
#define CANVASWIDGET_H

#include <QWidget>
#include <QPoint>
#include <QVector>
#include <QPainter>
#include <QMouseEvent>

class CanvasWidget : public QWidget
{
    Q_OBJECT

public:
    explicit CanvasWidget(QWidget *parent = nullptr);
    
    void setCurrentPolygon(int polygonNum);
    void clearAll();
    void mergePolygons();

signals:
    void polygonCompleted(int polygonNum);

protected:
    void paintEvent(QPaintEvent *event) override;
    void mousePressEvent(QMouseEvent *event) override;
    void mouseMoveEvent(QMouseEvent *event) override;
    void mouseReleaseEvent(QMouseEvent *event) override;

private:
    // Helper methods
    QPair<QString, int> findVertexNearPoint(const QPoint &pos);
    bool isPointInsidePolygon(const QPoint &point, const QVector<QPoint> &polygonPoints);
    void drawPolygon(QPainter &painter, const QVector<QPoint> &points, 
                     const QColor &fillColor, const QColor &lineColor, bool closed);
    QVector<QPair<double, double>> convexHull(const QVector<QPair<double, double>> &points);
    double crossProduct(const QPair<double, double> &o, 
                        const QPair<double, double> &a, 
                        const QPair<double, double> &b);

    // Polygon data
    QVector<QPoint> m_polygon1Points;
    QVector<QPoint> m_polygon2Points;
    QVector<QPoint> m_mergedPolygonPoints;

    // Drawing state
    int m_currentPolygon;
    bool m_isDrawing;
    bool m_polygon1Closed;
    bool m_polygon2Closed;
    bool m_merged;

    // Drag state for polygons
    bool m_isDragging;
    QPoint m_dragStartPos;
    QString m_draggedPolygon;

    // Vertex dragging state
    bool m_isDraggingVertex;
    QString m_draggedVertexPolygon;
    int m_draggedVertexIndex;

    // Styling constants
    static constexpr int POINT_RADIUS = 5;
    static constexpr int CLOSE_THRESHOLD = 15;
    static constexpr int VERTEX_GRAB_THRESHOLD = 10;
};

#endif // CANVASWIDGET_H
