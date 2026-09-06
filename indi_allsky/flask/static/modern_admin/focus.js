(() => {
    'use strict';
    const root=document.getElementById('focus-tool'), byId=id=>document.getElementById(id);
    const form=byId('focus-preview-form'), image=byId('focus-image'), message=byId('focus-message');
    let busy=false, timer=null, moving=false;
    async function jsonResponse(response) {
        if(response.redirected) throw new Error('Session expired. Sign in again.');
        let data;
        try {data=await response.json();}catch(error){throw new Error('The request could not be completed. Reload the page and retry.');}
        if(!response.ok) throw new Error(data.error || (data.focuser_error || []).join(' ') || 'Request failed.');
        return data;
    }
    function schedule() {
        clearTimeout(timer);
        if(byId('focus-auto').checked && !document.hidden) timer=setTimeout(load,Number(byId('focus-interval').value)*1000);
    }
    async function load() {
        if(busy || !form.reportValidity()) return;
        busy=true; Array.from(form.elements).forEach(element=>element.disabled=true); clearTimeout(timer); message.textContent='Loading preview…';
        const url=new URL(root.dataset.previewUrl,location.origin);
        url.searchParams.set('camera_id',root.dataset.camera);
        url.searchParams.set('zoom',byId('focus-zoom').value);
        url.searchParams.set('x_offset',byId('focus-x').value);
        url.searchParams.set('y_offset',byId('focus-y').value);
        try {
            const data=await jsonResponse(await fetch(url,{credentials:'same-origin',cache:'no-store'}));
            image.src='data:image/jpeg;base64,'+data.image_b64;
            await image.decode(); image.hidden=false;byId('focus-fullscreen').disabled=false;
            message.textContent=data.source+' · Camera '+data.camera_id+' · '+data.timestamp+' · '+Math.round(data.age_seconds)+' seconds old';
            byId('focus-score').textContent='Sharpness '+data.blur_score.toFixed(2)+' · Stars '+data.star_count;
            const row=document.createElement('tr');
            [data.timestamp,data.blur_score.toFixed(2),data.star_count,'Zoom '+url.searchParams.get('zoom')+'; x '+url.searchParams.get('x_offset')+'; y '+url.searchParams.get('y_offset')].forEach(value=>{const cell=document.createElement('td');cell.textContent=value;row.append(cell);});
            byId('focus-history').prepend(row);
            while(byId('focus-history').children.length>60) byId('focus-history').lastChild.remove();
        } catch(error) {byId('focus-fullscreen').disabled=true;image.hidden=true;image.removeAttribute('src');byId('focus-score').textContent='';message.textContent=error.message;byId('focus-auto').checked=false;}
        finally {busy=false;Array.from(form.elements).forEach(element=>element.disabled=false);schedule();}
    }
    form.addEventListener('submit',event=>{event.preventDefault();load();});
    form.addEventListener('reset',()=>{clearTimeout(timer);byId('focus-history').replaceChildren();setTimeout(load,0);});
    byId('focus-auto').addEventListener('change',schedule);
    byId('focus-interval').addEventListener('change',schedule);
    document.addEventListener('visibilitychange',schedule);
    window.addEventListener('pagehide',()=>clearTimeout(timer));
    byId('focus-fullscreen').addEventListener('click',async()=>{try {await byId('focus-figure').requestFullscreen();}catch(error){message.textContent='Fullscreen is unavailable.';}});
    document.addEventListener('fullscreenchange',()=>{byId('focus-exit-fullscreen').hidden=!document.fullscreenElement;});
    byId('focus-exit-fullscreen').addEventListener('click',()=>document.exitFullscreen());
    document.querySelectorAll('[data-focus-direction]').forEach(button=>button.addEventListener('click',async()=>{
        const fieldset=byId('focus-movement');
        if(moving || fieldset.disabled) return;
        const degrees=Number(byId('focus-degrees').value), direction=button.dataset.focusDirection;
        if(!window.confirm('Move the configured observatory focuser '+degrees+' degrees '+(direction==='cw'?'clockwise':'counter-clockwise')+'?')) return;
        moving=true;fieldset.disabled=true;byId('focus-move-message').textContent='Moving focuser…';
        try {
            const data=await jsonResponse(await fetch(root.dataset.moveUrl,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-CSRFToken':root.dataset.csrf},body:JSON.stringify({DIRECTION:direction,STEP_DEGREES:degrees})}));
            byId('focus-move-message').textContent='Movement completed: '+data.steps+' steps.';
        }catch(error){byId('focus-move-message').textContent=error.message;}
        finally{moving=false;fieldset.disabled=false;}
    }));
})();
