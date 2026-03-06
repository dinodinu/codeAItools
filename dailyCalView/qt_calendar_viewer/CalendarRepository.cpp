#include "CalendarRepository.h"
#include <QDirIterator>
#include <QRegularExpression>
#include <algorithm>

static const QMap<QString, int> kMonthMap = {
    {"jan", 1}, {"feb", 2}, {"mar", 3}, {"apr", 4},
    {"may", 5}, {"jun", 6}, {"jul", 7}, {"aug", 8},
    {"sep", 9}, {"oct", 10}, {"nov", 11}, {"dec", 12},
};

CalendarRepository::CalendarRepository(const QString &root)
    : m_root(root)
{
    load(root);
}

void CalendarRepository::reload()
{
    byDate.clear();
    dates.clear();
    load(m_root);
}

void CalendarRepository::load(const QString &root)
{
    static const QRegularExpression folderRe(R"(^(\d{2})([a-zA-Z]{3})'(\d{2})$)");
    static const QRegularExpression fileRe(
        R"(^(\d{2})(\d{2}).*\.(jpg|jpeg|png|bmp|webp|gif)$)",
        QRegularExpression::CaseInsensitiveOption);

    QDir rootDir(root);
    QStringList folders = rootDir.entryList(QDir::Dirs | QDir::NoDotAndDotDot, QDir::Name);

    for (const QString &folder : folders) {
        auto fm = folderRe.match(folder);
        if (!fm.hasMatch()) continue;

        QString monthToken = fm.captured(2).toLower();
        auto it = kMonthMap.find(monthToken);
        if (it == kMonthMap.end()) continue;

        int month = it.value();
        int year = 2000 + fm.captured(3).toInt();

        QDir subDir(rootDir.filePath(folder));
        QStringList files = subDir.entryList(QDir::Files, QDir::Name);

        for (const QString &file : files) {
            auto ffm = fileRe.match(file);
            if (!ffm.hasMatch()) continue;

            int day = ffm.captured(1).toInt();
            int monthInFile = ffm.captured(2).toInt();
            if (monthInFile != month) continue;

            QDate d(year, month, day);
            if (!d.isValid()) continue;

            byDate[d].append(subDir.filePath(file));
        }
    }

    dates = byDate.keys().toVector();
    std::sort(dates.begin(), dates.end());
}
