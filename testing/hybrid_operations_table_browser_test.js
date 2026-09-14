// Controller contract tests; the DataTables adapter is simulated, not a live browser.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(require('node:path').join(__dirname,
    '../indi_allsky/flask/static/modern_admin/operations-table.js'), 'utf8');

function fixture(overrides = {}, clipboardFailure = false) {
    const records = [
        {dataset: {search: 'Camera 1 upload', state: 'SUCCESS', queue: 'UPLOAD'}},
        {dataset: {search: 'Camera 2 upload', state: 'FAILED', queue: 'UPLOAD'}},
        {dataset: {search: 'Camera 1 generation', state: 'SUCCESS', queue: 'VIDEO'}},
    ];
    records.forEach(row => { row.hasAttribute = () => true; });
    records.forEach(row => { row.textContent = row.dataset.search + ' measured value'; });
    const placeholder = {hasAttribute: () => false, remove() { this.removed = true; }};
    const inputs = Object.fromEntries(['search','state','queue'].map(id => [id,
        {value: '', handlers: {}, addEventListener(name, fn) { this.handlers[name] = fn; }}]));
    const panels = [], copied = [];
    const count = {after: panel => panels.push(panel)};
    const forms = [];
    const config = {table: 'records', rowAttribute: 'data-search', count: 'count',
        countSuffix: ' shown', csrfToken: 'test-csrf', exportUrl: '/operations/export',
        emptyMessage: 'No records', filters: [
            {id: 'search', attribute: 'search', contains: true},
            {id: 'state', attribute: 'state'}, {id: 'queue', attribute: 'queue'},
        ], ...overrides};
    let options, predicate = () => true, onDraw;
    const visible = () => records.filter((_row, index) => predicate('', [], index));
    const api = {
        row: index => ({node: () => records[index]}),
        rows: options => { assert.equal(options.search, 'applied'); return {count: () => visible().length}; },
        search: {fixed: (_name, fn) => { predicate = fn; }},
        on: (_event, fn) => { onDraw = fn; },
        draw: () => onDraw(),
        buttons: {exportData: options => {
            assert.deepEqual(JSON.parse(JSON.stringify(options.columns)), config.exportColumns || ':not(:last-child)');
            if (options.escapeExcelFormula !== undefined) assert.equal(options.escapeExcelFormula, true);
            return {header: ['Record'], body: visible().map(row => [row.dataset.search])};
        }},
    };
    const document = {
        getElementById: id => id === 'hybrid-operations-table-config' ? {textContent: JSON.stringify(config)}
            : id === 'records' ? {querySelectorAll: () => [...records, placeholder]}
            : id === 'count' ? count : inputs[id],
        body: {appendChild: form => forms.push(form)},
        createElement: tag => tag === 'form' ? {children: [], appendChild(input) { this.children.push(input); },
            submit() { this.submitted = true; }, remove() { this.removed = true; }} : {
                children: [], style: {}, appendChild(child) { this.children.push(child); },
                setAttribute(name, value) { this[name] = value; },
                focus() { this.focused = true; }, select() { this.selected = true; },
            },
    };
    function DataTable(_element, opts) { options = opts; return api; }
    vm.runInNewContext(source, {document, DataTable, navigator: {clipboard: {writeText: async text => {
        if (clipboardFailure) throw new Error('Clipboard denied');
        copied.push(text);
    }}}});
    return {records, inputs, count, forms, options, api, placeholder, panels, copied,
        change(id, value, event = 'change') { inputs[id].value = value; inputs[id].handlers[event](); }};
}

const app = fixture();
assert(app.placeholder.removed);
assert.equal(app.count.textContent, '3 shown');
app.change('search', '  CAMERA 1  ', 'input');
assert.equal(app.count.textContent, '2 shown');
app.change('queue', 'upload');
assert.equal(app.count.textContent, '1 shown');
app.change('state', 'failed');
assert.equal(app.count.textContent, '0 shown');
app.change('search', '');
assert.equal(app.count.textContent, '1 shown');
for (const [index, format] of [[1, 'csv'], [2, 'xlsx']]) {
    app.options.buttons[index].action(null, app.api);
    const form = app.forms.at(-1);
    assert(form.submitted && form.removed && form.hidden);
    assert.equal(form.method, 'post'); assert.equal(form.action, '/operations/export');
    const values = Object.fromEntries(form.children.map(input => [input.name, input.value]));
    assert.equal(values.csrf_token, 'test-csrf'); assert.equal(values.format, format);
    assert.deepEqual(JSON.parse(values.table), {header: ['Record'], body: [['Camera 2 upload']]});
}
app.change('queue', 'up'); // Exact dropdown filters must not match a prefix.
assert.equal(app.count.textContent, '0 shown');
app.change('queue', ''); app.change('state', '');
assert.equal(app.count.textContent, '3 shown');
assert.equal(app.options.buttons[0].text, 'Copy');
const history = fixture({order:[[0,'desc']],columnDefs:[],exportColumns:[0,1,2,3,4,5]});
assert.equal(JSON.stringify(history.options.order), '[[0,"desc"]]');
assert.equal(history.options.columnDefs.length,0);

assert.equal(JSON.stringify(history.options.lengthMenu),'[20,50,100,-1]');
history.change('search','Camera 2');
history.options.buttons[1].action(null,history.api);
assert.equal(history.forms.length,1);
const textSearch = fixture({filters:[{id:'search',text:true,contains:true}]});
textSearch.change('search','measured value');
assert.equal(textSearch.count.textContent,'3 shown');
textSearch.change('search','absent');
assert.equal(textSearch.count.textContent,'0 shown');
console.log('Operations table controller: combined filters, counts, reset, empty rows, filtered export payload/CSRF and native attachment forms: PASS');

const pagedHistory = fixture({paging: false});
assert.equal(pagedHistory.options.paging, false);
assert.equal(pagedHistory.options.lengthChange, false);
assert.equal(pagedHistory.options.layout.topStart, null);
assert.equal(fixture().options.paging, true);

(async () => {
    const success = fixture();
    success.change('state', 'FAILED');
    await success.options.buttons[0].action(null, success.api);
    assert.deepEqual(success.copied, ['Record\nCamera 2 upload']);
    assert.equal(success.panels[0].children[0].textContent, 'Copied 1 record.');
    assert.equal(success.panels[0].children[1].hidden, true);
    const denied = fixture({exportColumns:[0]}, true);
    denied.change('state', 'FAILED');
    await denied.options.buttons[0].action(null, denied.api);
    const [status, fallback] = denied.panels[0].children;
    assert(status.textContent.includes('Automatic copy is unavailable'));
    assert.equal(fallback.value, 'Record\nCamera 2 upload');
    assert(fallback.readOnly && fallback.focused && fallback.selected && !fallback.hidden);
    denied.change('state', 'SUCCESS');
    await denied.options.buttons[0].action(null, denied.api);
    assert.equal(denied.panels.length, 1);
    assert.equal(fallback.value, 'Record\nCamera 1 upload\nCamera 1 generation');
    console.log('Copy: filtered payload, column selection, formula escaping option, success feedback and accessible denied-clipboard fallback PASS');
})().catch(error => { console.error(error); process.exitCode = 1; });
