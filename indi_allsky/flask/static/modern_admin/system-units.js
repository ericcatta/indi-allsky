(() => {
    'use strict';
    const root = document.getElementById('system-units');
    const result = document.getElementById('system-units-result');
    const forms = Array.from(root.querySelectorAll('form'));
    let submitted = false;
    forms.forEach(form => form.addEventListener('submit', async event => {
        event.preventDefault();
        if (submitted || form.querySelector('fieldset').disabled) return;
        if (!form.elements.confirmed.checked) {
            result.textContent = 'Confirm the device-wide change first.';
            return;
        }
        const payload = {CAMERA_ID: Number(root.dataset.camera), SERVICE_HIDDEN: form.dataset.unit, COMMAND_HIDDEN: form.elements.command.value};
        submitted = true;
        forms.forEach(item => { item.querySelector('fieldset').disabled = true; });
        result.textContent = payload.COMMAND_HIDDEN === 'validate_db'
            ? 'Checking media records… This may take a while.' : 'Submitting service request…';
        try {
            const response = await fetch(root.dataset.url, {method: 'POST', headers: {'Content-Type': 'application/json', 'X-CSRFToken': root.dataset.csrf}, body: JSON.stringify(payload)});
            if (response.redirected) {
                result.textContent = 'Session expired. Sign in and refresh service state.';
                return;
            }
            const data = await response.json();
            if (response.ok && data['success-message']) {
                if (payload.COMMAND_HIDDEN === 'validate_db') {
                    // The compatibility API returns numeric summary paragraphs.
                    // Render as text, never insert response markup into the page.
                    result.textContent = data['success-message'].replace(/<\/p>\s*<p>/g, '\n').replace(/<\/?p>/g, '');
                    return;
                }
                result.textContent = payload.COMMAND_HIDDEN === 'poweroff'
                    ? 'Shutdown request accepted. The connection will close; verify shutdown on the device. Turn it on again before reconnecting.'
                    : 'Request accepted. Refresh service state to verify the result.';
            } else {
                result.textContent = Object.values(data).flat().join(' ') || 'Request not confirmed. Refresh service state before retrying.';
            }
        } catch (error) {
            result.textContent = payload.COMMAND_HIDDEN === 'validate_db'
                ? 'The request outcome could not be confirmed. Check the validation result in system logs before retrying.'
                : 'The request outcome could not be confirmed. Refresh service state before retrying.';
        }
        // Even a lost response can hide an accepted action. Require an explicit
        // state refresh before another request; never automatically retry.
    }));
})();
