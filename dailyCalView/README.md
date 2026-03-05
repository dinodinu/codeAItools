# Daily Calendar Viewer

Desktop app to browse your calendar images in folders like `jan'26`, `feb'26`, etc. Available as a **Python (PySide6)** app or a **C++ (Qt6)** app.

## Features

- Starts on today's date (or nearest available)
- Day and month navigation (◀ ▶ ⏮ ⏭) via overlay buttons or arrow keys
- Today button to jump back quickly
- Go To Date with calendar picker
- Zoom controls (−, Fit, +)
- Floating overlay toolbar at bottom-right of image area
- Quit button
- Available as a native **macOS .app** (both Python and C++ builds)

## Folder/File Convention

- Folder format: `mon'yy` (example: `mar'26`)
- File format: `DDMM.ext` (example: `0503.jpg`)

## Python Version

### macOS App

Double-click **DailyCalendar.app** (must be in the same directory as the month folders).

To rebuild:

```bash
./venv/bin/pyinstaller DailyCalendar.spec
cp -R dist/DailyCalendar.app .
```

### Run from Source

```bash
cd /path/to/dailyCalendarSrirangam
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 calendar_viewer.py
```

## C++ Version (Qt6)

### Prerequisites

- Qt 6 (`brew install qt`)
- qmake (included with Qt)

### Build & Run

```bash
cd qt_calendar_viewer
qmake DailyCalendarViewer.pro
make
open DailyCalendarViewer.app
```

The `.app` must be in a location where the parent directory contains the month folders.

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Left / Right | Previous / next day |
| Up / Down | Next / previous month |
| T | Jump to today |
| G | Open date picker |
| Ctrl+= / Ctrl+- | Zoom in / out |
| Ctrl+0 | Fit to view |
| Ctrl+Q | Quit |
