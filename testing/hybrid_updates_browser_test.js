const fs=require('fs'),vm=require('vm'),assert=require('assert');
function fixture(){
 const elements={'upgrade-tool':{dataset:{url:'/upgrade',csrf:'signed',token:'observed'}},'upgrade-fields':{disabled:false},'upgrade-result':{textContent:''},'upgrade-backup':{checked:false},'upgrade-maintenance':{checked:false},'upgrade-form':{addEventListener(event,fn){this[event]=fn;}}};
 const calls=[];let reply,reject;
 vm.runInNewContext(fs.readFileSync('indi_allsky/flask/static/modern_admin/updates.js','utf8'),{document:{getElementById:id=>elements[id]},fetch:(url,options)=>{calls.push({url,options});return new Promise((r,j)=>{reply=r;reject=j;});}});
 return {elements,calls,submit:()=>elements['upgrade-form'].submit({preventDefault(){}}),confirm:()=>{elements['upgrade-backup'].checked=true;elements['upgrade-maintenance'].checked=true;},reply:r=>reply(r),reject:()=>reject(new Error('disconnected'))};
}
async function run(){
 let f=fixture();await f.submit();assert.equal(f.calls.length,0);assert(f.elements['upgrade-result'].textContent.includes('Confirm both'));
 f.confirm();f.elements['upgrade-fields'].disabled=true;await f.submit();assert.equal(f.calls.length,0);
 for(const kind of ['accepted','failure','redirect','network','html']){
  f=fixture();f.confirm();const pending=f.submit();await f.submit();assert.equal(f.calls.length,1);
  assert.equal(f.calls[0].options.headers['X-CSRFToken'],'signed');
  assert.deepEqual(JSON.parse(f.calls[0].options.body),{backup_confirmed:true,maintenance_confirmed:true,observed_token:'observed'});
  if(kind==='network')f.reject();else if(kind==='redirect')f.reply({redirected:true});else if(kind==='html')f.reply({json:async()=>{throw Error('html');}});else f.reply({json:async()=>({message:kind==='accepted'?'Job submitted':'Provider unavailable'})});
  await pending;assert(f.elements['upgrade-fields'].disabled);assert(!f.elements['upgrade-backup'].checked);assert(!f.elements['upgrade-maintenance'].checked);
  if(kind==='redirect')assert(f.elements['upgrade-result'].textContent.includes('Sign in'));
  if(['network','html'].includes(kind))assert(f.elements['upgrade-result'].textContent.includes('may already be running'));
  f.confirm();await f.submit();assert.equal(f.calls.length,1);
 }
 console.log('Updates controller: confirmations, permissions, CSRF, duplicate suppression, accepted/failed/expired/lost responses and explicit refresh: PASS');
}
run().catch(error=>{console.error(error);process.exitCode=1;});
