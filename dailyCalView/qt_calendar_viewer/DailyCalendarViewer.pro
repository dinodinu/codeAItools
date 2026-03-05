QT += core gui widgets

CONFIG += c++17
TARGET = DailyCalendarViewer
TEMPLATE = app

DESTDIR     = /Users/dinesh.ramalingam/Documents/Personal/dailyCalendarSrirangam/build
OBJECTS_DIR = /Users/dinesh.ramalingam/Documents/Personal/dailyCalendarSrirangam/build
MOC_DIR     = /Users/dinesh.ramalingam/Documents/Personal/dailyCalendarSrirangam/build
RCC_DIR     = /Users/dinesh.ramalingam/Documents/Personal/dailyCalendarSrirangam/build
UI_DIR      = /Users/dinesh.ramalingam/Documents/Personal/dailyCalendarSrirangam/build

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
