(function () {
    'use strict';
    const configNode = document.getElementById('hybrid-operations-table-config');
    if (!configNode || typeof DataTable === 'undefined') return;
    const config = JSON.parse(configNode.textContent);
    const element = document.getElementById(config.table);
    // DataTables supplies an accessible empty state; colspan placeholder rows
    // cannot be treated as data records.
    element.querySelectorAll('tbody tr').forEach(row => {
        if (!row.hasAttribute(config.rowAttribute)) row.remove();
    });
    const filters = config.filters.map(filter => ({
        ...filter, element: document.getElementById(filter.id),
    }));
    const table = new DataTable(element, {
        pageLength: 20,
        lengthMenu: [20, 50, 100, -1],
        order: [[1, 'desc']],
        layout: {topStart: 'pageLength', topEnd: 'buttons'},
        buttons: [
            {extend: 'copyHtml5', exportOptions: {columns: ':not(:last-child)', escapeExcelFormula: true}},
            ...['csv', 'xlsx'].map(format => ({
                text: format === 'csv' ? 'CSV' : 'Excel',
                action: function (_event, table) {
                    const data = table.buttons.exportData({columns: ':not(:last-child)'});
                    const form = document.createElement('form');
                    form.method = 'post';
                    form.action = config.exportUrl;
                    form.hidden = true;
                    const values = {csrf_token: config.csrfToken, format,
                        table: JSON.stringify({header: data.header, body: data.body})};
                    Object.entries(values).forEach(([name, value]) => {
                        const input = document.createElement('input');
                        input.type = 'hidden'; input.name = name; input.value = value;
                        form.appendChild(input);
                    });
                    document.body.appendChild(form);
                    form.submit();
                    form.remove();
                },
            })),
        ],
        language: {emptyTable: config.emptyMessage, zeroRecords: 'No records match the current filters.'},
        columnDefs: [{targets: -1, orderable: false}],
    });
    function normalize(value) { return String(value || '').trim().toLowerCase(); }
    table.search.fixed('hybrid-filters', (_text, _data, index) => {
        const row = table.row(index).node();
        return filters.every(filter => {
            const value = normalize(filter.element.value);
            const actual = normalize(row.dataset[filter.attribute]);
            return !value || (filter.contains ? actual.includes(value) : actual === value);
        });
    });
    const count = document.getElementById(config.count);
    function updateCount() {
        count.textContent = table.rows({search: 'applied'}).count() + (config.countSuffix || '');
    }
    table.on('draw', updateCount);
    filters.forEach(filter => {
        filter.element.addEventListener('input', () => table.draw());
        filter.element.addEventListener('change', () => table.draw());
    });
    table.draw();
})();
