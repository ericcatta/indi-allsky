/* Controller confirmations and duplicate submits; Google is not contacted. */
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync('indi_allsky/flask/static/modern_admin/youtube.js','utf8');
function fixture(confirmed) {
 const forms=['connect','refresh','revoke'].map(action=>({dataset:{youtubeAction:action},addEventListener(name,handler){this.submit=handler;}}));
 const buttons=forms.map(()=>({disabled:false})), status={hidden:true};
 const context={document:{getElementById:()=>status,querySelectorAll:selector=>selector.endsWith('button')?buttons:forms},window:{confirm:()=>confirmed,addEventListener(){}}};
 vm.runInNewContext(source,context);
 return {forms,buttons,status};
}
const cancelled=fixture(false);let stopped=0;
cancelled.forms[2].submit({preventDefault(){stopped++;}});
assert.equal(stopped,1);assert.equal(cancelled.buttons.some(button=>button.disabled),false);
for(const index of [0,1,2]) {
 const ready=fixture(true);let duplicates=0;
 ready.forms[index].submit({preventDefault(){throw Error('First authorized submit blocked');}});
 assert.equal(ready.buttons.every(button=>button.disabled),true);assert.equal(ready.status.hidden,false);
 ready.forms[index].submit({preventDefault(){duplicates++;}});
 assert.equal(duplicates,1);
}
console.log('YouTube revoke cancellation, action feedback and duplicate form prevention: PASS');
