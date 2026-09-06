const fs=require('fs'),vm=require('vm'),assert=require('assert');
function fixture(){
 const controls={},fields=[{disabled:false},{disabled:false},{disabled:false}],result={textContent:''};
 for(const id of ['CONNECTIONS_SELECT','WIFI_DEVICES_SELECT','SSID_SELECT','SSID_PSK','SSID_PRIORITY','SSID_RETRIES','HOTSPOT_DEVICES_SELECT','HOTSPOT_SSID','HOTSPOT_BAND','HOTSPOT_PSK','HOTSPOT_NOSECURITY']) controls[id]={value:'',checked:false,selectedOptions:[{textContent:'Test target'}],children:[],replaceChildren(option){this.children=[option];this.value='';},append(option){this.children.push(option);},addEventListener(event,fn){this[event]=fn;}};
 Object.assign(controls.CONNECTIONS_SELECT,{value:'test-uuid'});controls.WIFI_DEVICES_SELECT.value='wlan-test';
 controls.SSID_PRIORITY.value='0';controls.SSID_RETRIES.value='4';
 controls.HOTSPOT_DEVICES_SELECT.value='wlan-test';controls.HOTSPOT_SSID.value='Test';controls.HOTSPOT_BAND.value='bg';controls.HOTSPOT_PSK.value='test-password';
 const buttons={};for(const command of ['activate','deactivate','delete','autostart','noautostart','incpriority','decpriority','powersaveenable','powersavedisable','scanap','connectap','createhotspot']) buttons[command]={dataset:{networkCommand:command},textContent:command,closest:()=>fields[0],addEventListener(event,fn){this[event]=fn;}};
 const root={dataset:{url:'/network',csrf:'signed'},querySelectorAll:selector=>selector==='fieldset'?fields:Object.values(buttons)};
 const calls=[];let resolve,confirmation=true;
 vm.runInNewContext(fs.readFileSync('indi_allsky/flask/static/modern_admin/network.js','utf8'),{document:{getElementById:id=>id==='network-tool'?root:id==='network-result'?result:controls[id]},Option:function(text,value){this.textContent=text;this.value=value;},window:{confirm:()=>confirmation},fetch:(url,options)=>{calls.push({url,options});return new Promise(r=>resolve=r);}});
 return {controls,fields,buttons,result,calls,cancel:()=>confirmation=false,reply:data=>resolve(data)};
}
async function run(){
 let f=fixture();f.cancel();await f.buttons.delete.click();assert.equal(f.calls.length,0);
 for(const command of ['activate','deactivate','delete','autostart','noautostart','incpriority','decpriority','powersaveenable','powersavedisable']){
  f=fixture();const pending=f.buttons[command].click();f.buttons[command].click();assert.equal(f.calls.length,1);assert(f.fields.every(x=>x.disabled));
  assert.deepEqual(JSON.parse(f.calls[0].options.body),{COMMAND:command,CONNECTION:'test-uuid'});assert.equal(f.calls[0].options.headers['X-CSRFToken'],'signed');
  f.reply({ok:true,json:async()=>({'success-message':'Done'})});await pending;await f.buttons[command].click();assert.equal(f.calls.length,1);assert(f.result.textContent.includes('Refresh connections'));
 }
 f=fixture();await f.buttons.connectap.click();assert.equal(f.calls.length,0);
 const scan=f.buttons.scanap.click();f.reply({ok:true,json:async()=>({data:[{desc:'<script>untrusted SSID</script>',path:'/org/freedesktop/NetworkManager/AccessPoint/1'}]})});await scan;
 assert.equal(f.controls.SSID_SELECT.children[1].textContent,'<script>untrusted SSID</script>');assert(!f.fields[0].disabled);
 f.controls.SSID_SELECT.value='/org/freedesktop/NetworkManager/AccessPoint/1';f.controls.SSID_PSK.value='secret';
 const connect=f.buttons.connectap.click();assert.equal(JSON.parse(f.calls[1].options.body).PSK,'secret');f.reply({ok:true,json:async()=>({'success-message':'Connected'})});await connect;assert.equal(f.controls.SSID_PSK.value,'');
 f=fixture();const empty=f.buttons.scanap.click();f.reply({ok:true,json:async()=>({data:[]})});await empty;assert(f.result.textContent.includes('0 access points'));f.controls.WIFI_DEVICES_SELECT.change();await f.buttons.connectap.click();assert.equal(f.calls.length,1);
 for(const open of [true,false]) {f=fixture();f.controls.HOTSPOT_NOSECURITY.checked=open;const pending=f.buttons.createhotspot.click();assert.strictEqual(JSON.parse(f.calls[0].options.body).NOSECURITY,open);f.reply({redirected:true});await pending;assert(f.result.textContent.includes('Session expired'));assert.equal(f.controls.HOTSPOT_PSK.value,'');}
 f=fixture();const failure=f.buttons.activate.click();f.reply({ok:false,json:async()=>({'failure-message':'Provider failed'})});await failure;assert(f.result.textContent.includes('Provider failed'));await f.buttons.activate.click();assert.equal(f.calls.length,1);
 f=fixture();f.fields[0].disabled=true;await f.buttons.activate.click();assert.equal(f.calls.length,0);
 console.log('Network controller: all intents, scan results/empty state, target binding, security boolean, CSRF, pending/refresh guards, cancellation, permissions and errors: PASS');
}
run().catch(error=>{console.error(error);process.exitCode=1;});
