(() => {
    'use strict';
    const root=document.getElementById('focus-tool'), byId=id=>document.getElementById(id);
    const form=byId('focus-preview-form'), image=byId('focus-image'), message=byId('focus-message');
    let busy=false, timer=null, moving=false, stopped=false, previewController=null;
    async function jsonResponse(response) {
        if(response.redirected) throw new Error('Session expired. Sign in again.');
        let data;
        try {data=await response.json();}catch(error){throw new Error('The request could not be completed. Reload the page and retry.');}
        if(!response.ok) throw new Error(data.error || (data.focuser_error || []).join(' ') || 'Request failed.');
        return data;
    }
    function schedule() {
        clearTimeout(timer);
        if(!stopped && byId('focus-auto').checked && !document.hidden) timer=setTimeout(load,Number(byId('focus-interval').value)*1000);
    }
    async function load() {
        if(busy || stopped || !form.reportValidity()) return;
        busy=true; Array.from(form.elements).forEach(element=>element.disabled=true); clearTimeout(timer); message.textContent='Loading preview…';
        const url=new URL(root.dataset.previewUrl,location.origin);
        url.searchParams.set('camera_id',root.dataset.camera);
        url.searchParams.set('zoom',byId('focus-zoom').value);
        url.searchParams.set('x_offset',byId('focus-x').value);
        url.searchParams.set('y_offset',byId('focus-y').value);
        previewController=new AbortController();
        const controller=previewController;
        const timeout=setTimeout(()=>controller.abort(),15000);
        try {
            const data=await jsonResponse(await fetch(url,{credentials:'same-origin',cache:'no-store',signal:controller.signal}));
            if(stopped) return;
            image.src='data:image/jpeg;base64,'+data.image_b64;
            await image.decode(); if(stopped) return; image.hidden=false;byId('focus-fullscreen').disabled=false;
            message.textContent=data.source+' · Camera '+data.camera_id+' · '+data.timestamp+' · '+Math.round(data.age_seconds)+' seconds old';
            byId('focus-score').textContent='Sharpness '+data.blur_score.toFixed(2)+' · Stars '+data.star_count;
            const row=document.createElement('tr');
            [data.timestamp,data.blur_score.toFixed(2),data.star_count,'Zoom '+url.searchParams.get('zoom')+'; x '+url.searchParams.get('x_offset')+'; y '+url.searchParams.get('y_offset')].forEach(value=>{const cell=document.createElement('td');cell.textContent=value;row.append(cell);});
            byId('focus-history').prepend(row);
            while(byId('focus-history').children.length>60) byId('focus-history').lastChild.remove();
        } catch(error) {if(stopped) return; byId('focus-fullscreen').disabled=true;image.hidden=true;image.removeAttribute('src');byId('focus-score').textContent='';message.textContent=error.name==='AbortError'?'Preview request timed out. Refresh to retry.':error.message;byId('focus-auto').checked=false;}
        finally {clearTimeout(timeout);previewController=null;busy=false;if(!stopped){Array.from(form.elements).forEach(element=>element.disabled=false);schedule();}}
    }
    form.addEventListener('submit',event=>{event.preventDefault();load();});
    form.addEventListener('reset',()=>{clearTimeout(timer);byId('focus-history').replaceChildren();setTimeout(load,0);});
    byId('focus-auto').addEventListener('change',schedule);
    byId('focus-interval').addEventListener('change',schedule);
    document.addEventListener('visibilitychange',schedule);
    window.addEventListener('pagehide',()=>{stopped=true;if(expanded) setExpanded(false);clearTimeout(timer);if(previewController) previewController.abort();});
    window.addEventListener('pageshow',event=>{if(event.persisted){stopped=false;Array.from(form.elements).forEach(element=>element.disabled=false);schedule();}});
    const figure=byId('focus-figure'), expandButton=byId('focus-fullscreen'), exitButton=byId('focus-exit-fullscreen');
    let expanded=false, previousOverflow='';
    function setExpanded(value) {
        if(expanded===value) return;
        expanded=value;
        figure.classList.toggle('is-expanded',value);
        exitButton.hidden=!value;
        expandButton.setAttribute('aria-expanded',String(value));
        if(value) {previousOverflow=document.body.style.overflow;document.body.style.overflow='hidden';exitButton.focus();}
        else {document.body.style.overflow=previousOverflow;expandButton.focus();}
    }
    function closePreview() {
        setExpanded(false);
        if(document.fullscreenElement===figure && document.exitFullscreen) {
            Promise.resolve(document.exitFullscreen()).catch(()=>{message.textContent='Use your browser fullscreen control to finish exiting.';});
        }
    }
    expandButton.addEventListener('click',()=>{
        setExpanded(true);
        // The in-window preview is usable even if the browser ignores the native request.
        if(figure.requestFullscreen) {
            try {Promise.resolve(figure.requestFullscreen()).then(()=>{
                if(!expanded && document.fullscreenElement===figure) closePreview();
            }).catch(()=>{});} catch (_) { /* Keep the in-window preview available. */ }
        }
    });
    exitButton.addEventListener('click',closePreview);
    document.addEventListener('keydown',event=>{if(!expanded) return;if(event.key==='Escape'){event.preventDefault();closePreview();}else if(event.key==='Tab'){event.preventDefault();exitButton.focus();}});
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
