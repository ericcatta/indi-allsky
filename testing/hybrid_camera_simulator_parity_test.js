const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root=path.join(__dirname,'..');
const data=fs.readFileSync(path.join(root,'indi_allsky/flask/static/modern_admin/camera-simulator-data.js'),'utf8');
const legacy=fs.readFileSync(path.join(__dirname,'fixtures/camera_simulator_draw_before_hybrid.js'),'utf8');
const modern=fs.readFileSync(path.join(root,'indi_allsky/flask/static/modern_admin/camera-simulator.js'),'utf8');
const draw=modern.slice(modern.indexOf('function pixels2mm('),modern.indexOf('function update()'));
const catalog={};vm.createContext(catalog);vm.runInContext(data,catalog);
// Frozen catalog hash from e481b884: preserves every lens/sensor constant.
assert.equal(crypto.createHash('sha256').update(data).digest('hex'),'45ed651724b9bf6710bfa8777295f2f7a2be6b97314cde3dba833706fb2a2ccf');
function scene(source,method) {
    let calls=[],fields={};
    const context=new Proxy({}, {get:(_,name)=>(...args)=>calls.push([name,...args]),
        set:(_,name,value)=>{calls.push(['set',name,value]);return true;}});
    const canvas={getContext:()=>context,setAttribute(name,value){this[name]=value;}};
    const sandbox={window:{innerWidth:1280,innerHeight:720},document:{getElementById:id=>id==='image-circle-canvas'?canvas:fields[id]},
        $:selector=>({val:()=>fields[selector.slice(1)].value,text:()=>selector.includes('LENS')?'Test lens':'Test sensor'})};
    vm.createContext(sandbox);vm.runInContext(data+'\n'+source,sandbox);
    return (lens,sensor,x,y)=>{
        calls=[];
        fields={LENS_SELECT:{value:lens,selectedOptions:[{textContent:'Test lens'}]},SENSOR_SELECT:{value:sensor,selectedOptions:[{textContent:'Test sensor'}]},
            OFFSET_X:{value:String(x)},OFFSET_Y:{value:String(y)},'simulation-summary':{}};
        vm.runInContext(method+'()',sandbox);
        return JSON.parse(JSON.stringify(calls));
    };
}
const before=scene(legacy,'show_simulation'), after=scene(draw,'drawSimulation');
let scenarios=0;
for (const lens of Object.keys(catalog.icd)) for (const sensor of Object.keys(catalog.sd)) {
    for (const [x,y] of [[0,0],[-125,275]]) {
        assert.deepEqual(after(lens,sensor,x,y),before(lens,sensor,x,y),lens+'/'+sensor);
        scenarios++;
    }
}
assert(!modern.includes('camera_simulator_view'));
console.log('Hybrid simulator catalog and canvas parity: PASS ('+scenarios+' scenarios)');
