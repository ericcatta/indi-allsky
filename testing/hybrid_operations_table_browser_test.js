// Controller contract tests; the DataTables adapter is simulated, not a live browser.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(require('node:path').join(__dirname,
    '../indi_allsky/flask/static/modern_admin/operations-table.js'), 'utf8');

function fixture() {
    const records = [
        {dataset: {search: 'Camera 1 upload', state: 'SUCCESS', queue: 'UPLOAD'}},
        {dataset: {search: 'Camera 2 upload', state: 'FAILED', queue: 'UPLOAD'}},
        {dataset: {search: 'Camera 1 generation', state: 'SUCCESS', queue: 'VIDEO'}},
    ];
    records.forEach(row => { row.hasAttribute = () => true; });
    const placeholder = {hasAttribute: () => false, remove() { this.removed = true; }};
    const inputs = Object.fromEntries(['search','state','queue'].map(id => [id,
        {value: '', handlers: {}, addEventListener(name, fn) { this.handlers[name] = fn; }}]));
    const count = {};
    const forms = [];
    const config = {table: 'records', rowAttribute: 'data-search', count: 'count',
        countSuffix: ' shown', csrfToken: 'test-csrf', exportUrl: '/operations/export',
        emptyMessage: 'No records', filters: [
            {id: 'search', attribute: 'search', contains: true},
            {id: 'state', attribute: 'state'}, {id: 'queue', attribute: 'queue'},
        ]};
    let options, predicate = () => true, onDraw;
    const visible = () => records.filter((_row, index) => predicate('', [], index));
    const api = {
        row: index => ({node: () => records[index]}),
        rows: options => { assert.equal(options.search, 'applied'); return {count: () => visible().length}; },
        search: {fixed: (_name, fn) => { predicate = fn; }},
        on: (_event, fn) => { onDraw = fn; },
        draw: () => onDraw(),
        buttons: {exportData: options => {
            assert.equal(options.columns, ':not(:last-child)');
            return {header: ['Record'], body: visible().map(row => [row.dataset.search])};
        }},
    };
    const document = {
        getElementById: id => id === 'hybrid-operations-table-config' ? {textContent: JSON.stringify(config)}
            : id === 'records' ? {querySelectorAll: () => [...records, placeholder]}
            : id === 'count' ? count : inputs[id],
        body: {appendChild: form => forms.push(form)},
        createElement: tag => tag === 'form' ? {children: [], appendChild(input) { this.children.push(input); },
            submit() { this.submitted = true; }, remove() { this.removed = true; }} : {},
    };
    function DataTable(_element, opts) { options = opts; return api; }
    vm.runInNewContext(source, {document, DataTable});
    return {records, inputs, count, forms, options, api, placeholder,
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
assert.equal(app.options.buttons[0].extend, 'copyHtml5');
assert.equal(app.options.buttons[0].exportOptions.escapeExcelFormula, true);
console.log('Operations table controller: combined filters, counts, reset, empty rows, filtered export payload/CSRF and native attachment forms: PASS');
