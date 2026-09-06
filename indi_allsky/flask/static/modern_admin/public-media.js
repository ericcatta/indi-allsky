(function () {
    'use strict';
    const container = document.getElementById('public-media-preview');
    if (!container) return;
    const preview = container.querySelector('img, video');
    const status = document.getElementById('public-media-status');
    const failure = () => { document.getElementById('public-media-error').hidden = false; };
    preview.addEventListener('error', failure);
    if (preview.tagName === 'IMG' && preview.complete && !preview.naturalWidth) failure();
    if (preview.tagName === 'VIDEO' && preview.error) failure();
    const copy = document.getElementById('public-media-copy');
    copy.addEventListener('click', async () => {
        try { await navigator.clipboard.writeText(copy.dataset.permalink); status.textContent = 'Link copied.'; }
        catch (_) { status.textContent = 'Copy this link: ' + copy.dataset.permalink; }
    });
    const fullscreen = document.getElementById('public-media-fullscreen');
    if (!container.requestFullscreen) {
        fullscreen.disabled = true;
        fullscreen.title = 'Fullscreen is not available in this browser.';
    }
    fullscreen.addEventListener('click', async () => {
        try { await container.requestFullscreen(); }
        catch (_) { status.textContent = 'Fullscreen is not available in this browser.'; }
    });
    document.getElementById('public-media-exit').addEventListener('click', async () => {
        try { await document.exitFullscreen(); } catch (_) { /* Already closed. */ }
    });
})();
