// content.js — Injected into the active tab to extract reading-mode content

(function () {
  "use strict";

  /* ------------------------------------------------------------------ */
  /*  HTML  →  Markdown helpers                                         */
  /* ------------------------------------------------------------------ */

  const SKIP_TAGS = new Set(["script", "style", "noscript", "iframe", "svg",
    "nav", "footer", "header", "aside", "form", "button", "input", "select", "textarea"]);

  /** Convert an HTML element tree to Markdown (recursive). */
  function htmlToMarkdown(node, listDepth) {
    if (listDepth === undefined) listDepth = 0;

    if (node.nodeType === Node.TEXT_NODE) {
      const text = node.textContent.replace(/\s+/g, " ");
      return text;
    }

    if (node.nodeType !== Node.ELEMENT_NODE) return "";

    const tag = node.tagName.toLowerCase();

    if (SKIP_TAGS.has(tag)) return "";

    // Recursively process children
    let children = "";
    for (const child of node.childNodes) {
      children += htmlToMarkdown(child, listDepth);
    }
    children = children.trim();
    if (!children && !["img", "hr", "br"].includes(tag)) return "";

    switch (tag) {
      case "h1": return "\n\n# " + children + "\n\n";
      case "h2": return "\n\n## " + children + "\n\n";
      case "h3": return "\n\n### " + children + "\n\n";
      case "h4": return "\n\n#### " + children + "\n\n";
      case "h5": return "\n\n##### " + children + "\n\n";
      case "h6": return "\n\n###### " + children + "\n\n";

      case "p":
      case "div":
      case "section":
      case "article":
      case "main":
        return "\n\n" + children + "\n\n";

      case "br":
        return "  \n";

      case "hr":
        return "\n\n---\n\n";

      case "strong":
      case "b":
        return "**" + children + "**";

      case "em":
      case "i":
        return "*" + children + "*";

      case "del":
      case "s":
        return "~~" + children + "~~";

      case "code":
        return "`" + children + "`";

      case "pre": {
        const codeEl = node.querySelector("code");
        const lang = codeEl
          ? (codeEl.className.match(/language-(\S+)/) || [])[1] || ""
          : "";
        const codeText = (codeEl || node).textContent;
        return "\n\n```" + lang + "\n" + codeText + "\n```\n\n";
      }

      case "blockquote":
        return (
          "\n\n" +
          children
            .split("\n")
            .map((l) => "> " + l)
            .join("\n") +
          "\n\n"
        );

      case "a": {
        const href = node.getAttribute("href") || "";
        if (!href || href.startsWith("javascript:")) return children;
        // Resolve relative URLs
        let url;
        try {
          url = new URL(href, document.baseURI).href;
        } catch {
          url = href;
        }
        return "[" + children + "](" + url + ")";
      }

      case "img":
        return "";

      case "ul":
        return "\n\n" + Array.from(node.children)
          .filter((li) => li.tagName && li.tagName.toLowerCase() === "li")
          .map((li) => "  ".repeat(listDepth) + "- " + htmlToMarkdown(li, listDepth + 1).trim())
          .join("\n") + "\n\n";

      case "ol":
        return "\n\n" + Array.from(node.children)
          .filter((li) => li.tagName && li.tagName.toLowerCase() === "li")
          .map((li, i) => "  ".repeat(listDepth) + (i + 1) + ". " + htmlToMarkdown(li, listDepth + 1).trim())
          .join("\n") + "\n\n";

      case "li":
        return children;

      case "table":
        return "\n\n" + tableToMarkdown(node) + "\n\n";

      case "figure": {
        const caption = node.querySelector("figcaption");
        if (caption) return "\n\n*" + caption.textContent.trim() + "*\n\n";
        return "";
      }

      default:
        return children;
    }
  }

  /** Convert <table> element to Markdown table. */
  function tableToMarkdown(tableEl) {
    const rows = Array.from(tableEl.querySelectorAll("tr"));
    if (!rows.length) return "";

    const matrix = rows.map((tr) =>
      Array.from(tr.querySelectorAll("th, td")).map((cell) =>
        cell.textContent.trim().replace(/\|/g, "\\|").replace(/\n/g, " ")
      )
    );

    const colCount = Math.max(...matrix.map((r) => r.length));
    const padded = matrix.map((r) => {
      while (r.length < colCount) r.push("");
      return r;
    });

    let md = "| " + padded[0].join(" | ") + " |\n";
    md += "| " + padded[0].map(() => "---").join(" | ") + " |\n";
    for (let i = 1; i < padded.length; i++) {
      md += "| " + padded[i].join(" | ") + " |\n";
    }
    return md;
  }

  /* ------------------------------------------------------------------ */
  /*  Reading-mode content extraction                                   */
  /* ------------------------------------------------------------------ */

  function findReadingContent() {
    // 1. Try <article> or <main>
    const article = document.querySelector("article") || document.querySelector('[role="article"]');
    if (article) return article;

    const main = document.querySelector("main") || document.querySelector('[role="main"]');
    if (main) return main;

    // 2. Try common selectors used by news & blog sites
    const selectors = [
      ".post-content", ".entry-content", ".article-content",
      ".article-body", ".story-body", ".post-body",
      "#article-body", "#content", ".content",
      "[itemprop='articleBody']",
    ];
    for (const sel of selectors) {
      const el = document.querySelector(sel);
      if (el && el.textContent.trim().length > 200) return el;
    }

    // 3. Heuristic: largest text-heavy block
    const candidates = document.querySelectorAll("div, section");
    let best = null;
    let bestLen = 0;
    candidates.forEach((el) => {
      const len = el.innerText ? el.innerText.length : 0;
      if (len > bestLen) {
        bestLen = len;
        best = el;
      }
    });
    return best || document.body;
  }

  /* ------------------------------------------------------------------ */
  /*  Assemble the Markdown                                             */
  /* ------------------------------------------------------------------ */

  const root = findReadingContent();

  // Page title
  let title = document.title || "";

  // Metadata
  const meta = {};
  const descEl = document.querySelector('meta[name="description"]') || document.querySelector('meta[property="og:description"]');
  if (descEl) meta.description = descEl.getAttribute("content");

  const authorEl = document.querySelector('meta[name="author"]') || document.querySelector('[rel="author"]');
  if (authorEl) meta.author = authorEl.getAttribute("content") || authorEl.textContent;

  const dateEl = document.querySelector("time[datetime]") || document.querySelector('meta[property="article:published_time"]');
  if (dateEl) meta.date = dateEl.getAttribute("datetime") || dateEl.getAttribute("content") || dateEl.textContent;

  let md = "# " + title.trim() + "\n\n";

  if (meta.author) md += "**Author:** " + meta.author.trim() + "  \n";
  if (meta.date) md += "**Date:** " + meta.date.trim() + "  \n";
  if (meta.description) md += "**Description:** " + meta.description.trim() + "  \n";
  md += "**Source:** " + location.href + "\n\n---\n\n";

  md += htmlToMarkdown(root);

  // Clean up excessive blank lines
  md = md.replace(/\n{3,}/g, "\n\n").trim() + "\n";

  return { title: title, markdown: md };
})();
