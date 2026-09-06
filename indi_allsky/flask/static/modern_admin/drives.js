(() => {
    'use strict';
    const root=document.getElementById('drive-tool'), result=document.getElementById('drive-result'), metadata=document.getElementById('drive-metadata');
    let busy=false;
    root.querySelectorAll('[data-drive-command]').forEach(button=>button.addEventListener('click',async()=>{
        if(busy || button.disabled) return;
        const command=button.dataset.driveCommand, identifier=button.dataset.driveId || button.dataset.deviceId;
        if(command!=='getmetadata' && !window.confirm(command+' '+identifier+'? This can interrupt access to storage.')) return;
        busy=true;
        let refreshRequired=false;
        const enabled=[...root.querySelectorAll('[data-drive-command]')].filter(control=>!control.disabled);
        enabled.forEach(control=>control.disabled=true);result.textContent='Request in progress…';metadata.replaceChildren();
        try {
            const payload={COMMAND:command};payload[button.dataset.driveId?'DRIVE_ID':'DEVICE_ID']=identifier;
            const response=await fetch(root.dataset.url,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-CSRFToken':root.dataset.csrf},body:JSON.stringify(payload)});
            if(response.redirected) throw new Error('Session expired. Sign in again.');
            let data;try {data=await response.json();}catch(error){throw new Error('The request could not be completed. Refresh devices.');}
            if(!response.ok) throw new Error(data['failure-message'] || 'Drive command failed. Refresh devices before retrying.');
            result.textContent=data['success-message'] || 'Drive metadata loaded.';
            (data.drive_data || []).forEach(row=>{const tr=document.createElement('tr');[row[1],row[2]].forEach(value=>{const td=document.createElement('td');td.textContent=String(value);tr.append(td);});metadata.append(tr);});
            if(command!=='getmetadata') {refreshRequired=true;result.textContent+=' Refresh devices to verify the current state.';return;}
        }catch(error){refreshRequired=command!=='getmetadata';result.textContent=error.message+(refreshRequired?' Refresh devices before another command.':'');}
        finally {busy=false;if(!refreshRequired) enabled.forEach(control=>control.disabled=false);}
    }));
})();
