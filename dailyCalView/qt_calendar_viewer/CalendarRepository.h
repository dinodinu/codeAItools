#pragma once

#include <QDate>
#include <QDir>
#include <QMap>
#include <QString>
#include <QVector>

struct CalendarRepository {
    QMap<QDate, QVector<QString>> byDate;   // date -> list of image paths
    QVector<QDate> dates;                    // sorted available dates

    explicit CalendarRepository(const QString &root);
    bool hasData() const { return !byDate.isEmpty(); }

private:
    void load(const QString &root);
};
