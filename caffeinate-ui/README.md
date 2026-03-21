# Mini Process Viewer

A lightweight macOS process viewer with built-in **caffeinate** support. Keep your Mac awake while a selected process is running.

## Features

- **Tree view** of `/Applications/` processes with parent-child hierarchy
- **Filter** processes by name in real-time (recursive — matches propagate through the tree)
- **Caffeinate** a selected process (`caffeinate -w <pid>`) to prevent sleep
- **Kill** one or more selected processes with confirmation
- **Retry** caffeinate if the target process was restarted
- **Auto-refresh** after caffeinating; polls every 2 seconds for status changes
- **Keyboard shortcuts** — `Esc` to quit, arrow keys for navigation
- **Multi-select** with `Cmd`/`Shift`-click for batch kill
- macOS dark mode color scheme with native-style overlay scrollbars

## Requirements

- macOS 11+
- Python 3.9+
- PyQt5

```
pip3 install PyQt5
```

## Run

```
python3 caffeinate_qtUI.py
```

## Build as native .app

```
pip3 install py2app
python3 setup.py py2app
```

The app bundle is created at `~/caffeinate-ui-build/dist/Mini Process Viewer.app`. Drag it to `/Applications/` to install.

## Keyboard Shortcuts

| Key       | Action              |
|-----------|---------------------|
| `Esc`     | Quit                |
| `↑` / `↓` | Navigate processes  |
| `→`       | Expand tree node    |
| `←`       | Collapse tree node  |

## License

MIT
