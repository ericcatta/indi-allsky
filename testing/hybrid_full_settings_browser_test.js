const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../indi_allsky/flask/static/modern_admin/full-settings.js'), 'utf8');

async function run({canSave=true, response, duplicate=false, filterText=''}={}) {
    let submit, filterHandler, calls=0, sent;
    const classList = {add() {}, remove() {}};
    const control = value => ({value, checked:false, classList});
    const fields = {
        OWNER: control('Test observer'), CONFIG_NOTE: control('Keep this until saved'),
        RELOAD_ON_SAVE: {...control(''), checked:true}, FOCUS_MODE: {...control(''), checked:false},
        'OWNER-error': {hidden:true, textContent:''},
    };
    const row = {dataset:{fullSettingsSearch:'owner test observer'}, hidden:false};
    const count = {textContent:''};
    const section = {hidden:false,open:false,querySelectorAll:()=>[row],querySelector:()=>count};
    const button = {disabled:!canSave, textContent:'Save Full Settings'};
    const message = {hidden:true, textContent:'', className:''};
    const form = {noValidate:true,addEventListener:(name,callback)=>{submit=callback;},querySelectorAll:()=>[]};
    const filter = {value:filterText,addEventListener:(name,callback)=>{filterHandler=callback;}};
    const config = {fieldNames:['OWNER','CONFIG_NOTE','RELOAD_ON_SAVE','FOCUS_MODE'],checkboxNames:['RELOAD_ON_SAVE','FOCUS_MODE'],ajaxUrl:'/indi-allsky/ajax/config',csrfToken:'test-token',canSave};
    const elements = {...fields,'modern-admin-full-settings-form':form,'modern-admin-full-settings-save':button,
        'modern-admin-full-settings-message':message,'modern-admin-full-settings-filter':filter,
        'hybrid-full-settings-config':{textContent:JSON.stringify(config)}};
    vm.runInNewContext(source, {URL, window:{location:{href:'https://test.invalid/indi-allsky/modern-admin/settings/full'}},
        document:{getElementById:id=>elements[id] || null,querySelectorAll:()=>[section]},
        fetch:async (url,options)=>{
            calls++; sent=JSON.parse(options.body);
            assert.equal(url,'https://test.invalid/indi-allsky/ajax/config');
            assert.equal(options.headers['X-CSRFToken'],'test-token');
            if (response instanceof Error) throw response;
            return response || {ok:true,status:200,text:async()=>JSON.stringify({'success-message':'Saved'})};
        }});
    filterHandler();
    assert.equal(row.hidden, filterText !== '' && !'owner test observer'.includes(filterText.toLowerCase()));
    const promise = submit({preventDefault() {}});
    if (canSave) assert.equal(button.disabled,true);
    if (duplicate) await submit({preventDefault() {}});
    await promise;
    assert.equal(calls,canSave ? 1 : 0);
    assert.equal(button.disabled,!canSave);
    if(canSave) assert.deepEqual(sent,{OWNER:'Test observer',CONFIG_NOTE:'Keep this until saved',RELOAD_ON_SAVE:true,FOCUS_MODE:false});
    return {message:message.textContent,fields};
}
(async()=>{
    const success=await run({duplicate:true,filterText:'owner'});
    assert.equal(success.message,'Saved');
    assert.equal(success.fields.CONFIG_NOTE.value,'');
    assert.equal(success.fields.RELOAD_ON_SAVE.checked,false);
    await run({canSave:false,filterText:'missing'});
    const rejected=await run({response:{ok:false,status:400,text:async()=>JSON.stringify({OWNER:['Invalid owner']})}});
    assert.equal(rejected.fields['OWNER-error'].textContent,'Invalid owner');
    assert.equal(rejected.fields.CONFIG_NOTE.value,'Keep this until saved');
    assert.match((await run({response:{redirected:true}})).message,/session has expired/);
    assert.match((await run({response:{ok:false,status:500,text:async()=>'{}'}})).message,/could not be confirmed/);
    assert.match((await run({response:{ok:true,status:200,text:async()=>'<html>error</html>'}})).message,/unreadable response/);
    assert.match((await run({response:new Error('offline')})).message,/offline/);
    console.log('Hybrid full Settings controller: PASS');
})().catch(error=>{console.error(error);process.exitCode=1;});
