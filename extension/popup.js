document.addEventListener('DOMContentLoaded', () => {
    // Fetch the total blocked count from Chrome's local storage
    chrome.storage.local.get(['mitmBlockedCount'], (result) => {
        const count = result.mitmBlockedCount || 0;
        document.getElementById('ads-blocked').innerText = count;
    });
});
