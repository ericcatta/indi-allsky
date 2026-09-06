(() => {
    function overlay(width, height, diameter, offsetX, offsetY, angle) {
        const x = width / 2 + offsetX, y = height / 2 - offsetY;
        const reach = Math.hypot(width, height) + Math.abs(offsetX) + Math.abs(offsetY);
        const radians = angle * Math.PI / 180;
        const dx = Math.sin(radians) * reach, dy = Math.cos(radians) * reach;
        return {x, y, radius: diameter / 2, line: [x + dx, y - dy, x - dx, y + dy]};
    }
    if (typeof module !== 'undefined' && module.exports) { module.exports = {overlay}; return; }
    const byId = id => document.getElementById(id);
    const config = JSON.parse(byId('geometry-config').textContent);
    const form = byId('geometry-form'), canvas = byId('geometry-canvas');
    const preview = byId('geometry-preview'), status = byId('geometry-status');
    const names = ['IMAGE_CIRCLE_DIAMETER', 'OFFSET_X', 'OFFSET_Y', 'LINE_WIDTH', 'LINE_COLOR', 'KEOGRAM_ANGLE', 'AZIMUTH_ANGLE', 'KEOGRAM_LINE'];
    const fields = Object.fromEntries(names.map(name => [name, byId(name)]));
    const initial = Object.fromEntries(names.map(name => [name, fields[name].type === 'checkbox' ? fields[name].checked : fields[name].value]));
    const image = new Image();
    let loaded = false;
    function message(text) { status.textContent = text; }
    function values() {
        const numbers = ['IMAGE_CIRCLE_DIAMETER', 'OFFSET_X', 'OFFSET_Y', 'LINE_WIDTH', 'KEOGRAM_ANGLE'];
        const result = Object.fromEntries(numbers.map(name => [name, fields[name].value.trim() === '' ? NaN : Number(fields[name].value)]));
        const valid = numbers.every(name => Number.isFinite(result[name]))
            && ['IMAGE_CIRCLE_DIAMETER','OFFSET_X','OFFSET_Y','LINE_WIDTH'].every(name => Number.isInteger(result[name]))
            && result.IMAGE_CIRCLE_DIAMETER > 0 && result.IMAGE_CIRCLE_DIAMETER <= 100000
            && Math.abs(result.OFFSET_X) <= 100000 && Math.abs(result.OFFSET_Y) <= 100000
            && result.LINE_WIDTH > 0 && result.LINE_WIDTH <= 100
            && Math.abs(result.KEOGRAM_ANGLE) <= 180;
        if (!valid) { message('Enter a positive whole-pixel diameter, whole-pixel offsets, line width 1–100 and angle −180° to 180°. Pixel values must be within 100000.'); return null; }
        return result;
    }
    function syncAzimuth() {
        const angle = Number(fields.KEOGRAM_ANGLE.value);
        fields.AZIMUTH_ANGLE.value = angle < 0 ? 360 + angle : angle;
    }
    function draw() {
        if (!loaded) return;
        const v = values(); if (!v) return;
        const displayWidth = Math.max(canvas.getBoundingClientRect().width, 1);
        const density = window.devicePixelRatio || 1;
        canvas.width = Math.round(displayWidth * density);
        canvas.height = Math.round(canvas.width * image.naturalHeight / image.naturalWidth);
        const ctx = canvas.getContext('2d');
        ctx.scale(canvas.width / image.naturalWidth, canvas.height / image.naturalHeight);
        ctx.drawImage(image, 0, 0);
        const geometry = overlay(image.naturalWidth, image.naturalHeight, v.IMAGE_CIRCLE_DIAMETER, v.OFFSET_X, v.OFFSET_Y, v.KEOGRAM_ANGLE);
        ctx.strokeStyle = fields.LINE_COLOR.value;
        ctx.lineWidth = v.LINE_WIDTH * image.naturalWidth / displayWidth;
        ctx.beginPath();ctx.arc(geometry.x, geometry.y, geometry.radius, 0, Math.PI * 2);ctx.stroke();
        if (fields.KEOGRAM_LINE.checked) {
            ctx.beginPath();ctx.moveTo(geometry.line[0], geometry.line[1]);ctx.lineTo(geometry.line[2], geometry.line[3]);ctx.stroke();
        }
        message('Preview ' + image.naturalWidth + ' × ' + image.naturalHeight + ' pixels. Geometry changes are not saved.');
    }
    form.addEventListener('submit', event => { event.preventDefault(); draw(); });
    Object.entries(fields).forEach(([name, field]) => field.addEventListener('input', () => {
        if (name === 'AZIMUTH_ANGLE') {
            const angle = Number(field.value);
            if (!field.value.trim() || !Number.isFinite(angle) || angle < 0 || angle >= 360) { message('Azimuth must be between 0° and 359.9°.'); return; }
            fields.KEOGRAM_ANGLE.value = angle > 180 ? angle - 360 : angle;
        } else if (name === 'KEOGRAM_ANGLE') syncAzimuth();
        if (name === 'LINE_WIDTH' || name === 'LINE_COLOR') {
            try { localStorage.setItem('hybrid-image-circle-style', JSON.stringify({width:fields.LINE_WIDTH.value,color:fields.LINE_COLOR.value})); } catch (_) { /* Drawing remains available without local storage. */ }
        }
        draw();
    }));
    byId('geometry-fit').addEventListener('click', () => {
        if (!loaded) return;
        fields.IMAGE_CIRCLE_DIAMETER.value = Math.min(image.naturalWidth, image.naturalHeight);
        fields.OFFSET_X.value = 0;fields.OFFSET_Y.value = 0;draw();
    });
    byId('geometry-reset').addEventListener('click', () => {
        ['IMAGE_CIRCLE_DIAMETER','OFFSET_X','OFFSET_Y','KEOGRAM_ANGLE'].forEach(name => { fields[name].value = initial[name]; });
        fields.KEOGRAM_LINE.checked = initial.KEOGRAM_LINE;syncAzimuth();draw();
    });
    byId('geometry-copy').addEventListener('click', async () => {
        const v = values();if (!v) return;
        const text = JSON.stringify({LENS_IMAGE_CIRCLE:v.IMAGE_CIRCLE_DIAMETER,LENS_OFFSET_X:v.OFFSET_X,LENS_OFFSET_Y:v.OFFSET_Y,KEOGRAM_ANGLE:v.KEOGRAM_ANGLE},null,2);
        try { await navigator.clipboard.writeText(text);message('Geometry values copied.'); }
        catch (_) { message('Copy these values: ' + text); }
    });
    byId('geometry-review').addEventListener('click', () => {
        const v = values(); if (!v) return;
        const target = new URL(byId('geometry-review').dataset.settingsUrl, location.href);
        target.searchParams.set('helper_diameter',v.IMAGE_CIRCLE_DIAMETER);
        target.searchParams.set('helper_offset_x',v.OFFSET_X);
        target.searchParams.set('helper_offset_y',v.OFFSET_Y);
        if (target.searchParams.has('profile_id')) target.hash = 'geometry-lens-settings';
        location.assign(target.toString());
    });
    byId('geometry-fullscreen').addEventListener('click', async () => {
        try { await preview.requestFullscreen();draw(); } catch (_) { message('Fullscreen is not available in this browser.'); }
    });
    byId('geometry-exit').addEventListener('click', async () => { await document.exitFullscreen();draw(); });
    if (!preview.requestFullscreen) { byId('geometry-fullscreen').disabled=true;byId('geometry-fullscreen').title='Fullscreen is not available in this browser.'; }
    window.addEventListener('resize', draw);
    document.addEventListener('fullscreenchange', () => window.requestAnimationFrame(draw));
    try {
        const style = JSON.parse(localStorage.getItem('hybrid-image-circle-style'));
        if (style && Number.isInteger(Number(style.width)) && Number(style.width)>0 && Number(style.width)<=100) fields.LINE_WIDTH.value=style.width;
        if (style && [...fields.LINE_COLOR.options].some(option => option.value===style.color)) fields.LINE_COLOR.value=style.color;
    } catch (_) { /* Ignore missing/corrupt style preferences. */ }
    syncAzimuth();
    image.onload = () => { loaded=true;draw(); };
    image.onerror = () => {
        loaded=false;form.querySelector('fieldset').disabled=true;
        message('The image could not be loaded. Check the selected file or choose another image.');
    };
    if (config.imageUrl) image.src = config.imageUrl;
})();
