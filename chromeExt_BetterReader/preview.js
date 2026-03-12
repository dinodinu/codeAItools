// preview.js — Runs in the preview tab: renders markdown, handles copy/download/toggle

(function () {
  "use strict";

  const content = document.getElementById("content");
  const pageTitleEl = document.getElementById("pageTitle");
  const toggleBtn = document.getElementById("toggleBtn");
  const copyBtn = document.getElementById("copyBtn");
  const downloadBtn = document.getElementById("downloadBtn");
  const downloadHtmlBtn = document.getElementById("downloadHtmlBtn");
  const toast = document.getElementById("toast");
  const fontUpBtn = document.getElementById("fontUp");
  const fontDownBtn = document.getElementById("fontDown");
  const bgColorInput = document.getElementById("bgColor");
  const fgColorInput = document.getElementById("fgColor");
  const saveBtn = document.getElementById("saveBtn");
  const resetBtn = document.getElementById("resetBtn");

  const DEFAULTS = { fontSize: 18, bgColor: "#fafafa", fgColor: "#222222" };

  let markdownText = "";
  let pageTitle = "";
  let showingRaw = false;
  let fontSize = DEFAULTS.fontSize;

  // Apply settings to the page
  function applySettings(s) {
    fontSize = s.fontSize;
    content.style.fontSize = fontSize + "px";
    document.body.style.background = s.bgColor;
    content.style.color = s.fgColor;
    bgColorInput.value = s.bgColor;
    fgColorInput.value = s.fgColor;
  }

  // Load saved settings on startup
  chrome.storage.local.get("readerSettings", (result) => {
    if (result.readerSettings) {
      applySettings(result.readerSettings);
    }
  });

  // Load data from storage
  chrome.storage.local.get("previewData", (result) => {
    const data = result.previewData;
    if (!data || !data.markdown) {
      content.textContent = "No content extracted. Click the extension icon on an article page.";
      return;
    }

    markdownText = data.markdown;
    pageTitle = data.title || "page";

    document.title = pageTitle + " — Markdown Preview";
    pageTitleEl.textContent = pageTitle;

    content.innerHTML = renderMarkdown(markdownText);
  });

  // Toggle raw / rendered
  toggleBtn.addEventListener("click", () => {
    showingRaw = !showingRaw;
    if (showingRaw) {
      content.textContent = markdownText;
      content.classList.add("raw");
      toggleBtn.textContent = "Preview";
    } else {
      content.innerHTML = renderMarkdown(markdownText);
      content.classList.remove("raw");
      toggleBtn.textContent = "Raw";
    }
  });

  // Font size controls
  fontUpBtn.addEventListener("click", () => {
    fontSize = Math.min(40, fontSize + 2);
    content.style.fontSize = fontSize + "px";
  });

  fontDownBtn.addEventListener("click", () => {
    fontSize = Math.max(10, fontSize - 2);
    content.style.fontSize = fontSize + "px";
  });

  // Background color
  bgColorInput.addEventListener("input", () => {
    document.body.style.background = bgColorInput.value;
  });

  // Foreground (text) color
  fgColorInput.addEventListener("input", () => {
    content.style.color = fgColorInput.value;
  });

  // Save current settings
  saveBtn.addEventListener("click", () => {
    const settings = {
      fontSize: fontSize,
      bgColor: bgColorInput.value,
      fgColor: fgColorInput.value,
    };
    chrome.storage.local.set({ readerSettings: settings }, () => {
      showToast("Settings saved");
    });
  });

  // Reset to defaults
  resetBtn.addEventListener("click", () => {
    applySettings(DEFAULTS);
    chrome.storage.local.remove("readerSettings", () => {
      showToast("Reset to defaults");
    });
  });

  // Copy markdown to clipboard
  copyBtn.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(markdownText);
      showToast("Copied to clipboard!");
    } catch {
      const ta = document.createElement("textarea");
      ta.value = markdownText;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      ta.remove();
      showToast("Copied to clipboard!");
    }
  });

  // Download .md file
  downloadBtn.addEventListener("click", () => {
    downloadFile(sanitizeFilename(pageTitle) + ".md", markdownText, "text/markdown;charset=utf-8");
  });

  // Download as styled HTML
  downloadHtmlBtn.addEventListener("click", () => {
    const bg = bgColorInput.value;
    const fg = fgColorInput.value;
    const fs = fontSize;
    const renderedHtml = renderMarkdown(markdownText);
    const safeTitle = pageTitle.replace(/</g, "&lt;").replace(/>/g, "&gt;");
    const htmlDoc = `<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<title>${safeTitle}</title>
<style>
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    max-width: 820px; margin: 32px auto; padding: 0 24px 60px;
    background: ${bg}; color: ${fg};
    font-size: ${fs}px; line-height: 1.7;
  }
  h1 { font-size: ${Math.round(fs * 1.78)}px; margin: 24px 0 10px; }
  h2 { font-size: ${Math.round(fs * 1.39)}px; margin: 20px 0 8px; }
  h3 { font-size: ${Math.round(fs * 1.17)}px; margin: 16px 0 6px; }
  h4 { font-size: ${fs}px; margin: 14px 0 4px; }
  p { margin: 10px 0; }
  blockquote { border-left: 4px solid #ddd; padding-left: 14px; color: #555; margin: 12px 0; }
  pre { background: #f5f5f5; padding: 12px; border-radius: 6px; overflow-x: auto; font-size: ${Math.round(fs * 0.83)}px; }
  code { background: #f0f0f0; padding: 2px 5px; border-radius: 3px; font-size: ${Math.round(fs * 0.83)}px;
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace; }
  pre code { background: none; padding: 0; }
  table { border-collapse: collapse; width: 100%; margin: 12px 0; }
  th, td { border: 1px solid #ddd; padding: 8px 12px; text-align: left; }
  th { background: #f5f5f5; }
  ul, ol { padding-left: 24px; margin: 10px 0; }
  hr { border: none; border-top: 1px solid #ddd; margin: 20px 0; }
  a { color: #0969da; }
  del { text-decoration: line-through; color: #888; }
</style>
</head><body>${renderedHtml}</body></html>`;
    downloadFile(sanitizeFilename(pageTitle) + ".html", htmlDoc, "text/html;charset=utf-8");
  });

  function downloadFile(filename, content, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
    showToast("Downloaded as " + filename);
  }

  function showToast(msg) {
    toast.textContent = msg;
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), 2000);
  }

  function sanitizeFilename(name) {
    return name
      .replace(/[<>:"/\\|?*\x00-\x1f]/g, "")
      .replace(/\s+/g, "_")
      .substring(0, 100) || "page";
  }

  /** Lightweight Markdown → HTML renderer */
  function renderMarkdown(md) {
    let html = md;
    // Escape HTML entities
    html = html.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

    // Code blocks
    html = html.replace(/```(\w*)\n([\s\S]*?)\n```/g, (_, lang, code) =>
      "<pre><code>" + code + "</code></pre>");

    // Headings
    html = html.replace(/^###### (.+)$/gm, "<h6>$1</h6>");
    html = html.replace(/^##### (.+)$/gm, "<h5>$1</h5>");
    html = html.replace(/^#### (.+)$/gm, "<h4>$1</h4>");
    html = html.replace(/^### (.+)$/gm, "<h3>$1</h3>");
    html = html.replace(/^## (.+)$/gm, "<h2>$1</h2>");
    html = html.replace(/^# (.+)$/gm, "<h1>$1</h1>");

    // Horizontal rule
    html = html.replace(/^---$/gm, "<hr>");

    // Blockquote
    html = html.replace(/^&gt; (.+)$/gm, "<blockquote>$1</blockquote>");

    // Bold and italic
    html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    html = html.replace(/\*(.+?)\*/g, "<em>$1</em>");
    html = html.replace(/~~(.+?)~~/g, "<del>$1</del>");

    // Inline code
    html = html.replace(/`([^`]+)`/g, "<code>$1</code>");

    // Links
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g,
      '<a href="$2" target="_blank" rel="noopener">$1</a>');

    // Unordered lists
    html = html.replace(/^([ ]*)- (.+)$/gm, (_, indent, text) => {
      const depth = Math.floor(indent.length / 2);
      return "<li style='margin-left:" + (depth * 16) + "px'>" + text + "</li>";
    });
    html = html.replace(/((?:<li[^>]*>.*<\/li>\n?)+)/g, "<ul>$1</ul>");

    // Ordered lists
    html = html.replace(/^([ ]*)\d+\. (.+)$/gm, (_, indent, text) => {
      const depth = Math.floor(indent.length / 2);
      return "<oli style='margin-left:" + (depth * 16) + "px'>" + text + "</oli>";
    });
    html = html.replace(/((?:<oli[^>]*>.*<\/oli>\n?)+)/g, (m) =>
      "<ol>" + m.replace(/oli/g, "li") + "</ol>");

    // Tables
    html = html.replace(/^(\|.+\|)\n(\|[\s:|-]+\|)\n((?:\|.+\|\n?)+)/gm, (_, header, sep, body) => {
      const thCells = header.split("|").filter(c => c.trim()).map(c => "<th>" + c.trim() + "</th>").join("");
      const rows = body.trim().split("\n").map(row => {
        const cells = row.split("|").filter(c => c.trim()).map(c => "<td>" + c.trim() + "</td>").join("");
        return "<tr>" + cells + "</tr>";
      }).join("");
      return "<table><thead><tr>" + thCells + "</tr></thead><tbody>" + rows + "</tbody></table>";
    });

    // Paragraphs
    html = html.replace(/\n{2,}/g, "</p><p>");
    html = "<p>" + html + "</p>";
    html = html.replace(/<p>\s*<\/p>/g, "");

    return html;
  }
})();
