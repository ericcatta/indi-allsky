(() => {
    'use strict';
    document.querySelectorAll('.hybrid-camera-frame-card').forEach(card => {
        const image=card.querySelector('img'), status=card.querySelector('.now-frame-error');
        if (!image || !status) return;
        const failed=()=>{status.hidden=false;image.hidden=true;};
        image.addEventListener('error',failed);
        image.addEventListener('load',()=>{status.hidden=true;image.hidden=false;});
        if (image.complete && !image.naturalWidth) failed();
    });
})();
