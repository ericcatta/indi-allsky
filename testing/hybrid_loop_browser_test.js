/* Deterministic execution of the real Loop script; not a native-browser claim. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const template = fs.readFileSync(path.join(__dirname, '../indi_allsky/flask/templates/modern_admin/loop.html'), 'utf8');
const source = template.slice(template.indexOf('let modernAdminLoopState'), template.lastIndexOf('</script>'))
    .replace(/{{[\s\S]*?}}/g, value => value.includes('images_folder') ? '/images/__modern_admin_path__' : '/js/loop');
function fixture() {
    const requests=[], preloads=[], timers=new Map(), intervals=[], nodes={}, controls={};
    let timerId=0;
    for(const id of ['HISTORY_SELECT','FRAMEDELAY_SELECT','ROCK_CHECKBOX']) controls[id]={value:id==='HISTORY_SELECT'?'900':'100',checked:false,addEventListener(event,fn){this[event]=fn;}};
    for(const id of ['one','two']){
        nodes[`[data-loop-image="${id}"]`]={hidden:true,src:'',removeAttribute(){this.src='';}};
        nodes[`[data-loop-message="${id}"]`]={textContent:''};
    }
    const context={URLSearchParams,modernAdminLoopCameras:[{loop_id:'one',camera_id:1},{loop_id:'two',camera_id:2}],timestamp:0,refreshInterval:16000,
        document:{getElementById:id=>controls[id],querySelector:s=>nodes[s]},
        window:{setTimeout(fn,delay){const id=++timerId;timers.set(id,{fn,delay});return id;},clearTimeout:id=>timers.delete(id),setInterval:fn=>intervals.push(fn)},
        Image:class{constructor(){preloads.push(this);}},
        fetch:url=>new Promise((resolve,reject)=>requests.push({url,resolve,reject}))};
    vm.runInNewContext(source,context);
    return {context,requests,preloads,timers,intervals,controls,nodes,
        image:id=>nodes[`[data-loop-image="${id}"]`], message:id=>nodes[`[data-loop-message="${id}"]`],
        reply:async(index,images,ok=true)=>{requests[index].resolve({ok,json:async()=>({image_list:images,message:''})});await flush();}};
}
async function flush(){for(let i=0;i<12;i++)await Promise.resolve();}
const frames=[{url:'images/new.jpg'},{url:'images/middle.jpg'},{url:'images/old.jpg'}];
async function run(){
    const f=fixture();
    assert.equal(f.requests.length,2);
    assert.equal(new URL(f.requests[0].url,'http://test').searchParams.get('camera_id'),'1');
    assert.equal(new URL(f.requests[1].url,'http://test').searchParams.get('camera_id'),'2');
    // History changes immediately request both cameras and cannot be overwritten by old responses.
    assert.equal(typeof f.controls.HISTORY_SELECT.change,'function');
    f.controls.HISTORY_SELECT.value='14400';f.controls.HISTORY_SELECT.change();
    assert.equal(f.requests.length,4);
    assert.equal(new URL(f.requests[2].url,'http://test').searchParams.get('limit_s'),'14400');
    await f.reply(2,frames);await f.reply(0,[{url:'obsolete.jpg'}]);
    assert.equal(f.preloads.length,1);assert.equal(f.preloads[0].src,'/images/old.jpg');
    f.preloads[0].onload();assert.equal(f.image('one').hidden,false);assert.equal(f.timers.size,1);
    // Slow images do not get superseded by a timer starting another frame.
    let [id,timer]=[...f.timers][0];f.timers.delete(id);timer.fn();
    assert.equal(f.preloads[1].src,'/images/middle.jpg');assert.equal(f.timers.size,0);
    f.preloads[1].onload();assert.equal(f.image('one').src,'/images/middle.jpg');
    // Speed applies to the next frame without overlapping playback timers.
    f.controls.FRAMEDELAY_SELECT.value='200';f.controls.FRAMEDELAY_SELECT.change();
    assert.equal(f.timers.size,0);f.preloads.at(-1).onload();
    assert.equal([...f.timers.values()][0].delay,200);assert.equal(f.timers.size,1);
    // Rock follows oldest -> newest -> oldest without repeating endpoints.
    f.controls.ROCK_CHECKBOX.checked=true;f.controls.ROCK_CHECKBOX.change();
    const sequence=[];
    for(let i=0;i<5;i++){
        const preload=f.preloads.at(-1);sequence.push(preload.src);preload.onload();
        const [key,t]=[...f.timers][0];f.timers.delete(key);t.fn();
    }
    assert.deepEqual(sequence,['/images/old.jpg','/images/middle.jpg','/images/new.jpg','/images/middle.jpg','/images/old.jpg']);
    // Empty/new history clears a displayed frame and ignores any late image load.
    const obsolete=f.preloads.at(-1);f.controls.HISTORY_SELECT.value='900';f.controls.HISTORY_SELECT.change();
    assert.equal(f.image('one').hidden,true);assert.equal(f.image('one').src,'');
    await f.reply(4,[]);obsolete.onload();
    assert.equal(f.image('one').hidden,true);assert.match(f.message('one').textContent,/No frames/);assert.equal(f.timers.size,0);
    // A failed camera does not stop the other camera, and HTTP errors aren't accepted as data.
    await f.reply(5,frames,false);assert.match(f.message('two').textContent,/Error loading/);
    f.intervals[0]();f.intervals[0]();assert.equal(f.requests.length,7,'No duplicate refresh while pending');
    await f.reply(6,frames);const recovery=f.preloads.at(-1);recovery.onerror();
    assert.equal(f.image('one').hidden,true);assert.match(f.message('one').textContent,/Unable to load/);
    const [key,next]=[...f.timers][0];f.timers.delete(key);next.fn();f.preloads.at(-1).onload();
    assert.equal(f.image('one').hidden,false);assert.equal(f.message('one').textContent,'');
    assert.equal(f.image('two').hidden,true);
    // Network rejection and invalid response shape are reported, not left as silent stale frames.
    f.intervals[0]();f.requests.at(-1).reject(new Error('offline'));await flush();assert.equal(f.image('one').hidden,true);
    f.intervals[0]();await f.reply(f.requests.length-1,null);assert.match(f.message('one').textContent,/Error loading/);
    console.log('Loop controls: history, speed, bounce, camera isolation, stale responses, image errors and recovery PASS');
}
run().catch(error=>{console.error(error);process.exitCode=1;});
