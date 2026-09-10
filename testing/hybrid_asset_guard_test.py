#!/usr/bin/env python3
"""Hybrid asset guard allows shared libraries, rejects Classic and traversal."""
from hybrid_asset_guard import SHARED_FILES, check_asset


def run():
    for path in SHARED_FILES | {'modern_admin/navigation.js', 'virtualsky/stars.json'}:
        check_asset(path)
    for path in ('css/style.css', 'js/indi-allsky-tabs.js', 'images/logo_outline_full.png',
                 'modern_admin/../js/indi-allsky-tabs.js', '/modern_admin/navigation.js', None):
        try:
            check_asset(path)
        except AssertionError:
            pass
        else:
            raise AssertionError('Unclassified asset was accepted: ' + str(path))
    print('Hybrid asset guard: shared dependencies allowed; Classic and traversal rejected: PASS')


if __name__ == '__main__':
    run()
