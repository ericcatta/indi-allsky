const fs=require('fs'),vm=require('vm'),assert=require('assert');
const unit=command=>command==='hup'?'capture.service':command==='enable'?'indi.timer':'system';
function fixture(command='enable'){
 const form={dataset:{unit:unit(command),retentionToken:'a'.repeat(64)},elements:{confirmed:{checked:false},command:{value:command}},fields:{disabled:false},querySelector(){return this.fields;},addEventListener(e,fn){this[e]=fn;}};
 const root={dataset:{camera:'2',url:'/ajax/system',csrf:'signed',taskUrl:'/tasks/0'},querySelectorAll(){return [form];}},result={textContent:''},link={hidden:true},calls=[];let resolve,reject;
 vm.runInNewContext(fs.readFileSync('indi_allsky/flask/static/modern_admin/system-units.js','utf8'),{document:{getElementById:id=>id==='system-units'?root:id==='system-units-task'?link:result},fetch:(url,options)=>{calls.push({url,options});return new Promise((r,j)=>{resolve=r;reject=j;});}});
 return {form,result,link,calls,submit:()=>form.submit({preventDefault(){}}),reply:value=>resolve(value),reject:()=>reject(Error('network'))};
}
(async()=>{
 let f=fixture();await f.submit();assert.equal(f.calls.length,0);
 f.form.elements.confirmed.checked=true;f.form.fields.disabled=true;await f.submit();assert.equal(f.calls.length,0);
 for(const command of ['enable','poweroff','validate_db','hup','expire_data','backup_db']) for(const kind of ['success','error','network','redirect','html']){
  f=fixture(command);f.form.elements.confirmed.checked=true;
  const pending=f.submit();await f.submit();assert.equal(f.calls.length,1);
  assert.equal(f.calls[0].options.headers['X-CSRFToken'],'signed');
  assert.deepEqual(JSON.parse(f.calls[0].options.body),{CAMERA_ID:2,SERVICE_HIDDEN:unit(command),COMMAND_HIDDEN:command,...(command==='expire_data'?{RETENTION_TOKEN:'a'.repeat(64)}:{})});
  const queued=['hup','expire_data','backup_db'].includes(command);
  if(kind==='network')f.reject();else if(kind==='redirect')f.reply({redirected:true});else if(kind==='html')f.reply({json:async()=>{throw Error('html');}});else f.reply({ok:kind==='success',headers:{get:name=>name==='X-Hybrid-Task-Id'&&queued?'42':null},json:async()=>kind==='success'?{'success-message':command==='validate_db'?'<p>Images: 2</p><p>Removed 1 missing image entries</p>':'Job submitted'}:{form_global:['Unavailable']}});
  await pending;assert(f.form.fields.disabled);await f.submit();assert.equal(f.calls.length,1);
  assert(f.result.textContent.includes(kind==='success'?(queued?'Task submitted':command==='validate_db'?'Removed 1 missing image entries':'accepted'):kind==='error'?'Unavailable':kind==='redirect'?'Session expired':'could not be confirmed'));
  if(queued&&kind==='success'){assert.equal(f.link.href,'/tasks/42');assert(!f.link.hidden);}else assert(f.link.hidden);
 }
 for(const id of ['../escape','https://example.invalid','0']){
  f=fixture('expire_data');f.form.elements.confirmed.checked=true;const pending=f.submit();
  f.reply({ok:true,headers:{get:()=>id},json:async()=>({'success-message':'Submitted'})});await pending;assert(f.link.hidden);
 }
 console.log('System controls: confirmations, roles, CSRF, payloads, duplicate suppression, failure/expiry/lost responses, safe task receipts and links: PASS');
})().catch(error=>{console.error(error);process.exitCode=1;});
