
import time
from datetime import datetime
from datetime import timedelta  # noqa: F401
from collections import OrderedDict
import socket
import ssl
import urllib3.exceptions
import requests
import logging

from . import constants

from .flask import db


logger = logging.getLogger('indi_allsky')


class IndiAllskySmokeUpdate(object):

    hms_kml_base_url = 'https://satepsanone.nesdis.noaa.gov/pub/FIRE/web/HMS/Smoke_Polygons/KML/{now:%Y}/{now:%m}/hms_smoke{now:%Y}{now:%m}{now:%d}.kml'


    # folder name, rating
    hms_kml_folders = OrderedDict({
        # check from heavy to light, in order
        'Smoke (Heavy)'  : constants.SMOKE_RATING_HEAVY,
        'Smoke (Medium)' : constants.SMOKE_RATING_MEDIUM,
        'Smoke (Light)'  : constants.SMOKE_RATING_LIGHT,
    })


    def __init__(self, config):
        self.config = config

        self.hms_kml_data = None


    def update(self, camera):
        latitude = camera.latitude
        longitude = camera.longitude


        if camera.data:
            camera_data = dict(camera.data)
        else:
            camera_data = dict()


        if latitude > 0 and longitude < 0:
            # HMS data is only good for north western hemisphere
            try:
                smoke_rating = self.update_na_hms(camera)
            except NoSmokeData as e:
                # Leave previous values in place
                logger.error('No smoke data: %s', str(e))
                result = {'state': 'unavailable', 'reason': str(e)[:160], 'attempted_at': int(time.time())}
                camera_data['SMOKE_UPDATE_STATUS'] = result
                camera.data = camera_data
                db.session.commit()
                return result

        else:
            # all other regions report no data
            smoke_rating = constants.SMOKE_RATING_NODATA


        if smoke_rating:
            logger.info('Smoke rating: %s', constants.SMOKE_RATING_MAP_STR[smoke_rating])

            result = {'state': 'not_covered' if smoke_rating == constants.SMOKE_RATING_NODATA else 'available',
                      'attempted_at': int(time.time())}
            camera_data['SMOKE_UPDATE_STATUS'] = result
            camera_data['SMOKE_RATING'] = smoke_rating
            camera_data['SMOKE_DATA_TS'] = int(time.time())
            camera.data = camera_data
            db.session.commit()
            return result
        else:
            raise NoSmokeData('Smoke rating unavailable')


    def update_na_hms(self, camera):
        # this pulls data from NOAA Hazard Mapping System
        # https://www.ospo.noaa.gov/Products/land/hms.html
        from lxml import etree
        import shapely

        now = datetime.now()
        #now = datetime.now() - timedelta(days=1)  # testing

        hms_kml_url = self.hms_kml_base_url.format(**{'now' : now})


        # allow data to be reused
        if not self.hms_kml_data:
            try:
                self.hms_kml_data = self.download_kml(hms_kml_url)
            except socket.gaierror as e:
                logger.error('Name resolution error: %s', str(e))
                self.hms_kml_data = None
            except socket.timeout as e:
                logger.error('Timeout error: %s', str(e))
                self.hms_kml_data = None
            except requests.exceptions.ConnectTimeout as e:
                logger.error('Connection timeout: %s', str(e))
                self.hms_kml_data = None
            except requests.exceptions.ConnectionError as e:
                logger.error('Connection error: %s', str(e))
                self.hms_kml_data = None
            except requests.exceptions.ReadTimeout as e:
                logger.error('Connection error: %s', str(e))
                self.hms_kml_data = None
            except urllib3.exceptions.ReadTimeoutError as e:
                logger.error('Connection error: %s', str(e))
                self.hms_kml_data = None
            except ssl.SSLCertVerificationError as e:
                logger.error('Certificate error: %s', str(e))
                self.hms_kml_data = None
            except requests.exceptions.SSLError as e:
                logger.error('Certificate error: %s', str(e))
                self.hms_kml_data = None
            except requests.exceptions.RequestException as e:
                logger.error('Smoke download error: %s', str(e))
                self.hms_kml_data = None


        if isinstance(self.hms_kml_data, type(None)):
            raise NoSmokeData('No KML data')


        latitude = camera.latitude
        longitude = camera.longitude


        try:
            xml_root = etree.fromstring(self.hms_kml_data, parser=etree.XMLParser(resolve_entities=False, no_network=True))
        except etree.XMLSyntaxError as e:
            self.hms_kml_data = None  # force redownload
            raise NoSmokeData('Unable to parse XML: {0:s}'.format(str(e)))
        except ValueError as e:
            self.hms_kml_data = None  # force redownload
            raise NoSmokeData('Unable to parse XML: {0:s}'.format(str(e)))


        # look for a 1 square degree area (smoke within ~35 miles)
        location_area = shapely.Polygon((
            (float(longitude) - 0.5, float(latitude) - 0.5),
            (float(longitude) + 0.5, float(latitude) - 0.5),
            (float(longitude) + 0.5, float(latitude) + 0.5),
            (float(longitude) - 0.5, float(latitude) + 0.5),
        ))



        NS = {
            "kml" : "http://www.opengis.net/kml/2.2",
        }


        found_kml_folders = False
        for folder, rating in self.hms_kml_folders.items():
            p = ".//kml:Folder[contains(., '{0:s}')]".format(folder)
            #logger.info('Folder: %s', p)
            e_folder = xml_root.xpath(p, namespaces=NS)


            if not e_folder:
                logger.error('Folder not found: %s', folder)
                continue

            found_kml_folders = True


            for e_placemark in e_folder[0].xpath('.//kml:Placemark', namespaces=NS):
                for e_polygon in e_placemark.xpath('.//kml:Polygon', namespaces=NS):
                    e_coord = e_polygon.find(".//kml:coordinates", namespaces=NS)
                    if e_coord is None or not e_coord.text:
                        raise NoSmokeData('Missing polygon coordinates')

                    coord_list = list()
                    for line in e_coord.text.splitlines():
                        line = line.strip()

                        if not line:
                            continue

                        #logger.info('line: %s', pformat(line))
                        try:
                            p_long, p_lat, p_z = line.split(',')
                            coord_list.append((float(p_long), float(p_lat)))
                        except (TypeError, ValueError):
                            raise NoSmokeData('Invalid polygon coordinates')

                    try:
                        smoke_polygon = shapely.Polygon(coord_list)
                    except (ValueError, shapely.errors.GEOSException):
                        raise NoSmokeData('Invalid smoke polygon')
                    if smoke_polygon.is_empty or not smoke_polygon.is_valid:
                        raise NoSmokeData('Invalid smoke polygon')

                    if location_area.intersects(smoke_polygon):
                        # first match wins
                        return rating


        if not found_kml_folders:
            # without folders, there was no data to match
            raise NoSmokeData('No folders in KML')


        return constants.SMOKE_RATING_CLEAR  # no matches should mean clear



    def download_kml(self, url):
        logger.warning('Downloading %s', url)
        r = requests.get(url, allow_redirects=True, verify=True, timeout=(15.0, 30.0))

        try:
            if r.status_code >= 400:
                raise NoSmokeData('HTTP {0}'.format(r.status_code))
            return r.text.encode()
        finally:
            r.close()


class NoSmokeData(Exception):
    pass

