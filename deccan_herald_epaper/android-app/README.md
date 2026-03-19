# Android App: DH ePaper Downloader

This Android app replicates the Python script flow from this repository:

1. Fetch available editions from Deccan Herald API.
2. Resolve user edition input (name/code/edition number).
3. Fetch page metadata for a date.
4. Separate main pages and annexures.
5. Download all page PDFs.
6. Merge PDFs (main first, annexures last).
7. Save one merged PDF to Downloads.

## Open and Run

1. Open Android Studio.
2. Choose **Open** and select the `android-app` folder.
3. Let Gradle sync complete.
4. Run on device/emulator (Android 8+).

## One-Time SDK Setup (if build fails)

If CLI build reports "SDK location not found", create `local.properties` in the `android-app` folder with your SDK path:

```
sdk.dir=/Users/<your-user>/Library/Android/sdk
```

Then build from terminal:

```
./gradlew :app:assembleDebug
```

## App Usage

1. Enter date as `YYYY-MM-DD`.
2. Optionally tap **List Editions** to view all editions with number, code, and region, then tap any item to auto-fill the edition field.
3. Enter edition (for example `bengaluru`, `mangaluru`, `mysuru`, or edition number). Autocomplete suggestions are loaded from API.
4. Tap **Download and Merge PDF**.
5. The merged file is saved in Downloads as:
   - `DeccanHerald_<Edition>_<Date>.pdf`

## UX Improvements Included

- Date picker popup for selecting date (calendar icon and tap on date field).
- Edition autocomplete suggestions loaded live from the editions API.
- A **List Editions** button that opens a full editions dialog.
- Completion notification that opens the merged PDF when tapped.

## Notes

- Internet is required.
- Non-Bengaluru editions can return access denied if subscription is required.
- The app uses:
  - OkHttp for API and file download
  - pdfbox-android for PDF merge
