cmake_minimum_required(VERSION 3.16)
project(DailyCalendarViewer LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/build)
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/build)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/build)

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
    set(MACOSX_ICON "${CMAKE_CURRENT_SOURCE_DIR}/DailyCalendar.icns")
    if(EXISTS "${MACOSX_ICON}")
        set_source_files_properties(${MACOSX_ICON} PROPERTIES
            MACOSX_PACKAGE_LOCATION "Resources")
        target_sources(DailyCalendarViewer PRIVATE ${MACOSX_ICON})
    endif()
    set_target_properties(DailyCalendarViewer PROPERTIES
        MACOSX_BUNDLE TRUE
        MACOSX_BUNDLE_BUNDLE_NAME "Daily Calendar Viewer"
        MACOSX_BUNDLE_GUI_IDENTIFIER "com.srirangam.dailycalendar"
        MACOSX_BUNDLE_ICON_FILE "DailyCalendar"
    )
endif()
