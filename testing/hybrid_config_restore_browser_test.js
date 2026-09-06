// Exercise the browser controller without production requests or effects.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../indi_allsky/flask/static/modern_admin/config-restore.js'), 'utf8');

async function run({checked = false, disabled = false, response, reject, twice = false} = {}) {
    let handler, calls = 0, sent;
    const button = {disabled: false}, status = {textContent: ''};
    const form = {
        action: '/indi-allsky/ajax/config/restore',
        querySelector: selector => selector.startsWith('button') ? button : status,
        elements: {namedItem: () => ({checked, disabled})},
        addEventListener: (name, callback) => {assert.equal(name, 'submit'); handler = callback;},
    };
    class Payload extends Map {
        constructor() {super([['csrf_token', 'test-token'], ['CONFIG_UPLOAD', 'test-file']]);}
    }
    vm.runInNewContext(source, {
        document: {getElementById: () => form}, FormData: Payload,
        fetch: async (url, options) => {
            calls++; sent = options;
            assert.equal(url, form.action);
            assert.equal(options.headers['X-CSRFToken'], 'test-token');
            assert.equal(options.credentials, 'same-origin');
            assert.equal(options.body.get('CONFIG_UPLOAD'), 'test-file');
            if (reject) throw new Error('offline');
            return response || {ok: true, json: async () => ({'success-message': 'Restored Config'})};
        },
    });
    const first = handler({preventDefault() {}});
    assert.equal(button.disabled, true);
    if (twice) await handler({preventDefault() {}});
    await first;
    assert.equal(calls, 1);
    assert.equal(button.disabled, false);
    for (const flag of ['RESET_KEYS', 'FLUSH_CONFIGS']) {
        assert.equal(sent.body.get(flag), checked && !disabled ? 'true' : '');
    }
    return status.textContent;
}
(async () => {
    assert.equal(await run({twice: true}), 'Restored Config');
    assert.match(await run({checked: true}), /sign in again/);
    assert.equal(await run({checked: true, disabled: true}), 'Restored Config');
    assert.match(await run({reject: true}), /offline.*Check Config History/);
    assert.match(await run({response: {ok: false, json: async () => ({CONFIG_UPLOAD: ['Invalid JSON']})}}), /CONFIG_UPLOAD: Invalid JSON/);
    assert.match(await run({response: {redirected: true}}), /session has expired/);
    assert.match(await run({response: {ok: true, json: async () => {throw new Error('invalid response');}}}), /could not be confirmed/);
    console.log('Hybrid restore browser controller: PASS');
})().catch(error => {console.error(error); process.exitCode = 1;});
