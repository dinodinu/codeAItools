#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include <QLabel>
#include <QPushButton>

class CanvasWidget;

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    explicit MainWindow(QWidget *parent = nullptr);
    ~MainWindow() = default;

private slots:
    void switchPolygon();
    void onPolygonCompleted(int polygonNum);
    void mergePolygons();
    void clearAll();

private:
    void initUI();

    CanvasWidget *m_canvas;
    QLabel *m_statusLabel;
    QPushButton *m_switchBtn;
    QPushButton *m_mergeBtn;
    QPushButton *m_clearBtn;
};

#endif // MAINWINDOW_H
