"""Shared public ephemeris endpoint, independent of frontend page views."""
from datetime import datetime, timezone
import math
import ephem
from flask import current_app as app, jsonify, request
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.exc import NoResultFound
from . import db
from .base_views import BaseView
from .models import IndiAllSkyDbCameraTable, IndiAllSkyDbTleDataTable
from .. import constants


class AjaxAstroPanelView(BaseView):
    """
    Copyright(c) 2019 Radek Kaczorek  <rkaczorek AT gmail DOT com>

    Ported from https://github.com/rkaczorek/astropanel.git
    """

    methods = ['GET', 'POST']


    def dispatch_request(self):
        if request.method != 'GET':
            return jsonify({}), 400
        try:
            camera_id = int(request.args.get('camera_id', ''))
            if not 0 < camera_id <= 9223372036854775807:
                raise ValueError
        except (TypeError, ValueError):
            return jsonify(message='A valid camera_id is required.'), 400
        try:
            return self.get(camera_id)
        except NoResultFound:
            return jsonify(message='Camera not found.'), 404
        except SQLAlchemyError:
            db.session.rollback()
            app.logger.exception('Astropanel data could not be read')
            return jsonify(message='Astropanel data is temporarily unavailable.'), 503


    def get(self, camera_id):
        camera = IndiAllSkyDbCameraTable.query\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .one()


        satellites_visual = IndiAllSkyDbTleDataTable.query\
            .filter(IndiAllSkyDbTleDataTable.group == constants.SATELLITE_VISUAL)\
            .order_by(IndiAllSkyDbTleDataTable.title)\


        # init observer
        obs = ephem.Observer()

        # set geo position
        obs.lat = math.radians(camera.latitude)
        obs.lon = math.radians(camera.longitude)
        obs.elevation = camera.elevation

        # disable atmospheric refraction calcs
        obs.pressure = 0

        # update time
        utcnow = datetime.now(tz=timezone.utc)

        obs.date = utcnow

        sun = ephem.Sun()
        mercury = ephem.Mercury()
        venus = ephem.Venus()
        moon = ephem.Moon()
        mars = ephem.Mars()
        jupiter = ephem.Jupiter()
        saturn = ephem.Saturn()
        uranus = ephem.Uranus()
        neptune = ephem.Neptune()

        polaris_data = self.astropanel_get_polaris_data(obs)

        sun_position = self.astropanel_get_body_positions(obs, sun)
        sun_twilights = self.astropanel_get_sun_twilights(obs, sun)
        mercury_position = self.astropanel_get_body_positions(obs, mercury)
        venus_position = self.astropanel_get_body_positions(obs, venus)
        moon_position = self.astropanel_get_body_positions(obs, moon)
        mars_position = self.astropanel_get_body_positions(obs, mars)
        jupiter_position = self.astropanel_get_body_positions(obs, jupiter)
        saturn_position = self.astropanel_get_body_positions(obs, saturn)
        uranus_position = self.astropanel_get_body_positions(obs, uranus)
        neptune_position = self.astropanel_get_body_positions(obs, neptune)


        obs.date = utcnow
        sun.compute(obs)
        mercury.compute(obs)
        venus.compute(obs)
        moon.compute(obs)
        mars.compute(obs)
        jupiter.compute(obs)
        saturn.compute(obs)
        uranus.compute(obs)
        neptune.compute(obs)


        satellite_list = list()
        satellite_errors = list()
        for sat_entry in satellites_visual:
            try:
                sat = ephem.readtle(sat_entry.title, sat_entry.line1, sat_entry.line2)
            except ValueError as e:
                app.logger.error('Satellite TLE data error: %s', str(e))
                satellite_errors.append({'name': str(sat_entry.title), 'reason': 'Invalid orbital data'})
                continue

            try:
                sat.compute(obs)
            except ValueError as e:
                app.logger.error('Satellite computation error: %s', str(e))
                satellite_errors.append({'name': str(sat_entry.title), 'reason': 'Orbital data unavailable for this date'})
                continue

            try:
                # all next_pass() values can be None
                next_pass = obs.next_pass(sat)
            except ValueError as e:
                app.logger.error('Next pass error: %s', str(e))
                satellite_errors.append({'name': str(sat_entry.title), 'reason': 'Pass prediction unavailable'})
                continue


            sat_data = {
                'name'      : str(sat_entry.title).upper(),
                'az'        : round(math.degrees(sat.az), 2),
                'alt'       : round(math.degrees(sat.alt), 2),
                'elevation' : int(sat.elevation / 1000),
                'eclipsed'  : sat.eclipsed,
            }


            if not isinstance(next_pass[0], type(None)) and not isinstance(next_pass[4], type(None)):
                sat_data['rise'] = '{0:%Y-%m-%d %H:%M:%S}'.format(ephem.localtime(next_pass[0])),
                sat_data['duration'] = '{0:d}'.format((ephem.localtime(next_pass[4]) - ephem.localtime(next_pass[0])).seconds),
            else:
                sat_data['rise'] = 'None'
                sat_data['duration'] = 'None'


            if not isinstance(next_pass[2], type(None)):
                sat_data['transit'] = '{0:%Y-%m-%d %H:%M:%S}'.format(ephem.localtime(next_pass[2])),
            else:
                sat_data['transit'] = 'None'

            if not isinstance(next_pass[4], type(None)):
                sat_data['set'] = '{0:%Y-%m-%d %H:%M:%S}'.format(ephem.localtime(next_pass[4])),
            else:
                sat_data['set'] = 'None'


            satellite_list.append(sat_data)


        # sort by altitude
        satellite_list = sorted(satellite_list, key=lambda x: x['alt'], reverse=True)


        data = {
            'latitude'              : round(obs.lat, 2),
            'longitude'             : round(obs.lon, 2),
            'elevation'             : int(obs.elevation),
            'polaris_hour_angle'    : round(polaris_data[0], 5),
            'polaris_next_transit'  : '{0:s}'.format(polaris_data[1]),
            'polaris_alt'           : round(math.degrees(polaris_data[2]), 2),
            'moon_phase'            : self.astropanel_get_moon_phase(obs),
            'moon_light'            : int(moon.phase),
            'moon_rise'             : '{0:s}'.format(moon_position[0]),
            'moon_transit'          : '{0:s}'.format(moon_position[1]),
            'moon_set'              : '{0:s}'.format(moon_position[2]),
            'moon_az'               : round(math.degrees(moon.az), 2),
            'moon_alt'              : round(math.degrees(moon.alt), 2),
            'moon_ra'               : '{0:s}'.format(str(moon.ra)),
            'moon_dec'              : '{0:s}'.format(str(moon.dec)),
            'moon_new'              : '{0:%Y-%m-%d %H:%M:%S}'.format(ephem.localtime(ephem.next_new_moon(utcnow))),
            'moon_full'             : '{0:%Y-%m-%d %H:%M:%S}'.format(ephem.localtime(ephem.next_full_moon(utcnow))),
            'sun_at_start'          : sun_twilights[2][0],
            'sun_ct_start'          : sun_twilights[0][0],
            'sun_rise'              : '{0:s}'.format(sun_position[0]),
            'sun_transit'           : '{0:s}'.format(sun_position[1]),
            'sun_set'               : '{0:s}'.format(sun_position[2]),
            'sun_ct_end'            : sun_twilights[0][1],
            'sun_at_end'            : sun_twilights[2][1],
            'sun_az'                : round(math.degrees(sun.az), 2),
            'sun_alt'               : round(math.degrees(sun.alt), 2),
            'sun_ra'                : '{0:s}'.format(str(sun.ra)),
            'sun_dec'               : '{0:s}'.format(str(sun.dec)),
            'sun_equinox'           : '{0:%Y-%m-%d %H:%M:%S}'.format(ephem.localtime(ephem.next_equinox(utcnow))),
            'sun_solstice'          : '{0:%Y-%m-%d %H:%M:%S}'.format(ephem.localtime(ephem.next_solstice(utcnow))),
            'mercury_rise'          : '{0:s}'.format(mercury_position[0]),
            'mercury_transit'       : '{0:s}'.format(mercury_position[1]),
            'mercury_set'           : '{0:s}'.format(mercury_position[2]),
            'mercury_az'            : round(math.degrees(mercury.az), 2),
            'mercury_alt'           : round(math.degrees(mercury.alt), 2),
            'venus_rise'            : '{0:s}'.format(venus_position[0]),
            'venus_transit'         : '{0:s}'.format(venus_position[1]),
            'venus_set'             : '{0:s}'.format(venus_position[2]),
            'venus_az'              : round(math.degrees(venus.az), 2),
            'venus_alt'             : round(math.degrees(venus.alt), 2),
            'mars_rise'             : '{0:s}'.format(mars_position[0]),
            'mars_transit'          : '{0:s}'.format(mars_position[1]),
            'mars_set'              : '{0:s}'.format(mars_position[2]),
            'mars_az'               : round(math.degrees(mars.az), 2),
            'mars_alt'              : round(math.degrees(mars.alt), 2),
            'jupiter_rise'          : '{0:s}'.format(jupiter_position[0]),
            'jupiter_transit'       : '{0:s}'.format(jupiter_position[1]),
            'jupiter_set'           : '{0:s}'.format(jupiter_position[2]),
            'jupiter_az'            : round(math.degrees(jupiter.az), 2),
            'jupiter_alt'           : round(math.degrees(jupiter.alt), 2),
            'saturn_rise'           : '{0:s}'.format(saturn_position[0]),
            'saturn_transit'        : '{0:s}'.format(saturn_position[1]),
            'saturn_set'            : '{0:s}'.format(saturn_position[2]),
            'saturn_az'             : round(math.degrees(saturn.az), 2),
            'saturn_alt'            : round(math.degrees(saturn.alt), 2),
            'uranus_rise'           : '{0:s}'.format(uranus_position[0]),
            'uranus_transit'        : '{0:s}'.format(uranus_position[1]),
            'uranus_set'            : '{0:s}'.format(uranus_position[2]),
            'uranus_az'             : round(math.degrees(uranus.az), 2),
            'uranus_alt'            : round(math.degrees(uranus.alt), 2),
            'neptune_rise'          : '{0:s}'.format(neptune_position[0]),
            'neptune_transit'       : '{0:s}'.format(neptune_position[1]),
            'neptune_set'           : '{0:s}'.format(neptune_position[2]),
            'neptune_az'            : round(math.degrees(neptune.az), 2),
            'neptune_alt'           : round(math.degrees(neptune.alt), 2),
            'satellite_list'        : satellite_list,
            'satellite_errors'      : satellite_errors,
        }

        return jsonify(data)


    def astropanel_get_moon_phase(self, obs):
        target_date_utc = obs.date
        target_date_local = ephem.localtime(target_date_utc).date()
        next_full = ephem.localtime(ephem.next_full_moon(target_date_utc)).date()
        next_new = ephem.localtime(ephem.next_new_moon(target_date_utc)).date()
        next_last_quarter = ephem.localtime(ephem.next_last_quarter_moon(target_date_utc)).date()
        next_first_quarter = ephem.localtime(ephem.next_first_quarter_moon(target_date_utc)).date()
        previous_full = ephem.localtime(ephem.previous_full_moon(target_date_utc)).date()
        previous_new = ephem.localtime(ephem.previous_new_moon(target_date_utc)).date()
        previous_last_quarter = ephem.localtime(ephem.previous_last_quarter_moon(target_date_utc)).date()
        previous_first_quarter = ephem.localtime(ephem.previous_first_quarter_moon(target_date_utc)).date()

        if target_date_local in (next_full, previous_full):
            return 'Full'
        elif target_date_local in (next_new, previous_new):
            return 'New'
        elif target_date_local in (next_first_quarter, previous_first_quarter):
            return 'First Quarter'
        elif target_date_local in (next_last_quarter, previous_last_quarter):
            return 'Last Quarter'
        elif previous_new < next_first_quarter < next_full < next_last_quarter < next_new:
            return 'Waxing Crescent'
        elif previous_first_quarter < next_full < next_last_quarter < next_new < next_first_quarter:
            return 'Waxing Gibbous'
        elif previous_full < next_last_quarter < next_new < next_first_quarter < next_full:
            return 'Waning Gibbous'
        elif previous_last_quarter < next_new < next_first_quarter < next_full < next_last_quarter:
            return 'Waning Crescent'


    def astropanel_get_body_positions(self, obs, body):
        utcnow = datetime.now(tz=timezone.utc)

        obs.date = utcnow
        body.compute(obs)


        positions = []

        # test for always below horizon or always above horizon
        try:
            if ephem.localtime(obs.previous_rising(body)).date() == ephem.localtime(obs.date).date() and obs.previous_rising(body) < obs.previous_transit(body) < obs.previous_setting(body) < obs.date:
                positions.append(obs.previous_rising(body))
                positions.append(obs.previous_transit(body))
                positions.append(obs.previous_setting(body))
            elif ephem.localtime(obs.previous_rising(body)).date() == ephem.localtime(obs.date).date() and obs.previous_rising(body) < obs.previous_transit(body) < obs.date < obs.next_setting(body):
                positions.append(obs.previous_rising(body))
                positions.append(obs.previous_transit(body))
                positions.append(obs.next_setting(body))
            elif ephem.localtime(obs.previous_rising(body)).date() == ephem.localtime(obs.date).date() and obs.previous_rising(body) < obs.date < obs.next_transit(body) < obs.next_setting(body):
                positions.append(obs.previous_rising(body))
                positions.append(obs.next_transit(body))
                positions.append(obs.next_setting(body))
            elif ephem.localtime(obs.previous_rising(body)).date() == ephem.localtime(obs.date).date() and obs.date < obs.next_rising(body) < obs.next_transit(body) < obs.next_setting(body):
                positions.append(obs.next_rising(body))
                positions.append(obs.next_transit(body))
                positions.append(obs.next_setting(body))
            else:
                positions.append(obs.next_rising(body))
                positions.append(obs.next_transit(body))
                positions.append(obs.next_setting(body))
        except (ephem.NeverUpError, ephem.AlwaysUpError):
            try:
                if ephem.localtime(obs.previous_transit(body)).date() == ephem.localtime(obs.date).date() and obs.previous_transit(body) < obs.date:
                    positions.append('-')
                    positions.append(obs.previous_transit(body))
                    positions.append('-')
                elif ephem.localtime(obs.previous_transit(body)).date() == ephem.localtime(obs.date).date() and obs.next_transit(body) > obs.date:
                    positions.append('-')
                    positions.append(obs.next_transit(body))
                    positions.append('-')
                else:
                    positions.append('-')
                    positions.append('-')
                    positions.append('-')
            except (ephem.NeverUpError, ephem.AlwaysUpError):
                positions.append('-')
                positions.append('-')
                positions.append('-')

        if positions[0] != '-':
            positions[0] = ephem.localtime(positions[0]).strftime("%H:%M:%S")
        if positions[1] != '-':
            positions[1] = ephem.localtime(positions[1]).strftime("%H:%M:%S")
        if positions[2] != '-':
            positions[2] = ephem.localtime(positions[2]).strftime("%H:%M:%S")

        return positions


    def astropanel_get_sun_twilights(self, obs, sun):
        results = []

        """
        An observer at the North Pole would see the Sun circle the sky at 23.5° above the horizon all day.
        An observer at 90° – 23.5° = 66.5° would see the Sun spend the whole day on the horizon, making a circle along its circumference.
        An observer would have to be at 90° – 23.5° – 18° = 48.5° latitude or even further south in order for the Sun to dip low enough for them to observe the level of darkness defined as astronomical twilight.

        civil twilight = -6
        nautical twilight = -12
        astronomical twilight = -18

        get_sun_twilights(home)[0][0]    -	civil twilight end
        get_sun_twilights(home)[0][1]    -	civil twilight start

        get_sun_twilights(home)[1][0]    -	nautical twilight end
        get_sun_twilights(home)[1][1]    -	nautical twilight start

        get_sun_twilights(home)[2][0]    -	astronomical twilight end
        get_sun_twilights(home)[2][1]    -	astronomical twilight start
        """

        # remember entry observer horizon
        obs_horizon = obs.horizon

        # Twilights, their horizons and whether to use the centre of the Sun or not
        twilights = [('-6', True), ('-12', True), ('-18', True)]

        for twi in twilights:
            obs.horizon = twi[0]
            try:
                rising_setting = self.astropanel_get_body_positions(obs, sun)
                results.append((rising_setting[0], rising_setting[2]))
            except ephem.AlwaysUpError:
                results.append(('n/a', 'n/a'))

        # reset observer horizon to entry
        obs.horizon = obs_horizon

        return results


    def astropanel_get_polaris_data(self, obs):
        polaris_data = []

        """
        lst = 100.46 + 0.985647 * d + lon + 15 * ut [based on http://www.stargazing.net/kepler/altaz.html]
        d - the days from J2000 (1200 hrs UT on Jan 1st 2000 AD), including the fraction of a day
        lon - your longitude in decimal degrees, East positive
        ut - the universal time in decimal hours
        """

        j2000 = ephem.Date('2000/01/01 12:00:00')
        d = obs.date - j2000

        lon = math.degrees(obs.lon)

        ut_hms = obs.date.datetime().strftime("%H:%M:%S").split(':')
        ut = float(ut_hms[0]) + (float(ut_hms[1]) / 60) + (float(ut_hms[2]) / 3600)


        lst = 100.46 + 0.985647 * d + lon + 15 * ut
        lst = lst - int(lst / 360) * 360

        polaris = ephem.readdb("Polaris,f|M|F7,2:31:48.704,89:15:50.72,2.02,2000")
        polaris.compute()
        polaris_ra_deg = math.degrees(polaris.ra)

        # Polaris Hour Angle = LST - RA Polaris [expressed in degrees or 15*(h+m/60+s/3600)]
        pha = lst - polaris_ra_deg

        # normalize
        if pha < 0:
            pha += 360
        elif pha > 360:
            pha -= 360

        # append polaris hour angle
        polaris_data.append(pha)

        # append polaris next transit
        try:
            polaris_data.append(ephem.localtime(obs.next_transit(polaris)).strftime("%H:%M:%S"))
        except (ephem.NeverUpError, ephem.AlwaysUpError):
            polaris_data.append('-')

        # append polaris alt
        polaris_data.append(polaris.alt)

        return polaris_data

