(function () {
    'use strict';
    const form = document.getElementById('hybrid-mini-form');
    if (!form) return;
    const field = name => form.elements.namedItem(name);
    const element = id => document.getElementById('mini-' + id);
    const preview = element('preview-image'), play = element('play'), fullscreen = element('fullscreen');
    const controls = form.querySelector('fieldset'), submit = form.querySelector('button[type="submit"]');
    const status = element('preview-status'), result = element('result'), confirm = element('confirm');
    let pending = false, generation = 0, requestController, timer, images = [], index = 0;
    function payload() {
        return {CAMERA_ID:field('CAMERA_ID').value, IMAGE_ID:field('IMAGE_ID').value,
            PRE_SECONDS:field('PRE_SECONDS_SELECT').value, POST_SECONDS:field('POST_SECONDS_SELECT').value,
            FRAMERATE:field('FRAMERATE_SELECT').value, NOTE:field('NOTE').value};
    }
    function stop() { clearTimeout(timer); timer = null; play.textContent = 'Play preview'; }
    function showFrame() {
        const item = images[index];
        if (!item) return;
        preview.src = item.url; preview.hidden = false;
        element('frame-status').textContent = 'Preview frame ' + (index + 1) + ' of ' + images.length + ' · Image ' + item.id + ' · ' + item.created;
    }
    function advance() {
        index = (index + 1) % images.length; showFrame();
        timer = setTimeout(advance, 1000 / Number(field('FRAMERATE_SELECT').value));
    }
    play.addEventListener('click', () => {
        if (timer) { stop(); return; }
        if (!images.length) return;
        play.textContent = 'Pause preview';
        timer = setTimeout(advance, 1000 / Number(field('FRAMERATE_SELECT').value));
    });
    fullscreen.addEventListener('click', async () => {
        try { await element('preview-container').requestFullscreen(); }
        catch (_) { element('frame-status').textContent = 'Fullscreen is unavailable in this browser.'; }
    });
    element('exit-fullscreen').addEventListener('click', async () => {
        try { await document.exitFullscreen(); } catch (_) { /* Already outside fullscreen. */ }
    });
    preview.addEventListener('error', () => {
        stop(); element('frame-status').textContent = 'This preview file could not be loaded. Refresh after checking media availability.';
    });
    async function refresh() {
        if (controls.disabled) return;
        const version = ++generation;
        if (requestController) requestController.abort();
        requestController = new AbortController();
        stop(); images = []; index = 0; preview.hidden = true; play.disabled = fullscreen.disabled = true;
        confirm.checked = false; status.textContent = 'Loading interval…'; element('frame-status').textContent = '';
        try {
            const url = form.dataset.previewUrl + '?' + new URLSearchParams({...payload(), NOTE:''});
            const response = await fetch(url, {credentials:'same-origin',signal:requestController.signal,headers:{Accept:'application/json'}});
            if (response.redirected) throw new Error('Your session expired. Sign in again.');
            if (!response.ok) throw new Error('Preview unavailable (' + response.status + '). Check the image and camera.');
            const data = await response.json();
            if (version !== generation) return;
            images = data.images; index = 0;
            status.textContent = data.count + ' saved frames · approximately ' + data.seconds.toFixed(1) + ' seconds at this frame rate. Interval: ' + data.start + ' – ' + data.end + '. Missing files are skipped by generation.'
                + (data.limited ? ' Preview is limited to the first 1,000 records; generation uses the complete interval.' : '')
                + (!images.length ? ' No preview is available for this interval and camera access policy.' : '');
            play.disabled = !images.length; fullscreen.disabled = !images.length || !element('preview-container').requestFullscreen;
            showFrame();
        } catch (error) {
            if (error.name !== 'AbortError' && version === generation) status.textContent = error.message;
        }
    }
    element('refresh').addEventListener('click', refresh);
    ['PRE_SECONDS_SELECT','POST_SECONDS_SELECT','FRAMERATE_SELECT'].forEach(name => field(name).addEventListener('change', refresh));
    form.addEventListener('submit', async event => {
        event.preventDefault();
        if (pending || submit.matches(':disabled') || controls.disabled) return;
        if (!confirm.checked) { result.textContent = 'Confirm the camera, image and interval first.'; confirm.focus(); return; }
        pending = true; controls.disabled = true; confirm.checked = false; element('task').hidden = true;
        result.textContent = 'Submitting…';
        try {
            const response = await fetch(form.action, {method:'POST',credentials:'same-origin',
                headers:{'Content-Type':'application/json','Accept':'application/json','X-CSRFToken':field('csrf_token').value},body:JSON.stringify(payload())});
            if (response.redirected) throw new Error('Your session expired. Sign in again.');
            if (response.status >= 500) throw new Error('The server could not confirm the queue result.');
            const data = await response.json();
            if (!response.ok) { result.textContent = data['failure-message'] || 'Request rejected.'; return; }
            result.textContent = data['success-message'];
            element('task').href = data.task_url; element('task').hidden = false;
        } catch (error) {
            result.textContent = error.message + ' Check the task queue before retrying.';
        } finally { pending = false; controls.disabled = false; }
    });
    document.addEventListener('visibilitychange', () => { if (document.hidden) stop(); });
    window.addEventListener('pagehide', () => { stop(); if (requestController) requestController.abort(); });
    refresh();
})();
