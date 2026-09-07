(() => {
    'use strict';
    const get=id=>document.getElementById(id), root=get('upgrade-tool'), fields=get('upgrade-fields'), result=get('upgrade-result');
    let submitted=false;
    get('upgrade-form').addEventListener('submit',async event=>{
        event.preventDefault();
        if(submitted || fields.disabled) return;
        if(!get('upgrade-backup').checked || !get('upgrade-maintenance').checked) {
            result.textContent='Confirm both the backup and capture interruption first.';return;
        }
        submitted=true;fields.disabled=true;
        result.textContent='Submitting upgrade request…';
        try {
            const response=await fetch(root.dataset.url,{method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':root.dataset.csrf},body:JSON.stringify({backup_confirmed:true,maintenance_confirmed:true,observed_token:root.dataset.token})});
            if(response.redirected) {result.textContent='Session expired. Sign in and refresh upgrade status.';return;}
            const data=await response.json();
            result.textContent=data.message || 'Unexpected response. Refresh upgrade status before retrying.';
        } catch(error) {
            result.textContent='The request outcome could not be confirmed. Refresh upgrade status before retrying; an upgrade may already be running.';
        } finally {
            get('upgrade-backup').checked=false;get('upgrade-maintenance').checked=false;
            // A lost response may hide an accepted job: never retry automatically.
        }
    });
})();
