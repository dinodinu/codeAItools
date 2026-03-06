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
- **Config auto-creation** – if `config.json` is missing or points to a non-existent folder, a folder picker dialog prompts the user and saves the selection
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

## Configuration

All desktop versions (Python and C++) read `config.json` from the application's root directory:

```json
{
  "images_dir": "/path/to/calendar/images"
}
```

- If `config.json` **doesn't exist**, a folder picker dialog appears and the selection is saved to a new `config.json`.
- If the configured folder **doesn't exist**, the dialog appears again and `config.json` is updated.
- Relative paths are resolved against the application's root directory.

The **Android** version stores the selected folder URI in SharedPreferences. If no images are found in bundled assets, the app prompts the user to pick a folder via the system file picker.

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
