"""Explicit Hybrid/shared asset ownership for isolated route acceptance."""
SHARED_FILES = frozenset({
    'images/favicon_32.png', 'images/favicon_128.png',
    'bootstrap/bootstrap.min.css', 'bootstrap/bootstrap.bundle.min.js',
    'js/jquery-3.7.1.min.js', 'js/chart.umd.js', 'js/clipboard.min.js',
    'DataTables/datatables.min.css', 'DataTables/datatables.min.js',
    'html2canvas/html2canvas.min.js',
})


def check_asset(filename):
    assert isinstance(filename, str) and '..' not in filename.split('/'), 'Invalid asset path'
    assert filename in SHARED_FILES or filename.startswith(('modern_admin/', 'virtualsky/')), \
        'Hybrid requested a Classic or unclassified asset: ' + filename


def protect_assets(app):
    @app.url_defaults
    def check_static_url(endpoint, values):
        if endpoint == 'indi_allsky.static':
            check_asset(values.get('filename'))
