/* Controller failure paths; actual playback/copy/download are recorded separately. */
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync('indi_allsky/flask/static/modern_admin/public-media.js','utf8');
function fixture(clipboard,fullscreen) {
    const node=()=>({hidden:true,handlers:{},addEventListener(event,callback){this.handlers[event]=callback;}});
    const preview={...node(),tagName:'IMG',complete:true,naturalWidth:0};
    const nodes=Object.fromEntries(['preview','status','error','copy','fullscreen','exit'].map(id=>[id,node()]));
    nodes.preview.querySelector=()=>preview;nodes.preview.requestFullscreen=fullscreen;
    nodes.copy.dataset={permalink:'https://camera.example/view_image?id=2&camera_id=2'};
    vm.runInNewContext(source,{document:{getElementById:id=>nodes[id.replace('public-media-','')],exitFullscreen:async()=>{}},navigator:{clipboard}});
    return {nodes,preview};
}
(async()=>{
    let copied;
    const ok=fixture({writeText:async text=>{copied=text}},async()=>{});
    assert.equal(ok.nodes.error.hidden,false,'Already failed previews must show an error');
    await ok.nodes.copy.handlers.click();assert.equal(copied,ok.nodes.copy.dataset.permalink);assert.equal(ok.nodes.status.textContent,'Link copied.');
    const failed=fixture({writeText:async()=>{throw new Error('denied')}},async()=>{throw new Error('unsupported')});
    await failed.nodes.copy.handlers.click();assert.match(failed.nodes.status.textContent,/Copy this link: https:/);
    await failed.nodes.fullscreen.handlers.click();assert.match(failed.nodes.status.textContent,/not available/);
    const unsupported=fixture(undefined,undefined);assert.equal(unsupported.nodes.fullscreen.disabled,true);assert.match(unsupported.nodes.fullscreen.title,/not available/);
    await unsupported.nodes.copy.handlers.click();assert.match(unsupported.nodes.status.textContent,/Copy this link:/);
    console.log('Public media clipboard fallback, fullscreen capability errors and failed preview feedback: PASS');
})().catch(error=>{console.error(error);process.exitCode=1});
