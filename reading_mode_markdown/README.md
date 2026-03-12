# Better Reader — Chrome Extension

A Chrome extension that extracts the main reading content from any webpage and displays it in a clean, customizable preview. Download as Markdown or styled HTML, copy to clipboard, and adjust font size and colors to your preference.

## Features

- **One-click extraction** — click the extension icon on any page to instantly extract and preview the article content.
- **Smart content detection** — finds `<article>`, `<main>`, common blog/news selectors, or falls back to a heuristic for the largest text block.
- **HTML → Markdown conversion** — headings, bold/italic, links, lists, tables, blockquotes, code blocks.
- **Metadata capture** — page title, author, date, description, and source URL are included in the output.
- **Rendered preview** — article opens in a clean reading view in the same tab; use the browser back button to return.
- **Raw / Preview toggle** — switch between rendered view and raw Markdown.
- **Font size controls** — increase or decrease text size with A+ / A− buttons.
- **Color customization** — pick background and foreground (text) colors with color pickers.
- **Save / Reset settings** — persist your font size and color preferences across sessions, or reset to defaults.
- **Download as `.md`** — raw Markdown file download.
- **Download as HTML** — styled HTML file with your current font size and color settings applied.
- **Copy to clipboard** — copy the raw Markdown for pasting into notes or editors.

## Installation

1. Open Chrome and navigate to `chrome://extensions/`.
2. Enable **Developer mode** (toggle in the top-right corner).
3. Click **Load unpacked** and select the `reading_mode_markdown/` folder.
4. The Better Reader icon appears in the toolbar.

## Usage

1. Navigate to any article or blog post.
2. Click the extension icon — the page is replaced with a clean reading preview.
3. Use the toolbar to:
   - **A− / A+** — adjust font size
   - **BG / FG** color pickers — change background and text colors
   - **Save** — persist your settings | **Reset** — restore defaults
   - **Raw** — toggle raw Markdown view
   - **Copy MD** — copy Markdown to clipboard
   - **Download .md** — download as Markdown file
   - **Download HTML** — download as styled HTML file
4. Press the browser **Back** button to return to the original page.

## Files

| File | Purpose |
|------|---------|
| `manifest.json` | Chrome MV3 extension manifest |
| `background.js` | Service worker — handles icon click, injects content script, opens preview |
| `content.js` | Content script — extracts reading content and converts HTML → Markdown |
| `preview.html` | Full-page preview UI with toolbar |
| `preview.js` | Preview logic — rendering, font/color controls, save/reset, copy, download |
| `icon48.png` | Toolbar icon (48 × 48) |
| `icon128.png` | Extension page icon (128 × 128) |

## Requirements

- Google Chrome 110+ (Manifest V3)
- No external dependencies — pure vanilla JS.
