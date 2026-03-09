# Deccan Herald ePaper Downloader

Downloads all pages of the Bangalore edition of Deccan Herald ePaper for today's date, merges them into a single PDF with annexures at the end.

## Setup

```bash
cd deccan_herald_epaper
pip install -r requirements.txt
```

## Usage

```bash
# Download today's edition
python download_epaper.py

# Download a specific date
python download_epaper.py --date 2026-03-09

# Custom output filename
python download_epaper.py --output today_paper.pdf

# Keep individual page PDFs after merging
python download_epaper.py --keep-pages
```

## Notes

- The script tries multiple URL patterns to discover pages.
- If it fails to find pages, you may need to inspect the site in your browser and update the URL patterns in the script.
- If the site requires login, add your credentials to the session (see "Adding Login" below).

## Adding Login (if required)

If the ePaper requires a subscription login, add this after `create_session()`:

```python
session.post("https://epaper.deccanherald.com/login", data={
    "username": "your_email",
    "password": "your_password",
})
```

Adjust the login URL and field names based on the actual site.
