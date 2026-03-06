#pragma once

#include "CalendarRepository.h"

#include <QDate>
#include <QFileSystemWatcher>
#include <QLabel>
#include <QMainWindow>
#include <QPixmap>
#include <QScrollArea>
#include <QPushButton>
#include <QMap>
#include <QPair>
#include <QTimer>
#include <QVector>

class MainWindow : public QMainWindow {
    Q_OBJECT

public:
    explicit MainWindow(const CalendarRepository &repo, QWidget *parent = nullptr);

protected:
    void showEvent(QShowEvent *event) override;
    void resizeEvent(QResizeEvent *event) override;

private:
    static constexpr double kMinZoom = 0.25;
    static constexpr double kMaxZoom = 6.0;
    static constexpr double kZoomInStep = 1.25;
    static constexpr double kZoomOutStep = 1.0 / kZoomInStep;

    void positionOverlay();
    void addShortcuts();
    int nearestAvailableIndex(QDate target) const;
    int pickInitialIndex() const;

    void navigate(int step, const QString &unit);
    void goToToday();
    void goToSpecificDate();
    void zoom(double multiplier);

    void showCurrentDate();
    void loadImage(const QString &path);
    void refreshScaledPixmap();
    void rebuildFromRepo();
    void setupWatcher();
    void onFileSystemChanged();

    CalendarRepository m_repo;
    QVector<QDate> m_dates;
    QMap<QDate, int> m_dateToIndex;

    // month navigation helpers
    QVector<QPair<int,int>> m_monthOrder;                           // sorted (year, month)
    QMap<QPair<int,int>, QVector<int>> m_monthToDateIndices;
    QMap<QPair<int,int>, QMap<int,int>> m_monthDayToIndex;          // (year,month) -> day -> index
    QMap<QPair<int,int>, int> m_monthToOrderIndex;

    int m_currentIndex = 0;
    QPixmap m_currentPixmap;
    QString m_currentImagePath;
    bool m_initialShowDone = false;
    double m_zoomFactor = 1.0;

    QLabel *m_statusLabel = nullptr;
    QLabel *m_imageLabel = nullptr;
    QScrollArea *m_imageScroll = nullptr;
    QWidget *m_overlay = nullptr;
    QFileSystemWatcher *m_watcher = nullptr;
    QTimer *m_reloadTimer = nullptr;
};
