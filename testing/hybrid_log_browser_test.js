#!/usr/bin/env node
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const template = fs.readFileSync(path.join(__dirname, '../indi_allsky/flask/templates/modern_admin/log.html'), 'utf8');
const source = [...template.matchAll(/<script>([\s\S]*?)<\/script>/g)][0][1]
    .replace(/{{ url_for\('indi_allsky.js_log_view'\) }}/g, '/indi-allsky/js/log')
    .replace(/{{ csrf_token\(\)\|tojson }}/g, '"synthetic-csrf"');

async function test(response, expected) {
    const nodes = Object.fromEntries(['REFRESH_SELECT', 'LINES_SELECT', 'FILTER', 'modern-admin-log-output']
        .map(id => [id, {value: id === 'REFRESH_SELECT' ? '15' : id === 'LINES_SELECT' ? '25' : '',
                       textContent: '', addEventListener() {}}]));
    const requests = [];
    vm.runInNewContext(source, {
        document: {getElementById: id => nodes[id]},
        window: {clearInterval() {}, setInterval() {return 1;}},
        fetch: async (url, options) => {requests.push({url, options}); return response;}
    });
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(requests.length, 1);
    assert.equal(requests[0].options.headers['X-CSRFToken'], 'synthetic-csrf');
    assert.deepEqual(JSON.parse(requests[0].options.body), {lines: '25', filter: ''});
    assert.equal(nodes['modern-admin-log-output'].textContent, expected);
}

(async () => {
    await test({ok:true, json:async()=>({log:'<script>plain log text</script>'})}, '<script>plain log text</script>');
    await test({ok:true, redirected:true}, 'Session expired. Sign in and reload the log page.');
    await test({ok:false, json:async()=>({log:'must not display failed response as log'})}, 'Error loading log data. Check access and refresh the page.');
    await test({ok:true, json:async()=>{throw Error('HTML response');}}, 'Error loading log data. Check access and refresh the page.');
    console.log('Log controller CSRF, plain text, expired session and failed/malformed responses: PASS');
})().catch(error => {console.error(error); process.exitCode=1;});
