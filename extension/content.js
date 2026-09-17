console.log(`🛡️ MITM Extension loaded (Stealth Mode): ${window.location.href}`);

// These are domains the extension is NOT allowed to snipe
const WHITELIST = ['movieboxhd.net', 'mzfi.me', 'google.com'];

function isDomainFriendly(domain) {
    return WHITELIST.some(friendlyDomain => domain.includes(friendlyDomain));
}

// -------------------------------------------------------------------------
// PHASE 1: STEALTH POP-UP BLOCKER
// -------------------------------------------------------------------------
const scriptInjection = document.createElement('script');
scriptInjection.textContent = `
    const WHITELIST = ['movieboxhd.net', 'mzfi.me', 'google.com', 'accounts.google.com'];
    const originalOpen = window.open;
    
    window.open = function(url, name, features) {
        try {
            let targetDomain = url ? new URL(url, window.location.origin).hostname : "";
            const isFriendly = WHITELIST.some(d => targetDomain.includes(d));
            
            // If the popup is going to Google for login, let it through!
            if (targetDomain && isFriendly) {
                console.log("🛡️ MITM ALLOWED friendly window.open to:", url);
                return originalOpen.apply(this, arguments);
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
