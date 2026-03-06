# Daily Calendar Srirangam — Android App

Kotlin + Jetpack Compose app to browse daily calendar images.

## Features

- Opens on today's date (or nearest available)
- Day navigation: `< Day` / `Day >`
- Month navigation: `<< Month` / `Month >>`
- `Today` button to jump back
- `Go To` date picker
- Pinch-to-zoom + pan on image
- Zoom buttons: `Zoom -`, `Fit`, `Zoom +`
- `Quit` button
- Loading spinner while image decodes
- Status bar showing current image name
- **Folder picker** – if no bundled assets are found, prompts the user to select an external folder via the system file picker; the selection is persisted across app restarts
- Supports both bundled assets and external storage folders

## Setup

### 1. Copy calendar images into assets (optional)

If you want to bundle images into the APK:

```bash
cd android_calendar_viewer
chmod +x copy_assets.sh
./copy_assets.sh
```

This copies all month folders (e.g. `jan'26/`, `mar'26/`) from the parent directory into `app/src/main/assets/`.

Alternatively, skip this step — the app will prompt you to select an images folder on first launch.

### 2. Build

Open `android_calendar_viewer/` in Android Studio, or build from command line:

```bash
cd android_calendar_viewer
./gradlew assembleDebug
```

The APK will be at `app/build/outputs/apk/debug/app-debug.apk`.

### 3. Install on device

```bash
adb install app/build/outputs/apk/debug/app-debug.apk
```

## Folder/File Convention

Same as the desktop app:

- **Folder**: `mon'yy` (e.g. `mar'26`)
- **Image**: `DDMM.ext` (e.g. `0503.jpg`)

## Configuration

The app supports two image sources:

1. **Bundled assets** – images copied into `app/src/main/assets/` at build time
2. **External folder** – selected at runtime via the system folder picker

If no bundled images are found, the app shows a prompt to select a folder. The chosen folder URI is saved in SharedPreferences and persisted across restarts. The app takes persistable read permission on the selected folder.

## Requirements

- Android Studio Hedgehog (2023.1.1) or later
- JDK 17
- Android SDK 34
- `androidx.documentfile:documentfile:1.0.1` (included in dependencies)
