(function () {
    const form = document.getElementById('modern-admin-full-settings-form');
    const saveButton = document.getElementById('modern-admin-full-settings-save');
    const message = document.getElementById('modern-admin-full-settings-message');
    const filter = document.getElementById('modern-admin-full-settings-filter');
    const sections = Array.from(document.querySelectorAll('[data-full-settings-section]'));
    const config = JSON.parse(document.getElementById('hybrid-full-settings-config').textContent);
    const fieldNames = config.fieldNames;
    const checkboxNames = new Set(config.checkboxNames);
    const ajaxUrl = new URL(config.ajaxUrl, window.location.href).toString();
    const csrfToken = config.csrfToken;
    let pending = false;

    function setMessage(text, tone) {
        message.hidden = false;
        message.className = 'modern-admin-table-panel modern-admin-full-settings-message modern-admin-full-settings-message-' + tone;
        message.textContent = text;
    }

    function clearErrors() {
        form.querySelectorAll('.modern-admin-settings-edit-error').forEach((error) => {
            error.hidden = true;
            error.textContent = '';
        });
        form.querySelectorAll('.is-invalid').forEach((input) => {
            input.classList.remove('is-invalid');
        });
    }

    function collectPayload() {
        const payload = {};
        fieldNames.forEach((name) => {
            try {
                const input = document.getElementById(name);
                if (!input) {
                    return;
                }

                if (checkboxNames.has(name)) {
                    payload[name] = Boolean(input.checked);
                } else {
                    payload[name] = input.value;
                }
            } catch (error) {
                throw new Error('Unable to read field "' + name + '": ' + error.message);
            }
        });
        return payload;
    }

    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        if (pending || !config.canSave) return;
        pending = true;
        clearErrors();
        message.hidden = true;
        saveButton.disabled = true;
        saveButton.textContent = 'Saving...';

        try {
            form.noValidate = true;
            const payload = collectPayload();
            const response = await fetch(ajaxUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(payload)
            });

            if (response.redirected) {
                throw new Error('Your session has expired. Sign in again before saving.');
            }
            let data = {};
            let responseText = '';
            try {
                responseText = await response.text();
                data = responseText ? JSON.parse(responseText) : {};
            } catch (error) {
                throw new Error('The server returned an unreadable response. Check Config History before retrying.');
            }
            if (!response.ok) {
                Object.entries(data).forEach(([key, errors]) => {
                    const input = document.getElementById(key);
                    const error = document.getElementById(key + '-error');
                    if (input) {
                        input.classList.add('is-invalid');
                    }
                    if (error) {
                        error.textContent = Array.isArray(errors) ? errors.join(' ') : String(errors);
                        error.hidden = false;
                    }
                });
                setMessage(response.status >= 500 ? 'Save could not be confirmed. Check Config History before retrying.' : (data.form_global ? data.form_global.join(' ') : 'Please fix the highlighted fields. No config was saved.'), 'error');
                return;
            }

            setMessage(data['success-message'] || 'Saved new config', 'success');
            const note = document.getElementById('CONFIG_NOTE');
            if (note) {
                note.value = '';
            }
            const reload = document.getElementById('RELOAD_ON_SAVE');
            if (reload) {
                reload.checked = false;
            }
        } catch (error) {
            setMessage('Save could not be confirmed: ' + error.message + ' Check Config History before retrying.', 'error');
        } finally {
            pending = false;
            saveButton.disabled = !config.canSave;
            saveButton.textContent = 'Save Full Settings';
        }
    });

    function filterSettings() {
        const query = filter.value.trim().toLowerCase();
        sections.forEach((section) => {
            const rows = Array.from(section.querySelectorAll('[data-full-settings-row]'));
            let visibleCount = 0;
            rows.forEach((row) => {
                const matches = !query || row.dataset.fullSettingsSearch.indexOf(query) !== -1;
                row.hidden = !matches;
                if (matches) {
                    visibleCount += 1;
                }
            });

            const count = section.querySelector('[data-full-settings-visible-count]');
            if (count) {
                count.textContent = visibleCount;
            }

            section.hidden = visibleCount === 0;
            if (query && visibleCount > 0) {
                section.open = true;
            }
        });
    }

    filter.addEventListener('input', filterSettings);
    const initialSearch = new URL(window.location.href).searchParams.get('search');
    if (initialSearch) {
        filter.value = initialSearch;
        filterSettings();
    }
})();
