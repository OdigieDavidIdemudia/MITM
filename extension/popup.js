document.addEventListener('DOMContentLoaded', () => {
    // 1. Load the blocked counter
    chrome.storage.local.get(['mitmBlockedCount'], (result) => {
        const count = result.mitmBlockedCount || 0;
        document.getElementById('ads-blocked').innerText = count;
    });

    // 2. Perform a live connectivity check to the Linux server
    const statusText = document.getElementById('server-status');
    const indicator = document.querySelector('.status-indicator');
    
    statusText.innerText = "CHECKING UPLINK...";
    indicator.style.backgroundColor = "#ffce44"; // Yellow/Orange while checking

    fetch('http://192.168.252.10:5000/ping')
        .then(response => {
            if (response.ok) {
                statusText.innerText = "UPLINK ACTIVE";
                indicator.style.backgroundColor = "#a6fa83"; // Green
            } else {
                throw new Error("Bad response");
            }
        })
        .catch(err => {
            statusText.innerText = "SERVER OFFLINE";
            indicator.style.backgroundColor = "#ff7b72"; // Red
        });
});
