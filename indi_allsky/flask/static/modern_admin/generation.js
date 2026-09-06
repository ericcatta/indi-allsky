(function () {
    'use strict';
    const form = document.getElementById('hybrid-generation-form');
    if (!form) return;
    const fieldset = form.querySelector('fieldset');
    const button = form.querySelector('button[type="submit"]');
    const message = document.getElementById('generation-result');
    const description = document.getElementById('generation-action-description');
    const field = name => form.elements.namedItem(name);
    let pending = false;
    function describe() {
        field('CONFIRM1').checked = false;
        const action = field('ACTION_SELECT').value;
        description.textContent = action === 'none'
            ? 'Choose an action and check its scope before submitting.'
            : action.startsWith('delete_')
            ? 'Permanent deletion: only the selected camera and day/night period are affected. Original image deletion cannot be undone.'
            : action === 'upload_endofnight'
                ? 'Uploads current end-of-night data to the destinations already configured for this camera. The selected historical date is not used.'
                : 'Generation queues processing jobs for the selected camera and day/night period. Check their result in the task queue.';
        button.textContent = action === 'none' ? 'Submit action' : action.startsWith('delete_') ? 'Delete selected media' : action === 'upload_endofnight' ? 'Queue upload' : 'Queue generation';
    }
    field('ACTION_SELECT').addEventListener('change', describe);
    field('DAY_SELECT').addEventListener('change', () => { field('CONFIRM1').checked = false; });
    form.addEventListener('submit', async event => {
        event.preventDefault();
        if (pending || fieldset.disabled) return;
        const action = field('ACTION_SELECT').value;
        if (!action || action === 'none') { message.textContent = 'Choose an action.'; field('ACTION_SELECT').focus(); return; }
        if (!field('CONFIRM1').checked) { message.textContent = 'Confirm the selected camera, period and action before submitting.'; field('CONFIRM1').focus(); return; }
        const payload = {};
        ['CAMERA_ID','ACTION_SELECT','DAY_SELECT','csrf_token'].forEach(name => { payload[name] = field(name).value; });
        pending = true;
        fieldset.disabled = true;
        field('CONFIRM1').checked = false;
        message.textContent = 'Submitting…';
        try {
            const response = await fetch(form.action, {method:'POST', credentials:'same-origin',
                headers:{'Content-Type':'application/json','Accept':'application/json','X-CSRFToken':payload.csrf_token},
                body:JSON.stringify(payload)});
            if (response.redirected) throw new Error('Your session expired. Sign in again.');
            const result = await response.json();
            if (!response.ok || !result['success-message']) {
                if (response.status >= 500) throw new Error('Server error; the action may have partially completed.');
                const errors = Object.entries(result).map(([name, value]) =>
                    (name === 'form_global' ? '' : name + ': ') + (Array.isArray(value) ? value.join(' ') : String(value)));
                message.textContent = errors.join(' ') || 'The action was rejected.';
                return;
            }
            message.textContent = result['success-message'] + '. Refresh dates and tasks to inspect the result.';
            field('ACTION_SELECT').value = 'none';
            describe();
        } catch (error) {
            message.textContent = 'The result could not be confirmed. ' + error.message + ' Check the task queue and media before retrying.';
        } finally {
            pending = false;
            fieldset.disabled = false;
        }
    });
    describe();
})();
