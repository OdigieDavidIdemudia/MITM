// Store DRM detection state per tab
let drmData = {};

// Listen for messages from the content script or the popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === "DRM_LOG" && sender.tab) {
        const tabId = sender.tab.id;
        
        // Initialize set for this tab if it doesn't exist
        if (!drmData[tabId]) {
            drmData[tabId] = new Set();
        }
        
        // Add the detected DRM system (e.g., com.widevine.alpha)
        drmData[tabId].add(message.data.keySystem);
        
        // Show a red "DRM" badge on the extension icon in the toolbar
        chrome.action.setBadgeText({ text: "DRM", tabId: tabId });
        chrome.action.setBadgeBackgroundColor({ color: "#FF0000", tabId: tabId });
    }
    
    if (message.type === "GET_DRM_INFO") {
        const tabId = message.tabId;
        // Convert Set back to an Array so it can be sent over messaging
        const data = drmData[tabId] ? Array.from(drmData[tabId]) : [];
        sendResponse({ found: data.length > 0, systems: data });
    }
});

// Clean up data when a tab is closed to prevent memory leaks
chrome.tabs.onRemoved.addListener((tabId) => {
    delete drmData[tabId];
});

// Clean up data when a tab is refreshed/navigates to a new page
chrome.tabs.onUpdated.addListener((tabId, changeInfo) => {
    if (changeInfo.status === 'loading') {
        delete drmData[tabId];
        chrome.action.setBadgeText({ text: "", tabId: tabId }); // Clear the badge
    }
});
