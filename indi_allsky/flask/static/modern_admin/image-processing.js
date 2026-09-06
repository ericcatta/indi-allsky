(() => {
    const byId=id=>document.getElementById(id), form=byId('fits-processing-form');
    const status=byId('processing-status'), image=byId('processing-image'), download=byId('processing-download');
    const buttons=[byId('processing-run'),byId('processing-source'),byId('processing-reset')];
    let pending=false;
    function message(text) {status.textContent=text;}
    async function run(source) {
        if(pending || byId('processing-parameters').disabled) return;
        pending=true;buttons.forEach(button=>{button.disabled=true;});
        image.hidden=true;download.hidden=true;byId('processing-fullscreen').disabled=true;
        document.querySelectorAll('.processing-field-error').forEach(error=>{error.hidden=true;error.textContent='';});
        const payload={};
        form.querySelectorAll('input[name],select[name],textarea[name]').forEach(field=>{
            if(field.name==='csrf_token') return;
            payload[field.name]=field.type==='checkbox'?field.checked:field.value;
        });
        payload.DISABLE_PROCESSING=source;
        byId('processing-parameters').disabled=true;
        message(source?'Preparing source preview…':'Processing FITS…');
        try {
            const response=await fetch(form.action,{method:'POST',headers:{'Content-Type':'application/json','Accept':'application/json','X-CSRFToken':form.querySelector('[name="csrf_token"]').value},body:JSON.stringify(payload)});
            if(response.redirected) throw new Error('Your session expired. Sign in and retry.');
            let result;
            try {result=await response.json();} catch (_) {throw new Error('The server returned an unreadable response. Try again or check the system log.');}
            if(!response.ok) {
                byId('processing-search').value='';
                filterParameters();
                Object.entries(result).forEach(([key,errors])=>{
                    const target=byId(key+'-error');
                    if(target){target.hidden=false;target.textContent=Array.isArray(errors)?errors.join(' '):String(errors);target.closest('details').open=true;}
                });
                throw new Error(Array.isArray(result.form_global)?result.form_global.join(' '):'Processing failed. Check the parameters.');
            }
            if(!result.image_b64 || !['image/png','image/jpeg'].includes(result.mime_type)) throw new Error(result.message || 'The server returned no preview.');
            const url='data:'+result.mime_type+';base64,'+result.image_b64;
            image.src=url;image.hidden=false;
            download.href=url;download.download='camera-'+result.camera_id+'-'+payload.FRAME_TYPE+'-'+result.fits_id+(result.mime_type==='image/png'?'.png':'.jpg');download.hidden=false;
            byId('processing-fullscreen').disabled=!byId('processing-preview').requestFullscreen;
            message((source?'Source':'Processed')+' preview: '+result.width+' × '+result.height+' pixels in '+result.processing_elapsed_s+' s.'+(result.message?' '+result.message:''));
        } catch(error) {message(error.message);}
        finally {byId('processing-parameters').disabled=false;pending=false;buttons.forEach(button=>{button.disabled=false;});}
    }
    form.addEventListener('submit',event=>{event.preventDefault();run(false);});
    byId('processing-source').addEventListener('click',()=>run(true));
    form.addEventListener('reset',()=>{byId('processing-search').value='';filterParameters();document.querySelectorAll('.processing-field-error').forEach(error=>{error.hidden=true;error.textContent='';});image.hidden=true;download.hidden=true;byId('processing-fullscreen').disabled=true;message('Parameters reset. Generate a new preview.');});
    form.addEventListener('change',()=>{if(!pending&&!image.hidden)message('Parameters changed. Generate a new preview to update the image.');});
    function filterParameters() {
        const query=byId('processing-search').value.trim().toLowerCase();
        document.querySelectorAll('.processing-group').forEach(group=>{
            let count=0;
            group.querySelectorAll('[data-processing-row]').forEach(row=>{row.hidden=!row.dataset.search.includes(query);if(!row.hidden)count++;});
            group.hidden=!count;if(query&&count)group.open=true;
        });
    }
    byId('processing-search').addEventListener('input',filterParameters);
    image.addEventListener('error',()=>{image.hidden=true;download.hidden=true;byId('processing-fullscreen').disabled=true;message('The generated preview could not be decoded by this browser.');});
    byId('processing-fullscreen').addEventListener('click',async()=>{
        try {await byId('processing-preview').requestFullscreen();} catch (_) {message('Fullscreen is not available in this browser.');}
    });
    byId('processing-exit').addEventListener('click',()=>document.exitFullscreen());
})();
