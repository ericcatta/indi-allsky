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
            result.textContent = 'Confirm this action first.';
            return;
        }
        const payload = {CAMERA_ID: Number(root.dataset.camera), SERVICE_HIDDEN: form.dataset.unit, COMMAND_HIDDEN: form.elements.command.value};
        if (payload.COMMAND_HIDDEN === 'expire_data') payload.RETENTION_TOKEN = form.dataset.retentionToken;
        const cleanup = ['flush_images', 'flush_16min_images', 'flush_timelapses', 'flush_daytime'].includes(payload.COMMAND_HIDDEN);
        submitted = true;
        forms.forEach(item => { item.querySelector('fieldset').disabled = true; });
        result.textContent = payload.COMMAND_HIDDEN === 'validate_db'
            ? 'Checking media records… This may take a while.' : 'Submitting request…';
        try {
            const response = await fetch(root.dataset.url, {method: 'POST', headers: {'Content-Type': 'application/json', 'X-CSRFToken': root.dataset.csrf}, body: JSON.stringify(payload)});
            if (response.redirected) {
                result.textContent = 'Session expired. Sign in and refresh service state.';
                return;
            }
            const data = await response.json();
            if (response.ok && data['success-message']) {
                const taskId = response.headers && response.headers.get('X-Hybrid-Task-Id');
                if (taskId && /^[1-9]\d*$/.test(taskId)) {
                    const link = document.getElementById('system-units-task');
                    link.href = root.dataset.taskUrl.replace(/\/0$/, '/' + taskId);
                    link.hidden = false;
                    result.textContent = 'Task submitted. Open its details to check completion.';
                    return;
                }
                if (cleanup) {
                    result.textContent = data['success-message'];
                    return;
                }
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
            result.textContent = cleanup
                ? 'Deletion outcome could not be confirmed. Inspect this camera’s media and system logs before retrying.'
                : payload.COMMAND_HIDDEN === 'validate_db'
                ? 'The request outcome could not be confirmed. Check the validation result in system logs before retrying.'
                : 'The request outcome could not be confirmed. Refresh service state before retrying.';
        }
        // Even a lost response can hide an accepted action. Require an explicit
        // state refresh before another request; never automatically retry.
    }));
})();
