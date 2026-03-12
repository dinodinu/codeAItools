# Reading Mode to Markdown — Chrome Extension

A Chrome extension that extracts the main reading content from any webpage and lets you download or copy it as a Markdown file.

## Features

- **Smart content extraction** — detects `<article>`, `<main>`, common blog/news selectors, or falls back to a heuristic for the largest text block.
- **HTML → Markdown conversion** — headings, bold/italic, links, images, lists, tables, blockquotes, code blocks.
- **Metadata capture** — page title, author, date, description, and source URL are included in the output.
- **Download as `.md`** — one-click download with a sanitized filename.
- **Copy to clipboard** — paste directly into your notes.
- **Preview** — see the first 5 000 characters in the popup before saving.

## Installation

1. Open Chrome and navigate to `chrome://extensions/`.
2. Enable **Developer mode** (toggle in the top-right corner).
3. Click **Load unpacked** and select the `reading_mode_markdown/` folder.
4. The extension icon (blue **M**) appears in the toolbar.

## Usage

1. Navigate to any article or blog post.
2. Click the extension icon.
3. Press **Extract**.
4. Review the preview, then **Download .md** or **Copy** to clipboard.

## Files

| File | Purpose |
|------|---------|
| `manifest.json` | Chrome MV3 extension manifest |
| `popup.html` | Popup UI |
| `popup.js` | Popup logic (extract, download, copy) |
| `content.js` | Content script injected to extract & convert HTML → Markdown |
| `icon48.png` | Toolbar icon (48 × 48) |
| `icon128.png` | Extension page icon (128 × 128) |

## Requirements

- Google Chrome 110+ (Manifest V3)
- No external dependencies — pure vanilla JS.
