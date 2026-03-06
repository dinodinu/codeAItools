#include "CalendarRepository.h"
#include "MainWindow.h"

#include <QApplication>
#include <QDate>
#include <QDir>
#include <QFile>
#include <QFileDialog>
#include <QIcon>
#include <QJsonDocument>
#include <QJsonObject>
#include <QMessageBox>
#include <QPainter>
#include <QPalette>
#include <QPixmap>
#include <QProcess>
#include <QStyleHints>
#include <QTemporaryDir>

static QString findImageRoot(const QString &appPath)
{
#ifdef Q_OS_MACOS
    // Walk up from executable to find .app parent
    QDir dir(appPath);
    while (dir.cdUp()) {
        if (dir.dirName().endsWith(".app"))
            return QDir(dir.filePath("..")).canonicalPath();
    }
#endif
    return QFileInfo(appPath).absolutePath();
}

static bool isDarkTheme()
{
#if QT_VERSION >= QT_VERSION_CHECK(6, 5, 0)
    auto scheme = QGuiApplication::styleHints()->colorScheme();
    if (scheme != Qt::ColorScheme::Unknown)
        return scheme == Qt::ColorScheme::Dark;
#endif
    const QPalette pal = QGuiApplication::palette();
    return pal.color(QPalette::Window).lightnessF() < 0.5;
}

static QPixmap makeCalendarIcon(int sz, const QDate &date, bool dark)
{
    QPixmap pm(sz, sz);
    pm.fill(Qt::transparent);
    QPainter p(&pm);
    p.setRenderHint(QPainter::Antialiasing);

    int m = static_cast<int>(sz * 0.04);
    int r = static_cast<int>(sz * 0.08);
    QRect body(m, m, sz - 2 * m, sz - 2 * m);

    // Shadow
    p.setPen(Qt::NoPen);
    p.setBrush(QColor(0, 0, 0, dark ? 80 : 40));
    p.drawRoundedRect(body.adjusted(2, 2, 2, 2), r, r);

    // Body
    p.setBrush(dark ? QColor(44, 44, 46) : QColor(255, 255, 255));
    p.setPen(QPen(dark ? QColor(68, 68, 70) : QColor(200, 200, 200), qMax(1, sz / 128)));
    p.drawRoundedRect(body, r, r);

    // Red header
    int hh = static_cast<int>(sz * 0.28);
    QRect header(body.x(), body.y(), body.width(), hh);
    p.setPen(Qt::NoPen);
    p.setBrush(dark ? QColor(200, 40, 40) : QColor(220, 50, 50));
    p.drawRoundedRect(header.adjusted(0, 0, 0, r), r, r);
    p.drawRect(header.adjusted(0, r, 0, 0));

    // Month text
    QFont mf("Helvetica", qMax(1, static_cast<int>(sz * 0.11)));
    mf.setBold(true);
    p.setFont(mf);
    p.setPen(QColor(255, 255, 255));
    p.drawText(header, Qt::AlignCenter, date.toString("MMM").toUpper());

    // Day number
    QFont df("Helvetica", qMax(1, static_cast<int>(sz * 0.35)));
    df.setBold(true);
    p.setFont(df);
    p.setPen(dark ? QColor(230, 230, 230) : QColor(50, 50, 50));
    QRect dayRect(body.x(), body.y() + hh, body.width(), body.height() - hh);
    p.drawText(dayRect, Qt::AlignCenter, QString::number(date.day()));

    p.end();
    return pm;
}

static QIcon makeDateIcon(const QDate &date)
{
    bool dark = isDarkTheme();
    QIcon icon;
    for (int sz : {16, 32, 64, 128, 256})
        icon.addPixmap(makeCalendarIcon(sz, date, dark));
    return icon;
}

#ifdef Q_OS_MACOS
static void updateBundleIcon(const QDate &date)
{
    // Find the .app bundle path
    QDir dir(QCoreApplication::applicationDirPath());
    while (dir.cdUp()) {
        if (dir.dirName().endsWith(".app"))
            break;
    }
    if (!dir.dirName().endsWith(".app"))
        return;

    QString bundlePath = dir.absolutePath();
    QString resourcesPath = bundlePath + "/Contents/Resources";
    QString icnsPath = resourcesPath + "/DailyCalendar.icns";

    // Check if the icon already matches today
    QString stampPath = resourcesPath + "/.icon_date";
    QFile stampFile(stampPath);
    if (stampFile.exists() && stampFile.open(QIODevice::ReadOnly)) {
        QString stamp = QString::fromUtf8(stampFile.readAll()).trimmed();
        stampFile.close();
        bool dark = isDarkTheme();
        QString expected = date.toString(Qt::ISODate)
                           + (dark ? "-dark" : "-light");
        if (stamp == expected)
            return;
    }

    QTemporaryDir tmpDir;
    if (!tmpDir.isValid())
        return;

    QString iconsetPath = tmpDir.path() + "/DailyCalendar.iconset";
    QDir().mkpath(iconsetPath);

    bool dark = isDarkTheme();
    for (int sz : {16, 32, 64, 128, 256, 512, 1024}) {
        makeCalendarIcon(sz, date, dark).save(
            iconsetPath + QStringLiteral("/icon_%1x%1.png").arg(sz));
        if (sz <= 512)
            makeCalendarIcon(sz * 2, date, dark).save(
                iconsetPath + QStringLiteral("/icon_%1x%1@2x.png").arg(sz));
    }

    QProcess iconutil;
    iconutil.start("iconutil",
                   {"--convert", "icns", iconsetPath, "--output", icnsPath});
    if (!iconutil.waitForFinished(5000))
        return;

    // Touch the app bundle so macOS refreshes its icon cache
    QProcess::execute("touch", {bundlePath});

    // Write stamp so we skip regeneration on subsequent launches today
    if (stampFile.open(QIODevice::WriteOnly | QIODevice::Truncate)) {
        bool darkNow = isDarkTheme();
        stampFile.write((date.toString(Qt::ISODate)
                         + (darkNow ? "-dark" : "-light")).toUtf8());
        stampFile.close();
    }
}
#endif

int main(int argc, char *argv[])
{
    QApplication app(argc, argv);
    app.setWindowIcon(makeDateIcon(QDate::currentDate()));
#ifdef Q_OS_MACOS
    updateBundleIcon(QDate::currentDate());
#endif

    QString defaultRoot = findImageRoot(app.applicationFilePath());
    QString root = defaultRoot;
    QString configPath = defaultRoot + "/config.json";

    auto promptAndSaveFolder = [&](const QString &dialogTitle) -> bool {
        QString chosen = QFileDialog::getExistingDirectory(
            nullptr, dialogTitle, defaultRoot);
        if (chosen.isEmpty())
            return false;
        root = chosen;
        QJsonObject newCfg;
        newCfg["images_dir"] = chosen;
        QFile out(configPath);
        if (out.open(QIODevice::WriteOnly | QIODevice::Truncate)) {
            out.write(QJsonDocument(newCfg).toJson());
            out.close();
        }
        return true;
    };

    QFile configFile(configPath);
    if (configFile.exists()) {
        if (configFile.open(QIODevice::ReadOnly)) {
            QJsonObject cfg = QJsonDocument::fromJson(configFile.readAll()).object();
            configFile.close();
            QString imagesDir = cfg.value("images_dir").toString();
            if (!imagesDir.isEmpty()) {
                QDir d(imagesDir);
                if (!d.isAbsolute())
                    d = QDir(defaultRoot + "/" + imagesDir);
                if (d.exists()) {
                    root = d.canonicalPath();
                } else {
                    if (!promptAndSaveFolder(
                            QObject::tr("Configured folder not found – Select Calendar Images Folder")))
                        return 1;
                }
            }
        }
    } else {
        // config.json doesn't exist – ask user to pick a folder and create it
        if (!promptAndSaveFolder(
                QObject::tr("No config found – Select Calendar Images Folder")))
            return 1;
    }
    CalendarRepository repo(root);

    if (!repo.hasData()) {
        QMessageBox::critical(
            nullptr,
            QObject::tr("No Images Found"),
            QObject::tr("No valid calendar images were found.\n\n"
                        "Expected folders like jan'26 with files such as 0101.jpg"));
        return 1;
    }

    MainWindow window(repo);
    window.show();
    return app.exec();
}
