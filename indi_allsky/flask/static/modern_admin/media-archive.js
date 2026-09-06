(function () {
    'use strict';
    document.querySelectorAll('[data-archive-id]').forEach(card => {
        const preview = card.querySelector('img, video');
        if (!preview) return;
        const failed = () => { card.querySelector('.archive-preview-error').hidden = false; };
        preview.addEventListener('error', failed);
        if (preview.tagName === 'IMG' && preview.complete && !preview.naturalWidth) failed();
        if (preview.tagName === 'VIDEO' && preview.error) failed();
    });
})();
