(function () {
    'use strict';
    const button = document.getElementById('hybrid-menu-button');
    const toggle = document.getElementById('hybrid-menu-toggle');
    const drawer = document.getElementById('hybrid-navigation');
    const scrim = document.querySelector('.hybrid-menu-scrim');
    if (!button || !toggle || !drawer || !scrim) return;
    function setOpen(open, restoreFocus) {
        toggle.checked = open;
        drawer.inert = !open;
        drawer.setAttribute('aria-hidden', String(!open));
        button.setAttribute('aria-expanded', String(open));
        button.setAttribute('aria-label', open ? 'Close navigation menu' : 'Open navigation menu');
        if (open) {
            const first = drawer.querySelector('a[href]');
            if (first) first.focus();
        } else if (restoreFocus) {
            button.focus();
        }
    }
    // Each page starts with unobscured content, regardless of old saved state.
    setOpen(false, false);
    button.addEventListener('click', () => setOpen(!toggle.checked, true));
    scrim.addEventListener('click', () => setOpen(false, true));
    drawer.addEventListener('click', event => {
        if (event.target.closest('a[href]')) setOpen(false, false);
    });
    document.addEventListener('keydown', event => {
        if (event.key === 'Escape' && toggle.checked) {
            event.preventDefault();
            setOpen(false, true);
        }
    });
})();
