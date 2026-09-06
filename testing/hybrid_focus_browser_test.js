const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync('indi_allsky/flask/static/modern_admin/focus.js','utf8');
function element(value='') {return {value,disabled:false,hidden:true,checked:false,textContent:'',children:[],dataset:{},listeners:{},addEventListener(k,f){this.listeners[k]=f;},reportValidity(){return true;},removeAttribute(k){delete this[k];},decode:async()=>{},append(node){this.children.push(node);},prepend(node){this.children.unshift(node);},replaceChildren(){this.children=[];}};}
async function run(){
 const ids={};['focus-tool','focus-preview-form','focus-image','focus-message','focus-auto','focus-interval','focus-zoom','focus-x','focus-y','focus-history','focus-score','focus-fullscreen','focus-figure','focus-exit-fullscreen','focus-movement','focus-degrees','focus-move-message'].forEach(id=>ids[id]=element());
 ids['focus-tool'].dataset={camera:'2',previewUrl:'/preview',moveUrl:'/move',csrf:'token'};
 ids['focus-zoom'].value='5';ids['focus-x'].value='12';ids['focus-y'].value='-15';ids['focus-interval'].value='5';ids['focus-degrees'].value='24';
 const form=ids['focus-preview-form'];form.elements=[ids['focus-zoom'],ids['focus-x'],ids['focus-y'],ids['focus-auto']];
 const move=element();move.dataset.focusDirection='cw';let requests=[],resolveRequest;
 const document={hidden:false,getElementById:id=>ids[id],querySelectorAll:()=>[move],createElement:()=>element(),addEventListener(){}};
 const context={document,location:{origin:'http://localhost'},URL,console,setTimeout:()=>1,clearTimeout(){},window:{addEventListener(){},confirm:()=>true},fetch:(url,options)=>{requests.push({url:String(url),options});return new Promise(resolve=>resolveRequest=resolve);}};
 vm.runInNewContext(source,context);
 const submit=()=>form.listeners.submit({preventDefault(){}});
 submit();submit();assert.equal(requests.length,1);assert(ids['focus-zoom'].disabled);
 assert(requests[0].url.includes('camera_id=2') && requests[0].url.includes('y_offset=-15'));
 resolveRequest({ok:true,json:async()=>({image_b64:'jpeg',source:'Saved frame',camera_id:2,timestamp:'now',age_seconds:7,blur_score:12.5,star_count:3})});
 await new Promise(setImmediate);
 assert.equal(ids['focus-image'].hidden,false);assert.equal(ids['focus-history'].children.length,1);assert.equal(ids['focus-zoom'].disabled,false);
 assert(ids['focus-message'].textContent.includes('Camera 2'));
 submit();resolveRequest({ok:false,json:async()=>({error:'Source unavailable'})});await new Promise(setImmediate);
 assert(ids['focus-image'].hidden);assert.equal(ids['focus-score'].textContent,'');assert.equal(ids['focus-message'].textContent,'Source unavailable');
 submit();resolveRequest({redirected:true});await new Promise(setImmediate);assert(ids['focus-message'].textContent.includes('Sign in'));
 ids['focus-movement'].disabled=true;await move.listeners.click();assert.equal(requests.length,3);
 ids['focus-movement'].disabled=false;const pending=move.listeners.click();move.listeners.click();assert.equal(requests.length,4);
 assert.deepEqual(JSON.parse(requests[3].options.body),{DIRECTION:'cw',STEP_DEGREES:24});assert.equal(requests[3].options.headers['X-CSRFToken'],'token');
 resolveRequest({ok:false,json:async()=>({focuser_error:['Movement completed. Release failed; inspect before retrying.']})});await pending;
 assert(ids['focus-move-message'].textContent.includes('Movement completed.'));assert.equal(ids['focus-movement'].disabled,false);
 console.log('Native Focus browser controller: target camera, duplicate prevention, decode, errors, expired session, permissions and movement feedback: PASS');
}
run().catch(error=>{console.error(error);process.exitCode=1;});
