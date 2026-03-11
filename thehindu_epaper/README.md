# The Hindu ePaper Downloader

A command-line tool to download The Hindu ePaper edition and save it as a single PDF.

## Features

- Download any regional edition (Bangalore, Chennai, Delhi, etc.)
- Download today's paper or a specific date
- Two download modes: per-page or bulk
- Merges all pages into a single PDF automatically
- List all available editions for any date

## Requirements

- Python 3.7+
- A valid **The Hindu** digital subscriber account (for PDF downloads)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Download today's Bangalore edition (default)
python3 download_epaper.py

# Download a specific edition
python3 download_epaper.py --edition chennai

# Download a specific date
python3 download_epaper.py --date 2025-03-10

# List all available editions
python3 download_epaper.py --list-editions

# Use bulk download mode (single request for all pages)
python3 download_epaper.py --bulk

# Specify output filename
python3 download_epaper.py --output today.pdf

# Keep individual page PDFs after merging
python3 download_epaper.py --keep-pages
```

## Authentication

PDF downloads require a valid subscriber session. Provide your browser cookies using `--cookie` or the `TH_COOKIE` environment variable.

**To get your cookies:**

1. Log in to https://epaper.thehindu.com/reader in your browser
2. Open Developer Tools (F12) → Console
3. Type: `document.cookie`
4. Copy the output

```bash
# Pass via flag
python3 download_epaper.py --cookie "name=value; name2=value2"

# Or via environment variable
export TH_COOKIE="name=value; name2=value2"
python3 download_epaper.py
```

## Options

| Flag | Short | Description |
|------|-------|-------------|
| `--date` | `-d` | Date in YYYY-MM-DD format (default: today IST) |
| `--edition` | `-e` | Edition name or ID (default: bangalore) |
| `--list-editions` | `-l` | List all available editions and exit |
| `--cookie` | `-c` | Browser cookie string for authenticated downloads |
| `--output` | `-o` | Output PDF filename |
| `--download-dir` | | Directory for temporary page PDFs (default: `pages`) |
| `--keep-pages` | | Keep individual page PDFs after merging |
| `--bulk` | | Use bulk endpoint instead of per-page download |
