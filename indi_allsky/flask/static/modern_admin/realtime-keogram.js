(() => {
    'use strict';
    const root = document.getElementById('realtime-tool');
    if (!root || !root.dataset.url) return;
    const image = document.getElementById('modern-admin-keogram-image');
    const result = document.getElementById('realtime-result');
    const status = document.getElementById('realtime-status');
    const refresh = document.getElementById('realtime-refresh');
    const download = document.getElementById('realtime-download');
    const interval = Math.max(5000, Number(root.dataset.interval) || 15000);
    let busy = false, stopped = false, objectUrl = null, controller = null;
    async function update() {
        if (busy || stopped || document.hidden) return;
        busy = true;
        refresh.disabled = true;
        controller = new AbortController();
        const timeout = window.setTimeout(() => controller.abort(), 15000);
        try {
            const url = new URL(root.dataset.url, window.location.href);
            url.searchParams.set('t', Date.now());
            const response = await fetch(url.href, {credentials:'same-origin', cache:'no-store', signal:controller.signal});
            if (response.status === 404) throw new Error('No realtime keogram is available for this camera yet.');
            if (!response.ok || response.redirected || !(response.headers.get('Content-Type') || '').startsWith('image/')) {
                throw new Error('Unable to refresh the preview. Check your connection and sign-in.');
            }
            const blob = await response.blob();
            if (stopped) return;
            const next = URL.createObjectURL(blob);
            try {
                const decoded = new Image();
                decoded.src = next;
                await decoded.decode();
            } catch (error) {
                URL.revokeObjectURL(next);
                throw new Error('The preview image could not be decoded.');
            }
            if (stopped) { URL.revokeObjectURL(next); return; }
            const previous = objectUrl;
            objectUrl = next;
            image.src = next;
            result.hidden = false;
            download.hidden = false;
            if (previous) URL.revokeObjectURL(previous);
            const modified = Date.parse(response.headers.get('Last-Modified') || '');
            status.textContent = Number.isFinite(modified)
                ? (Date.now() - modified > Math.max(120000, interval * 3) ? 'Preview is stale. Last updated: ' : 'Last updated: ') + new Date(modified).toLocaleString()
                : 'Preview loaded. Update time is unavailable.';
        } catch (error) {
            if (!stopped) status.textContent = error.message + (objectUrl ? ' The last loaded preview is retained.' : '');
        } finally {
            window.clearTimeout(timeout);
            busy = false;
            if (!stopped) refresh.disabled = false;
        }
    }
    refresh.addEventListener('click', update);
    const timer = window.setInterval(update, interval);
    window.addEventListener('pagehide', () => {
        stopped = true;
        window.clearInterval(timer);
        if (controller) controller.abort();
        if (objectUrl) URL.revokeObjectURL(objectUrl);
    });
    window.addEventListener('pageshow', event => { if (event.persisted) window.location.reload(); });
    update();
})();
