# Filter Coffee

A dead-simple macOS menu bar app that wraps the built-in `caffeinate` command — keeps your Mac awake without ever touching the terminal.

## How to use

1. Open `FilterCoffee.xcodeproj` in **Xcode 15+`**
2. Press **⌘R** to build and run
3. A coffee-cup icon appears in your **menu bar** — click it to open the panel

**To keep your Mac awake:** click **Keep Mac Awake**  
**To let it sleep again:** click **Stop — Let Mac Sleep**

The icon changes to a moon when your Mac is allowed to sleep, and a coffee cup when it's being kept awake. A live elapsed timer shows how long caffeinate has been running.

## Options

| Option | What it does |
|---|---|
| Display sleep | Prevents the screen from turning off (`-d`) |
| System sleep | Prevents sleep entirely — AC power only (`-s`) |
| Disk idle sleep | Prevents the disk from idle-spinning down (`-m`) |
| Auto-stop timer | Automatically stops caffeinate after N minutes (`-t`) |

Options are locked while caffeinate is running — stop first, then adjust.

## Requirements

- macOS 13 Ventura or later
- Xcode 15+ (to build)

## How it works

Filter Coffee launches `/usr/bin/caffeinate` (a built-in macOS system tool) as a background process with your chosen flags. When you click Stop — or quit the app — the process is terminated and your Mac returns to its normal sleep behaviour.

No network access. No data collection. Sandboxing is disabled so it can spawn system processes.
