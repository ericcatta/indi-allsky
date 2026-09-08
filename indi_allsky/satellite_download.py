"""Refresh shared satellite catalogs without discarding the last usable group."""
import logging
import socket
import ssl

import requests
import urllib3.exceptions
from sqlalchemy.exc import SQLAlchemyError

from . import constants
from .flask import db
from .flask.models import IndiAllSkyDbTleDataTable


logger = logging.getLogger('indi_allsky')


class SatelliteUpdateFailure(ValueError):
    """A provider response cannot safely replace the saved catalog."""


class IndiAllskyUpdateSatelliteData(object):
    tle_urls = {
        constants.SATELLITE_VISUAL: 'https://celestrak.org/NORAD/elements/gp.php?GROUP=visual&FORMAT=tle',
        constants.SATELLITE_STARLINK: 'https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle',
        constants.SATELLITE_STATIONS: 'https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=tle',
    }
    group_names = {
        constants.SATELLITE_VISUAL: 'visual',
        constants.SATELLITE_STARLINK: 'starlink',
        constants.SATELLITE_STATIONS: 'stations',
    }

    def __init__(self, config):
        self.config = config

    def update(self):
        result = {'updated': [], 'failed': [], 'groups': []}
        for group, url in self.tle_urls.items():
            name = self.group_names[group]
            row = {'group': group, 'name': name}
            try:
                count = self.import_entries(group, self.download_tle(url))
            except SatelliteUpdateFailure as error:
                row.update(status='failed', reason=str(error))
            except (requests.exceptions.RequestException, socket.gaierror, socket.timeout,
                    ssl.SSLCertVerificationError, urllib3.exceptions.ReadTimeoutError):
                row.update(status='failed', reason='Network or TLS failure')
            except SQLAlchemyError:
                row.update(status='failed', reason='Database update failed')
            else:
                row.update(status='updated', entries=count)
            result['groups'].append(row)
            if row['status'] == 'updated':
                result['updated'].append(name)
            else:
                result['failed'].append(name)
                logger.error('Satellite group %s: %s; previous catalog retained', name, row['reason'])
        return result

    def import_entries(self, group, tle_data):
        # Validate the complete response before starting replacement. Empty,
        # truncated or malformed HTTP-200 responses are not an empty catalog.
        if not isinstance(tle_data, str) or not tle_data.strip():
            raise SatelliteUpdateFailure('Empty TLE response')
        lines = tle_data.splitlines()
        if len(lines) % 3:
            raise SatelliteUpdateFailure('Incomplete TLE record')
        entries = []
        for index in range(0, len(lines), 3):
            title, line1, line2 = lines[index:index + 3]
            if (not title.strip() or len(title) > 24 or len(line1) != 69 or len(line2) != 69
                    or not line1.startswith('1 ') or not line2.startswith('2 ')
                    or line1[2:7] != line2[2:7]):
                raise SatelliteUpdateFailure('Malformed TLE record')
            entries.append({'title': title.strip().upper(), 'line1': line1.strip(),
                            'line2': line2.strip(), 'group': group})
        # Delete and insert belong to one transaction. Failed insertion/commit
        # rolls back this group while earlier successful groups remain committed.
        try:
            IndiAllSkyDbTleDataTable.query.filter(IndiAllSkyDbTleDataTable.group == group).delete()
            db.session.bulk_insert_mappings(IndiAllSkyDbTleDataTable, entries)
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            raise
        logger.warning('Updated %d satellites in group %s', len(entries), self.group_names[group])
        return len(entries)

    def download_tle(self, url):
        logger.warning('Downloading %s', url)
        response = requests.get(url, allow_redirects=True, verify=True, timeout=(15.0, 30.0))
        try:
            if response.status_code >= 400:
                raise SatelliteUpdateFailure('HTTP {0}'.format(response.status_code))
            return response.text
        finally:
            response.close()
