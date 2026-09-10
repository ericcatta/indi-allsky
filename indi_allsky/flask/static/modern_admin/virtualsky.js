(function () {
    'use strict';
    const flags = {CONSTELLATIONS:'constellations', CONSTELLATIONLABELS:'constellationlabels',
        SHOWSTARS:'showstars', SHOWSTARLABELS:'showstarlabels', SHOWPLANETS:'showplanets', SHOWPLANETLABELS:'showplanetlabels'};
    function overlayOptions(values, frame, width, config) {
        if (config.latitude == null || config.longitude == null)
            throw new Error('Camera location is unavailable; the sky overlay cannot be aligned.');
        const number = key => {
            if (values[key] === '' || !Number.isFinite(Number(values[key]))) throw new Error('Enter valid overlay values.');
            return Number(values[key]);
        };
        const diameter = number('IMAGE_CIRCLE_DIAMETER');
        if (!(frame.width > 0 && frame.height > 0 && width > 0 && diameter > 0) || !Number.isFinite(Number(frame.timestamp)))
            throw new Error('Image dimensions, capture time and a positive circle diameter are required.');
        const scale = width / frame.width, size = diameter * scale;
        const latitude = Number(config.latitude) + number('LATITUDE_OFFSET');
        const longitude = Number(config.longitude) + number('LONGITUDE_OFFSET');
        if (!Number.isFinite(latitude) || Math.abs(latitude) > 90 || !Number.isFinite(longitude))
            throw new Error('The adjusted latitude must be between −90 and 90 degrees.');
        const az = ((180 + number('AZIMUTH_ANGLE')) % 360 + 360) % 360;
        const result = {width:size, height:size, latitude, longitude, az,
            magnitude:number('MAGNITUDE'), clock:new Date((Number(frame.timestamp) - Number(config.timeOffset)) * 1000),
            left:(width-size)/2 + number('OFFSET_X')*scale,
            top:(frame.height*scale-size)/2 - number('OFFSET_Y')*scale};
        for (const [key, option] of Object.entries(flags)) result[option] = Boolean(values[key]);
        return result;
    }
    if (typeof module !== 'undefined') module.exports = {overlayOptions};
    if (typeof document === 'undefined') return;
    const node = document.getElementById('virtualsky-config');
    if (!node) return;
    const config = JSON.parse(node.textContent), form = document.getElementById('virtualsky-controls');
    const image = document.getElementById('modern-admin-virtualsky-image');
    const wrapper = document.getElementById('virtualsky-wrapper'), clip = document.getElementById('virtualsky-clip');
    const map = document.getElementById('hybrid-starmap'), message = document.getElementById('modern-admin-virtualsky-message');
    const refresh = document.getElementById('virtualsky-refresh'), download = document.getElementById('virtualsky-download');
    const fullscreen = document.getElementById('virtualsky-fullscreen');
    const exitFullscreen = document.getElementById('virtualsky-exit-fullscreen');
    let frame = null, sky = null, pending = false, exporting = false, timer = null, stopped = false;
    function draw() {
        if (!frame) return;
        try {
            const values = Object.fromEntries(Array.from(form.elements).filter(el => el.name).map(el => [el.name, el.type === 'checkbox' ? el.checked : el.value]));
            const options = overlayOptions(values, frame, image.clientWidth, config);
            if (!window.S || typeof window.S.virtualsky !== 'function') throw new Error('Sky map library could not be loaded. Reload this page.');
            clip.style.left = image.offsetLeft + 'px'; clip.style.top = image.offsetTop + 'px';
            clip.style.width = image.clientWidth + 'px'; clip.style.height = image.clientHeight + 'px';
            map.style.left = options.left + 'px'; map.style.top = options.top + 'px';
            if (!sky) {
                sky = window.S.virtualsky({...options, id:'hybrid-starmap',
                    projection:'fisheye', live:false, mouse:false, keyboard:false, transparent:true,
                    showgalaxy:true, gridstep:30, gridlines_eq:true, gradient:false,
                    showdate:false, showposition:false, cardinalpoints:true, credit:false});
            } else {
                sky.setLatitude(options.latitude); sky.setLongitude(options.longitude);
                sky.az_off = options.az - 180;
                sky.changeMagnitude(options.magnitude - sky.magnitude);
                sky.constellation.lines = options.constellations; sky.constellation.labels = options.constellationlabels;
                for (const key of ['showstars','showstarlabels','showplanets','showplanetlabels']) sky[key] = options[key];
                sky.setClock(options.clock); sky.calendarUpdate(); sky.resize(options.width, options.height); sky.draw();
            }
            clip.hidden = false; download.disabled = exporting; fullscreen.disabled = false;
            message.textContent = 'Frame captured ' + options.clock.toLocaleString() + '. Overlay preview updated.';
        } catch (error) {
            clip.hidden = true; download.disabled = true; message.textContent = error.message;
        }
    }
    async function load() {
        if (pending || stopped) return;
        if (exporting) { timer = setTimeout(load, 1000); return; }
        pending = true; refresh.disabled = true; clearTimeout(timer);
        download.disabled = true;
        const controller = new AbortController(), timeout = setTimeout(() => controller.abort(), 15000);
        let imageTimeout;
        try {
            const url = new URL(config.loopUrl, window.location.href);
            url.search = new URLSearchParams({camera_id:config.cameraId, limit_s:900, timestamp:config.timestamp});
            const response = await fetch(url, {signal:controller.signal, cache:'no-store'});
            if (!response.ok) throw new Error('Unable to load frame (' + response.status + ').');
            const data = await response.json(), entry = (data.image_list || [])[0];
            if (!entry) throw new Error(data.message || 'No frame from this camera in the last 15 minutes.');
            const src = entry.url.startsWith('images/') ? config.imagesBase + entry.url.slice(7) : entry.url;
            const target = new URL(src, window.location.href);
            if (!['http:', 'https:'].includes(target.protocol)) throw new Error('Unsupported image URL.');
            image.src = target.href;
            await Promise.race([image.decode(), new Promise((_, reject) => {
                imageTimeout = setTimeout(() => reject(new Error('Image loading timed out. Try Refresh frame.')), 15000);
            })]);
            frame = entry; wrapper.hidden = false; draw();
        } catch (error) {
            frame = null; wrapper.hidden = true; download.disabled = true; fullscreen.disabled = true;
            message.textContent = error.name === 'AbortError' ? 'Frame request timed out. Try Refresh frame.' : error.message;
        } finally {
            clearTimeout(timeout); clearTimeout(imageTimeout); pending = false; refresh.disabled = false;
            if (!stopped) timer = setTimeout(load, Math.max(1000, Number(config.refreshInterval) || 16000));
        }
    }
    form.addEventListener('submit', event => event.preventDefault());
    form.addEventListener('input', draw);
    form.addEventListener('change', draw);
    form.addEventListener('reset', () => setTimeout(draw, 0));
    refresh.addEventListener('click', load);
    new ResizeObserver(draw).observe(image);
    fullscreen.addEventListener('click', async () => {
        try { if (document.fullscreenElement) await document.exitFullscreen(); else await wrapper.requestFullscreen(); }
        catch (_) { message.textContent = 'Fullscreen is unavailable in this browser.'; }
    });
    exitFullscreen.addEventListener('click', async () => {
        try { await document.exitFullscreen(); fullscreen.focus(); }
        catch (_) { message.textContent = 'Unable to exit fullscreen. Use your browser fullscreen control.'; }
    });
    download.addEventListener('click', async () => {
        if (exporting || pending || !frame) return;
        exporting = true; download.disabled = true;
        const controller = new AbortController(), timeout = setTimeout(() => controller.abort(), 15000);
        try {
            // Do not silently export an overlay with the remote frame omitted.
            if (new URL(image.src).origin !== window.location.origin) {
                const response = await fetch(image.src, {mode:'cors', signal:controller.signal});
                if (!response.ok) throw new Error('Remote frame is unavailable for export.');
                await response.blob();
            }
            const canvas = await window.html2canvas(wrapper, {backgroundColor:null, scale:1, useCORS:true});
            const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'));
            if (!blob) throw new Error('PNG could not be created.');
            const url = URL.createObjectURL(blob), link = document.createElement('a');
            link.href = url; link.download = 'virtualsky_camera_' + config.cameraId + '_' + frame.timestamp + '.png';
            link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
            message.textContent = 'Overlay PNG download started.';
        } catch (_) { message.textContent = 'Overlay download failed. Remote images may require CORS permission.'; }
        finally { clearTimeout(timeout); exporting = false; download.disabled = !frame || clip.hidden; }
    });
    window.addEventListener('pagehide', () => { stopped = true; clearTimeout(timer); });
    window.addEventListener('pageshow', () => {
        if (stopped) { stopped = false; load(); }
    });
    load();
}());
