cmake_minimum_required(VERSION 3.16)
project(DailyCalendarViewer LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)

find_package(Qt6 REQUIRED COMPONENTS Core Gui Widgets)

add_executable(DailyCalendarViewer
    main.cpp
    CalendarRepository.h CalendarRepository.cpp
    MainWindow.h MainWindow.cpp
)

target_link_libraries(DailyCalendarViewer PRIVATE
    Qt6::Core Qt6::Gui Qt6::Widgets
)

if(APPLE)
    set_target_properties(DailyCalendarViewer PROPERTIES
        MACOSX_BUNDLE TRUE
        MACOSX_BUNDLE_BUNDLE_NAME "Daily Calendar Viewer"
        MACOSX_BUNDLE_GUI_IDENTIFIER "com.srirangam.dailycalendar"
    )
endif()
