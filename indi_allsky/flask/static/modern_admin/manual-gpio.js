(() => {
    'use strict';
    const root=document.getElementById('gpio-tool'), result=document.getElementById('gpio-result');
    let busy=false;
    root.querySelectorAll('[data-gpio-id]').forEach(button=>button.addEventListener('click',async()=>{
        if(busy || button.closest('fieldset').disabled) return;
        const state=Number(button.dataset.gpioState);
        if(!window.confirm('Set BCM pin '+button.dataset.gpioName+' '+(state?'On':'Off')+'? Check the connected device before confirming.')) return;
        busy=true;
        const enabled=[...root.querySelectorAll('fieldset')].filter(field=>!field.disabled);
        enabled.forEach(field=>field.disabled=true);
        result.textContent='Setting output…';
        try {
            const response=await fetch(root.dataset.url,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-CSRFToken':root.dataset.csrf},body:JSON.stringify({PIN_ID:Number(button.dataset.gpioId),NEW_PIN_STATE:state})});
            if(response.redirected) throw new Error('Session expired. Sign in again.');
            let data;
            try {data=await response.json();} catch(error) {throw new Error('The request could not be completed. Refresh the page.');}
            if(!response.ok) throw new Error(data['failure-message'] || 'GPIO request failed. Inspect the pin before retrying.');
            result.textContent='Command reported '+(data.pin_state?'On':'Off')+' for BCM '+data.pin_name+'. Refresh pin states to read the current output.';
        }catch(error){result.textContent=error.message;}
        finally {busy=false;enabled.forEach(field=>field.disabled=false);}
    }));
})();
