const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync('indi_allsky/flask/static/modern_admin/realtime-keogram.js','utf8');
async function run(){
 const nodes={};for(const id of ['realtime-tool','modern-admin-keogram-image','realtime-result','realtime-status','realtime-refresh','realtime-download'])nodes[id]={hidden:true,addEventListener(e,f){this[e]=f;}};
 nodes['realtime-tool'].dataset={url:'/images/ccd_test-camera-2/realtime_keogram.jpg',interval:'15000'};
 let requests=[],queue=[],revoked=[],seq=0,failDecode=false,events={},tick,aborts=0;
 const doc={hidden:false,getElementById:id=>nodes[id]};
 const url=URL;url.createObjectURL=()=>`blob:${++seq}`;url.revokeObjectURL=x=>revoked.push(x);
 const response=(status=200,type='image/jpeg',modified=new Date().toUTCString(),redirected=false)=>({status,ok:status===200,redirected,headers:{get:k=>k==='Content-Type'?type:modified},blob:async()=>({})});
 queue.push(response());
 const win={location:{href:'https://fixture/indi-allsky/modern-admin/observatory/realtime-keogram?camera_id=2',reload(){}},setInterval:f=>(tick=f,1),clearInterval(){tick=null;},setTimeout:()=>2,clearTimeout(){},addEventListener:(e,f)=>events[e]=f};
 vm.runInNewContext(source,{document:doc,window:win,URL:url,Date,Number,Math,Error,Image:class{async decode(){if(failDecode)throw Error('bad');}},AbortController:class{signal={};abort(){aborts++;}},fetch:async(u,options)=>{requests.push({u,options});const r=queue.shift();if(r instanceof Error)throw r;return await r;}});
 const settle=()=>new Promise(resolve=>setImmediate(resolve));await settle();
 assert(!nodes['realtime-result'].hidden && !nodes['realtime-download'].hidden);
 assert(requests[0].u.includes('ccd_test-camera-2') && requests[0].options.credentials==='same-origin');
 const old=nodes['modern-admin-keogram-image'].src;
 for(const r of [response(404),response(200,'text/html'),response(200,'image/jpeg','',true),new Error('offline')]){
  queue.push(r);await nodes['realtime-refresh'].click();assert.equal(nodes['modern-admin-keogram-image'].src,old);assert(!nodes['realtime-refresh'].disabled);
 }
 failDecode=true;queue.push(response());await nodes['realtime-refresh'].click();assert.equal(nodes['modern-admin-keogram-image'].src,old);assert(nodes['realtime-status'].textContent.includes('decoded'));failDecode=false;
 queue.push(response(200,'image/jpeg','Mon, 01 Jan 2024 00:00:00 GMT'));await nodes['realtime-refresh'].click();assert(nodes['realtime-status'].textContent.includes('stale'));assert(revoked.includes(old));
 const count=requests.length;doc.hidden=true;await tick();assert.equal(requests.length,count);doc.hidden=false;
 let finish;queue.push(new Promise(r=>finish=r));const pending=nodes['realtime-refresh'].click();await nodes['realtime-refresh'].click();assert.equal(requests.length,count+1);
 events.pagehide();finish(response());await pending;assert(aborts && !tick);
 console.log('Realtime preview: camera URL, success, stale/missing/session/network/decode errors, retained image, hidden tab, duplicate prevention and teardown: PASS');
}
run().catch(e=>{console.error(e);process.exitCode=1;});
