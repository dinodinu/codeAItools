// preview.js — Runs in the preview tab: renders markdown, handles copy/download/toggle

(function () {
  "use strict";

  const content = document.getElementById("content");
  const pageTitleEl = document.getElementById("pageTitle");
  const toggleBtn = document.getElementById("toggleBtn");
  const copyBtn = document.getElementById("copyBtn");
  const downloadBtn = document.getElementById("downloadBtn");
  const toast = document.getElementById("toast");

  let markdownText = "";
  let pageTitle = "";
  let showingRaw = false;

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
    const filename = sanitizeFilename(pageTitle) + ".md";
    const blob = new Blob([markdownText], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
    showToast("Downloaded as " + filename);
  });

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
