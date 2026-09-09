const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const code = fs.readFileSync('indi_allsky/flask/static/modern_admin/media-archive.js', 'utf8');
function card(saved = false, ready = 0) {
    const events = {};
    const preview = {tagName: 'VIDEO', readyState: ready, videoWidth: 4712, videoHeight: 750,
        addEventListener: (name, fn) => { events[name] = fn; }};
    const dimensions = {textContent: saved ? '640 × 480' : 'Not recorded'};
    const error = {hidden: true};
    return {events, preview, dimensions, error, querySelector: selector =>
        selector === 'img, video' ? preview : selector === '[data-preview-dimensions]' ? (saved ? null : dimensions) : error};
}
const a = card(), b = card(false, 4), saved = card(true);
vm.runInNewContext(code, {document: {querySelectorAll: () => [a, b, saved]}});
assert.match(a.dimensions.textContent, /load preview/);
assert.equal(b.dimensions.textContent, '4712 × 750 (preview)');
a.events.loadedmetadata();
assert.equal(a.dimensions.textContent, '4712 × 750 (preview)');
a.preview.videoWidth = 1920; a.preview.videoHeight = 1080; a.events.resize();
assert.equal(a.dimensions.textContent, '1920 × 1080 (preview)');
assert.equal(b.dimensions.textContent, '4712 × 750 (preview)');
a.events.emptied(); assert.match(a.dimensions.textContent, /load preview/);
a.preview.videoWidth = 0; a.events.loadedmetadata(); assert.match(a.dimensions.textContent, /unavailable/);
a.events.error(); assert.equal(a.error.hidden, false); assert.match(a.dimensions.textContent, /preview unavailable/);
saved.events.error(); assert.equal(saved.dimensions.textContent, '640 × 480');
for (const name of ['output_detail.html', '_media_archive_content.html']) {
    const template = fs.readFileSync('indi_allsky/flask/templates/modern_admin/' + name, 'utf8');
    assert.match(template, /item.video and \(not item.width or not item.height\)/);
    assert.match(template, /data-preview-dimensions/);
    assert.match(template, /archive-v2/);
}
console.log('Archive dimensions: cached/delayed metadata, resize, missing/error, camera isolation and saved values: PASS');
