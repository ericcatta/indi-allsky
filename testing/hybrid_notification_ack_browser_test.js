const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname,'../indi_allsky/flask/static/modern_admin/notification-ack.js'),'utf8');
function fixture(fetch) {
    const button = {disabled:false}, status = {}, state = {classList:{remove(){}}};
    let submit;
    const form = {action:'/notifications/1/acknowledge',elements:{namedItem:()=>({value:'csrf-test'})},
        querySelector:selector=>selector.startsWith('button')?button:status,
        addEventListener:(_,handler)=>{submit=handler;}};
    vm.runInNewContext(source,{document:{getElementById:()=>form,querySelectorAll:()=>[state]},fetch});
    return {button,status,state,submit:()=>submit({preventDefault(){}})};
}
(async () => {
    let resolve,calls=0;
    const app=fixture((url,options)=>{
        calls++;
        assert.equal(url,'/notifications/1/acknowledge');
        assert.equal(options.headers['X-CSRFToken'],'csrf-test');
        assert.equal(options.body,'{}');
        return new Promise(done=>{resolve=done;});
    });
    const pending=app.submit();await app.submit();
    assert.equal(calls,1);assert.equal(app.button.disabled,true);
    resolve({ok:true,json:async()=>({allowed:true,message:'Notification acknowledged'})});
    await pending;
    assert.equal(app.state.textContent,'Yes');assert.equal(app.button.disabled,true);
    await app.submit();assert.equal(calls,1);
    for (const response of [
        {ok:false,json:async()=>({allowed:false,message:'Notification does not exist'})},
        {redirected:true},
        {ok:true,json:async()=>{throw new Error('Invalid response');}},
    ]) {
        const error=fixture(async()=>response);await error.submit();
        assert.equal(error.button.disabled,false);assert.match(error.status.textContent,/could not be confirmed/);
        assert.notEqual(error.state.textContent,'Yes');
    }
    const network=fixture(async()=>{throw new Error('Network unavailable');});await network.submit();
    assert.equal(network.button.disabled,false);
    assert.match(network.status.textContent,/Refresh this page/);
    console.log('Hybrid notification acknowledgement controller: PASS');
})().catch(error=>{console.error(error);process.exitCode=1;});
