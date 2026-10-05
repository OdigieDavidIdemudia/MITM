document.addEventListener("DOMContentLoaded", async () => {
    // Get the current active tab
    let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (!tab) return;

    // Ask the background script if it has detected any DRM for this specific tab
    chrome.runtime.sendMessage({ type: "GET_DRM_INFO", tabId: tab.id }, (response) => {
        const statusDiv = document.getElementById("status");
        const listUl = document.getElementById("drm-list");
        
        if (response && response.found) {
            statusDiv.innerHTML = `<span class="drm-found">DRM Detected!</span>`;
            
            // List out every DRM system that was requested
            response.systems.forEach(system => {
                let li = document.createElement("li");
                li.textContent = system;
                listUl.appendChild(li);
            });
        } else {
            statusDiv.innerHTML = `<span class="no-drm">No DRM detected.</span>`;
        }
    });
});
