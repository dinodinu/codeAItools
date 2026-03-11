#!/usr/bin/env python3
"""
The Hindu ePaper Downloader
Downloads all pages of The Hindu ePaper edition and merges them into a single PDF.

Usage:
    python3 download_epaper.py                          # Today's Bangalore edition
    python3 download_epaper.py --edition chennai        # Today's Chennai edition
    python3 download_epaper.py --date 2025-03-10        # Specific date
    python3 download_epaper.py --list-editions          # List all available editions
    python3 download_epaper.py --cookie "name=val;..."  # With auth cookie for PDFs

Authentication:
    PDF downloads require a valid subscriber session. Provide your browser cookies
    using --cookie or by setting the TH_COOKIE environment variable.

    To get cookies:
    1. Log in to https://epaper.thehindu.com/reader in your browser
    2. Open Developer Tools (F12) -> Console
    3. Type: document.cookie
    4. Copy the output and pass it via --cookie
"""

import argparse
import os
import re
import sys
from datetime import datetime, timezone, timedelta

import requests
from PyPDF2 import PdfMerger

# ── Constants ───────────────────────────────────────────────────────────────────
API_BASE = "https://epaper.thehindu.com/ccidist-ws/th/"
DEFAULT_EDITION = "bangalore"
IST = timezone(timedelta(hours=5, minutes=30))

EDITION_NAME_MAP = {
    "Bangalore": "Bengaluru",
    "Mangalore": "Mangaluru",
}

# ── Helpers ─────────────────────────────────────────────────────────────────────

def today_ist():
    """Return today's date in IST as YYYY-MM-DD."""
    return datetime.now(IST).strftime("%Y-%m-%d")


def clean_edition_title(title):
    """Remove 'EPaper-' prefix and map legacy names."""
    name = title.replace("EPaper-", "")
    return EDITION_NAME_MAP.get(name, name)


def parse_cookies(cookie_str):
    """Parse a cookie string into a dict."""
    cookies = {}
    if not cookie_str:
        return cookies
    for part in cookie_str.split(";"):
        part = part.strip()
        if "=" in part:
            key, val = part.split("=", 1)
            cookies[key.strip()] = val.strip()
    return cookies


# ── API Functions ───────────────────────────────────────────────────────────────

def fetch_editions(session, date_str):
    """Fetch all available editions (regions) for a given date."""
    url = (
        f"{API_BASE}?json=true"
        f"&fromDate={date_str}&toDate={date_str}"
        f"&skipSections=true&os=web&excludePublications=*-*"
    )
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    editions = []
    for pub in data.get("publications", []):
        web_issues = pub.get("issues", {}).get("web", [])
        if web_issues:
            issue = web_issues[0]
            editions.append({
                "id": pub["id"],
                "title": clean_edition_title(pub["title"]),
                "page_count": issue.get("pageCount", 0),
                "issue_id": issue.get("id"),
                "download_url": issue.get("downloadPagesUrl", ""),
            })
    return editions


def resolve_edition(editions, query):
    """Find an edition matching the user query (fuzzy match on name or id)."""
    q = query.lower().strip()
    # Exact id match
    for e in editions:
        if e["id"].lower() == q or e["id"].lower() == f"th_{q}":
            return e
    # Name match
    for e in editions:
        if q in e["title"].lower():
            return e
    # Partial id match
    for e in editions:
        if q in e["id"].lower():
            return e
    return None


def fetch_issue_details(session, edition_id, date_str):
    """Fetch issue details with sections for an edition."""
    url = (
        f"{API_BASE}{edition_id}/issues/"
        f"?epubName={edition_id}_web&limit=1"
        f"&skipSections=false"
        f"&fromDate={date_str}&toDate={date_str}"
    )
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_opf_manifest(session, edition_id, issue_id):
    """Fetch and parse the OPF package manifest to get page PDF filenames."""
    url = f"{API_BASE}{edition_id}/issues/{issue_id}/OPS/package.opf"
    resp = session.get(url, timeout=30)
    resp.raise_for_status()

    # Use regex to extract PDF items - avoids XML namespace issues with cci: prefix
    pdf_files = re.findall(
        r'<item\s[^>]*href="([^"]*_pdf\.pdf)"[^>]*media-type="application/pdf"',
        resp.text,
    )
    # Also match reversed attribute order
    pdf_files += re.findall(
        r'<item\s[^>]*media-type="application/pdf"[^>]*href="([^"]*_pdf\.pdf)"',
        resp.text,
    )
    # Deduplicate while preserving order
    seen = set()
    unique = []
    for f in pdf_files:
        if f not in seen:
            seen.add(f)
            unique.append(f)
    return unique


def download_pdf(session, url, filepath):
    """Download a single PDF file."""
    resp = session.get(url, timeout=60, stream=True)
    if resp.status_code == 307:
        location = resp.headers.get("Location", "")
        if "registration" in location or "login" in location:
            return False, "auth_required"
    resp.raise_for_status()

    content_type = resp.headers.get("Content-Type", "")
    if "text/html" in content_type:
        return False, "auth_required"

    with open(filepath, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    return True, "ok"


def download_via_pagespdf(session, download_url, page_count, filepath):
    """Download all pages as a single PDF using the pagespdf POST endpoint."""
    pages = list(range(1, page_count + 1))
    resp = session.post(
        download_url,
        json={"pages": pages},
        timeout=120,
        stream=True,
        allow_redirects=False,
    )

    if resp.status_code == 307:
        location = resp.headers.get("Location", "")
        if "registration" in location or "login" in location:
            return False, "auth_required"

    if resp.status_code >= 500:
        return False, "server_error"

    resp.raise_for_status()

    content_type = resp.headers.get("Content-Type", "")
    if "text/html" in content_type:
        return False, "auth_required"

    with open(filepath, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    return True, "ok"


def merge_pdfs(pdf_paths, output_path):
    """Merge multiple PDFs into one."""
    merger = PdfMerger()
    for path in pdf_paths:
        try:
            merger.append(path)
        except Exception as e:
            print(f"  Warning: Could not merge {os.path.basename(path)}: {e}")
    merger.write(output_path)
    merger.close()


# ── Main ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Download The Hindu ePaper as PDF"
    )
    parser.add_argument(
        "--date", "-d",
        default=today_ist(),
        help="Date in YYYY-MM-DD format (default: today IST)"
    )
    parser.add_argument(
        "--edition", "-e",
        default=DEFAULT_EDITION,
        help=f"Edition name or ID (default: {DEFAULT_EDITION})"
    )
    parser.add_argument(
        "--list-editions", "-l",
        action="store_true",
        help="List all available editions and exit"
    )
    parser.add_argument(
        "--cookie", "-c",
        default=os.environ.get("TH_COOKIE", ""),
        help="Browser cookie string for authenticated PDF downloads"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output PDF filename (default: TheHindu_<Edition>_<Date>.pdf)"
    )
    parser.add_argument(
        "--download-dir",
        default="pages",
        help="Directory for downloaded page PDFs (default: pages)"
    )
    parser.add_argument(
        "--keep-pages",
        action="store_true",
        help="Keep individual page PDFs after merging"
    )
    parser.add_argument(
        "--bulk",
        action="store_true",
        help="Use bulk pagespdf endpoint instead of per-page download"
    )

    args = parser.parse_args()

    # Set up session
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://epaper.thehindu.com/reader",
    })

    if args.cookie:
        session.cookies.update(parse_cookies(args.cookie))

    date_str = args.date

    # Fetch editions
    print(f"Fetching editions for {date_str}...")
    try:
        editions = fetch_editions(session, date_str)
    except Exception as e:
        print(f"Error fetching editions: {e}", file=sys.stderr)
        sys.exit(1)

    if not editions:
        print(f"No editions available for {date_str}")
        sys.exit(1)

    # List editions mode
    if args.list_editions:
        print(f"\nAvailable editions for {date_str}:")
        print(f"{'ID':<30} {'Edition':<25} {'Pages':>5}")
        print("-" * 62)
        for e in editions:
            print(f"{e['id']:<30} {e['title']:<25} {e['page_count']:>5}")
        sys.exit(0)

    # Resolve edition
    edition = resolve_edition(editions, args.edition)
    if not edition:
        print(f"Edition '{args.edition}' not found. Available editions:")
        for e in editions:
            print(f"  {e['id']} - {e['title']}")
        sys.exit(1)

    edition_id = edition["id"]
    edition_title = edition["title"]
    page_count = edition["page_count"]
    issue_id = edition["issue_id"]
    download_url = edition["download_url"]

    print(f"Edition: {edition_title} ({edition_id})")
    print(f"Issue ID: {issue_id}, Pages: {page_count}")

    output_name = args.output or f"TheHindu_{edition_title}_{date_str}.pdf"

    # ── Bulk download mode ──────────────────────────────────────────────────
    if args.bulk:
        print(f"\nDownloading all {page_count} pages via bulk endpoint...")
        ok, status = download_via_pagespdf(session, download_url, page_count, output_name)
        if ok:
            size_mb = os.path.getsize(output_name) / (1024 * 1024)
            print(f"\nSaved: {output_name} ({size_mb:.1f} MB)")
            return
        if status == "auth_required":
            print("\nAuthentication required for PDF downloads.")
            print("Please provide your browser cookies using --cookie.")
            print("See --help for instructions.")
            sys.exit(1)
        # Server error — fall through to per-page download
        print(f"Bulk endpoint returned a server error. Falling back to per-page download...")

    # ── Per-page download mode ──────────────────────────────────────────────
    print(f"\nFetching page manifest...")
    try:
        pdf_files = fetch_opf_manifest(session, edition_id, issue_id)
    except Exception as e:
        print(f"Error fetching manifest: {e}", file=sys.stderr)
        sys.exit(1)

    if not pdf_files:
        print("No page PDFs found in manifest.")
        sys.exit(1)

    print(f"Found {len(pdf_files)} page PDFs")

    # Create download directory
    os.makedirs(args.download_dir, exist_ok=True)

    # Download each page
    base_url = f"{API_BASE}{edition_id}/issues/{issue_id}/OPS/"
    downloaded = []
    auth_failed = False

    for i, pdf_file in enumerate(pdf_files, 1):
        page_path = os.path.join(args.download_dir, f"page_{i:03d}.pdf")
        pdf_url = base_url + pdf_file

        print(f"  Downloading page {i}/{len(pdf_files)}...", end=" ", flush=True)

        try:
            ok, status = download_pdf(session, pdf_url, page_path)
            if ok:
                size_kb = os.path.getsize(page_path) / 1024
                print(f"OK ({size_kb:.0f} KB)")
                downloaded.append(page_path)
            elif status == "auth_required":
                print("AUTH REQUIRED")
                auth_failed = True
                break
        except Exception as e:
            print(f"FAILED: {e}")

    if auth_failed:
        print(f"\nAuthentication required for PDF downloads.")
        print("Please provide your browser cookies using --cookie.")
        print("See --help for instructions.")
        # Clean up any partial downloads
        for p in downloaded:
            os.remove(p)
        sys.exit(1)

    if not downloaded:
        print("No pages were downloaded.")
        sys.exit(1)

    # Merge PDFs
    print(f"\nMerging {len(downloaded)} pages...")
    merge_pdfs(downloaded, output_name)

    size_mb = os.path.getsize(output_name) / (1024 * 1024)
    print(f"Saved: {output_name} ({size_mb:.1f} MB)")

    # Clean up
    if not args.keep_pages:
        for p in downloaded:
            os.remove(p)
        try:
            os.rmdir(args.download_dir)
        except OSError:
            pass
        print("Cleaned up individual page files.")


if __name__ == "__main__":
    main()
