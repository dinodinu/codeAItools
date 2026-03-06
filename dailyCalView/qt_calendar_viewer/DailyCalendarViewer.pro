QT += core gui widgets

CONFIG += c++17
TARGET = DailyCalendarViewer
TEMPLATE = app

DESTDIR     = /Users/dinesh.ramalingam/Code/build/dailyCalView
OBJECTS_DIR = /Users/dinesh.ramalingam/Code/build/dailyCalView
MOC_DIR     = /Users/dinesh.ramalingam/Code/build/dailyCalView
RCC_DIR     = /Users/dinesh.ramalingam/Code/build/dailyCalView
UI_DIR      = /Users/dinesh.ramalingam/Code/build/dailyCalView

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
