const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const source=fs.readFileSync('indi_allsky/flask/static/modern_admin/generation.js','utf8');
function fixture(fetch,disabled=false) {
    const fields=Object.fromEntries(Object.entries({CAMERA_ID:'2',ACTION_SELECT:'generate_video',DAY_SELECT:'2026-09-06_night',csrf_token:'csrf'}).map(([k,value])=>[k,{value,focus(){},addEventListener(name,fn){this.change=fn;}}]));
    fields.CONFIRM1={checked:false,focus(){}};
    const fieldset={disabled},button={},message={},description={};let submit;
    const form={action:'/indi-allsky/ajax/generate',querySelector:s=>s==='fieldset'?fieldset:button,elements:{namedItem:n=>fields[n]},addEventListener:(_,fn)=>submit=fn};
    vm.runInNewContext(source,{document:{getElementById:id=>({'hybrid-generation-form':form,'generation-result':message,'generation-action-description':description})[id]},fetch});
    return {fields,fieldset,message,button,description,submit:()=>submit({preventDefault(){}})};
}
(async()=>{
    let calls=0,resolve;
    const f=fixture(async(url,options)=>{calls++;assert.equal(url,'/indi-allsky/ajax/generate');assert.equal(JSON.parse(options.body).CAMERA_ID,'2');assert.equal(options.headers['X-CSRFToken'],'csrf');return new Promise(done=>resolve=done);});
    await f.submit();assert.equal(calls,0);assert.match(f.message.textContent,/Confirm/);
    f.fields.CONFIRM1.checked=true;const pending=f.submit();await f.submit();assert.equal(calls,1);assert.equal(f.fieldset.disabled,true);
    resolve({ok:true,json:async()=>({'success-message':'Job submitted'})});await pending;
    assert.equal(f.fieldset.disabled,false);assert.equal(f.fields.CONFIRM1.checked,false);assert.equal(f.fields.ACTION_SELECT.value,'none');assert.match(f.message.textContent,/Job submitted/);
    const ordinary=fixture(()=>assert.fail('Ordinary user must not submit'),true);ordinary.fields.CONFIRM1.checked=true;await ordinary.submit();
    for(const response of [{redirected:true},{ok:false,status:500,json:async()=>({})},{ok:false,status:400,json:async()=>({DAY_SELECT:['Invalid date']})}]) {
        const error=fixture(async()=>response);error.fields.CONFIRM1.checked=true;await error.submit();assert.equal(error.fieldset.disabled,false);assert.notEqual(error.message.textContent,'Submitting…');assert.equal(error.fields.CONFIRM1.checked,false);
    }
    const scope=fixture(()=>{});scope.fields.CONFIRM1.checked=true;scope.fields.DAY_SELECT.change();assert.equal(scope.fields.CONFIRM1.checked,false);
    scope.fields.ACTION_SELECT.value='delete_images';scope.fields.ACTION_SELECT.change();assert.match(scope.description.textContent,/Permanent deletion/);
    scope.fields.ACTION_SELECT.value='upload_endofnight';scope.fields.ACTION_SELECT.change();assert.match(scope.description.textContent,/historical date is not used/);
    console.log('Hybrid generation confirmation, role gate, duplicate submission, failure and scope changes: PASS');
})().catch(e=>{console.error(e);process.exitCode=1;});
