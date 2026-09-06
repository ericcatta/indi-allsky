const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../indi_allsky/flask/static/modern_admin/account.js'), 'utf8');
async function run(response, duplicate = false) {
    let handler, calls = 0;
    const values = Object.fromEntries(['NAME', 'CURRENT_PASSWORD', 'NEW_PASSWORD', 'NEW_PASSWORD2', 'csrf_token'].map(name => [name, {value: name + '-test'}]));
    const button = {disabled: false}, status = {textContent: ''};
    const form = {action: '/indi-allsky/ajax/user', elements: {namedItem: name => values[name]},
        querySelector: selector => selector.startsWith('button') ? button : status,
        addEventListener: (event, callback) => {handler = callback;}};
    vm.runInNewContext(source, {document: {getElementById: () => form}, fetch: async (url, options) => {
        calls++;
        assert.equal(url, form.action);
        assert.equal(options.method, 'POST');
        assert.equal(options.credentials, 'same-origin');
        assert.equal(options.headers['X-CSRFToken'], 'csrf_token-test');
        assert.deepEqual(JSON.parse(options.body), {NAME:'NAME-test', CURRENT_PASSWORD:'CURRENT_PASSWORD-test', NEW_PASSWORD:'NEW_PASSWORD-test', NEW_PASSWORD2:'NEW_PASSWORD2-test'});
        if (response instanceof Error) throw response;
        return response;
    }});
    const first = handler({preventDefault() {}});
    assert.equal(button.disabled, true);
    if (duplicate) await handler({preventDefault() {}});
    await first;
    assert.equal(calls, 1);
    assert.equal(button.disabled, false);
    return {values, status: status.textContent};
}
(async () => {
    let result = await run({ok: true, json: async () => ({'success-message':'Account saved'})}, true);
    assert.equal(result.status, 'Account saved');
    for (const name of ['CURRENT_PASSWORD','NEW_PASSWORD','NEW_PASSWORD2']) assert.equal(result.values[name].value, '');
    assert.equal(result.values.NAME.value, 'NAME-test');
    result = await run({ok: false, json: async () => ({CURRENT_PASSWORD:['Invalid password']})});
    assert.equal(result.status, 'Invalid password');
    assert.equal(result.values.CURRENT_PASSWORD.value, 'CURRENT_PASSWORD-test');
    assert.match((await run({redirected:true})).status, /session has expired/);
    assert.equal((await run(new Error('Network unavailable'))).status, 'Network unavailable');
    assert.equal((await run({ok:true, json:async () => {throw new Error('Invalid response');}})).status, 'Invalid response');
    console.log('Hybrid account browser controller: PASS');
})().catch(error => {console.error(error); process.exitCode = 1;});
