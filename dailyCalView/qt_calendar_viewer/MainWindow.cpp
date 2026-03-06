#include "MainWindow.h"

#include <QAction>
#include <QCalendarWidget>
#include <QDialog>
#include <QDialogButtonBox>
#include <QDir>
#include <QHBoxLayout>
#include <QImageReader>
#include <QSet>
#include <QSizePolicy>
#include <QVBoxLayout>
#include <algorithm>
#include <cmath>

MainWindow::MainWindow(const CalendarRepository &repo, QWidget *parent)
    : QMainWindow(parent), m_repo(repo), m_dates(repo.dates)
{
    // Build lookup tables
    for (int i = 0; i < m_dates.size(); ++i)
        m_dateToIndex[m_dates[i]] = i;

    QSet<QPair<int,int>> monthSet;
    for (const auto &d : m_dates) {
        auto key = qMakePair(d.year(), d.month());
        monthSet.insert(key);
        m_monthToDateIndices[key].append(m_dateToIndex[d]);
        m_monthDayToIndex[key][d.day()] = m_dateToIndex[d];
    }
    m_monthOrder = monthSet.values().toVector();
    std::sort(m_monthOrder.begin(), m_monthOrder.end());
    for (int i = 0; i < m_monthOrder.size(); ++i)
        m_monthToOrderIndex[m_monthOrder[i]] = i;

    m_currentIndex = pickInitialIndex();
    resize(1200, 800);

    // Status label
    m_statusLabel = new QLabel;
    m_statusLabel->setAlignment(Qt::AlignCenter);
    m_statusLabel->setStyleSheet("color: #bbb; font-size: 12px;");
    m_statusLabel->setSizePolicy(QSizePolicy::Minimum, QSizePolicy::Preferred);
    m_statusLabel->setMinimumWidth(40);

    // Image area
    m_imageLabel = new QLabel(tr("No image"));
    m_imageLabel->setAlignment(Qt::AlignCenter);
    m_imageLabel->setStyleSheet("background: #111; color: #ddd;");
    m_imageLabel->setMinimumSize(1, 1);

    m_imageScroll = new QScrollArea;
    m_imageScroll->setWidget(m_imageLabel);
    m_imageScroll->setWidgetResizable(false);
    m_imageScroll->setAlignment(Qt::AlignCenter);
    m_imageScroll->setStyleSheet("background: #111;");

    // --- Buttons ---
    const QString overlayBtnStyle =
        "QPushButton { color: #ddd; background: rgba(50,50,50,200); "
        "border: 1px solid #444; border-radius: 4px; padding: 5px 12px; font-size: 12px; } "
        "QPushButton:hover { background: rgba(80,80,80,230); color: #fff; }";

    auto makeBtn = [&](const QString &text, const QString &tip) {
        auto *btn = new QPushButton(text);
        btn->setToolTip(tip);
        btn->setStyleSheet(overlayBtnStyle);
        btn->setSizePolicy(QSizePolicy::Fixed, QSizePolicy::Fixed);
        return btn;
    };

    auto *prevMonthBtn = makeBtn(QStringLiteral("\u23ee"), tr("Previous Month"));
    auto *prevDayBtn   = makeBtn(QStringLiteral("\u25c0"), tr("Previous Day"));
    auto *nextDayBtn   = makeBtn(QStringLiteral("\u25b6"), tr("Next Day"));
    auto *nextMonthBtn = makeBtn(QStringLiteral("\u23ed"), tr("Next Month"));
    auto *todayBtn     = makeBtn(tr("Today"), tr("Today"));
    auto *gotoBtn      = makeBtn(tr("Go To Date"), tr("Go To Date"));
    auto *zoomOutBtn   = makeBtn(QStringLiteral("\u2212"), tr("Zoom Out"));
    auto *fitBtn       = makeBtn(tr("Fit"), tr("Fit to Window"));
    auto *zoomInBtn    = makeBtn(QStringLiteral("+"), tr("Zoom In"));
    auto *quitBtn      = makeBtn(tr("Quit"), tr("Quit"));

    connect(prevMonthBtn, &QPushButton::clicked, this, [this]{ navigate(-1, "month"); });
    connect(prevDayBtn,   &QPushButton::clicked, this, [this]{ navigate(-1, "day"); });
    connect(nextDayBtn,   &QPushButton::clicked, this, [this]{ navigate( 1, "day"); });
    connect(nextMonthBtn, &QPushButton::clicked, this, [this]{ navigate( 1, "month"); });
    connect(todayBtn,     &QPushButton::clicked, this, &MainWindow::goToToday);
    connect(gotoBtn,      &QPushButton::clicked, this, &MainWindow::goToSpecificDate);
    connect(zoomOutBtn,   &QPushButton::clicked, this, [this]{ zoom(kZoomOutStep); });
    connect(fitBtn,       &QPushButton::clicked, this, [this]{ zoom(0); });
    connect(zoomInBtn,    &QPushButton::clicked, this, [this]{ zoom(kZoomInStep); });
    connect(quitBtn,      &QPushButton::clicked, this, &QWidget::close);

    // Overlay widget
    m_overlay = new QWidget(m_imageScroll);
    m_overlay->setStyleSheet("background: rgba(0, 0, 0, 150); border-radius: 8px;");

    auto *overlayLayout = new QHBoxLayout(m_overlay);
    overlayLayout->setContentsMargins(10, 6, 10, 6);
    overlayLayout->addWidget(prevMonthBtn);
    overlayLayout->addWidget(prevDayBtn);
    overlayLayout->addSpacing(8);
    overlayLayout->addWidget(todayBtn);
    overlayLayout->addWidget(gotoBtn);
    overlayLayout->addSpacing(8);
    overlayLayout->addWidget(nextDayBtn);
    overlayLayout->addWidget(nextMonthBtn);
    overlayLayout->addStretch(1);
    overlayLayout->addWidget(zoomOutBtn);
    overlayLayout->addWidget(fitBtn);
    overlayLayout->addWidget(zoomInBtn);
    overlayLayout->addSpacing(8);
    overlayLayout->addWidget(m_statusLabel);
    overlayLayout->addSpacing(8);
    overlayLayout->addWidget(quitBtn);

    // Main layout
    auto *central = new QWidget;
    auto *mainLayout = new QHBoxLayout(central);
    mainLayout->setContentsMargins(0, 0, 0, 0);
    mainLayout->setSpacing(0);
    mainLayout->addWidget(m_imageScroll, 1);
    setCentralWidget(central);

    addShortcuts();
    setupWatcher();
}

// ---- Events ----

void MainWindow::showEvent(QShowEvent *event)
{
    QMainWindow::showEvent(event);
    positionOverlay();
    if (m_initialShowDone) return;
    m_initialShowDone = true;
    showCurrentDate();
}

void MainWindow::resizeEvent(QResizeEvent *event)
{
    QMainWindow::resizeEvent(event);
    positionOverlay();
    if (!m_currentImagePath.isEmpty())
        loadImage(m_currentImagePath);
    else
        refreshScaledPixmap();
}

// ---- Overlay positioning ----

void MainWindow::positionOverlay()
{
    auto *vp = m_imageScroll->viewport();
    QRect vpGeo = vp->geometry();
    QSize hint = m_overlay->sizeHint();
    int ow = qMin(hint.width(), vpGeo.width() - 20);
    int oh = hint.height();
    int x = vpGeo.x() + vpGeo.width() - ow - 10;
    int y = vpGeo.y() + vpGeo.height() - oh - 10;
    m_overlay->setGeometry(x, y, ow, oh);
    m_overlay->raise();
}

// ---- Shortcuts ----

void MainWindow::addShortcuts()
{
    struct ShortcutDef { QString key; std::function<void()> handler; };
    ShortcutDef defs[] = {
        {"Right", [this]{ navigate( 1, "day"); }},
        {"Left",  [this]{ navigate(-1, "day"); }},
        {"Up",    [this]{ navigate( 1, "month"); }},
        {"Down",  [this]{ navigate(-1, "month"); }},
        {"T",     [this]{ goToToday(); }},
        {"G",     [this]{ goToSpecificDate(); }},
        {"Ctrl+=", [this]{ zoom(kZoomInStep); }},
        {"Ctrl+-", [this]{ zoom(kZoomOutStep); }},
        {"Ctrl+0", [this]{ zoom(0); }},
        {"Ctrl+Q", [this]{ close(); }},
    };
    for (auto &d : defs) {
        auto *action = new QAction(this);
        action->setShortcut(QKeySequence(d.key));
        connect(action, &QAction::triggered, this, d.handler);
        addAction(action);
    }
}

// ---- Navigation ----

int MainWindow::nearestAvailableIndex(QDate target) const
{
    auto it = std::lower_bound(m_dates.begin(), m_dates.end(), target);
    int pos = static_cast<int>(it - m_dates.begin());
    if (pos == 0) return 0;
    if (pos >= m_dates.size()) return m_dates.size() - 1;
    int diffBefore = m_dates[pos - 1].daysTo(target);
    int diffAfter  = target.daysTo(m_dates[pos]);
    return (diffBefore <= diffAfter) ? pos - 1 : pos;
}

int MainWindow::pickInitialIndex() const
{
    return nearestAvailableIndex(QDate::currentDate());
}

void MainWindow::navigate(int step, const QString &unit)
{
    if (unit == "day") {
        m_currentIndex = (m_currentIndex + step + m_dates.size()) % m_dates.size();
    } else {
        QDate cur = m_dates[m_currentIndex];
        auto curKey = qMakePair(cur.year(), cur.month());
        int mi = m_monthToOrderIndex[curKey];
        int ti = (mi + step + m_monthOrder.size()) % m_monthOrder.size();
        auto targetMonth = m_monthOrder[ti];
        const auto &indices = m_monthToDateIndices[targetMonth];
        auto dayIt = m_monthDayToIndex[targetMonth].find(cur.day());
        if (dayIt != m_monthDayToIndex[targetMonth].end()) {
            m_currentIndex = dayIt.value();
        } else {
            m_currentIndex = (step > 0) ? indices.last() : indices.first();
        }
    }
    showCurrentDate();
}

void MainWindow::goToToday()
{
    m_currentIndex = nearestAvailableIndex(QDate::currentDate());
    showCurrentDate();
}

void MainWindow::goToSpecificDate()
{
    QDate current = m_dates[m_currentIndex];
    QDialog dialog(this);
    dialog.setWindowTitle(tr("Go To Date"));

    auto *layout = new QVBoxLayout(&dialog);
    auto *calendar = new QCalendarWidget(&dialog);
    calendar->setSelectedDate(current);
    calendar->setGridVisible(true);
    layout->addWidget(calendar);

    auto *buttons = new QDialogButtonBox(
        QDialogButtonBox::Ok | QDialogButtonBox::Cancel);
    connect(buttons, &QDialogButtonBox::accepted, &dialog, &QDialog::accept);
    connect(buttons, &QDialogButtonBox::rejected, &dialog, &QDialog::reject);
    layout->addWidget(buttons);

    if (dialog.exec() != QDialog::Accepted) return;

    QDate target = calendar->selectedDate();
    auto it = m_dateToIndex.find(target);
    m_currentIndex = (it != m_dateToIndex.end()) ? it.value()
                                                  : nearestAvailableIndex(target);
    showCurrentDate();

    QDate shown = m_dates[m_currentIndex];
    if (shown != target) {
        m_statusLabel->setText(
            tr("No exact image for %1. Showing nearest: %2")
                .arg(target.toString(Qt::ISODate), shown.toString(Qt::ISODate)));
    }
}

// ---- Zoom ----

void MainWindow::zoom(double multiplier)
{
    if (multiplier != 0.0)
        m_zoomFactor = qBound(kMinZoom, m_zoomFactor * multiplier, kMaxZoom);
    else
        m_zoomFactor = 1.0;
    refreshScaledPixmap();
}

// ---- Image display ----

void MainWindow::showCurrentDate()
{
    QDate targetDate = m_dates[m_currentIndex];
    const auto &images = m_repo.byDate[targetDate];
    setWindowTitle(targetDate.toString("dddd, dd MMMM yyyy")
                   + QStringLiteral("  \u2014  Daily Calendar Viewer"));

    if (!images.isEmpty()) {
        m_zoomFactor = 1.0;
        loadImage(images.first());
        if (images.size() == 1) {
            m_statusLabel->setText(tr("Showing %1").arg(QFileInfo(images.first()).fileName()));
        } else {
            m_statusLabel->setText(
                tr("Showing first of %1 images: %2")
                    .arg(images.size())
                    .arg(QFileInfo(images.first()).fileName()));
        }
    } else {
        m_statusLabel->setText(tr("No images found for this date"));
        m_currentImagePath.clear();
        m_currentPixmap = QPixmap();
        m_imageLabel->setText(tr("No image"));
        m_imageLabel->setPixmap(QPixmap());
        m_imageLabel->adjustSize();
    }
    positionOverlay();
}

void MainWindow::loadImage(const QString &path)
{
    m_currentImagePath = path;

    QImageReader reader(path);
    reader.setAutoTransform(true);

    QSize targetSize = m_imageScroll->viewport()->size();
    QSize sourceSize = reader.size();
    if (targetSize.width() > 0 && targetSize.height() > 0
        && sourceSize.width() > 0 && sourceSize.height() > 0) {
        sourceSize.scale(targetSize, Qt::KeepAspectRatio);
        reader.setScaledSize(sourceSize);
    }

    QImage image = reader.read();
    if (image.isNull()) {
        m_statusLabel->setText(tr("Failed to load: %1").arg(QFileInfo(path).fileName()));
        return;
    }

    m_currentPixmap = QPixmap::fromImage(image);
    refreshScaledPixmap();
}

void MainWindow::refreshScaledPixmap()
{
    if (m_currentPixmap.isNull()) return;

    QSize viewport = m_imageScroll->viewport()->size();
    if (viewport.width() <= 0 || viewport.height() <= 0) return;

    QSize fitSize = m_currentPixmap.size();
    fitSize.scale(viewport, Qt::KeepAspectRatio);
    QSize zoomedSize = fitSize * m_zoomFactor;

    QPixmap scaled = m_currentPixmap.scaled(
        zoomedSize, Qt::KeepAspectRatio, Qt::FastTransformation);
    m_imageLabel->setPixmap(scaled);
    m_imageLabel->resize(scaled.size());
}

// ---- File system watcher ----

void MainWindow::setupWatcher()
{
    m_watcher = new QFileSystemWatcher(this);
    m_reloadTimer = new QTimer(this);
    m_reloadTimer->setSingleShot(true);
    m_reloadTimer->setInterval(500);

    connect(m_reloadTimer, &QTimer::timeout, this, &MainWindow::onFileSystemChanged);

    auto scheduleReload = [this](const QString &) {
        m_reloadTimer->start();
    };
    connect(m_watcher, &QFileSystemWatcher::directoryChanged, this, scheduleReload);
    connect(m_watcher, &QFileSystemWatcher::fileChanged, this, scheduleReload);

    // Watch root and all subdirectories
    QString root = m_repo.rootPath();
    m_watcher->addPath(root);
    QDir rootDir(root);
    for (const QString &sub : rootDir.entryList(QDir::Dirs | QDir::NoDotAndDotDot))
        m_watcher->addPath(rootDir.filePath(sub));
}

void MainWindow::onFileSystemChanged()
{
    QDate currentDate;
    if (!m_dates.isEmpty())
        currentDate = m_dates[m_currentIndex];

    m_repo.reload();
    rebuildFromRepo();

    // Re-watch directories (they may have been added/removed)
    if (!m_watcher->directories().isEmpty())
        m_watcher->removePaths(m_watcher->directories());
    QString root = m_repo.rootPath();
    m_watcher->addPath(root);
    QDir rootDir(root);
    for (const QString &sub : rootDir.entryList(QDir::Dirs | QDir::NoDotAndDotDot))
        m_watcher->addPath(rootDir.filePath(sub));

    if (m_dates.isEmpty()) return;

    // Try to stay on the same date
    if (currentDate.isValid()) {
        auto it = m_dateToIndex.find(currentDate);
        m_currentIndex = (it != m_dateToIndex.end()) ? it.value()
                                                      : nearestAvailableIndex(currentDate);
    } else {
        m_currentIndex = pickInitialIndex();
    }
    showCurrentDate();
}

void MainWindow::rebuildFromRepo()
{
    m_dates = m_repo.dates;
    m_dateToIndex.clear();
    m_monthOrder.clear();
    m_monthToDateIndices.clear();
    m_monthDayToIndex.clear();
    m_monthToOrderIndex.clear();

    for (int i = 0; i < m_dates.size(); ++i)
        m_dateToIndex[m_dates[i]] = i;

    QSet<QPair<int,int>> monthSet;
    for (const auto &d : m_dates) {
        auto key = qMakePair(d.year(), d.month());
        monthSet.insert(key);
        m_monthToDateIndices[key].append(m_dateToIndex[d]);
        m_monthDayToIndex[key][d.day()] = m_dateToIndex[d];
    }
    m_monthOrder = monthSet.values().toVector();
    std::sort(m_monthOrder.begin(), m_monthOrder.end());
    for (int i = 0; i < m_monthOrder.size(); ++i)
        m_monthToOrderIndex[m_monthOrder[i]] = i;
}
