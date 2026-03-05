#!/usr/bin/env bash
# Copies calendar month folders into the Android assets directory.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ASSETS_DIR="$SCRIPT_DIR/app/src/main/assets"
CALENDAR_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

mkdir -p "$ASSETS_DIR"

for dir in "$CALENDAR_ROOT"/*/; do
    folder_name="$(basename "$dir")"
    # Match month folders like jan'26
    if [[ "$folder_name" =~ ^[a-zA-Z]{3}\'[0-9]{2}$ ]]; then
        echo "Copying $folder_name ..."
        cp -r "$dir" "$ASSETS_DIR/$folder_name"
    fi
done

echo "Done. Assets copied to $ASSETS_DIR"
