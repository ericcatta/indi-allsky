"""Hybrid-owned Observatory context and form adapters.

The optional Classic pages reuse these adapters; Hybrid does not import the
Classic frontend. Scientific processing remains in the existing services.
"""
from datetime import datetime
import math

from flask import request
from .base_views import TemplateView
from .forms import IndiAllskyVirtualSkyHelperForm, IndiAllskyChartHistoryForm
from ..modern_admin_observatory_tools import ModernAdminVirtualSkyContextService
from ..modern_admin_sensor_panel import build_sensor_rows


class HybridVirtualSkyContextView(TemplateView):
    page_title = 'VirtualSky'
    image_loop_view = 'indi_allsky.js_image_loop_view'
    context_service = ModernAdminVirtualSkyContextService()


    def get_context(self):
        context = super(HybridVirtualSkyContextView, self).get_context()

        context['image_loop_view'] = self.image_loop_view


        timestamp = int(request.args.get('timestamp', 0))
        context['timestamp'] = timestamp


        context['form_virtualsky'] = IndiAllskyVirtualSkyHelperForm(
            data=self.context_service.build_form_data(self.camera),
        )


        refreshInterval_ms = math.ceil(self.indi_allsky_config.get('CCD_EXPOSURE_MAX', 15.0)) * 1000
        context['refreshInterval'] = refreshInterval_ms + 1000  # additional time for exposures to download


        ### Camera DB settings
        if self.indi_allsky_config.get('PRIVACY_MODE'):
            # reduce precision for privacy
            context['camera_latitude'] = float(round(self.camera.latitude))
            context['camera_longitude'] = float(round(self.camera.longitude))
        else:
            context['camera_latitude'] = self.camera.latitude
            context['camera_longitude'] = self.camera.longitude


        ### Calculate time offset
        context['time_offset'] = self.camera.utc_offset - datetime.now().astimezone().utcoffset().total_seconds()


        return context


class HybridSqmContextView(TemplateView):
    page_title = 'SQM'

    def get_context(self):
        context = super(HybridSqmContextView, self).get_context()

        refreshInterval_ms = math.ceil(self.indi_allsky_config.get('CCD_EXPOSURE_MAX', 15.0)) * 1000
        context['refreshInterval'] = refreshInterval_ms + 1000  # additional time for exposures to download

        return context


class HybridChartContextView(TemplateView):
    page_title = 'Charts'

    def get_context(self):
        context = super(HybridChartContextView, self).get_context()

        context['timestamp'] = int(request.args.get('timestamp', 0))

        refreshInterval_ms = math.ceil(self.indi_allsky_config.get('CCD_EXPOSURE_MAX', 15.0)) * 1000
        context['refreshInterval'] = refreshInterval_ms + 1000  # additional time for exposures to download

        context['form_history'] = IndiAllskyChartHistoryForm()


        if self.camera.data:
            camera_data = dict(self.camera.data)
        else:
            camera_data = dict()


        custom_chart_1_key = camera_data.get('custom_chart_1_key', 'sensor_user_10')
        custom_chart_2_key = camera_data.get('custom_chart_2_key', 'sensor_user_11')
        custom_chart_3_key = camera_data.get('custom_chart_3_key', 'sensor_user_12')
        custom_chart_4_key = camera_data.get('custom_chart_4_key', 'sensor_user_13')
        custom_chart_5_key = camera_data.get('custom_chart_5_key', 'sensor_user_14')
        custom_chart_6_key = camera_data.get('custom_chart_6_key', 'sensor_user_15')
        custom_chart_7_key = camera_data.get('custom_chart_7_key', 'sensor_user_16')
        custom_chart_8_key = camera_data.get('custom_chart_8_key', 'sensor_user_17')
        custom_chart_9_key = camera_data.get('custom_chart_9_key', 'sensor_user_18')


        context['label_custom_chart_1'] = camera_data.get(custom_chart_1_key, 'Unset')
        context['min_custom_chart_1'] = camera_data.get('custom_chart_1_min', 0.0)
        context['label_custom_chart_2'] = camera_data.get(custom_chart_2_key, 'Unset')
        context['min_custom_chart_2'] = camera_data.get('custom_chart_2_min', 0.0)
        context['label_custom_chart_3'] = camera_data.get(custom_chart_3_key, 'Unset')
        context['min_custom_chart_3'] = camera_data.get('custom_chart_3_min', 0.0)
        context['label_custom_chart_4'] = camera_data.get(custom_chart_4_key, 'Unset')
        context['min_custom_chart_4'] = camera_data.get('custom_chart_4_min', 0.0)
        context['label_custom_chart_5'] = camera_data.get(custom_chart_5_key, 'Unset')
        context['min_custom_chart_5'] = camera_data.get('custom_chart_5_min', 0.0)
        context['label_custom_chart_6'] = camera_data.get(custom_chart_6_key, 'Unset')
        context['min_custom_chart_6'] = camera_data.get('custom_chart_6_min', 0.0)
        context['label_custom_chart_7'] = camera_data.get(custom_chart_7_key, 'Unset')
        context['min_custom_chart_7'] = camera_data.get('custom_chart_7_min', 0.0)
        context['label_custom_chart_8'] = camera_data.get(custom_chart_8_key, 'Unset')
        context['min_custom_chart_8'] = camera_data.get('custom_chart_8_min', 0.0)
        context['label_custom_chart_9'] = camera_data.get(custom_chart_9_key, 'Unset')
        context['min_custom_chart_9'] = camera_data.get('custom_chart_9_min', 0.0)


        return context


class HybridSensorPanelContextView(TemplateView):
    page_title = 'Sensor Panel'

    def get_context(self):
        context = super(HybridSensorPanelContextView, self).get_context()

        image_data = self.latest_image_entry.data if self.latest_image_entry else None
        rows = build_sensor_rows(self.camera.data, image_data)
        show_all = request.args.get('all') == '1'
        user_rows = [row for row in rows['user'] if show_all or row['used']]
        temp_rows = [row for row in rows['temp'] if show_all or row['used']]
        for group in (user_rows, temp_rows):
            for row in group:
                row['index'] = int(row['slot'].rsplit('_', 1)[1])

        # Age of the "current" values
        if self.latest_image_entry:
            context['last_update'] = self.latest_image_entry.createDate
            context['last_update_age_s'] = int((self.camera_now - self.latest_image_entry.createDate).total_seconds())
        else:
            context['last_update'] = None
            context['last_update_age_s'] = None

        context['show_all'] = bool(show_all)
        context['refreshInterval'] = 5000  # ms
        context['user_rows'] = user_rows
        context['temp_rows'] = temp_rows

        return context
