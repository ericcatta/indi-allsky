const fs=require('fs'),vm=require('vm'),assert=require('assert');
async function run(){
 const field={disabled:false}, unavailable={disabled:true}, result={textContent:''};
 const button={dataset:{gpioId:'2',gpioName:'13',gpioState:'0'},closest:()=>field,addEventListener(k,f){this.click=f;}};
 const root={dataset:{url:'/gpio',csrf:'signed'},querySelectorAll:selector=>selector==='fieldset'?[field,unavailable]:[button]};
 let calls=[],resolve,confirm=true;
 vm.runInNewContext(fs.readFileSync('indi_allsky/flask/static/modern_admin/manual-gpio.js','utf8'),{
 document:{getElementById:id=>id==='gpio-tool'?root:result},window:{confirm:()=>confirm},fetch:(url,options)=>{calls.push({url,options});return new Promise(r=>resolve=r);}});
 confirm=false;await button.click();assert.equal(calls.length,0);
 confirm=true;const pending=button.click();button.click();assert.equal(calls.length,1);assert(field.disabled);
 assert.deepEqual(JSON.parse(calls[0].options.body),{PIN_ID:2,NEW_PIN_STATE:0});assert.equal(calls[0].options.headers['X-CSRFToken'],'signed');
 resolve({ok:true,json:async()=>({pin_state:false,pin_name:'13'})});await pending;
 assert(result.textContent.includes('Off for BCM 13'));assert(!field.disabled && unavailable.disabled);
 const failure=button.click();resolve({ok:false,json:async()=>({'failure-message':'Inspect state before retrying'})});await failure;
 assert.equal(result.textContent,'Inspect state before retrying');assert(!field.disabled);
 const expired=button.click();resolve({redirected:true});await expired;assert(result.textContent.includes('Session expired'));
 field.disabled=true;await button.click();assert.equal(calls.length,3);
 console.log('GPIO controller: confirmation/cancel, explicit Off, CSRF, duplicate prevention, errors and retained disabled controls: PASS');
}
run().catch(error=>{console.error(error);process.exitCode=1;});
