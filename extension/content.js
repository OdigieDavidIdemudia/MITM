console.log(`🛡️ MITM Extension loaded (Stealth Mode): ${window.location.href}`);

// These are domains the extension is NOT allowed to snipe
const WHITELIST = ['movieboxhd.net', 'mzfi.me', 'google.com'];

function isDomainFriendly(domain) {
    return WHITELIST.some(friendlyDomain => domain.includes(friendlyDomain));
}

// -------------------------------------------------------------------------
// PHASE 1: STEALTH POP-UP BLOCKER & HEURISTIC ENGINE
// -------------------------------------------------------------------------
const scriptInjection = document.createElement('script');
scriptInjection.textContent = `
    const WHITELIST = ['movieboxhd.net', 'mzfi.me', 'google.com', 'accounts.google.com'];
    const originalOpen = window.open;
    
    function scoreDomain(domain) {
        let score = 0; let flags = [];
        if (!domain) return {score, flags};
        const noVowels = domain.replace(/[aeiou.-]/ig, '');
        if (noVowels.length > 8 && (noVowels.length / domain.length) > 0.7) { score += 50; flags.push("high_entropy"); }
        if (/(ad|track|analytics|metric|click|pop|banner)/i.test(domain)) { score += 40; flags.push("suspicious_keyword"); }
        if (/\\.(xyz|top|win|bid|stream)$/i.test(domain)) { score += 30; flags.push("spam_tld"); }
        return { score, flags };
    }
    
    window.open = function(url, name, features) {
        try {
            let targetDomain = url ? new URL(url, window.location.origin).hostname : "";
            const isFriendly = WHITELIST.some(d => targetDomain.includes(d));
            
            if (targetDomain && isFriendly) {
                return originalOpen.apply(this, arguments);
            } else if (targetDomain) {
                let analysis = scoreDomain(targetDomain);
                if (analysis.score >= 40) {
                    // Send message out of isolated world to extension world via custom event
                    window.dispatchEvent(new CustomEvent('MITM_ML_SUGGEST', { detail: { domain: targetDomain, analysis: analysis } }));
                }
            }
        } catch(e) {}

        console.log("🛡️ MITM STEALTH BLOCKED window.open to:", url);
        return { closed: false, focus: function() {}, close: function() {}, postMessage: function() {}, document: { write: function(){} } };
    };

    const originalClick = HTMLElement.prototype.click;
    HTMLElement.prototype.click = function() {
        if (this.tagName === 'A' && this.target === '_blank') {
            try {
                let targetDomain = new URL(this.href, window.location.origin).hostname;
                const isFriendly = WHITELIST.some(d => targetDomain.includes(d));
                if (isFriendly) return originalClick.apply(this, arguments);
            } catch(e) {}
            return;
        }
        return originalClick.apply(this, arguments);
    };
`;
(document.head || document.documentElement).appendChild(scriptInjection);
scriptInjection.remove();

// Bridge to listen to the ML engine from the page context
window.addEventListener('MITM_ML_SUGGEST', (e) => {
    chrome.runtime.sendMessage({
        type: "ML_SUGGEST",
        data: e.detail
    });
});

// -------------------------------------------------------------------------
// PHASE 2: CAPTURE-PHASE EVENT INTERCEPTOR (With Whitelist)
// -------------------------------------------------------------------------
document.addEventListener('click', function(e) {
    let target = e.target;
    while (target && target.tagName !== 'A') {
        target = target.parentNode;
    }

    if (target && target.tagName === 'A' && target.target === '_blank') {
        try {
            const linkDomain = new URL(target.href, window.location.href).hostname;
            const currentDomain = window.location.hostname;
            
            // If it's a cross-origin link AND it's not on our whitelist, kill it!
            if (linkDomain !== currentDomain && !isDomainFriendly(linkDomain)) {
                console.log("🛡️ MITM STEALTH BLOCKED CROSS-ORIGIN POPUP:", target.href);
                e.preventDefault();
                e.stopPropagation();
            }
        } catch (err) {}
    }
}, true);
