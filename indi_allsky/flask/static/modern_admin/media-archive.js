(function () {
    'use strict';
    document.querySelectorAll('[data-archive-id]').forEach(card => {
        const preview = card.querySelector('img, video');
        if (!preview) return;
        const dimensions = card.querySelector('[data-preview-dimensions]');
        const updateDimensions = () => {
            if (!dimensions) return;
            dimensions.textContent = preview.videoWidth > 0 && preview.videoHeight > 0
                ? `${preview.videoWidth} × ${preview.videoHeight} (preview)`
                : 'Not recorded; preview dimensions unavailable';
        };
        const failed = () => {
            card.querySelector('.archive-preview-error').hidden = false;
            if (dimensions) dimensions.textContent = 'Not recorded; preview unavailable';
        };
        preview.addEventListener('error', failed);
        if (preview.tagName === 'VIDEO' && dimensions) {
            preview.addEventListener('loadedmetadata', updateDimensions);
            preview.addEventListener('resize', updateDimensions);
            preview.addEventListener('emptied', () => { dimensions.textContent = 'Not recorded; load preview to inspect'; });
            if (preview.readyState >= 1) updateDimensions();
            else dimensions.textContent = 'Not recorded; load preview to inspect';
        }
        if (preview.tagName === 'IMG' && preview.complete && !preview.naturalWidth) failed();
        if (preview.tagName === 'VIDEO' && preview.error) failed();
    });
})();
