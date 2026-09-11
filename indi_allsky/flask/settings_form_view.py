"""Hybrid Settings form context and Flask adapters.

Classic may reuse this view while installed; Hybrid never imports Classic to
prepare a form. Camera metadata, OAuth state, network metadata and WTForms
remain in their original evaluation order.
"""
import ipaddress
import socket

import psutil
from cryptography.fernet import InvalidToken
from flask import current_app as app, url_for
from flask_login import login_required
from sqlalchemy.orm.exc import NoResultFound

from .base_views import FormView
from .forms import IndiAllskyConfigForm


class HybridSettingsFormView(FormView):
    page_title = 'Config'
    decorators = [login_required]

    def get_context(self):
        context = super(HybridSettingsFormView, self).get_context()

        context['camera_minGain'] = self.camera.minGain
        context['camera_maxGain'] = self.camera.maxGain
        context['camera_minBinning'] = self.camera.minBinning
        context['camera_maxBinning'] = self.camera.maxBinning
        context['camera_minExposure'] = self.camera.minExposure

        if self.camera.maxExposure > 120:
            context['camera_maxExposure'] = 120
        else:
            context['camera_maxExposure'] = self.camera.maxExposure


        context['config_id'] = self.indi_allsky_config_id


        ### a few checks to start
        fits_enabled = self.indi_allsky_config.get('IMAGE_SAVE_FITS')
        fits_save_period = self.indi_allsky_config.get('IMAGE_SAVE_FITS_PERIOD', 7200)

        if fits_enabled and fits_save_period < 600:
            # Only warn if saving more often than every 10 minutes
            context['fits_enabled'] = fits_enabled


        context['mark_detections_enabled'] = self.indi_allsky_config.get('DETECT_DRAW')


        ### timezone validator
        if not self.validate_longitude_timezone():
            context['longitude_validation_message'] = '<span class="badge rounded-pill bg-warning text-dark">Warning</span><span class="text-warning"> Longitude validation failed.  Incorrect time, timezone, or longitude could cause this condition</span>'
        else:
            context['longitude_validation_message'] = ''


        if self.latest_image_entry:
            dh_level_default = self.indi_allsky_config.get('DEW_HEATER', {}).get('LEVEL_DEF', 0)
            dh_level_low = self.indi_allsky_config.get('DEW_HEATER', {}).get('LEVEL_LOW', 33)
            dh_level_med = self.indi_allsky_config.get('DEW_HEATER', {}).get('LEVEL_MED', 66)
            dh_level_high = self.indi_allsky_config.get('DEW_HEATER', {}).get('LEVEL_HIGH', 100)

            dh_thold_diff_low = self.indi_allsky_config.get('DEW_HEATER', {}).get('THOLD_DIFF_LOW', -15)
            dh_thold_diff_med = self.indi_allsky_config.get('DEW_HEATER', {}).get('THOLD_DIFF_MED', -10)
            dh_thold_diff_high = self.indi_allsky_config.get('DEW_HEATER', {}).get('THOLD_DIFF_HIGH', -5)


            fan_level_default = self.indi_allsky_config.get('FAN', {}).get('LEVEL_DEF', 0)
            fan_level_low = self.indi_allsky_config.get('FAN', {}).get('LEVEL_LOW', 33)
            fan_level_med = self.indi_allsky_config.get('FAN', {}).get('LEVEL_MED', 66)
            fan_level_high = self.indi_allsky_config.get('FAN', {}).get('LEVEL_HIGH', 100)

            fan_thold_diff_low = self.indi_allsky_config.get('FAN', {}).get('THOLD_DIFF_LOW', -10)
            fan_thold_diff_med = self.indi_allsky_config.get('FAN', {}).get('THOLD_DIFF_MED', -5)
            fan_thold_diff_high = self.indi_allsky_config.get('FAN', {}).get('THOLD_DIFF_HIGH', 0)


            dh_temp_slot_var = self.indi_allsky_config.get('DEW_HEATER', {}).get('TEMP_USER_VAR_SLOT', 'sensor_user_10')
            dh_dewpoint_slot_var = self.indi_allsky_config.get('DEW_HEATER', {}).get('DEWPOINT_USER_VAR_SLOT', 'sensor_user_2')

            fan_temp_slot_var = self.indi_allsky_config.get('FAN', {}).get('TEMP_USER_VAR_SLOT', 'sensor_user_10')


            raw_mag = self.latest_image_entry.data.get('camera_sqm_raw_mag', 0.0)
            if raw_mag:
                mag_offset = self.indi_allsky_config.get('CAMERA_SQM', {}).get('MAGNITUDE_OFFSET', 25.0)

                context['camera_sqm_raw_mag_str'] = '{0:0.2f}'.format(raw_mag)
                context['camera_sqm_calc_sqm_str'] = '{0:0.2f}'.format(mag_offset + raw_mag)  # raw_mag is negative
            else:
                context['camera_sqm_raw_mag_str'] = 'Not available'
                context['camera_sqm_calc_sqm_str'] = 'Not available'


            if self.latest_image_entry.data.get(dh_temp_slot_var):
                dh_temp = self.latest_image_entry.data[dh_temp_slot_var]
                context['dh_temp_str'] = '{0:0.1f}°'.format(dh_temp)
            else:
                dh_temp = None
                context['dh_temp_str'] = 'Not available'

            if self.latest_image_entry.data.get(dh_dewpoint_slot_var):
                dh_dewpoint = self.latest_image_entry.data[dh_dewpoint_slot_var]
                context['dh_dewpoint_str'] = '{0:0.1f}°'.format(dh_dewpoint)
            else:
                dh_dewpoint = None
                context['dh_dewpoint_str'] = 'Not available'


            dh_manual_target = self.indi_allsky_config.get('DEW_HEATER', {}).get('MANUAL_TARGET', 0.0)
            if not dh_manual_target:
                if not isinstance(dh_temp, type(None)) and not isinstance(dh_dewpoint, type(None)):
                    dh_temp_delta = dh_temp - dh_dewpoint
                    context['dh_temp_delta_str'] = 'Δ{0:+0.1f}°'.format(dh_temp_delta)

                    dh_target_low = dh_dewpoint + dh_thold_diff_low
                    dh_target_med = dh_dewpoint + dh_thold_diff_med
                    dh_target_high = dh_dewpoint + dh_thold_diff_high
                    context['dh_target_low_str'] = '{0:0.1f}°'.format(dh_target_low)
                    context['dh_target_med_str'] = '{0:0.1f}°'.format(dh_target_med)
                    context['dh_target_high_str'] = '{0:0.1f}°'.format(dh_target_high)


                    if dh_temp_delta <= dh_thold_diff_high:
                        # set dew heater to high
                        context['dh_status_str'] = '{0:d}% (High)'.format(dh_level_high)
                    elif dh_temp_delta <= dh_thold_diff_med:
                        # set dew heater to medium
                        context['dh_status_str'] = '{0:d}% (Medium)'.format(dh_level_med)
                    elif dh_temp_delta <= dh_thold_diff_low:
                        # set dew heater to low
                        context['dh_status_str'] = '{0:d}% (Low)'.format(dh_level_low)
                    else:
                        context['dh_status_str'] = '{0:d}% (Default)'.format(dh_level_default)

                else:
                    context['dh_temp_delta_str'] = 'Not available'
                    context['dh_target_low_str'] = 'n/a'
                    context['dh_target_med_str'] = 'n/a'
                    context['dh_target_high_str'] = 'n/a'
                    context['dh_status_str'] = 'n/a'
            else:
                if not isinstance(dh_temp, type(None)):
                    dh_temp_delta = dh_temp - dh_manual_target
                    context['dh_temp_delta_str'] = 'Δ{0:+0.1f}° (manual target)'.format(dh_temp_delta)

                    dh_target_low = dh_manual_target + dh_thold_diff_low
                    dh_target_med = dh_manual_target + dh_thold_diff_med
                    dh_target_high = dh_manual_target + dh_thold_diff_high
                    context['dh_target_low_str'] = '{0:0.1f}°'.format(dh_target_low)
                    context['dh_target_med_str'] = '{0:0.1f}°'.format(dh_target_med)
                    context['dh_target_high_str'] = '{0:0.1f}°'.format(dh_target_high)

                    if dh_temp_delta <= dh_thold_diff_high:
                        # set dew heater to high
                        context['dh_status_str'] = '{0:d}% (High)'.format(dh_level_high)
                    elif dh_temp_delta <= dh_thold_diff_med:
                        # set dew heater to medium
                        context['dh_status_str'] = '{0:d}% (Medium)'.format(dh_level_med)
                    elif dh_temp_delta <= dh_thold_diff_low:
                        # set dew heater to low
                        context['dh_status_str'] = '{0:d}% (Low)'.format(dh_level_low)
                    else:
                        context['dh_status_str'] = '{0:d}% (Default)'.format(dh_level_default)
                else:
                    context['dh_temp_delta_str'] = 'Not available'
                    context['dh_target_low_str'] = 'n/a'
                    context['dh_target_med_str'] = 'n/a'
                    context['dh_target_high_str'] = 'n/a'
                    context['dh_status_str'] = 'n/a'


            if self.latest_image_entry.data.get(fan_temp_slot_var):
                fan_temp = self.latest_image_entry.data[fan_temp_slot_var]
                context['fan_temp_str'] = '{0:0.1f}°'.format(fan_temp)
            else:
                fan_temp = None
                context['fan_temp_str'] = 'Not available'


            fan_target = self.indi_allsky_config.get('FAN', {}).get('TARGET', 30.0)
            if not isinstance(fan_temp, type(None)):
                fan_temp_delta = fan_temp - fan_target
                context['fan_temp_delta_str'] = 'Δ{0:+0.1f}°'.format(fan_temp_delta)

                fan_target_low = fan_target + fan_thold_diff_low
                fan_target_med = fan_target + fan_thold_diff_med
                fan_target_high = fan_target + fan_thold_diff_high
                context['fan_target_low_str'] = '{0:0.1f}°'.format(fan_target_low)
                context['fan_target_med_str'] = '{0:0.1f}°'.format(fan_target_med)
                context['fan_target_high_str'] = '{0:0.1f}°'.format(fan_target_high)


                if fan_temp_delta > fan_thold_diff_high:
                    # set fan to high
                    context['fan_status_str'] = '{0:d}% (High)'.format(fan_level_high)
                elif fan_temp_delta > fan_thold_diff_med:
                    # set fan to medium
                    context['fan_status_str'] = '{0:d}% (Medium)'.format(fan_level_med)
                elif fan_temp_delta > fan_thold_diff_low:
                    # set fan to low
                    context['fan_status_str'] = '{0:d}% (Low)'.format(fan_level_low)
                else:
                    context['fan_status_str'] = '{0:d}% (Default)'.format(fan_level_default)

            else:
                context['fan_temp_delta_str'] = 'Not available'
                context['fan_target_low_str'] = 'n/a'
                context['fan_target_med_str'] = 'n/a'
                context['fan_target_high_str'] = 'n/a'
                context['fan_status_str'] = 'n/a'
        else:
            context['camera_sqm_raw_mag_str'] = 'Not available'
            context['camera_sqm_calc_sqm_str'] = 'Not available'

            context['dh_temp_str'] = 'Not available'
            context['dh_dewpoint_str'] = 'Not available'
            context['dh_temp_delta_str'] = 'Not available'
            context['dh_target_low_str'] = 'n/a'
            context['dh_target_med_str'] = 'n/a'
            context['dh_target_high_str'] = 'n/a'
            context['dh_status_str'] = 'n/a'

            context['fan_temp_str'] = 'Not available'
            context['fan_temp_delta_str'] = 'Not available'
            context['fan_target_low_str'] = 'n/a'
            context['fan_target_med_str'] = 'n/a'
            context['fan_target_high_str'] = 'n/a'
            context['fan_status_str'] = 'n/a'


        from ..modern_admin_full_config_form import (
            build_full_config_form_defaults,
            apply_full_config_form_display_fields,
            apply_full_config_form_encoded_fields,
        )
        form_data = build_full_config_form_defaults(self.indi_allsky_config)


        apply_full_config_form_display_fields(self.indi_allsky_config, form_data)

        form_data['YOUTUBE__REDIRECT_URI'] = url_for('indi_allsky.youtube_oauth2callback_view', _external=True)

        try:
            self._miscDb.getState('YOUTUBE_CREDENTIALS')
            form_data['YOUTUBE__CREDS_STORED'] = True
        except NoResultFound:
            form_data['YOUTUBE__CREDS_STORED'] = False
        except InvalidToken:
            app.logger.error('Invalid Fernet decryption key')
            form_data['YOUTUBE__CREDS_STORED'] = False
        except ValueError as e:
            app.logger.error('Invalid Fernet decryption key: %s', str(e))
            form_data['YOUTUBE__CREDS_STORED'] = False


        apply_full_config_form_encoded_fields(self.indi_allsky_config, form_data)

        # populated from flask config
        network_list = list()

        network_list.extend(app.config.get('ADMIN_NETWORKS', []))

        net_info = psutil.net_if_addrs()
        for dev, addr_info in net_info.items():
            if dev == 'lo':
                # skip loopback
                continue

            for addr in addr_info:
                if addr.family == socket.AF_INET:  # 2
                    cidr = ipaddress.IPv4Network('0.0.0.0/{0:s}'.format(addr.netmask)).prefixlen
                    network_cidr = '{0:s}/{1:d}'.format(addr.address, cidr)
                elif addr.family == socket.AF_INET6:  # 10
                    network_cidr = '{0:s}/{1:d}'.format(addr.address, 64)  # assume /64 for ipv6
                elif addr.family == socket.AF_PACKET:  # 17
                    continue
                else:
                    #app.logger.error('Unknown address family: %d', addr.family)
                    continue


                try:
                    network = ipaddress.ip_network(network_cidr, strict=False)
                    network_list.append('{0:s} [{1:s}]'.format(str(network), dev))
                except ValueError:
                    app.logger.error('Invalid network: %s', network_cidr)
                    continue


        admin_network_text = '\n'.join(network_list)
        form_data['ADMIN_NETWORKS_FLASK'] = admin_network_text

        context['form_config'] = IndiAllskyConfigForm(data=form_data)

        return context

