// Execute production native-form guard; this does not claim browser acceptance.
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const forms=[false,false,true].map(disabled=>({button:{disabled},events:{},attrs:{},
 querySelectorAll(){return [this.button]},addEventListener(n,f){this.events[n]=f},
 setAttribute(n,v){this.attrs[n]=v},removeAttribute(n){delete this.attrs[n]}}));
let show;
vm.runInNewContext(fs.readFileSync('indi_allsky/flask/static/modern_admin/camera-management.js','utf8'),{
 document:{querySelectorAll:()=>forms},window:{addEventListener:(event,fn)=>{assert.equal(event,'pageshow');show=fn}}});
let prevented=0;const event={preventDefault(){prevented++}};
forms[0].events.submit(event);
assert.equal(prevented,0);assert.equal(forms[0].attrs['aria-busy'],'true');
assert(forms.every(f=>f.button.disabled));
forms[0].events.submit(event);forms[1].events.submit(event);assert.equal(prevented,2);
show();assert.equal(forms[0].button.disabled,false);assert.equal(forms[1].button.disabled,false);assert.equal(forms[2].button.disabled,true);
assert.equal(forms[0].attrs['aria-busy'],undefined);
forms[1].events.submit(event);assert.equal(prevented,2);
console.log('Camera form guard: native first submit, duplicate/cross-form prevention and back-navigation permission state: PASS');
