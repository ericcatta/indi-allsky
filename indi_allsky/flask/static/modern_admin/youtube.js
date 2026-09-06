(() => {
    let pending = false;
    const status = document.getElementById('youtube-action-status');
    document.querySelectorAll('[data-youtube-action]').forEach(form => {
        form.addEventListener('submit', event => {
            if (pending) { event.preventDefault(); return; }
            if (form.dataset.youtubeAction === 'revoke' && !window.confirm('Revoke YouTube authorization for all camera profiles? Uploaded videos will be kept.')) {
                event.preventDefault(); return;
            }
            pending = true;
            document.querySelectorAll('[data-youtube-action] button').forEach(button => { button.disabled = true; });
            status.hidden = false;
            status.textContent = form.dataset.youtubeAction === 'connect' ? 'Opening Google authorization…' : 'Waiting for Google…';
        });
    });
    // Back/forward cache must not leave successful or cancelled forms locked.
    window.addEventListener('pageshow', event => { if (event.persisted) window.location.reload(); });
})();
