(() => {
    'use strict';
    const controls = document.getElementById('panorama-loop-controls');
    const data = document.getElementById('panorama-loop-frames');
    const image = document.getElementById('modern-admin-media-featured-image');
    if (!controls || !data || !image) return;
    const frames = JSON.parse(data.textContent);
    if (!frames.length) return;
    const figure = image.closest('figure');
    const viewer = figure.closest('section');
    const toggle = document.getElementById('panorama-loop-toggle');
    const previous = document.getElementById('panorama-loop-prev');
    const next = document.getElementById('panorama-loop-next');
    const speed = document.getElementById('panorama-loop-speed');
    const status = document.getElementById('panorama-loop-status');
    let index = 0, requested = 0, playing = frames.length > 1, busy = false;
    let stopped = false, timer = null, cancelLoad = null, displayed = false;

    function clearTimer() {
        window.clearTimeout(timer);
        timer = null;
    }
    function updateControls() {
        toggle.textContent = playing ? 'Pause' : 'Play';
        toggle.setAttribute('aria-pressed', String(playing));
        previous.disabled = next.disabled = busy || frames.length < 2;
        toggle.disabled = frames.length < 2;
        controls.setAttribute('aria-busy', String(busy));
        status.setAttribute('aria-live', playing ? 'off' : 'polite');
    }
    function schedule() {
        clearTimer();
        if (playing && !busy && !stopped && !document.hidden) {
            timer = window.setTimeout(() => show(requested + 1), Number(speed.value));
        }
    }
    function pause() {
        playing = false;
        clearTimer();
        updateControls();
    }
    function preload(url) {
        return new Promise((resolve, reject) => {
            const pending = new Image();
            let finished = false;
            const finish = (error) => {
                if (finished) return;
                finished = true;
                window.clearTimeout(timeout);
                pending.onload = pending.onerror = null;
                cancelLoad = null;
                error ? reject(error) : resolve();
            };
            const timeout = window.setTimeout(() => finish(new Error('timeout')), 15000);
            cancelLoad = () => finish(new Error('cancelled'));
            pending.onload = () => finish();
            pending.onerror = () => finish(new Error('unavailable'));
            pending.src = url;
        });
    }
    async function show(target) {
        if (busy || stopped || document.hidden) return;
        requested = (target + frames.length) % frames.length;
        const frame = frames[requested];
        busy = true;
        clearTimer();
        updateControls();
        status.textContent = 'Loading frame ' + (requested + 1) + ' of ' + frames.length + '…';
        try {
            if (!frame.preview_url) throw new Error('no preview');
            await preload(frame.preview_url);
            if (stopped) return;
            index = requested;
            displayed = true;
            image.hidden = false;
            image.src = frame.preview_url;
            image.alt = frame.title;
            image.dataset.originalUrl = frame.url || frame.preview_url;
            figure.dataset.mediaIndex = String(index);
            figure.setAttribute('aria-label', 'Open ' + frame.title);
            const caption = figure.querySelectorAll('figcaption span');
            caption[0].textContent = frame.filename;
            caption[1].textContent = frame.age;
            viewer.querySelector('h3').textContent = frame.title;
            viewer.querySelector('[data-loop-created]').textContent = frame.created;
            viewer.querySelector('[data-loop-timeofday]').textContent = frame.timeofday;
            const link = viewer.querySelector('[data-loop-original]');
            link.hidden = !frame.url;
            if (frame.url) link.href = frame.url;
            else link.removeAttribute('href');
            status.textContent = 'Frame ' + (index + 1) + ' of ' + frames.length;
        } catch (error) {
            if (!stopped && error.message !== 'cancelled') {
                pause();
                image.hidden = !displayed;
                status.textContent = 'Frame ' + (requested + 1) + ' could not be loaded. Playback paused. ' + (displayed ? 'Showing frame ' + (index + 1) + '. ' : 'No preview available. ') + 'Use Next or Previous to continue.';
            }
        } finally {
            busy = false;
            updateControls();
            schedule();
        }
    }
    toggle.addEventListener('click', () => {
        playing = !playing;
        updateControls();
        schedule();
    });
    previous.addEventListener('click', () => { pause(); show(requested - 1); });
    next.addEventListener('click', () => { pause(); show(requested + 1); });
    speed.addEventListener('change', schedule);
    controls.addEventListener('keydown', (event) => {
        if (event.target === speed || !['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
        event.preventDefault();
        pause();
        show(requested + (event.key === 'ArrowLeft' ? -1 : 1));
    });
    // Freeze the displayed frame before the delegated lightbox handler reads its index.
    function freezeFrame() {
        pause();
        if (cancelLoad) cancelLoad();
        requested = index;
        status.textContent = displayed ? 'Frame ' + (index + 1) + ' of ' + frames.length + ' — paused' : 'Playback paused.';
    }
    figure.addEventListener('click', freezeFrame);
    figure.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' || event.key === ' ') freezeFrame();
    });
    document.addEventListener('visibilitychange', schedule);
    window.addEventListener('pagehide', () => {
        stopped = true;
        clearTimer();
        if (cancelLoad) cancelLoad();
    });
    window.addEventListener('pageshow', (event) => {
        if (event.persisted) { stopped = false; updateControls(); schedule(); }
    });
    updateControls();
    show(0);
})();
