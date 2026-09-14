(function () {
    'use strict';
    const configNode = document.getElementById('hybrid-operations-table-config');
    if (!configNode || typeof DataTable === 'undefined') return;
    const config = JSON.parse(configNode.textContent);
    const exportColumns = config.exportColumns || ':not(:last-child)';
    const element = document.getElementById(config.table);
    // DataTables supplies an accessible empty state; colspan placeholder rows
    // cannot be treated as data records.
    element.querySelectorAll('tbody tr').forEach(row => {
        if (!row.hasAttribute(config.rowAttribute)) row.remove();
    });
    const filters = config.filters.map(filter => ({
        ...filter, element: document.getElementById(filter.id),
    }));
    let copyPanel;
    async function copyRecords(_event, api) {
        const data = api.buttons.exportData({columns: exportColumns, escapeExcelFormula: true});
        const text = [data.header, ...data.body].map(row => row.join('\t')).join('\n');
        if (!copyPanel) {
            const panel = document.createElement('div');
            const status = document.createElement('p');
            status.setAttribute('role', 'status');
            const fallback = document.createElement('textarea');
            fallback.setAttribute('aria-label', 'Table data to copy');
            fallback.readOnly = true;
            fallback.rows = 6;
            fallback.style.width = '100%';
            panel.appendChild(status);
            panel.appendChild(fallback);
            document.getElementById(config.count).after(panel);
            copyPanel = {status, fallback};
        }
        copyPanel.fallback.hidden = true;
        copyPanel.status.textContent = 'Copying filtered records…';
        try {
            await navigator.clipboard.writeText(text);
            copyPanel.status.textContent = `Copied ${data.body.length} ${data.body.length === 1 ? 'record' : 'records'}.`;
        } catch (_) {
            copyPanel.fallback.value = text;
            copyPanel.fallback.hidden = false;
            copyPanel.status.textContent = 'Automatic copy is unavailable. Press Ctrl+C or Command+C to copy the selected records.';
            copyPanel.fallback.focus();
            copyPanel.fallback.select();
        }
    }
    const table = new DataTable(element, {
        paging: config.paging !== false,
        lengthChange: config.paging !== false,
        pageLength: 20,
        lengthMenu: [20, 50, 100, -1],
        order: config.order || [[1, 'desc']],
        layout: {topStart: config.paging === false ? null : 'pageLength', topEnd: 'buttons'},
        buttons: [
            {text: 'Copy', action: copyRecords},
            ...['csv', 'xlsx'].map(format => ({
                text: format === 'csv' ? 'CSV' : 'Excel',
                action: function (_event, table) {
                    const data = table.buttons.exportData({columns: exportColumns});
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
        columnDefs: config.columnDefs || [{targets: -1, orderable: false}],
    });
    function normalize(value) { return String(value || '').trim().toLowerCase(); }
    table.search.fixed('hybrid-filters', (_text, _data, index) => {
        const row = table.row(index).node();
        return filters.every(filter => {
            const value = normalize(filter.element.value);
            const actual = normalize(filter.text ? row.textContent : row.dataset[filter.attribute]);
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
