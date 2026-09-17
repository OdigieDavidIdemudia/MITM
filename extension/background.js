const SERVER_URL = "http://192.168.252.10:5000/report-ad";

const WHITELIST = ['movieboxhd.net', 'mzfi.me', 'google.com'];

function isDomainFriendly(domain) {
    return WHITELIST.some(friendlyDomain => domain.includes(friendlyDomain));
}

// Increment our local block counter for the UI Dashboard
function incrementBlockCount() {
    chrome.storage.local.get(['mitmBlockedCount'], (result) => {
        const count = result.mitmBlockedCount || 0;
        chrome.storage.local.set({mitmBlockedCount: count + 1});
    });
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === "REPORT_AD") {
        incrementBlockCount(); // Update the UI counter!
        fetch(SERVER_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                url: sender.tab ? sender.tab.url : "unknown",
                domain: sender.tab ? new URL(sender.tab.url).hostname : "unknown",
                reason: message.data.reason,
                htmlSnippet: message.data.htmlSnippet,
                timestamp: new Date().toISOString()
            })
        }).catch(e => console.error(e));
        return true; 
    }
    
    if (message.type === "ML_SUGGEST") {
        fetch("http://192.168.252.10:5000/ml-suggest", {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                domain: message.data.domain,
                analysis: message.data.analysis
            })
        }).catch(e => console.error(e));
        return true;
    }
});

chrome.webNavigation.onCreatedNavigationTarget.addListener((details) => {
    chrome.tabs.get(details.sourceTabId, (sourceTab) => {
        if (chrome.runtime.lastError || !sourceTab) return;
        
        try {
            const targetDomain = new URL(details.url).hostname;
            const sourceDomain = new URL(sourceTab.url).hostname;
            
            if (targetDomain !== sourceDomain && targetDomain !== "" && !isDomainFriendly(targetDomain)) {
                console.log(`🛡️ MITM TAB SNIPER: Assassinated popup to ${targetDomain}`);
                
                chrome.tabs.remove(details.tabId);
                incrementBlockCount(); // Update the UI counter!
                
                fetch(SERVER_URL, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        url: details.url,
                        domain: targetDomain,
                        reason: "tab_sniper_kill",
                        htmlSnippet: "Popup spawned by " + sourceDomain,
                        timestamp: new Date().toISOString()
                    })
                }).catch(e => {});
            }
        } catch (e) {}
    });
});
