# CMakeLists.txt – Line-by-Line Explanation

## 1. Minimum CMake Version

```cmake
cmake_minimum_required(VERSION 3.16)
```

Declares that this project requires CMake 3.16 or newer. Version 3.16 is needed because it introduced better support for `CMAKE_AUTOMOC` and Qt integration. Older versions of CMake will refuse to configure the project.

## 2. Project Declaration

```cmake
project(DailyCalendarViewer LANGUAGES CXX)
```

Defines the project name as **DailyCalendarViewer** and declares that it uses only C++ (`CXX`). This name is used by CMake for the generated build system, IDE project files, and as the default target name.

## 3. C++ Standard

```cmake
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
```

- `CMAKE_CXX_STANDARD 17` – requests the C++17 standard for all targets.
- `CMAKE_CXX_STANDARD_REQUIRED ON` – makes this a hard requirement; CMake will error out if the compiler doesn't support C++17 instead of silently falling back to an older standard.

## 4. Qt Auto-MOC

```cmake
set(CMAKE_AUTOMOC ON)
```

Enables **automatic Meta-Object Compilation**. Qt classes that use the `Q_OBJECT` macro need a MOC (Meta-Object Compiler) pass to generate signal/slot glue code. With `AUTOMOC ON`, CMake detects headers containing `Q_OBJECT` and runs `moc` automatically during the build — no manual `moc` invocation needed.

## 5. Build Output Directories

```cmake
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/build)
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/build)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/build)
```

Redirects all build artifacts into a `build/` subdirectory within the CMake binary directory:

| Variable | Controls |
|---|---|
| `CMAKE_RUNTIME_OUTPUT_DIRECTORY` | Executables (`.app`, binaries) |
| `CMAKE_ARCHIVE_OUTPUT_DIRECTORY` | Static libraries (`.a`) |
| `CMAKE_LIBRARY_OUTPUT_DIRECTORY` | Shared/dynamic libraries (`.dylib`, `.so`) |

This keeps the build tree organized and the source directory clean.

## 6. Finding Qt

```cmake
find_package(Qt6 REQUIRED COMPONENTS Core Gui Widgets)
```

Locates the Qt 6 installation on the system and makes three modules available:

- **Qt6::Core** – fundamental non-GUI classes (strings, files, JSON, event loop)
- **Qt6::Gui** – low-level graphics (painting, images, fonts, icons)
- **Qt6::Widgets** – high-level UI elements (windows, buttons, dialogs, scroll areas)

The `REQUIRED` keyword means configuration fails immediately if Qt 6 is not found.

## 7. Executable Target

```cmake
add_executable(DailyCalendarViewer
    main.cpp
    CalendarRepository.h CalendarRepository.cpp
    MainWindow.h MainWindow.cpp
)
```

Creates the executable target from five source files:

| File | Role |
|---|---|
| `main.cpp` | Application entry point – loads config, creates the window |
| `CalendarRepository.h/.cpp` | Scans image folders and builds a date-to-image-path mapping |
| `MainWindow.h/.cpp` | The main UI window with image display, navigation, and zoom |

Headers are listed so that `AUTOMOC` can find and process any `Q_OBJECT` macros in them.

## 8. Linking Qt Libraries

```cmake
target_link_libraries(DailyCalendarViewer PRIVATE
    Qt6::Core Qt6::Gui Qt6::Widgets
)
```

Links the three Qt modules to the executable. `PRIVATE` means these dependencies are only needed to build this target — they won't propagate to anything that depends on it (not relevant here since it's a final executable, but it's good practice).

## 9. macOS App Bundle Configuration

```cmake
if(APPLE)
```

The entire block below only applies on macOS/Apple platforms.

### 9a. Icon Handling

```cmake
    set(MACOSX_ICON "${CMAKE_CURRENT_SOURCE_DIR}/DailyCalendar.icns")
    if(EXISTS "${MACOSX_ICON}")
        set_source_files_properties(${MACOSX_ICON} PROPERTIES
            MACOSX_PACKAGE_LOCATION "Resources")
        target_sources(DailyCalendarViewer PRIVATE ${MACOSX_ICON})
    endif()
```

- Sets the path to the `.icns` icon file.
- **Only if the file exists:** marks it to be copied into the `Resources` folder inside the `.app` bundle, and adds it as a source so CMake knows to include it in the build.
- This conditional avoids a build error if the icon file hasn't been generated yet.

### 9b. Bundle Properties

```cmake
    set_target_properties(DailyCalendarViewer PROPERTIES
        MACOSX_BUNDLE TRUE
        MACOSX_BUNDLE_BUNDLE_NAME "Daily Calendar Viewer"
        MACOSX_BUNDLE_GUI_IDENTIFIER "com.srirangam.dailycalendar"
        MACOSX_BUNDLE_ICON_FILE "DailyCalendar"
    )
endif()
```

| Property | Effect |
|---|---|
| `MACOSX_BUNDLE TRUE` | Builds a `.app` bundle instead of a bare executable |
| `MACOSX_BUNDLE_BUNDLE_NAME` | The human-readable name shown in Finder and the Dock |
| `MACOSX_BUNDLE_GUI_IDENTIFIER` | Reverse-DNS identifier used by macOS for app identity |
| `MACOSX_BUNDLE_ICON_FILE` | References the icon filename (without `.icns` extension) inside `Resources` |

## Build Instructions

```sh
# Configure (generates build system in the build/ directory)
cmake -B build

# Build the project
cmake --build build
```

On macOS this produces `build/build/DailyCalendarViewer.app`.
