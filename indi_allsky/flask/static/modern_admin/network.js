(() => {
    'use strict';
    const root=document.getElementById('network-tool'), result=document.getElementById('network-result');
    const field=id=>document.getElementById(id), value=id=>field(id).value;
    let busy=false, refreshRequired=false, scanInterface=null;
    const accessPoints=field('SSID_SELECT'), wifi=field('WIFI_DEVICES_SELECT');
    function clearScan(message) {
        scanInterface=null;accessPoints.replaceChildren(new Option(message,''));
    }
    if(wifi) wifi.addEventListener('change',()=>clearScan('Scan this interface to choose an access point'));
    root.querySelectorAll('[data-network-command]').forEach(button=>button.addEventListener('click',async()=>{
        if(busy || refreshRequired || button.disabled || button.closest('fieldset').disabled) return;
        const command=button.dataset.networkCommand, payload={COMMAND:command};
        let target;
        if(command==='scanap' || command==='connectap') {
            payload.INTERFACE=value('WIFI_DEVICES_SELECT');target=payload.INTERFACE;
            if(!target) {result.textContent='Choose a Wi-Fi interface.';return;}
            if(command==='connectap') {
                if(scanInterface!==target || !value('SSID_SELECT')) {result.textContent='Scan this interface and choose an access point first.';return;}
                Object.assign(payload,{AP_PATH:value('SSID_SELECT'),PSK:value('SSID_PSK'),PRIORITY:value('SSID_PRIORITY'),RETRIES:value('SSID_RETRIES')});
                target+=' / '+accessPoints.selectedOptions[0].textContent;
            }
        } else if(command==='createhotspot') {
            Object.assign(payload,{INTERFACE:value('HOTSPOT_DEVICES_SELECT'),SSID:value('HOTSPOT_SSID'),BAND:value('HOTSPOT_BAND'),PSK:value('HOTSPOT_PSK'),NOSECURITY:field('HOTSPOT_NOSECURITY').checked});
            if(!payload.INTERFACE || !payload.SSID) {result.textContent='Choose a Wi-Fi interface and enter a hotspot name.';return;}
            if(!payload.NOSECURITY && payload.PSK.length<8) {result.textContent='Enter a hotspot password with at least 8 characters.';return;}
            target=payload.INTERFACE+' / '+payload.SSID+(payload.NOSECURITY?' — OPEN, without a password':'');
        } else {
            payload.CONNECTION=value('CONNECTIONS_SELECT');
            if(!payload.CONNECTION) {result.textContent='Choose a saved connection.';return;}
            target=field('CONNECTIONS_SELECT').selectedOptions[0].textContent;
        }
        if(!window.confirm(button.textContent+': '+target+'? '+(command==='scanap'?'This enables the Wi-Fi radio if it is off.':'This may interrupt remote access. Keep local access available.'))) return;
        busy=true;
        const enabled=[...root.querySelectorAll('fieldset')].filter(control=>!control.disabled);
        enabled.forEach(control=>control.disabled=true);
        result.textContent='Request in progress. Network operations can take up to 30 seconds…';
        if(command==='scanap') clearScan('Scanning…');
        try {
            const response=await fetch(root.dataset.url,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json','X-CSRFToken':root.dataset.csrf},body:JSON.stringify(payload)});
            if(response.redirected) throw new Error('Session expired. Sign in again.');
            let data;try {data=await response.json();}catch(error){throw new Error('No valid result was received.');}
            if(!response.ok) throw new Error(data['failure-message'] || 'Network command failed.');
            if(command==='scanap') {
                const points=data.data;
                if(!Array.isArray(points)) throw new Error('Invalid access point results.');
                clearScan(points.length?'Choose an access point':'No access points found');
                points.forEach(point=>accessPoints.append(new Option(point.desc,point.path)));
                scanInterface=payload.INTERFACE;
                result.textContent=points.length+' access points found on '+scanInterface+'.';
            } else {
                refreshRequired=true;
                result.textContent=(data['success-message'] || 'Command accepted.')+' Refresh connections to verify the current state.';
            }
        } catch(error) {
            refreshRequired=true;
            result.textContent=error.message+' The network may have changed. Reconnect if necessary and refresh connections before another command.';
        } finally {
            field('SSID_PSK').value='';field('HOTSPOT_PSK').value='';
            busy=false;if(!refreshRequired) enabled.forEach(control=>control.disabled=false);
        }
    }));
})();
