#!/usr/bin/env python3
"""
Deccan Herald ePaper Downloader
Downloads all pages of the Bengaluru City edition for today's date,
then merges them into a single PDF (annexures/supplements at the end).

Requirements:
    pip install requests PyPDF2

Usage:
    python download_epaper.py
    python download_epaper.py --date 2026-03-09
    python download_epaper.py --edition mangaluru
    python download_epaper.py --list-editions
    python download_epaper.py --output my_paper.pdf
"""

import argparse
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
from PyPDF2 import PdfMerger

API_BASE = "https://api-epaper-prod.deccanherald.com"
DEFAULT_EDITION = "bengaluru"  # Default: Bengaluru City
PUBLISHER = "DH"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, */*",
    "Origin": "https://epaper.deccanherald.com",
    "Referer": "https://epaper.deccanherald.com/",
}

# Section names that indicate annexures / supplements (case-insensitive)
ANNEXURE_KEYWORDS = [
    "supplement", "annexure", "annex", "pullout", "tabloid",
    "extra", "special", "magazine", "metrolife", "leisurefolio",
]


def parse_args():
    parser = argparse.ArgumentParser(description="Download Deccan Herald ePaper")
    parser.add_argument(
        "--date",
        type=str,
        default=datetime.now().strftime("%Y-%m-%d"),
        help="Date in YYYY-MM-DD format (default: today)",
    )
    parser.add_argument(
        "--edition",
        type=str,
        default=DEFAULT_EDITION,
        help="City edition name or number (default: bengaluru). Use --list-editions to see all.",
    )
    parser.add_argument(
        "--list-editions",
        action="store_true",
        help="List all available city editions and exit",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output merged PDF filename (default: DeccanHerald_<edition>_<date>.pdf)",
    )
    parser.add_argument(
        "--download-dir",
        type=str,
        default="pages",
        help="Directory to store individual page PDFs (default: pages)",
    )
    parser.add_argument(
        "--keep-pages",
        action="store_true",
        help="Keep individual page PDFs after merging",
    )
    return parser.parse_args()


def create_session():
    session = requests.Session()
    session.headers.update(HEADERS)
    adapter = requests.adapters.HTTPAdapter(
        max_retries=requests.adapters.Retry(
            total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504]
        )
    )
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def fetch_editions(session):
    """Fetch the list of all available editions from the API."""
    url = f"{API_BASE}/epaper/editions"
    resp = session.get(url, params={"publisher": PUBLISHER}, timeout=30)
    resp.raise_for_status()
    editions = []
    for group in resp.json():
        for ed in group.get("editions", []):
            editions.append({
                "id": ed["id"],
                "edition_number": ed["edition_number"],
                "name": ed["edition_name"],
                "short_code": ed.get("edition_short_code", ""),
                "region": group.get("parent_edition", ""),
            })
    return editions


def resolve_edition(editions, query):
    """
    Resolve a user query (name, short code, or edition number) to an edition dict.
    Returns the matching edition or None.
    """
    q = query.strip().lower()

    # Try exact edition_number match
    if q.isdigit():
        num = int(q)
        for ed in editions:
            if ed["edition_number"] == num or ed["id"] == num:
                return ed

    # Try name / short_code substring match
    for ed in editions:
        if q == ed["name"].lower() or q == ed["short_code"].lower():
            return ed

    # Fuzzy substring match
    for ed in editions:
        if q in ed["name"].lower():
            return ed

    return None


def fetch_edition_data(session, date_str, edition_number):
    """Fetch page metadata from the Deccan Herald ePaper API."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    api_date = dt.strftime("%Y%m%d")  # API expects YYYYMMDD

    url = f"{API_BASE}/epaper/data"
    params = {"date": api_date, "edition": edition_number, "publisher": PUBLISHER}

    resp = session.get(url, params=params, timeout=30)
    if resp.status_code == 403:
        print(f"[ERROR] Access denied. Non-Bengaluru editions require a paid subscription.")
        print("        Log in or use --edition bengaluru (free).")
        sys.exit(1)
    if resp.status_code == 404:
        print(f"[ERROR] No edition found for {date_str}.")
        print("        The paper may not have been published on this date.")
        sys.exit(1)
    resp.raise_for_status()
    return resp.json()


def extract_page_info(edition_data):
    """
    Extract page PDF URLs from the API response.
    Returns (main_pages, annexures) — each a list of (display_name, pdf_url) tuples.
    """
    data_url_suffix = edition_data.get("data_url_suffix", "")
    sections = edition_data.get("data", {}).get("sections", [])

    main_pages = []
    annexures = []

    for section in sections:
        section_id = section.get("id", "")
        section_name = section.get("name", "")
        is_annexure_section = section_id != "Main" or any(
            kw in section_name.lower() for kw in ANNEXURE_KEYWORDS
        )

        for page in section.get("pages", []):
            page_no = page.get("pageNo", "??")
            display_name = page.get("displayName", f"Page {page_no}")

            # Build the PDF URL
            pdf_file = page.get("pdfFile", "")
            if not pdf_file:
                # Derive from imgThumbFile: webepaper/photos/thumbs/{id}.png → webepaper/pdf/{id}.pdf
                thumb = page.get("imgThumbFile", "")
                match = re.search(r"(\d+)\.\w+$", thumb)
                if match:
                    page_id = match.group(1)
                    pdf_file = f"webepaper/pdf/{page_id}.pdf"
                else:
                    print(f"  [!] Cannot determine PDF for {display_name}, skipping")
                    continue

            pdf_url = data_url_suffix + pdf_file

            entry = (display_name, pdf_url)
            if is_annexure_section:
                annexures.append(entry)
            else:
                main_pages.append(entry)

    return main_pages, annexures


def download_pdf(session, url, filepath):
    """Download a single PDF file. Returns True on success."""
    try:
        resp = session.get(url, timeout=60, stream=True)
        resp.raise_for_status()

        with open(filepath, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

        file_size = os.path.getsize(filepath)
        if file_size < 500:
            os.remove(filepath)
            print(f"  [!] Skipping — file too small ({file_size} bytes)")
            return False

        print(f"  [OK] {os.path.basename(filepath)} ({file_size / 1024:.1f} KB)")
        return True

    except requests.RequestException as e:
        print(f"  [ERROR] Failed: {e}")
        return False


def merge_pdfs(pdf_files, output_path):
    """Merge multiple PDF files into one."""
    merger = PdfMerger()
    for pdf_file in pdf_files:
        try:
            merger.append(pdf_file)
        except Exception as e:
            print(f"  [!] Could not add {pdf_file}: {e}")
    merger.write(output_path)
    merger.close()


def print_editions(editions):
    """Print a formatted table of available editions."""
    print(f"{'ID':<4} {'Edition No':<12} {'Name':<35} {'Code':<8} {'Region'}")
    print("-" * 75)
    for ed in editions:
        print(f"{ed['id']:<4} {ed['edition_number']:<12} {ed['name']:<35} {ed['short_code']:<8} {ed['region']}")


def main():
    args = parse_args()
    date_str = args.date

    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        print(f"[ERROR] Invalid date format: {date_str}. Use YYYY-MM-DD.")
        sys.exit(1)

    session = create_session()

    # Fetch available editions
    print("[*] Fetching available editions...")
    editions = fetch_editions(session)

    if args.list_editions:
        print()
        print_editions(editions)
        print(f"\nUsage: python3 download_epaper.py --edition <name>")
        print(f"  e.g. --edition mangaluru")
        print(f"  e.g. --edition davangere")
        print(f"  e.g. --edition 'hubbali city'")
        print(f"\nNote: Non-Bengaluru editions require a paid subscription.")
        sys.exit(0)

    # Resolve the requested edition
    edition = resolve_edition(editions, args.edition)
    if not edition:
        print(f"[ERROR] Edition '{args.edition}' not found.")
        print(f"        Use --list-editions to see all available editions.")
        sys.exit(1)

    edition_label = edition["name"].replace(" ", "_").replace(",", "")
    output_file = args.output or f"DeccanHerald_{edition_label}_{date_str}.pdf"
    download_dir = Path(args.download_dir)
    download_dir.mkdir(parents=True, exist_ok=True)

    print("Deccan Herald ePaper Downloader")
    print("================================")
    print(f"Edition : {edition['name']} (#{edition['edition_number']})")
    print(f"Date    : {date_str}")
    print(f"Output  : {output_file}")
    print()

    # Step 1: Fetch edition metadata from API
    print("[*] Fetching edition data from API...")
    edition_data = fetch_edition_data(session, date_str, edition["edition_number"])
    edition_name = edition_data.get("data", {}).get("edition", edition["name"])
    print(f"[+] Edition: {edition_name}")

    # Step 2: Extract page PDF URLs
    main_pages, annexures = extract_page_info(edition_data)

    if not main_pages and not annexures:
        print("[ERROR] No pages found in the API response.")
        sys.exit(1)

    print(f"[+] Found {len(main_pages)} main page(s), {len(annexures)} annexure(s)")

    # Step 3: Download all main pages
    downloaded_main = []
    if main_pages:
        print(f"\n[*] Downloading {len(main_pages)} main page(s)...")
        for i, (name, url) in enumerate(main_pages, 1):
            print(f"  [{i}/{len(main_pages)}] {name}")
            filepath = download_dir / f"page_{i:03d}.pdf"
            if download_pdf(session, url, str(filepath)):
                downloaded_main.append(str(filepath))
            time.sleep(0.3)

    # Step 4: Download annexures / supplements
    downloaded_annexures = []
    if annexures:
        print(f"\n[*] Downloading {len(annexures)} annexure(s)...")
        for i, (name, url) in enumerate(annexures, 1):
            print(f"  [{i}/{len(annexures)}] {name}")
            filepath = download_dir / f"annexure_{i:03d}.pdf"
            if download_pdf(session, url, str(filepath)):
                downloaded_annexures.append(str(filepath))
            time.sleep(0.3)

    all_downloaded = downloaded_main + downloaded_annexures

    if not all_downloaded:
        print("\n[ERROR] No pages were successfully downloaded.")
        sys.exit(1)

    # Step 5: Merge all PDFs — main pages first, then annexures at the end
    print(f"\n[*] Merging {len(all_downloaded)} PDF(s)...")
    merge_pdfs(all_downloaded, output_file)

    # Step 6: Cleanup individual pages
    if not args.keep_pages:
        for f in all_downloaded:
            try:
                os.remove(f)
            except OSError:
                pass
        try:
            download_dir.rmdir()
        except OSError:
            pass

    final_size = os.path.getsize(output_file) / (1024 * 1024)
    print(f"\n{'='*40}")
    print(f"Done! {output_file} ({final_size:.1f} MB)")
    print(f"Pages: {len(downloaded_main)} main + {len(downloaded_annexures)} annexure(s)")


if __name__ == "__main__":
    main()
