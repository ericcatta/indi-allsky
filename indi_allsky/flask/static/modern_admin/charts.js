(() => {
    'use strict';
    const root = document.getElementById('chart-tool');
    const history = document.getElementById('HISTORY_SELECT');
    const message = document.getElementById('modern-admin-chart-message');
    const colors = ['#9fc2ff', '#f4f1eb', '#9bd7b2', '#e7c87c', '#c2a4ed', '#ed9b9b'];
    const charts = [...root.querySelectorAll('canvas[data-key]')].map((canvas, index) => {
        const histogram = canvas.dataset.key === 'histogram';
        const keys = histogram ? ['red', 'green', 'blue', 'gray'] : [canvas.dataset.key];
        const chart = new Chart(canvas, {
            type: 'line',
            data: {datasets: keys.map((key, channel) => ({
                label: histogram ? key : canvas.dataset.label, data: [],
                borderColor: histogram ? ['#ed7777', '#7ccc96', '#82acff', '#bfc4cd'][channel] : colors[index % colors.length],
                pointRadius: histogram ? 0 : 2, tension: histogram ? 0 : 0.15
            }))},
            options: {animation: false, maintainAspectRatio: false,
                plugins: {legend: {labels: {color: '#a9b0ba'}}},
                scales: {x: {type: histogram ? 'linear' : 'category', ticks: {color: '#777f8b'}},
                         y: {ticks: {color: '#777f8b'}}}}
        });
        return {chart, keys, histogram, status: canvas.closest('article').querySelector('.chart-series-status')};
    });
    let active = null, generation = 0;
    function points(value) {
        if (!Array.isArray(value)) throw new Error('invalid_series');
        if (!value.every(point => point && ['string', 'number'].includes(typeof point.x)
            && (point.y === null || (typeof point.y === 'number' && Number.isFinite(point.y))))) {
            throw new Error('invalid_point');
        }
        return value;
    }
    async function load(force = false) {
        if (active && !force) return;
        if (active) active.abort();
        const controller = new AbortController();
        active = controller;
        const current = ++generation;
        message.textContent = 'Loading chart data...';
        try {
            const query = new URLSearchParams({camera_id: root.dataset.camera,
                limit_s: history.value || '900', timestamp: root.dataset.timestamp});
            const response = await fetch(root.dataset.url + '?' + query, {signal: controller.signal});
            if (response.redirected) throw new Error('session_expired');
            if (!response.ok) throw new Error('request_failed');
            const data = await response.json();
            if (!data || !data.chart_data || typeof data.chart_data !== 'object') throw new Error('invalid_response');
            // Validate the complete response before replacing any displayed series.
            const updates = charts.map(item => item.keys.map(key => points(
                item.histogram ? data.chart_data.histogram?.[key] : data.chart_data[key])));
            if (current !== generation) return;
            charts.forEach((item, index) => {
                updates[index].forEach((values, series) => {item.chart.data.datasets[series].data = values;});
                item.chart.update();
                const hasReadings = updates[index].some(values => values.some(point => point.y !== null));
                item.status.textContent = hasReadings ? '' : 'No readings in the selected range.';
            });
            message.textContent = data.message || 'Charts updated.';
        } catch (error) {
            if (current !== generation || error.name === 'AbortError') return;
            message.textContent = error.message === 'session_expired'
                ? 'Session expired. Sign in and reload this page.'
                : 'Could not load charts. Previously displayed values may be out of date.';
        } finally {
            if (current === generation) active = null;
        }
    }
    history.addEventListener('change', () => load(true));
    load();
    const timer = window.setInterval(() => load(), Math.max(1000, Number(root.dataset.refresh) || 15000));
    window.addEventListener('pagehide', () => {window.clearInterval(timer); if (active) active.abort();});
})();
