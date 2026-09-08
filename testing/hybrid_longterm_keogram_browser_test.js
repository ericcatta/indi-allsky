const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync('indi_allsky/flask/static/modern_admin/longterm-keogram.js','utf8');
function fixture(fetch,badImage=false) {
 const fields=Object.fromEntries(Object.entries({CAMERA_ID:'2',END_SELECT:'today',DAYS_SELECT:'30',PIXELS_SELECT:'5',ALIGNMENT_SELECT:'60',OFFSET_SELECT:'0',csrf_token:'csrf'}).map(([k,value])=>[k,{value}]));
 fields.REVERSE={checked:true};fields.LABEL={checked:false};const fieldset={},events={},nodes={};
 for(const id of ['status','error','image','download','age','result','download-row','empty'])nodes['longterm-'+id]={hidden:false,src:'old-image',href:'old-download',textContent:''};
 const form={action:'/indi-allsky/js/longtermkeogram',elements:{namedItem:n=>fields[n]},querySelector:()=>fieldset,addEventListener:(n,f)=>events[n]=f,setAttribute(){},removeAttribute(){}};
 vm.runInNewContext(source,{document:{getElementById:id=>id==='longterm-form'?form:nodes[id]},fetch,Image:class {set src(v){badImage?this.onerror():this.onload();}}});
 return {nodes,fields,fieldset,submit:()=>events.submit({preventDefault(){}}),reset:()=>events.reset()};
}
(async()=>{
 let calls=0,resolve;
 const f=fixture(async(url,options)=>{calls++;assert.equal(url,'/indi-allsky/js/longtermkeogram');const p=JSON.parse(options.body);assert.equal(p.CAMERA_ID,'2');assert.equal(p.REVERSE,true);assert.equal(p.LABEL,false);assert.equal(options.headers['X-CSRFToken'],'csrf');return new Promise(r=>resolve=r);});
 const pending=f.submit();await f.submit();assert.equal(calls,1);assert.equal(f.fieldset.disabled,true);
 resolve({ok:true,json:async()=>({image_b64:['YWJj'],processing_time:0.3})});await pending;
 assert.equal(f.nodes['longterm-image'].src,'data:image/jpeg;base64,YWJj');assert.equal(f.nodes['longterm-download'].href,f.nodes['longterm-image'].src);assert.equal(f.nodes['longterm-empty'].hidden,true);assert.equal(f.fieldset.disabled,false);f.reset();assert.equal(f.nodes['longterm-status'].textContent,'');
 for(const response of [{redirected:true},{status:403},{ok:false,json:async()=>({DAYS_SELECT:['Invalid period']})},{ok:true,json:async()=>({'failure-message':'Cannot save'})},{ok:true,json:async()=>({image_b64:[]})}]){
  const e=fixture(async()=>response);await e.submit();assert.equal(e.fieldset.disabled,false);assert.equal(e.nodes['longterm-error'].hidden,false);assert.equal(e.nodes['longterm-image'].src,'old-image');assert.equal(e.nodes['longterm-download'].href,'old-download');
 }
 // Every editable option must reach the request unchanged, including offset
 // signs and the two independent checkboxes.
 const options={END_SELECT:'lastyear',DAYS_SELECT:'42',PIXELS_SELECT:'2',ALIGNMENT_SELECT:'120',OFFSET_SELECT:'-3600'};
 const changed=fixture(async(url,request)=>{
  const payload=JSON.parse(request.body);
  for(const [key,value] of Object.entries(options))assert.equal(payload[key],value);
  assert.equal(payload.REVERSE,false);assert.equal(payload.LABEL,true);
  return {ok:true,json:async()=>({image_b64:'YWJj'})};
 });
 for(const [key,value] of Object.entries(options))changed.fields[key].value=value;
 changed.fields.REVERSE.checked=false;changed.fields.LABEL.checked=true;
 await changed.submit();assert.equal(changed.nodes['longterm-image'].src,'data:image/jpeg;base64,YWJj');
 const broken=fixture(async()=>({ok:true,json:async()=>({image_b64:'YWJj'})}),true);await broken.submit();assert.equal(broken.nodes['longterm-image'].src,'old-image');assert.match(broken.nodes['longterm-error'].textContent,/could not be loaded/);
 const network=fixture(async()=>{throw new Error('Network unavailable');});await network.submit();assert.equal(network.fieldset.disabled,false);assert.equal(network.nodes['longterm-error'].hidden,false);
 console.log('Long-term keogram controls: scoped payload, CSRF, duplicate prevention, preview/download, reset and errors preserve prior result: PASS');
})().catch(e=>{console.error(e);process.exitCode=1;});
