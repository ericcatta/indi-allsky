(function () {
    'use strict';
    const form = document.getElementById('hybrid-notification-ack');
    if (!form) return;
    const button = form.querySelector('button[type="submit"]');
    const status = form.querySelector('[role="status"]');
    let pending = false;
    form.addEventListener('submit', async event => {
        event.preventDefault();
        if (pending || button.disabled) return;
        pending = true;
        button.disabled = true;
        status.textContent = 'Acknowledging notification…';
        let confirmed = false;
        try {
            const response = await fetch(form.action, {
                method: 'POST', credentials: 'same-origin',
                headers: {'Content-Type': 'application/json', 'X-CSRFToken': form.elements.namedItem('csrf_token').value},
                body: '{}',
            });
            if (response.redirected) throw new Error('Your session has expired. Sign in again.');
            const result = await response.json();
            if (!response.ok || !result.allowed) throw new Error(result.message || 'Acknowledgement failed.');
            confirmed = true;
            status.textContent = result.message;
            button.textContent = 'Acknowledged';
            document.querySelectorAll('[data-notification-ack-state]').forEach(element => {
                element.textContent = 'Yes';
                element.classList.remove('modern-admin-status-warning');
            });
        } catch (error) {
            status.textContent = 'Acknowledgement could not be confirmed: ' + error.message + ' Refresh this page to check its status.';
        } finally {
            pending = false;
            button.disabled = confirmed;
        }
    });
})();
