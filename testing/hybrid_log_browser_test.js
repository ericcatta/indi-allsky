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
const flush = () => new Promise(resolve => setImmediate(resolve));
const abortError = () => Object.assign(new Error('aborted'), {name: 'AbortError'});

function fixture(ignoreAbort = false) {
    const nodes = Object.fromEntries(['REFRESH_SELECT', 'LINES_SELECT', 'FILTER', 'modern-admin-log-output', 'modern-admin-log-status']
        .map(id => [id, {value: id === 'REFRESH_SELECT' ? '15' : id === 'LINES_SELECT' ? '25' : '',
            textContent: '', handlers: {}, addEventListener(event, fn) {this.handlers[event] = fn;}}]));
    const requests = [], timers = new Map();
    let nextTimer = 0, periodic;
    const scope = {
        document: {getElementById: id => nodes[id]}, AbortController,
        window: {
            clearInterval() {}, setInterval(fn) {periodic = fn; return 1;},
            setTimeout(fn, ms) {assert.equal(ms, 15000); timers.set(++nextTimer, fn); return nextTimer;},
            clearTimeout(id) {timers.delete(id);},
        },
        fetch: (url, options) => new Promise((resolve, reject) => {
            requests.push({url, options, resolve, reject});
            if (!ignoreAbort) options.signal.addEventListener('abort', () => reject(abortError()));
        }),
    };
    vm.runInNewContext(source, scope);
    assert.equal(requests[0].options.headers['X-CSRFToken'], 'synthetic-csrf');
    assert.deepEqual(JSON.parse(requests[0].options.body), {lines: '25', filter: ''});
    return {nodes, requests, timers, scope, poll: () => periodic(),
        output: () => nodes['modern-admin-log-output'].textContent,
        status: () => nodes['modern-admin-log-status'].textContent};
}
const response = log => ({ok: true, json: async () => ({log})});

(async () => {
    for (const [reply, output, status] of [
        [response('<script>plain log text</script>'), '<script>plain log text</script>', 'Updated.'],
        [response(''), '[No log data]', 'Updated.'],
        [response('[No matching lines]'), '[No matching lines]', 'Updated.'],
        [{ok: true, redirected: true}, '', 'Session expired.'],
        [{ok: false}, '', 'Error loading log data.'],
        [{ok: true, json: async () => {throw Error('HTML response');}}, '', 'Error loading log data.'],
        [{ok: true, json: async () => ({log: {unexpected: true}})}, '', 'Error loading log data.'],
        [response('ERROR: Log file missing'), '', 'ERROR: Log file missing'],
    ]) {
        const f = fixture(); f.requests[0].resolve(reply); await flush();
        assert.equal(f.output(), output); assert.ok(f.status().startsWith(status), f.status());
        assert.equal(f.timers.size, 0);
    }
    // Delayed responses must never overwrite a newer filter, even if abort is ignored.
    const race = fixture(true);
    race.nodes.FILTER.value = 'new'; race.nodes.FILTER.handlers.input();
    assert.equal(race.requests[0].options.signal.aborted, true);
    race.requests[1].resolve(response('new result')); await flush();
    race.requests[0].resolve(response('old result')); await flush();
    assert.equal(race.output(), 'new result'); assert.equal(race.timers.size, 0);

    const timeout = fixture(); timeout.poll();
    assert.equal(timeout.requests.length, 1, 'polling must not overlap an active request');
    [...timeout.timers.values()][0](); await flush();
    assert.match(timeout.status(), /timed out/); assert.equal(timeout.output(), '');
    timeout.poll(); assert.match(timeout.status(), /timed out/, 'automatic retry must retain failure until success');
    timeout.requests[1].resolve(response('recovered')); await flush();
    assert.equal(timeout.output(), 'recovered');
    timeout.poll(); timeout.requests[2].reject(Error('offline')); await flush();
    assert.equal(timeout.output(), 'recovered'); assert.match(timeout.status(), /Showing previous log data/);
    timeout.nodes.LINES_SELECT.value = '100'; timeout.nodes.LINES_SELECT.handlers.change();
    assert.equal(timeout.output(), '', 'different selection must not display old data');
    timeout.requests[3].resolve(response('100-line selection')); await flush();
    assert.equal(JSON.parse(timeout.requests[3].options.body).lines, '100');
    assert.equal(timeout.output(), '100-line selection');

    // Deadline covers body decoding too, not just receipt of HTTP headers.
    const body = fixture();
    body.requests[0].resolve({ok: true, json: () => new Promise((resolve, reject) => {
        body.requests[0].options.signal.addEventListener('abort', () => reject(abortError()));
    })});
    await flush(); [...body.timers.values()][0](); await flush();
    assert.match(body.status(), /timed out/); assert.equal(body.timers.size, 0);
    body.nodes.REFRESH_SELECT.value = '5'; body.nodes.REFRESH_SELECT.handlers.change();
    assert.equal(body.requests.length, 2);
    body.requests[1].resolve(response('retry succeeded')); await flush();
    assert.equal(body.output(), 'retry succeeded');
    console.log('Log: CSRF, text/errors, response ordering, bounded polling, fetch/body deadline and recovery: PASS');
})().catch(error => {console.error(error); process.exitCode = 1;});
