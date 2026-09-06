/* Exercise preview request state, recovery and parameter visibility without a server. */
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const code=fs.readFileSync('indi_allsky/flask/static/modern_admin/image-processing.js','utf8');
function fixture() {
 const nodes={};
 for(const id of ['fits-processing-form','processing-status','processing-image','processing-download','processing-run','processing-source','processing-reset','processing-fullscreen','processing-parameters','processing-search','processing-preview','processing-exit']) nodes[id]={hidden:false,disabled:false,value:'',events:{},addEventListener(e,f){this.events[e]=f;}};
 const row={dataset:{search:'image rotate'},hidden:false},group={hidden:false,open:false,querySelectorAll:()=>[row]},error={hidden:true,closest:()=>group};nodes['IMAGE_ROTATE-error']=error;
 const fields=[{name:'FRAME_TYPE',value:'light'},{name:'IMAGE_ROTATE',value:'invalid'},{name:'FLAG',type:'checkbox',checked:true}];
 nodes['fits-processing-form'].querySelectorAll=()=>fields;nodes['fits-processing-form'].querySelector=()=>({value:'csrf'});
 nodes['processing-preview'].requestFullscreen=async()=>{};
 const requests=[];let finish;
 vm.runInNewContext(code,{document:{getElementById:id=>nodes[id],querySelectorAll:s=>s==='.processing-group'?[group]:[error]},fetch:(url,options)=>{requests.push(JSON.parse(options.body));return new Promise(resolve=>{finish=resolve;});}});
 return {nodes,row,group,error,requests,finish:(value)=>finish(value),async settle(){await new Promise(resolve=>setImmediate(resolve));}};
}
(async()=>{
 const f=fixture(),n=f.nodes;
 n['processing-source'].events.click();n['processing-source'].events.click();assert.equal(f.requests.length,1);assert.equal(f.requests[0].DISABLE_PROCESSING,true);assert.equal(n['processing-parameters'].disabled,true);
 f.finish({ok:true,json:async()=>({image_b64:'AA==',mime_type:'image/png',camera_id:2,fits_id:7,width:64,height:48,processing_elapsed_s:0.1})});await f.settle();
 assert.equal(n['processing-download'].download,'camera-2-light-7.png');assert.equal(n['processing-parameters'].disabled,false);
 n['processing-search'].value='nothing';n['processing-search'].events.input();assert(f.row.hidden&&f.group.hidden);
 n['fits-processing-form'].events.reset();assert.equal(f.row.hidden,false);assert(n['processing-image'].hidden);
 n['processing-search'].value='nothing';n['processing-search'].events.input();n['processing-source'].events.click();
 f.finish({ok:false,json:async()=>({IMAGE_ROTATE:['Bad rotation'],form_global:['Fix parameters']})});await f.settle();
 assert.equal(f.group.hidden,false);assert.equal(f.group.open,true);assert.equal(f.error.textContent,'Bad rotation');assert.equal(n['processing-status'].textContent,'Fix parameters');
 n['processing-source'].events.click();f.finish({redirected:true});await f.settle();assert.match(n['processing-status'].textContent,/session expired/);assert.equal(n['processing-source'].disabled,false);
 n['processing-source'].events.click();f.finish({ok:true,json:async()=>{throw Error('html');}});await f.settle();assert.match(n['processing-status'].textContent,/unreadable/);assert(n['processing-download'].hidden);
 console.log('FITS controller: duplicate prevention, output identity, search/reset, visible validation and failed-session recovery: PASS');
})().catch(error=>{console.error(error);process.exitCode=1;});
