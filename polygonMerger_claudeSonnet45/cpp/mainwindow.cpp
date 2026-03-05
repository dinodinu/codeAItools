#include "mainwindow.h"
#include "canvaswidget.h"

#include <QWidget>
#include <QVBoxLayout>
#include <QHBoxLayout>

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
    , m_canvas(nullptr)
    , m_statusLabel(nullptr)
    , m_switchBtn(nullptr)
    , m_mergeBtn(nullptr)
    , m_clearBtn(nullptr)
{
    initUI();
}

void MainWindow::initUI()
{
    setWindowTitle("Polygon Merger - Draw and Merge Polygons");
    setGeometry(100, 100, 1000, 700);

    // Create central widget
    QWidget *centralWidget = new QWidget(this);
    setCentralWidget(centralWidget);

    // Main layout
    QVBoxLayout *mainLayout = new QVBoxLayout(centralWidget);

    // Canvas widget
    m_canvas = new CanvasWidget(this);
    mainLayout->addWidget(m_canvas);

    // Control panel
    QHBoxLayout *controlLayout = new QHBoxLayout();

    // Status label
    m_statusLabel = new QLabel("Click to draw Polygon 1 (blue). Close polygon by clicking near first point.", this);
    m_statusLabel->setStyleSheet("font-size: 12pt; padding: 5px;");
    controlLayout->addWidget(m_statusLabel);

    // Buttons
    m_switchBtn = new QPushButton("Switch to Polygon 2", this);
    connect(m_switchBtn, &QPushButton::clicked, this, &MainWindow::switchPolygon);
    m_switchBtn->setEnabled(false);
    controlLayout->addWidget(m_switchBtn);

    m_mergeBtn = new QPushButton("Merge Polygons", this);
    connect(m_mergeBtn, &QPushButton::clicked, this, &MainWindow::mergePolygons);
    m_mergeBtn->setEnabled(false);
    controlLayout->addWidget(m_mergeBtn);

    m_clearBtn = new QPushButton("Clear All", this);
    connect(m_clearBtn, &QPushButton::clicked, this, &MainWindow::clearAll);
    controlLayout->addWidget(m_clearBtn);

    mainLayout->addLayout(controlLayout);

    // Connect canvas signals
    connect(m_canvas, &CanvasWidget::polygonCompleted, this, &MainWindow::onPolygonCompleted);
}

void MainWindow::switchPolygon()
{
    m_canvas->setCurrentPolygon(2);
    m_statusLabel->setText("Click to draw Polygon 2 (red). Close polygon by clicking near first point.");
    m_switchBtn->setEnabled(false);
}

void MainWindow::onPolygonCompleted(int polygonNum)
{
    if (polygonNum == 1) {
        m_statusLabel->setText("Polygon 1 completed! Drag polygon to move or drag vertices to adjust. Click \"Switch to Polygon 2\".");
        m_switchBtn->setEnabled(true);
    } else if (polygonNum == 2) {
        m_statusLabel->setText("Both polygons completed! Drag polygons/vertices to adjust. Click \"Merge Polygons\" to combine.");
        m_mergeBtn->setEnabled(true);
    }
}

void MainWindow::mergePolygons()
{
    m_canvas->mergePolygons();
    m_statusLabel->setText("Merged! Drag any polygon/vertex to adjust. Re-click \"Merge\" after editing to update.");
    // Keep merge button enabled so users can re-merge after moving polygons
}

void MainWindow::clearAll()
{
    m_canvas->clearAll();
    m_statusLabel->setText("Click to draw Polygon 1 (blue). Close polygon by clicking near first point.");
    m_switchBtn->setEnabled(false);
    m_mergeBtn->setEnabled(false);
}
