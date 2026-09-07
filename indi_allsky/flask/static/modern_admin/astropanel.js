(() => {
    'use strict';
    const root = document.getElementById('astropanel-tool');
    const status = document.getElementById('astropanel-status');
    const refresh = document.getElementById('astropanel-refresh');
    const fields = [...root.querySelectorAll('[data-astro-field]')];
    const planets = ['mercury', 'venus', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune'];
    const node = name => document.getElementById('modern-admin-' + name);
    const scalarValue = value => Array.isArray(value) && value.length === 1 ? value[0] : value;
    const display = (input, unit = '') => { const value = scalarValue(input); return value == null || value === '' ? 'Unavailable' : String(value) + unit; };
    let active = null, loaded = false;
    function row(values) {
        const result = document.createElement('tr');
        values.forEach(value => {
            const cell = document.createElement('td');
            cell.textContent = display(value);
            result.appendChild(cell);
        });
        return result;
    }
    function emptyRow(text, columns) {
        const result = row([text]); result.firstChild.colSpan = columns; return result;
    }
    function validate(data) {
        if (!data || typeof data !== 'object' || Array.isArray(data) || !Array.isArray(data.satellite_list)) throw Error('invalid_response');
        const keys = ['moon_phase','moon_light','moon_rise','moon_set','sun_alt','sun_rise','sun_set','polaris_hour_angle','polaris_alt',
            ...fields.map(field => field.dataset.astroField),
            ...planets.flatMap(planet => ['rise','transit','set','alt','az'].map(key => planet + '_' + key))];
        const scalar = value => value === null || typeof value === 'string' || (typeof value === 'number' && Number.isFinite(value));
        if (!keys.every(key => Object.hasOwn(data, key) && scalar(data[key]))) throw Error('invalid_response');
        if (!data.satellite_list.every(satellite => satellite && ['name','alt','az','rise','transit','set','duration','elevation']
            .every(key => Object.hasOwn(satellite, key) && scalar(scalarValue(satellite[key]))))) throw Error('invalid_satellites');
    }
    async function load() {
        if (active) return;
        const controller = new AbortController(); active = controller;
        refresh.disabled = true; status.textContent = 'Loading astropanel data...';
        try {
            const response = await fetch(root.dataset.url + '?' + new URLSearchParams({camera_id:root.dataset.camera}), {signal:controller.signal});
            if (response.redirected) throw Error('session_expired');
            if (!response.ok) throw Error('request_failed');
            const data = await response.json(); validate(data);
            const planetRows = planets.map(planet => row([planet.charAt(0).toUpperCase() + planet.slice(1),
                data[planet+'_rise'], data[planet+'_transit'], data[planet+'_set'], display(data[planet+'_alt'],' deg'), display(data[planet+'_az'],' deg')]));
            const satelliteRows = data.satellite_list.map(satellite => row([satellite.name,display(satellite.alt,' deg'),
                display(satellite.az,' deg'),satellite.rise,satellite.transit,satellite.set,satellite.duration,satellite.elevation]));
            node('moon-phase').textContent = display(data.moon_phase) + ' (' + display(data.moon_light, '%') + ')';
            node('moon-times').textContent = 'Rise ' + display(data.moon_rise) + ' · Set ' + display(data.moon_set);
            node('sun-alt').textContent = display(data.sun_alt, ' deg');
            node('sun-times').textContent = 'Rise ' + display(data.sun_rise) + ' · Set ' + display(data.sun_set);
            node('polaris-ha').textContent = display(data.polaris_hour_angle, ' deg hour angle');
            node('polaris-alt').textContent = 'Altitude ' + display(data.polaris_alt, ' deg');
            fields.forEach(field => {field.textContent = display(data[field.dataset.astroField]);});
            node('planet-rows').replaceChildren(...planetRows);
            node('satellite-rows').replaceChildren(...(satelliteRows.length ? satelliteRows : [emptyRow('No satellite data available.', 8)]));
            loaded = true; status.textContent = 'Updated ' + new Date().toLocaleTimeString() + ' · refreshes every minute.';
        } catch (error) {
            if (error.name === 'AbortError') return;
            if (!loaded) {
                ['moon-phase','moon-times','sun-alt','sun-times','polaris-ha','polaris-alt'].forEach(key => {node(key).textContent = 'Unavailable';});
                fields.forEach(field => {field.textContent = 'Unavailable';});
                node('planet-rows').replaceChildren(emptyRow('Astropanel data unavailable.', 6));
                node('satellite-rows').replaceChildren(emptyRow('Satellite data unavailable.', 8));
            }
            status.textContent = (error.message === 'session_expired' ? 'Session expired. Sign in and reload this page.' : 'Could not update astropanel. Try Refresh.')
                + (loaded ? ' Displayed values are from the last successful update and may be out of date.' : '');
        } finally { active = null; refresh.disabled = false; }
    }
    refresh.addEventListener('click', load);
    const timer = window.setInterval(load, 60000);
    window.addEventListener('pagehide', () => {window.clearInterval(timer); if (active) active.abort();});
    load();
})();
