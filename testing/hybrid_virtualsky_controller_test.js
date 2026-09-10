/* Controller effects are simulated; this does not prove native canvas rendering. */
const assert = require('node:assert/strict');
const fs = require('node:fs'), vm = require('node:vm');
const source = fs.readFileSync('indi_allsky/flask/static/modern_admin/virtualsky.js', 'utf8');
const flush = () => new Promise(resolve => setImmediate(resolve));
function deferred() { let resolve; const promise = new Promise(r => { resolve = r; }); return {promise, resolve}; }
function fixture() {
    const ids = ['virtualsky-config','virtualsky-controls','modern-admin-virtualsky-image',
        'virtualsky-wrapper','virtualsky-clip','hybrid-starmap','modern-admin-virtualsky-message',
        'virtualsky-refresh','virtualsky-download','virtualsky-fullscreen','virtualsky-exit-fullscreen'];
    const elements = Object.fromEntries(ids.map(id => [id, {style:{}, events:{}, disabled:false,
        addEventListener(name, fn) { this.events[name] = fn; }, focus() { this.focused=true; }}]));
    const byId = id => elements[id], form = byId('virtualsky-controls'), image = byId('modern-admin-virtualsky-image');
    const defaults = {AZIMUTH_ANGLE:0,LATITUDE_OFFSET:0,LONGITUDE_OFFSET:0,IMAGE_CIRCLE_DIAMETER:600,
        OFFSET_X:0,OFFSET_Y:0,MAGNITUDE:6,CONSTELLATIONS:true,CONSTELLATIONLABELS:false,
        SHOWSTARS:true,SHOWSTARLABELS:false,SHOWPLANETS:true,SHOWPLANETLABELS:false};
    form.elements = Object.entries(defaults).map(([name,value]) => ({name, type:typeof value==='boolean'?'checkbox':'number', value:String(value), checked:value}));
    const config = {cameraId:2,latitude:46,longitude:8,timeOffset:0,timestamp:0,refreshInterval:5000,
        loopUrl:'/loop',imagesBase:'/images/'};
    byId('virtualsky-config').textContent = JSON.stringify(config);
    Object.assign(image, {clientWidth:320,clientHeight:240,offsetLeft:0,offsetTop:0,decode:async () => {}});
    const state = {requests:[], created:[], links:[], timers:new Map(), events:{}, engine:null, captures:0};
    let nextTimer=0;
    const doc = {getElementById:byId, fullscreenElement:null,
        createElement() { const link={click() { this.clicked=true; }}; state.links.push(link); return link; },
        async exitFullscreen() { doc.fullscreenElement=null; }};
    byId('virtualsky-wrapper').requestFullscreen = async () => { doc.fullscreenElement=byId('virtualsky-wrapper'); };
    const win = {location:{href:'http://fixture.test/sky',origin:'http://fixture.test'},
        addEventListener(name,fn) { state.events[name]=fn; },
        S:{virtualsky(options) {
            state.created.push(options);
            state.engine={...options,constellation:{lines:options.constellations,labels:options.constellationlabels},
                setLatitude(v) { this.latitude=v; },setLongitude(v) { this.longitude=v; },
                changeMagnitude(v) { this.magnitude+=v; },setClock(v) { this.clock=v; },calendarUpdate() {},
                resize(w,h) { this.width=w; this.height=h; },draw() {}};
            return state.engine;
        }},
        async html2canvas() { state.captures++; return {toBlob(fn) { fn({type:'image/png'}); }}; }};
    class TestURL extends URL {}
    TestURL.createObjectURL=()=> 'blob:synthetic'; TestURL.revokeObjectURL=()=>{};
    vm.runInNewContext(source,{document:doc,window:win,URL:TestURL,URLSearchParams,AbortController,
        ResizeObserver:class { constructor(fn) { state.resize=fn; } observe() {} },
        setTimeout(fn,ms) { const id=++nextTimer;state.timers.set(id,{fn,ms});return id; },
        clearTimeout(id) { state.timers.delete(id); },
        fetch(url,options) { const d=deferred();state.requests.push({url:String(url),options,...d});return d.promise; }});
    state.byId=byId; state.form=form; state.image=image; state.win=win; state.doc=doc;
    state.frame={width:640,height:480,timestamp:1700000000,url:'images/frame.jpg'};
    state.respond = async (index, data, status=200) => {
        state.requests[index].resolve({ok:status===200,status,json:async()=>data});await flush();
    };
    state.runTimer=async ms => {const item=[...state.timers].find(([,t])=>t.ms===ms);assert.ok(item);state.timers.delete(item[0]);item[1].fn();await flush();};
    return state;
}
(async () => {
    const f=fixture();
    assert.equal(new URL(f.requests[0].url).searchParams.get('camera_id'),'2');
    f.byId('virtualsky-refresh').events.click();assert.equal(f.requests.length,1);
    await f.respond(0,{image_list:[f.frame]});
    assert.equal(f.created.length,1);assert.equal(f.image.src,'http://fixture.test/images/frame.jpg');
    assert.equal(f.byId('virtualsky-wrapper').hidden,false);
    const offset=f.form.elements.find(x=>x.name==='OFFSET_X');
    offset.value='24';f.form.events.input();
    assert.equal(f.byId('hybrid-starmap').style.left,'22px');
    assert.equal(f.requests.length,1,'Alignment preview must update without fetching another frame');
    offset.value='';f.form.events.input();
    assert.equal(f.byId('virtualsky-clip').hidden,true);
    offset.value='0';f.form.events.input();
    assert.equal(f.byId('hybrid-starmap').style.left,'10px');
    assert.equal(f.byId('virtualsky-clip').hidden,false);
    for (const [name,key] of [['CONSTELLATIONS','lines'],['CONSTELLATIONLABELS','labels']]) {
        const input=f.form.elements.find(x=>x.name===name);input.checked=!input.checked;f.form.events.change();
        assert.equal(f.engine.constellation[key],input.checked);
    }
    for (const name of ['SHOWSTARS','SHOWSTARLABELS','SHOWPLANETS','SHOWPLANETLABELS']) {
        const input=f.form.elements.find(x=>x.name===name);input.checked=!input.checked;f.form.events.change();
        assert.equal(f.engine[name.toLowerCase()],input.checked);
    }
    f.image.clientWidth=160;f.image.clientHeight=120;f.resize();assert.equal(f.engine.width,150);
    assert.equal(f.created.length,1,'Refresh/controls must reuse the planetarium');
    const diameter=f.form.elements.find(x=>x.name==='IMAGE_CIRCLE_DIAMETER');diameter.value='0';f.form.events.change();
    assert.equal(f.byId('virtualsky-clip').hidden,true);assert.equal(f.byId('virtualsky-download').disabled,true);
    diameter.value='600';f.form.events.reset();await f.runTimer(0);assert.equal(f.byId('virtualsky-clip').hidden,false);
    await f.byId('virtualsky-fullscreen').events.click();assert.ok(f.doc.fullscreenElement);
    await f.byId('virtualsky-fullscreen').events.click();assert.equal(f.doc.fullscreenElement,null);
    await f.byId('virtualsky-fullscreen').events.click();
    await f.byId('virtualsky-exit-fullscreen').events.click();
    assert.equal(f.doc.fullscreenElement,null);
    assert.equal(f.byId('virtualsky-fullscreen').focused,true);
    f.doc.exitFullscreen=async()=>{throw Error('blocked');};
    await f.byId('virtualsky-exit-fullscreen').events.click();
    assert.match(f.byId('modern-admin-virtualsky-message').textContent,/Use your browser fullscreen control/);
    const capture=deferred();f.win.html2canvas=()=>{f.captures++;return capture.promise;};
    const first=f.byId('virtualsky-download').events.click();await f.byId('virtualsky-download').events.click();
    assert.equal(f.captures,1);assert.equal(f.byId('virtualsky-download').disabled,true);
    capture.resolve({toBlob(fn){fn({type:'image/png'});}});await first;
    assert.equal(f.links[0].clicked,true);assert.equal(f.links[0].download,'virtualsky_camera_2_1700000000.png');
    f.byId('virtualsky-refresh').events.click();await f.respond(1,{},503);
    assert.equal(f.byId('virtualsky-wrapper').hidden,true);assert.match(f.byId('modern-admin-virtualsky-message').textContent,/503/);
    f.byId('virtualsky-refresh').events.click();await f.respond(2,{image_list:[]});
    assert.match(f.byId('modern-admin-virtualsky-message').textContent,/No frame/);
    f.byId('virtualsky-refresh').events.click();await f.respond(3,{image_list:[f.frame]});
    assert.equal(f.byId('virtualsky-wrapper').hidden,false);assert.equal(f.created.length,1);
    f.events.pagehide();assert.equal([...f.timers.values()].some(t=>t.ms===5000),false);
    f.events.pageshow({persisted:true});
    assert.equal(f.requests.length,5,'Returning with browser Back must resume frame refresh');
    await f.respond(4,{image_list:[f.frame]});
    assert.equal([...f.timers.values()].some(t=>t.ms===5000),true);
    f.win.html2canvas=async()=>({toBlob(fn){fn(null);}});
    await f.byId('virtualsky-download').events.click();
    assert.equal(f.links.length,1,'A failed encoder must not start a download');
    assert.match(f.byId('modern-admin-virtualsky-message').textContent,/download failed/);
    assert.equal(f.byId('virtualsky-download').disabled,false);
    const remote=fixture();remote.frame.url='https://cdn.example.invalid/frame.jpg';
    await remote.respond(0,{image_list:[remote.frame]});
    const exportRemote=remote.byId('virtualsky-download').events.click();
    assert.equal(remote.requests[1].options.mode,'cors');
    await remote.respond(1,{},403);await exportRemote;
    assert.equal(remote.captures,0,'Never export an overlay when the remote frame is unavailable');
    assert.match(remote.byId('modern-admin-virtualsky-message').textContent,/CORS/);
    const broken=fixture();broken.image.decode=async()=>{throw Error('Image decode failed');};
    await broken.respond(0,{image_list:[broken.frame]});
    assert.equal(broken.byId('virtualsky-wrapper').hidden,true);
    assert.equal(broken.byId('virtualsky-refresh').disabled,false);
    assert.match(broken.byId('modern-admin-virtualsky-message').textContent,/decode failed/);
    const missingLibrary=fixture();missingLibrary.win.S=null;
    await missingLibrary.respond(0,{image_list:[missingLibrary.frame]});
    assert.equal(missingLibrary.byId('virtualsky-download').disabled,true);
    assert.match(missingLibrary.byId('modern-admin-virtualsky-message').textContent,/library could not be loaded/);
    console.log('VirtualSky controller: scope, flags, reuse, resize, reset, export, duplicate requests, errors and recovery: PASS (effects simulated)');
})().catch(error=>{console.error(error);process.exitCode=1;});
