(() => {
    const form = document.getElementById('longterm-form');
    if (!form) return;
    const fieldset = form.querySelector('fieldset');
    const status = document.getElementById('longterm-status');
    const error = document.getElementById('longterm-error');
    let busy = false;
    form.addEventListener('reset', () => {
        if (!busy) { status.textContent = ''; error.hidden = true; }
    });
    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        if (busy) return;
        const payload = {};
        for (const name of ['CAMERA_ID', 'END_SELECT', 'DAYS_SELECT', 'PIXELS_SELECT', 'ALIGNMENT_SELECT', 'OFFSET_SELECT']) {
            payload[name] = form.elements.namedItem(name).value;
        }
        for (const name of ['REVERSE', 'LABEL']) payload[name] = form.elements.namedItem(name).checked;
        busy = true; fieldset.disabled = true; form.setAttribute('aria-busy', 'true');
        error.hidden = true; status.textContent = 'Generating… This may take a few minutes.';
        try {
            const response = await fetch(form.action, {
                method: 'POST', headers: {'Content-Type': 'application/json', 'X-CSRFToken': form.elements.namedItem('csrf_token').value},
                body: JSON.stringify(payload)
            });
            if (response.redirected || response.status === 401 || response.status === 403) throw new Error('Session expired or access denied. Reload the page and sign in.');
            const data = await response.json();
            if (!response.ok || data['failure-message']) {
                throw new Error(data['failure-message'] || Object.values(data).flat().filter(v => typeof v === 'string').join(' ') || 'Generation failed. Try again.');
            }
            const encoded = Array.isArray(data.image_b64) ? data.image_b64[0] : data.image_b64;
            if (typeof encoded !== 'string' || !/^[A-Za-z0-9+/]+={0,2}$/.test(encoded)) throw new Error('The generated image is unavailable. Try again.');
            const url = 'data:image/jpeg;base64,' + encoded;
            const image = new Image();
            await new Promise((resolve, reject) => { image.onload = resolve; image.onerror = () => reject(new Error('The generated image could not be loaded.')); image.src = url; });
            document.getElementById('longterm-image').src = url;
            document.getElementById('longterm-download').href = url;
            document.getElementById('longterm-age').textContent = 'Generated just now. ';
            document.getElementById('longterm-result').hidden = false;
            document.getElementById('longterm-download-row').hidden = false;
            document.getElementById('longterm-empty').hidden = true;
            status.textContent = Number.isFinite(data.processing_time) ? `Generated in ${data.processing_time} seconds.` : 'Keogram generated.';
        } catch (failure) {
            status.textContent = '';
            error.textContent = failure.message || 'Generation failed. Try again.'; error.hidden = false;
        } finally {
            busy = false; fieldset.disabled = false; form.removeAttribute('aria-busy');
        }
    });
})();
