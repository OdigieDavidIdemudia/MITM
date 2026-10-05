(function() {
    // Save a reference to the original function
    const originalRequestMediaKeySystemAccess = navigator.requestMediaKeySystemAccess;
    
    if (!originalRequestMediaKeySystemAccess) {
        return; // The browser doesn't support EME at all
    }

    // Override the function with our own hook
    navigator.requestMediaKeySystemAccess = function(keySystem, supportedConfigurations) {
        // Dispatch a custom event to the content script alerting it of the DRM request
        window.dispatchEvent(new CustomEvent("DRM_DETECTED_EVENT", {
            detail: {
                keySystem: keySystem,
                url: window.location.href,
                timestamp: Date.now()
            }
        }));

        console.log(`[DRM Detector] Intercepted request for DRM key system: ${keySystem}`);

        // Call the original function and return its result so we don't break video playback
        return originalRequestMediaKeySystemAccess.apply(this, arguments);
    };
})();
