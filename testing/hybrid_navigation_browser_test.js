const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
function element() {
    return {attrs:{},events:{},focused:false,setAttribute(key,value){this.attrs[key]=value;},
        addEventListener(key,callback){this.events[key]=callback;},focus(){this.focused=true;}};
}
const button=element(), toggle={checked:true}, drawer=element(), scrim=element(), first=element();
drawer.querySelector=()=>first;
const document=element();
document.getElementById=id=>({'hybrid-menu-button':button,'hybrid-menu-toggle':toggle,'hybrid-navigation':drawer}[id]);
document.querySelector=()=>scrim;
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../indi_allsky/flask/static/modern_admin/navigation.js'),'utf8'),{document});
assert.equal(toggle.checked,false);
assert.equal(drawer.inert,true);
button.events.click();
assert.equal(toggle.checked,true);
assert.equal(drawer.inert,false);
assert.equal(button.attrs['aria-expanded'],'true');
assert.equal(first.focused,true);
let prevented=false;
document.events.keydown({key:'Escape',preventDefault(){prevented=true;}});
assert.equal(prevented,true);
assert.equal(toggle.checked,false);
assert.equal(button.focused,true);
button.events.click();
drawer.events.click({target:{closest:()=>({})}});
assert.equal(toggle.checked,false);
button.events.click();
drawer.events.click({target:{closest:()=>null}});
assert.equal(toggle.checked,true);
scrim.events.click();
assert.equal(toggle.checked,false);
console.log('Hybrid navigation controller: PASS');
