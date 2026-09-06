const fs=require('fs'),vm=require('vm'),assert=require('assert');
async function run(){
 const result={textContent:''}, metadata={children:[],replaceChildren(){this.children=[];},append(row){this.children.push(row);}};
 const button={disabled:false,dataset:{driveCommand:'getmetadata',driveId:'drive'},addEventListener(k,f){this.click=f;}},protectedButton={disabled:true};
 const root={dataset:{url:'/drives',csrf:'signed'},querySelectorAll:()=>[button,protectedButton]};
 protectedButton.addEventListener=()=>{};
 let calls=[],resolve,confirmed=true;
 vm.runInNewContext(fs.readFileSync('indi_allsky/flask/static/modern_admin/drives.js','utf8'),{
 document:{getElementById:id=>id==='drive-tool'?root:id==='drive-result'?result:metadata,createElement:()=>({children:[],append(child){this.children.push(child);}})},window:{confirm:()=>confirmed},fetch:(url,options)=>{calls.push({url,options});return new Promise(r=>resolve=r);}});
 const pending=button.click();button.click();assert.equal(calls.length,1);
 resolve({ok:true,json:async()=>({drive_data:[[0,'Model','<script>not markup</script>']]})});await pending;
 assert.equal(metadata.children[0].children[1].textContent,'<script>not markup</script>');assert(!button.disabled && protectedButton.disabled);
 button.dataset={driveCommand:'mount',deviceId:'volume'};confirmed=false;await button.click();assert.equal(calls.length,1);
 confirmed=true;const mount=button.click();assert.deepEqual(JSON.parse(calls[1].options.body),{COMMAND:'mount',DEVICE_ID:'volume'});assert.equal(calls[1].options.headers['X-CSRFToken'],'signed');
 resolve({ok:true,json:async()=>({'success-message':'Mount Successful'})});await mount;
 assert(button.disabled && protectedButton.disabled);assert(result.textContent.includes('Refresh devices'));
 await button.click();assert.equal(calls.length,2);
 console.log('Drive controller: metadata as text, duplicates, confirmation/cancel, target/CSRF and fresh-inventory requirement: PASS');
}
run().catch(error=>{console.error(error);process.exitCode=1;});
