(function () {
    'use strict';
    const form = document.getElementById('hybrid-account-form');
    if (!form) return;
    const button = form.querySelector('button[type="submit"]');
    const status = form.querySelector('[data-account-status]');
    let pending = false;
    form.addEventListener('submit', async function (event) {
        event.preventDefault();
        if (pending) return;
        const fields = ['NAME', 'CURRENT_PASSWORD', 'NEW_PASSWORD', 'NEW_PASSWORD2'];
        const payload = {};
        fields.forEach(name => { payload[name] = form.elements.namedItem(name).value; });
        pending = true;
        button.disabled = true;
        status.textContent = 'Saving…';
        try {
            const response = await fetch(form.action, {
                method: 'POST', credentials: 'same-origin',
                headers: {'Content-Type': 'application/json', 'X-CSRFToken': form.elements.namedItem('csrf_token').value},
                body: JSON.stringify(payload)
            });
            if (response.redirected) throw new Error('Your session has expired. Sign in again.');
            const result = await response.json();
            if (!response.ok) {
                throw new Error(Object.values(result).flat().join(' ') || 'Unable to save account.');
            }
            if (!result || Array.isArray(result) ||
                typeof result['success-message'] !== 'string' ||
                !result['success-message'].trim()) {
                throw new Error('Save not confirmed. Check your account before trying again.');
            }
            status.textContent = result['success-message'];
            ['CURRENT_PASSWORD', 'NEW_PASSWORD', 'NEW_PASSWORD2'].forEach(name => {
                form.elements.namedItem(name).value = '';
            });
        } catch (error) {
            status.textContent = error.message;
        } finally {
            pending = false;
            button.disabled = false;
        }
    });
})();
