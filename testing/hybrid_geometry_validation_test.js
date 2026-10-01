const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const source = fs.readFileSync(path.join(__dirname, '../indi_allsky/flask/static/modern_admin/image-geometry.js'), 'utf8');

async function run() {
    const elements = {};
    const get = id => elements[id] ||= {value: '0', type: 'number', checked: false,
        textContent: '', events: {}, addEventListener(event, fn) { this.events[event] = fn; }};
    get('geometry-config').textContent = JSON.stringify({imageUrl: ''});
    get('IMAGE_CIRCLE_DIAMETER').value = '3000';
    get('LINE_WIDTH').value = '5';
    get('LINE_COLOR').options = [];
    get('KEOGRAM_LINE').type = 'checkbox';
    get('geometry-review').dataset = {settingsUrl: '/settings/cameras?profile_id=second'};
    const copied = [], destinations = [];
    vm.runInNewContext(source, {
        document: {getElementById: get, addEventListener() {}},
        window: {addEventListener() {}}, Image: class {},
        localStorage: {getItem() { return null; }, setItem() {}},
        navigator: {clipboard: {async writeText(text) { copied.push(JSON.parse(text)); }}},
        location: {href: 'https://example.test/geometry', assign(url) { destinations.push(url); }}, URL,
    });
    for (const invalid of ['360', '-1', '', 'NaN', 'Infinity']) {
        get('AZIMUTH_ANGLE').value = invalid;
        get('AZIMUTH_ANGLE').events.input();
        await get('geometry-copy').events.click();
        get('geometry-review').events.click();
        assert.match(get('geometry-status').textContent, /Azimuth must be/);
        assert.equal(copied.length, 0, invalid);
        assert.equal(destinations.length, 0, invalid);
    }
    for (const [azimuth, angle] of [['0', 0], ['180', 180], ['270', -90], ['359.9', -0.10000000000002274]]) {
        get('AZIMUTH_ANGLE').value = azimuth;
        get('AZIMUTH_ANGLE').events.input();
        // Browser inputs convert assigned numbers to strings.
        get('KEOGRAM_ANGLE').value = String(get('KEOGRAM_ANGLE').value);
        await get('geometry-copy').events.click();
        assert.equal(copied.at(-1).KEOGRAM_ANGLE, angle);
        assert.equal(copied.at(-1).LENS_IMAGE_CIRCLE, 3000);
        get('geometry-review').events.click();
        assert.equal(new URL(destinations.at(-1)).searchParams.get('profile_id'), 'second');
    }
    console.log('Geometry: invalid azimuth blocks copy/review; valid angle recovery preserves scoped draft: PASS');
}
run().catch(error => { console.error(error); process.exitCode = 1; });
