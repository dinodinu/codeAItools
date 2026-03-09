# Deccan Herald ePaper Downloader — Complete Guide

A Python script that automatically downloads every page of any **Deccan Herald** city edition as individual PDFs and merges them into a single newspaper PDF file. Supports all 10 city editions (Bengaluru, Mangaluru, Mysuru, Hubbali, Davangere, Gulburga, Hosapete, Belgavi, Kolar, Bagalkote).

---

## Table of Contents

1. [How the Script Works](#how-the-script-works)
2. [Prerequisites](#prerequisites)
3. [Usage on Desktop (macOS / Windows / Linux)](#usage-on-desktop)
4. [Usage on Mobile](#usage-on-mobile)
   - [iOS / iPadOS](#ios--ipados)
   - [Android](#android)
5. [Command-Line Options](#command-line-options)
6. [Troubleshooting](#troubleshooting)

---

## How the Script Works

The script operates in 7 steps:

### Step 0 — Fetch Available Editions

The script first queries the editions API to get all available city editions:

```
GET https://api-epaper-prod.deccanherald.com/epaper/editions?publisher=DH
```

This returns a list of all editions with their IDs, edition numbers, names, and short codes:

| ID | Edition No | Name | Code | Region |
|----|-----------|------|------|--------|
| 2 | 2 | Bengaluru City | BC | Karnataka |
| 6 | 10 | Mangaluru | M | Karnataka |
| 10 | 45 | Mysuru | B1_Y | Karnataka |
| 5 | 9 | Hubbali City | H | Karnataka |
| 8 | 13 | Davangere | D | Karnataka |
| 7 | 12 | Gulburga | G_G | Karnataka |
| 43 | 135 | Hosapete | S | Karnataka |
| 4 | 8 | Belgavi, Uttar Kannada | H1 | Karnataka |
| 1 | 6 | Kolar, Chikkaballapura, Tumkur | B2 | Karnataka |
| 3 | 7 | Bagalkote, Haveri, Gadag | H2_H | Karnataka |

The user's `--edition` argument is then resolved against this list using fuzzy substring matching on the edition name, short code, or edition number.

### Step 1 — Fetch Edition Metadata

The script calls the Deccan Herald ePaper API with the resolved edition number:

```
GET https://api-epaper-prod.deccanherald.com/epaper/data
    ?date=YYYYMMDD
    &edition=<edition_number>
    &publisher=DH
```

- The edition number is determined from the `--edition` argument (default: `2` for Bengaluru City).
- The API returns a JSON response containing:
  - `data_url_suffix` — CDN base URL (e.g. `https://assets-prod.deccanherald.com/DH/20260309/data/`)
  - `data.sections[]` — array of sections, each containing an array of pages
  - Each page has: `pageNo`, `displayName`, `pdfFile`, `imgThumbFile`, and article metadata

### Step 2 — Extract PDF URLs

For each page in the API response:
- If `pdfFile` is present (e.g. `webepaper/pdf/1679444.pdf`), it is combined with `data_url_suffix` to form the full download URL.
- If `pdfFile` is empty, the script derives the page ID from `imgThumbFile` (e.g. `webepaper/photos/thumbs/1679445.png` → ID `1679445`) and constructs the URL as `webepaper/pdf/{id}.pdf`.

Full URL example:
```
https://assets-prod.deccanherald.com/DH/20260309/data/webepaper/pdf/1679444.pdf
```

### Step 3 — Classify Pages

Pages are classified into two groups:
- **Main pages** — pages belonging to the "Main" section (Front Page, State, Nation, Business, Sports, etc.)
- **Annexures** — pages from non-Main sections or sections whose names contain keywords like "supplement", "pullout", "tabloid", "magazine", etc.

### Step 4 — Download All Page PDFs

Each page PDF is downloaded sequentially with:
- 0.3-second delay between downloads (to be respectful to the server)
- Automatic retry (up to 3 retries with exponential backoff on server errors)
- Validation that the downloaded file is at least 500 bytes

Files are saved into a `pages/` directory as `page_001.pdf`, `page_002.pdf`, etc.

### Step 5 — Merge into Single PDF

All downloaded PDFs are merged in order using PyPDF2:
1. Main pages first (in page-number order)
2. Annexures / supplements appended at the end

The output is saved as `DeccanHerald_<Edition>_YYYY-MM-DD.pdf` (e.g. `DeccanHerald_Bengaluru_City_2026-03-09.pdf`).

### Step 6 — Cleanup

Individual page PDFs and the `pages/` directory are deleted after merging (unless `--keep-pages` is used).

---

## Prerequisites

- **Python 3.7+**
- Two Python packages:
  ```
  pip3 install requests PyPDF2
  ```

---

## Usage on Desktop

### macOS / Linux

```bash
cd ~/deccan_herald_epaper

# Install dependencies (one-time)
pip3 install requests PyPDF2

# Download today's Bengaluru edition (default)
python3 download_epaper.py

# Download a specific date
python3 download_epaper.py --date 2026-03-09

# Download a different city edition
python3 download_epaper.py --edition mangaluru
python3 download_epaper.py --edition mysuru
python3 download_epaper.py --edition 'hubbali city'

# List all available editions
python3 download_epaper.py --list-editions

# Custom output filename
python3 download_epaper.py --output today.pdf

# Keep individual page PDFs after merging
python3 download_epaper.py --keep-pages
```

### Windows

```powershell
cd C:\Users\YourName\deccan_herald_epaper

# Install dependencies (one-time)
pip install requests PyPDF2

# Download today's Bengaluru edition
python download_epaper.py

# Download Mangaluru edition
python download_epaper.py --edition mangaluru
```

---

## Usage on Mobile

### iOS / iPadOS

#### Option A: Pyto (Recommended)

[Pyto](https://apps.apple.com/app/pyto-python-3/id1436650069) is a full Python 3 IDE for iOS/iPadOS (paid app on the App Store).

1. **Install Pyto** from the App Store.
2. **Transfer the script** — open `download_epaper.py` in the Files app and choose "Open in Pyto", or copy-paste the code into a new file in Pyto.
3. **Install dependencies** — open Pyto's terminal (the `>_` icon) and run:
   ```
   pip install requests PyPDF2
   ```
4. **Run the script** — tap the ▶️ play button.
5. **Find the PDF** — the merged PDF is saved in Pyto's documents folder. Open the Files app → Pyto → locate `DeccanHerald_Bengaluru_YYYY-MM-DD.pdf`. Share or open it from there.

**Tip:** To auto-open the PDF after download, add these lines at the very end of the `main()` function (before `if __name__`):

```python
    # iOS (Pyto) — auto-open the PDF
    try:
        import sharing
        sharing.quick_look(output_file)
    except ImportError:
        pass
```

#### Option B: Pythonista 3

[Pythonista 3](https://apps.apple.com/app/pythonista-3/id1085978097) is another Python IDE for iOS (paid app).

1. Install Pythonista 3 from the App Store.
2. Open StaSh (Pythonista's built-in shell) by running:
   ```python
   import requests as r; exec(r.get('https://bit.ly/get-stash').text)
   ```
3. In StaSh, install PyPDF2:
   ```
   pip install PyPDF2
   ```
   (`requests` is pre-installed in Pythonista)
4. Create or import the script and run it.

#### Option C: a-Shell

[a-Shell](https://apps.apple.com/app/a-shell/id1473805438) is a free terminal emulator for iOS with Python built in.

1. Install a-Shell from the App Store.
2. Run:
   ```bash
   pip install requests PyPDF2
   ```
3. Transfer `download_epaper.py` via iCloud/Files, then:
   ```bash
   python download_epaper.py
   ```
4. The PDF will be in a-Shell's documents, accessible from the Files app.

#### Option D: iSH (Alpine Linux emulator)

[iSH](https://apps.apple.com/app/ish-shell/id1436902243) is a free Linux shell for iOS.

1. Install iSH from the App Store.
2. Set up Python:
   ```bash
   apk add python3 py3-pip
   pip3 install requests PyPDF2
   ```
3. Transfer the script and run:
   ```bash
   python3 download_epaper.py
   ```
> **Note:** iSH is slower than native apps like Pyto since it emulates Linux.

#### Option E: iOS Shortcut + SSH (Remote execution)

If you have a Mac/server that is always on:

1. Keep the script on your Mac.
2. On your iPhone/iPad, open the **Shortcuts** app.
3. Create a new Shortcut with the action **"Run Script over SSH"**:
   - Host: your Mac's IP or hostname
   - User: your macOS username
   - Authentication: password or SSH key
   - Script:
     ```bash
     cd ~/deccan_herald_epaper && python3 download_epaper.py
     ```
4. Optionally add a second action to copy the PDF to iCloud:
   ```bash
   cp ~/deccan_herald_epaper/DeccanHerald_Bengaluru_*.pdf ~/Library/Mobile\ Documents/com~apple~CloudDocs/
   ```
5. Run the Shortcut — the PDF appears in your Files app under iCloud.

---

### Android

#### Option A: Termux (Recommended)

[Termux](https://f-droid.org/en/packages/com.termux/) is a free, powerful terminal emulator for Android. Install it from **F-Droid** (recommended) or the Play Store.

1. **Install Termux** from F-Droid.
2. **Set up Python:**
   ```bash
   pkg update && pkg install python
   pip install requests PyPDF2
   ```
3. **Transfer the script** — either clone from a repo or copy the file:
   ```bash
   # Option: copy from Downloads (grant storage access first)
   termux-setup-storage
   cp ~/storage/downloads/download_epaper.py ~/
   ```
4. **Run:**
   ```bash
   python download_epaper.py
   ```
5. **Find the PDF:**
   ```bash
   # Copy to Downloads for easy access
   cp DeccanHerald_Bengaluru_*.pdf ~/storage/downloads/
   ```
   Open your Downloads folder to find the PDF.

**Tip — Daily automation with Termux:Boot:**

Install [Termux:Boot](https://f-droid.org/en/packages/com.termux.boot/) and create a boot script:

```bash
mkdir -p ~/.termux/boot
cat > ~/.termux/boot/download_paper.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
cd ~/deccan_herald_epaper
python download_epaper.py
cp DeccanHerald_Bengaluru_*.pdf ~/storage/downloads/
EOF
chmod +x ~/.termux/boot/download_paper.sh
```

Or schedule it with `cron`:
```bash
pkg install cronie termux-services
sv-enable crond
crontab -e
# Add: 0 7 * * * cd ~/deccan_herald_epaper && python download_epaper.py && cp *.pdf ~/storage/downloads/
```

#### Option B: Pydroid 3

[Pydroid 3](https://play.google.com/store/apps/details?id=ru.iiec.pydroid3) is a Python IDE for Android (free with ads, or paid premium).

1. Install Pydroid 3 from the Play Store.
2. Open the app → Menu → Pip → install `requests` and `PyPDF2`.
3. Open or paste `download_epaper.py`.
4. Tap ▶️ to run.
5. The PDF is saved in Pydroid's working directory (usually accessible via the file manager).

#### Option C: QPython

[QPython](https://play.google.com/store/apps/details?id=org.qpython.qpy) is another free Python environment for Android.

1. Install from the Play Store.
2. Install packages via QPYPI (built-in package manager).
3. Import and run the script.

---

## Command-Line Options

| Option | Description | Default |
|---|---|---|
| `--edition NAME` | City edition by name, short code, or number | `bengaluru` |
| `--list-editions` | List all available city editions and exit | — |
| `--date YYYY-MM-DD` | Date of the edition to download | Today |
| `--output FILENAME` | Output merged PDF filename | `DeccanHerald_<edition>_<date>.pdf` |
| `--download-dir DIR` | Directory for temporary page PDFs | `pages` |
| `--keep-pages` | Keep individual page PDFs after merging | Disabled (cleanup) |

The `--edition` argument supports flexible matching:
- Full name: `--edition 'Bengaluru City'`
- Partial name: `--edition mangaluru`, `--edition hubbal`, `--edition kolar`
- Short code: `--edition BC`, `--edition M`
- Edition number: `--edition 2`

### Examples

```bash
# Today's Bengaluru paper (default)
python3 download_epaper.py

# Mangaluru edition
python3 download_epaper.py --edition mangaluru

# Mysuru edition for a specific date
python3 download_epaper.py --edition mysuru --date 2026-03-08

# List all editions
python3 download_epaper.py --list-editions

# Save with custom name, keep individual pages
python3 download_epaper.py --edition davangere --output paper.pdf --keep-pages
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| **"No edition found"** error | The paper may not be published on that date (e.g. holidays). Try a different date. |
| **"Edition not found"** error | The edition name didn't match. Run `--list-editions` to see valid names. |
| **"Access denied"** error (403) | Non-Bengaluru editions require a paid subscription. Bengaluru City is free for guests. |
| **Empty/tiny PDF files** | The server may be temporarily unavailable. Re-run the script. |
| **SSL errors on older Python** | Upgrade Python to 3.10+ or install `urllib3<2`. |
| **ModuleNotFoundError** | Run `pip3 install requests PyPDF2` to install dependencies. |
| **Permission errors on Android** | In Termux, run `termux-setup-storage` first to grant file access. |
| **Slow on iSH** | iSH emulates a CPU — use Pyto or a-Shell for better performance on iOS. |
