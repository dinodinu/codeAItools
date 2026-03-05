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
#include <QPixmap>

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

static QPixmap makeCalendarIcon(int sz, const QDate &date)
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
    p.setBrush(QColor(0, 0, 0, 40));
    p.drawRoundedRect(body.adjusted(2, 2, 2, 2), r, r);

    // White body
    p.setBrush(QColor(255, 255, 255));
    p.setPen(QPen(QColor(200, 200, 200), qMax(1, sz / 128)));
    p.drawRoundedRect(body, r, r);

    // Red header
    int hh = static_cast<int>(sz * 0.28);
    QRect header(body.x(), body.y(), body.width(), hh);
    p.setPen(Qt::NoPen);
    p.setBrush(QColor(220, 50, 50));
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
    p.setPen(QColor(50, 50, 50));
    QRect dayRect(body.x(), body.y() + hh, body.width(), body.height() - hh);
    p.drawText(dayRect, Qt::AlignCenter, QString::number(date.day()));

    p.end();
    return pm;
}

static QIcon makeDateIcon(const QDate &date)
{
    QIcon icon;
    for (int sz : {16, 32, 64, 128, 256})
        icon.addPixmap(makeCalendarIcon(sz, date));
    return icon;
}

int main(int argc, char *argv[])
{
    QApplication app(argc, argv);
    app.setWindowIcon(makeDateIcon(QDate::currentDate()));

    QString defaultRoot = findImageRoot(app.applicationFilePath());
    QString root = defaultRoot;
    QString configPath = defaultRoot + "/config.json";
    QFile configFile(configPath);
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
                // Configured folder doesn't exist – ask user to pick a new one
                QString chosen = QFileDialog::getExistingDirectory(
                    nullptr,
                    QObject::tr("Configured folder not found – Select Calendar Images Folder"),
                    defaultRoot);
                if (chosen.isEmpty())
                    return 1;
                root = chosen;
                // Update config.json with the new path
                QJsonObject newCfg;
                newCfg["images_dir"] = chosen;
                QFile out(configPath);
                if (out.open(QIODevice::WriteOnly | QIODevice::Truncate)) {
                    out.write(QJsonDocument(newCfg).toJson());
                    out.close();
                }
            }
        }
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
