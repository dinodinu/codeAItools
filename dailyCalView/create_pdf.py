#!/usr/bin/env python3
"""Create a single PDF from all daily calendar images in chronological order."""

import os
import re
import sys
from pathlib import Path

from PIL import Image


# Base directory containing month folders
BASE_DIR = Path(os.path.expanduser(
    "~/Documents/Personal/dailyCalendarSrirangam"
))

# Month folder pattern: e.g. "01jan'26", "02feb'26"
MONTH_FOLDER_RE = re.compile(r"^(\d{2})\w+'\d{2}$")

# Image filename pattern: DDMM.jpg
IMAGE_RE = re.compile(r"^(\d{2})(\d{2})\.jpg$", re.IGNORECASE)

OUTPUT_FILE = BASE_DIR / "DailyCalendar_Srirangam_2026.pdf"


def collect_images() -> list[Path]:
    """Return all calendar image paths sorted chronologically (by month then day)."""
    images = []

    # Sort month folders by their numeric prefix
    month_dirs = sorted(
        (d for d in BASE_DIR.iterdir() if d.is_dir() and MONTH_FOLDER_RE.match(d.name)),
        key=lambda d: int(MONTH_FOLDER_RE.match(d.name).group(1)),
    )

    for month_dir in month_dirs:
        month_num = int(MONTH_FOLDER_RE.match(month_dir.name).group(1))

        # Collect and sort images within each month by day
        month_images = []
        for f in month_dir.iterdir():
            m = IMAGE_RE.match(f.name)
            if m and f.is_file():
                day = int(m.group(1))
                month_images.append((day, f))

        month_images.sort(key=lambda t: t[0])
        images.extend(path for _, path in month_images)

    return images


def create_pdf(image_paths: list[Path], output: Path) -> None:
    """Combine images into a single PDF, one image per page."""
    if not image_paths:
        print("No images found.")
        sys.exit(1)

    print(f"Found {len(image_paths)} images. Creating PDF...")

    # Open first image separately (Pillow needs it for save)
    first = Image.open(image_paths[0]).convert("RGB")

    rest = []
    for i, p in enumerate(image_paths[1:], start=2):
        img = Image.open(p).convert("RGB")
        rest.append(img)
        if i % 50 == 0:
            print(f"  Processed {i}/{len(image_paths)} images...")

    first.save(
        output,
        save_all=True,
        append_images=rest,
        resolution=150.0,
    )

    # Close images
    first.close()
    for img in rest:
        img.close()

    print(f"PDF saved to: {output}")


def main():
    if not BASE_DIR.is_dir():
        print(f"Directory not found: {BASE_DIR}")
        sys.exit(1)

    images = collect_images()
    create_pdf(images, OUTPUT_FILE)


if __name__ == "__main__":
    main()
