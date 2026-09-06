const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const code=fs.readFileSync('indi_allsky/flask/static/modern_admin/mini-generation.js','utf8');
function fixture(fetch,ordinary=false) {
    function node(value='') {return {value,disabled:false,hidden:false,checked:false,listeners:{},addEventListener(name,fn){this.listeners[name]=fn},focus(){}};}
    const fields=Object.fromEntries(Object.entries({CAMERA_ID:'2',IMAGE_ID:'2',PRE_SECONDS_SELECT:'240',POST_SECONDS_SELECT:'120',FRAMERATE_SELECT:'10',NOTE:'',csrf_token:'token'}).map(([k,v])=>[k,node(v)]));
    const nodes=Object.fromEntries(['exit-fullscreen','preview-image','play','fullscreen','preview-container','preview-status','result','confirm','frame-status','refresh','task'].map(id=>[id,node()]));
    const controls=node(),submit={matches:()=>ordinary};let onSubmit;
    const form={elements:{namedItem:n=>fields[n]},dataset:{previewUrl:'/preview'},action:'/queue',querySelector:s=>s==='fieldset'?controls:submit,addEventListener:(event,fn)=>onSubmit=fn};
    vm.runInNewContext(code,{URLSearchParams,AbortController,fetch,clearTimeout,setTimeout,window:{addEventListener(){}},document:{getElementById:id=>id==='hybrid-mini-form'?form:nodes[id.replace('mini-','')],addEventListener(){}}});
    return {fields,nodes,controls,submit:()=>onSubmit({preventDefault(){}})};
}
(async()=>{
    const preview={ok:true,json:async()=>({images:[],count:0,seconds:0,start:'start',end:'end'})};
    let calls=0,resolve;
    const f=fixture(async(url,options)=>{
        if(url.startsWith('/preview'))return preview;
        calls++; assert.equal(JSON.parse(options.body).CAMERA_ID,'2');assert.equal(options.headers['X-CSRFToken'],'token');
        return new Promise(done=>resolve=done);
    });
    await f.submit();assert.equal(calls,0);assert.match(f.nodes.result.textContent,/Confirm/);
    f.nodes.confirm.checked=true;const pending=f.submit();await f.submit();assert.equal(calls,1);assert.equal(f.controls.disabled,true);
    resolve({ok:true,status:200,json:async()=>({'success-message':'Job submitted',task_url:'/tasks/1'})});await pending;
    assert.equal(f.controls.disabled,false);assert.equal(f.nodes.confirm.checked,false);assert.equal(f.nodes.task.href,'/tasks/1');assert.equal(f.nodes.task.hidden,false);
    const ordinary=fixture(async()=>preview,true);ordinary.nodes.confirm.checked=true;await ordinary.submit();assert.notEqual(ordinary.nodes.result.textContent,'Submitting…');
    for(const response of [{redirected:true},{status:500},{status:400,ok:false,json:async()=>({'failure-message':'Invalid interval'})}]){
        const error=fixture(async url=>url.startsWith('/preview')?preview:response);error.nodes.confirm.checked=true;await error.submit();
        assert.equal(error.controls.disabled,false);assert.equal(error.nodes.confirm.checked,false);assert.notEqual(error.nodes.result.textContent,'Submitting…');
    }
    console.log('Hybrid mini controls: role, confirmation, duplicate submissions, failure recovery and task result: PASS');
})().catch(error=>{console.error(error);process.exitCode=1});
