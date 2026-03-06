# Daily Calendar Viewer (Qt/C++)

A native Qt 6 desktop application for browsing daily calendar images organized by month folders. Designed for collections where each day has a corresponding image (e.g., temple calendars).

## Features

- **Day & month navigation** – step through images by day or month with on-screen buttons or keyboard shortcuts
- **Go to date** – jump to any date via a calendar picker dialog
- **Today button** – instantly navigate to today's image (or the nearest available date)
- **Zoom** – zoom in, zoom out, or fit-to-window
- **Auto-fit** – images are scaled to fit the viewport on load
- **File system watcher** – automatically detects new or changed images and refreshes
- **Dark mode support** – adapts icon rendering to the system colour scheme
- **Dynamic app icon** (macOS) – generates a calendar icon showing today's date, updates daily, and respects dark/light mode
- **Config auto-creation** – if `config.json` is missing or points to a non-existent folder, a folder picker dialog prompts the user and saves the selection

## Expected Image Structure

Images must be organised under a root folder with month subfolders:

```
<images_dir>/
├── 01jan'26/
│   ├── 0101.jpg
│   ├── 0201.jpg
│   └── ...
├── 02feb'26/
│   ├── 0102.jpg
│   └── ...
└── ...
```

- **Folder pattern:** `DDmon'YY` (e.g., `01jan'26`, `03mar'25`)
- **File pattern:** `DDMM*.jpg|jpeg|png|bmp|webp|gif` (e.g., `0101.jpg` = day 01, month 01)

## Configuration

The app reads `config.json` from the same directory as the executable (or the parent of the `.app` bundle on macOS):

```json
{
  "images_dir": "/path/to/calendar/images"
}
```

- If `config.json` **doesn't exist**, a folder picker dialog appears and the selection is saved to a new `config.json`.
- If the configured folder **doesn't exist**, the dialog appears again and `config.json` is updated.
- Relative paths are resolved against the application's root directory.

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `→` | Next day |
| `←` | Previous day |
| `↑` | Next month |
| `↓` | Previous month |
| `T` | Go to today |
| `G` | Go to specific date |
| `Ctrl+=` | Zoom in |
| `Ctrl+-` | Zoom out |
| `Ctrl+0` | Fit to window |
| `Ctrl+Q` | Quit |

## Building

### Prerequisites

- Qt 6 (Core, Gui, Widgets)
- CMake ≥ 3.16 **or** qmake
- C++17-capable compiler

### With CMake

```sh
cmake -B build
cmake --build build
```

### With qmake

```sh
qmake
make
```

## Source Files

| File | Description |
|------|-------------|
| `main.cpp` | Entry point – config loading, app icon generation, folder validation |
| `CalendarRepository.h/.cpp` | Scans image folders, maps dates to image paths |
| `MainWindow.h/.cpp` | Main UI – image display, navigation, zoom, overlay controls |
| `CMakeLists.txt` | CMake build configuration |
| `DailyCalendarViewer.pro` | qmake build configuration |

## macOS App Bundle

On macOS the build produces `DailyCalendarViewer.app` with:

- Bundle identifier: `com.srirangam.dailycalendar`
- Auto-generated `.icns` icon showing today's date (regenerated on launch when the date or theme changes)
