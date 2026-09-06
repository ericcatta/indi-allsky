(function () {
    'use strict';
    const form = document.getElementById('hybrid-config-restore');
    if (!form) return;
    const button = form.querySelector('button[type="submit"]');
    const status = form.querySelector('[data-restore-status]');
    let pending = false;
    form.addEventListener('submit', async function (event) {
        event.preventDefault();
        if (pending) return;
        const payload = new FormData(form);
        // The existing endpoint treats any nonempty string as true.
        ['RESET_KEYS', 'FLUSH_CONFIGS'].forEach(function (name) {
            const field = form.elements.namedItem(name);
            payload.set(name, field.checked && !field.disabled ? 'true' : '');
        });
        pending = true;
        button.disabled = true;
        status.textContent = 'Restoring configuration…';
        try {
            const response = await fetch(form.action, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {'X-CSRFToken': payload.get('csrf_token')},
                body: payload,
            });
            if (response.redirected) {
                throw new Error('Your session has expired. Sign in again before restoring.');
            }
            const result = await response.json();
            if (!response.ok) {
                const errors = Object.entries(result).map(function ([field, messages]) {
                    return field + ': ' + (Array.isArray(messages) ? messages.join('; ') : String(messages));
                });
                throw new Error(errors.join(' — ') || 'Restore failed.');
            }
            status.textContent = result['success-message'] || 'Configuration restored.';
            if (payload.get('RESET_KEYS')) {
                status.textContent += ' Security keys were reset; sign in again.';
            }
        } catch (error) {
            status.textContent = 'Restore could not be confirmed: ' + error.message + ' Check Config History before retrying.';
        } finally {
            pending = false;
            button.disabled = false;
        }
    });
})();
