// background.js — Service worker: on icon click, extract content and open preview tab

chrome.action.onClicked.addListener(async (tab) => {
  try {
    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      files: ["content.js"],
    });

    const data = results?.[0]?.result;
    if (!data || !data.markdown) {
      console.error("Could not extract content from this page.");
      return;
    }

    // Store data and navigate the current tab to the preview page
    // (pushes a history entry so the back button returns to the original page)
    await chrome.storage.local.set({
      previewData: {
        markdown: data.markdown,
        title: data.title || "page",
        sourceUrl: tab.url,
      },
    });

    chrome.tabs.update(tab.id, { url: chrome.runtime.getURL("preview.html") });
  } catch (err) {
    console.error("Extraction error:", err.message);
  }
});
