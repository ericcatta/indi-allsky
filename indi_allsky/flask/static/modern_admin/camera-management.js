(() => {
    const forms = Array.from(document.querySelectorAll('form[data-camera-management-form]'));
    const buttons = forms.flatMap(form => Array.from(form.querySelectorAll('button')));
    const original = buttons.map(button => button.disabled);
    let pending = false;
    forms.forEach(form => form.addEventListener('submit', event => {
        if (pending) { event.preventDefault(); return; }
        pending = true;
        form.setAttribute('aria-busy', 'true');
        buttons.forEach(button => { button.disabled = true; });
    }));
    window.addEventListener('pageshow', () => {
        pending = false;
        forms.forEach(form => form.removeAttribute('aria-busy'));
        buttons.forEach((button, index) => { button.disabled = original[index]; });
    });
})();
