/**
 * Modo local: simular fallo de comunicación con el backend
 */
(() => {
    if (!window.__FORCE_API_OFFLINE__) {
        return;
    }

    const originalFetch = window.fetch ? window.fetch.bind(window) : null;
    if (!originalFetch) {
        return;
    }

    window.fetch = (input, init) => {
        const url = typeof input === 'string' ? input : (input && input.url) || '';
        if (url.startsWith('/api/')) {
            return Promise.reject(new TypeError('Network error (modo local)'));
        }
        return originalFetch(input, init);
    };
})();
