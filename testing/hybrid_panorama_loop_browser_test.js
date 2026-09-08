/* Execute the shipped controller with controlled DOM/image events; not native-browser acceptance. */
const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
const source = fs.readFileSync('indi_allsky/flask/static/modern_admin/panorama-loop.js', 'utf8');
const settle = () => new Promise(resolve => setImmediate(resolve));
function fixture(count = 3) {
    const node = () => ({dataset:{},hidden:false,disabled:false,events:{},attrs:{},
        addEventListener(name,fn){this.events[name]=fn;},setAttribute(name,value){this.attrs[name]=value;},removeAttribute(name){delete this[name];}});
    const nodes = Object.fromEntries(['panorama-loop-controls','panorama-loop-frames','modern-admin-media-featured-image','panorama-loop-toggle','panorama-loop-prev','panorama-loop-next','panorama-loop-speed','panorama-loop-status'].map(id=>[id,node()]));
    const frames = Array.from({length:count},(_,i)=>({title:'Panorama '+i,filename:'camera2-'+i+'.jpg',preview_url:'/preview-'+i+'.jpg',url:'/original-'+i+'.jpg',created:'date '+i,age:'age '+i,timeofday:'Night'}));
    nodes['panorama-loop-frames'].textContent=JSON.stringify(frames);
    nodes['panorama-loop-speed'].value='350';
    const figure=node(), caption=[node(),node()], viewer=node(), parts={};
    for(const selector of ['h3','[data-loop-created]','[data-loop-timeofday]','[data-loop-original]'])parts[selector]=node();
    nodes['modern-admin-media-featured-image'].closest=()=>figure;
    figure.closest=()=>viewer;figure.querySelectorAll=()=>caption;viewer.querySelector=s=>parts[s];
    const timers=new Map(), loads=[], events={}, doc={hidden:false,getElementById:id=>nodes[id],addEventListener:(e,f)=>events[e]=f};
    let seq=0;
    const win={setTimeout(fn,ms){timers.set(++seq,{fn,ms});return seq;},clearTimeout(id){timers.delete(id);},addEventListener:(e,f)=>events[e]=f};
    vm.runInNewContext(source,{document:doc,window:win,Image:class{set src(value){this.url=value;loads.push(this);}},JSON,Number,String,Error});
    return {nodes,frames,figure,caption,parts,timers,loads,events,doc,
        click(id){nodes['panorama-loop-'+id].events.click();},
        tick(ms){const match=[...timers].find(([,v])=>v.ms===ms);assert(match,'Expected timer '+ms);timers.delete(match[0]);match[1].fn();}};
}
async function run(){
    const f=fixture(), image=f.nodes['modern-admin-media-featured-image'];
    assert.equal(f.loads.length,1);assert(f.nodes['panorama-loop-next'].disabled);
    f.loads[0].onload();await settle();
    assert.equal(image.src,'/preview-0.jpg');assert.equal(f.figure.dataset.mediaIndex,'0');
    f.tick(350);assert.equal(f.loads.length,2);
    f.click('next');assert.equal(f.loads.length,2,'Overlapping load ignored');
    f.loads[1].onload();await settle();
    assert.equal(image.src,'/preview-1.jpg');assert.equal(image.dataset.originalUrl,'/original-1.jpg');
    assert.equal(f.figure.dataset.mediaIndex,'1');assert.equal(f.parts['[data-loop-original]'].href,'/original-1.jpg');
    assert.equal(f.caption[0].textContent,'camera2-1.jpg');assert.equal(f.parts['h3'].textContent,'Panorama 1');
    f.click('next');f.loads[2].onerror();await settle();
    assert.equal(image.src,'/preview-1.jpg');assert.equal(f.figure.dataset.mediaIndex,'1');
    assert.match(f.nodes['panorama-loop-status'].textContent,/could not be loaded/);
    assert.equal(f.nodes['panorama-loop-toggle'].textContent,'Play');assert.equal(f.timers.size,0);
    f.click('next');assert.equal(f.loads[3].url,'/preview-0.jpg','Can move past failed frame');
    f.loads[3].onload();await settle();
    let prevented=false;f.nodes['panorama-loop-controls'].events.keydown({target:{},key:'ArrowLeft',preventDefault(){prevented=true;}});
    assert(prevented);assert.equal(f.loads[4].url,'/preview-2.jpg');f.loads[4].onload();await settle();
    f.click('toggle');assert(f.timers.size);
    f.doc.hidden=true;f.events.visibilitychange();assert.equal(f.timers.size,0);
    f.doc.hidden=false;f.events.visibilitychange();assert(f.timers.size);
    f.figure.events.keydown({key:'Enter'});assert.equal(f.timers.size,0,'Lightbox opener freezes frame');
    f.nodes['panorama-loop-speed'].value='2000';f.click('toggle');f.tick(2000);
    f.tick(15000);await settle();assert.match(f.nodes['panorama-loop-status'].textContent,/could not be loaded/);
    f.click('next');const last=f.loads.at(-1);f.events.pagehide();await settle();
    assert.equal(last.onload,null);assert.equal(f.timers.size,0);
    const old=image.src;f.events.pageshow({persisted:true});assert.equal(image.src,old);
    const freezing=fixture();freezing.loads[0].onload();await settle();
    freezing.tick(350);const pending=freezing.loads[1];
    freezing.figure.events.click();await settle();
    assert.equal(pending.onload,null,'Opening lightbox cancels pending advance');
    assert.equal(freezing.figure.dataset.mediaIndex,'0');assert.equal(freezing.timers.size,0);
    const one=fixture(1);one.loads[0].onload();await settle();
    assert(one.nodes['panorama-loop-toggle'].disabled && one.nodes['panorama-loop-next'].disabled);
    assert.equal(one.timers.size,0);
    const broken=fixture();broken.loads[0].onerror();await settle();
    assert(broken.nodes['modern-admin-media-featured-image'].hidden);
    assert.match(broken.nodes['panorama-loop-status'].textContent,/No preview available/);
    console.log('Panorama loop: playback, frame/detail/lightbox identity, pause, navigation, keyboard, timeout, failed frame recovery, hidden page and teardown: PASS');
}
run().catch(error=>{console.error(error);process.exitCode=1;});
