(() => {
    'use strict';
    const root=document.getElementById('sensor-tool'), status=document.getElementById('sensor-status');
    const refresh=document.getElementById('sensor-refresh'), showAll=document.getElementById('sensor-show-all');
    const bodies=['user','temp'].map(group=>document.getElementById('sensor-'+group+'-rows'));
    let active=null;
    function filter() { bodies.forEach(body=>[...body.children].forEach(row=>{row.hidden=!showAll.checked && row.dataset.used!=='true';})); }
    function rows(values, group) {
        if(!Array.isArray(values) || values.length!==60) throw Error('invalid_response');
        return values.map((value,index)=>{
            if(!value || value.slot!==`sensor_${group}_${index}` || typeof value.label!=='string' || typeof value.used!=='boolean'
                || !(value.value===null || typeof value.value==='string' || (typeof value.value==='number' && Number.isFinite(value.value)))) throw Error('invalid_response');
            const row=document.createElement('tr');row.dataset.used=String(value.used);
            [value.slot,value.label,value.value===null?'Unavailable':String(value.value)].forEach(text=>{
                const cell=document.createElement('td');cell.textContent=text;row.appendChild(cell);
            });return row;
        });
    }
    async function load() {
        if(active)return;
        active=new AbortController();refresh.disabled=true;
        try {
            const response=await fetch(root.dataset.url+'?'+new URLSearchParams({camera_id:root.dataset.camera}),{signal:active.signal});
            if(response.redirected)throw Error('session_expired');
            if(!response.ok)throw Error('request_failed');
            const data=await response.json();
            if(!data || !data.readings || !(data.last_update===null || typeof data.last_update==='string'))throw Error('invalid_response');
            const updates=['user','temp'].map(group=>rows(data.readings[group],group));
            updates.forEach((values,index)=>bodies[index].replaceChildren(...values));filter();
            status.textContent=data.last_update===null?'No image metadata from the last 15 minutes.':`Last image: ${data.last_update} · age ${data.last_update_age_s} s`;
        } catch(error) {
            if(error.name!=='AbortError')status.textContent=(error.message==='session_expired'?'Session expired. Sign in and reload.':'Could not update sensors. Try Refresh.')+' Displayed readings may be out of date.';
        } finally {active=null;refresh.disabled=false;}
    }
    showAll.addEventListener('change',filter);refresh.addEventListener('click',load);
    const timer=window.setInterval(load,5000);
    window.addEventListener('pagehide',()=>{window.clearInterval(timer);if(active)active.abort();});
    filter();load();
})();
