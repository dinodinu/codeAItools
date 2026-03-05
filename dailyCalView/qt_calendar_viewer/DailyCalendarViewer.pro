QT += core gui widgets

CONFIG += c++17
TARGET = DailyCalendarViewer
TEMPLATE = app

SOURCES += \
    main.cpp \
    CalendarRepository.cpp \
    MainWindow.cpp

HEADERS += \
    CalendarRepository.h \
    MainWindow.h

macx {
    ICON = DailyCalendar.icns
    QMAKE_TARGET_BUNDLE_PREFIX = com.srirangam
    QMAKE_BUNDLE = DailyCalendarViewer
}
