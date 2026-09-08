const fs=require('fs'),vm=require('vm'),assert=require('assert');
function fixture(command='enable'){
 const form={dataset:{unit:command==='poweroff'?'system':'indi.timer'},elements:{confirmed:{checked:false},command:{value:command}},fields:{disabled:false},querySelector(){return this.fields;},addEventListener(e,fn){this[e]=fn;}};
 const root={dataset:{camera:'2',url:'/ajax/system',csrf:'signed'},querySelectorAll(){return [form];}},result={textContent:''},calls=[];let resolve,reject;
 vm.runInNewContext(fs.readFileSync('indi_allsky/flask/static/modern_admin/system-units.js','utf8'),{document:{getElementById:id=>id==='system-units'?root:result},fetch:(url,options)=>{calls.push({url,options});return new Promise((r,j)=>{resolve=r;reject=j;});}});
 return {form,result,calls,submit:()=>form.submit({preventDefault(){}}),reply:value=>resolve(value),reject:()=>reject(Error('network'))};
}
(async()=>{
 let f=fixture();await f.submit();assert.equal(f.calls.length,0);
 f.form.elements.confirmed.checked=true;f.form.fields.disabled=true;await f.submit();assert.equal(f.calls.length,0);
 for(const command of ['enable','poweroff']) for(const kind of ['success','error','network','redirect','html']){
  f=fixture(command);f.form.elements.confirmed.checked=true;
  const pending=f.submit();await f.submit();assert.equal(f.calls.length,1);
  assert.equal(f.calls[0].options.headers['X-CSRFToken'],'signed');
  assert.deepEqual(JSON.parse(f.calls[0].options.body),{CAMERA_ID:2,SERVICE_HIDDEN:command==='poweroff'?'system':'indi.timer',COMMAND_HIDDEN:command});
  if(kind==='network')f.reject();else if(kind==='redirect')f.reply({redirected:true});else if(kind==='html')f.reply({json:async()=>{throw Error('html');}});else f.reply({ok:kind==='success',json:async()=>kind==='success'?{'success-message':'Job submitted'}:{form_global:['Unavailable']}});
  await pending;assert(f.form.fields.disabled);await f.submit();assert.equal(f.calls.length,1);
  assert(f.result.textContent.includes(kind==='success'?'accepted':kind==='error'?'Unavailable':kind==='redirect'?'Session expired':'could not be confirmed'));
 }
 console.log('System controls: confirmation, permissions, CSRF, scoped payload, duplicate suppression, failed/expired/lost responses: PASS');
})().catch(error=>{console.error(error);process.exitCode=1;});
