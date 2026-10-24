(function () {
    'use strict';
    const button = document.getElementById('hybrid-menu-button');
    const toggle = document.getElementById('hybrid-menu-toggle');
    const drawer = document.getElementById('hybrid-navigation');
    const scrim = document.querySelector('.hybrid-menu-scrim');
    if (!button || !toggle || !drawer || !scrim) return;
    const desktop = window.matchMedia('(min-width: 1040px)');
    const close = drawer.querySelector('.hybrid-drawer-close');
    const content = document.getElementById('hybrid-main-content');
    function setOpen(open, restoreFocus) {
        open = open && !desktop.matches;
        toggle.checked = open;
        drawer.inert = !desktop.matches && !open;
        drawer.setAttribute('aria-hidden', String(drawer.inert));
        button.setAttribute('aria-expanded', String(open));
        button.setAttribute('aria-label', open ? 'Close navigation menu' : 'Open navigation menu');
        document.body.classList.toggle('hybrid-navigation-open', open);
        if (content) content.inert = open;
        if (open) {
            const first = drawer.querySelector('a[aria-current="page"], a[href]');
            if (first) first.focus();
        } else if (restoreFocus && !desktop.matches) {
            button.focus();
        }
    }
    setOpen(false, false);
    desktop.addEventListener('change', () => setOpen(false, false));
    button.addEventListener('click', () => setOpen(!toggle.checked, true));
    scrim.addEventListener('click', () => setOpen(false, true));
    if (close) close.addEventListener('click', () => setOpen(false, true));
    drawer.addEventListener('click', event => {
        if (event.target.closest('a[href]')) setOpen(false, false);
    });
    document.addEventListener('keydown', event => {
        if (event.key === 'Escape') {
            document.querySelectorAll('.hybrid-control-disclosure[open]').forEach(disclosure => {
                disclosure.open = false;
                disclosure.querySelector('summary').focus();
            });
            if (toggle.checked) {
                event.preventDefault();
                setOpen(false, true);
            }
        }
        if (event.key === 'Tab' && toggle.checked) {
            const targets = Array.from(drawer.querySelectorAll('a[href], button, summary')).filter(target => target.getClientRects().length);
            const first = targets[0], last = targets[targets.length - 1];
            if (event.shiftKey && document.activeElement === first) {
                event.preventDefault(); last.focus();
            } else if (!event.shiftKey && document.activeElement === last) {
                event.preventDefault(); first.focus();
            }
        }
    });
    const disclosures = document.querySelectorAll('.hybrid-control-disclosure');
    disclosures.forEach(disclosure => disclosure.addEventListener('toggle', () => {
        if (disclosure.open) disclosures.forEach(other => { if (other !== disclosure) other.open = false; });
    }));
    document.addEventListener('click', event => {
        disclosures.forEach(disclosure => {
            if (disclosure.open && !disclosure.contains(event.target)) disclosure.open = false;
        });
    });
})();
