// 1. Inject inject.js into the main page context so it can override the real window.navigator
const script = document.createElement('script');
script.src = chrome.runtime.getURL('inject.js');
script.onload = function() {
    this.remove(); // Clean up the script tag after it executes
};
(document.head || document.documentElement).appendChild(script);

// 2. Listen for the custom event dispatched from our injected script
window.addEventListener("DRM_DETECTED_EVENT", (event) => {
    // Forward the data from the webpage context to the extension's background service worker
    chrome.runtime.sendMessage({
        type: "DRM_LOG",
        data: event.detail
    });
});
