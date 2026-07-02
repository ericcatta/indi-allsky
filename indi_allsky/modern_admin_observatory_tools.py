class ModernAdminSqmSummaryService:
    def build_context(self, image_data, sqm_summary):
        return {
            'modern_admin_sqm'        : image_data.get('sqm', 0.0),
            'modern_admin_stars'      : image_data.get('stars', 0),
            'modern_admin_moon_phase' : image_data.get('moon_phase', 0.0),
            'modern_admin_sqm_summary': sqm_summary,
        }


class ModernAdminLongTermKeogramDisplayService:
    def format_generated_age(self, image_age_s):
        image_age_days = int(image_age_s / 86400)
        image_age_hours = int((image_age_s % 86400) / 3600)
        image_age_minutes = int(((image_age_s % 86400) % 3600) / 60)

        return 'Generated {0:d} days, {1:d} hours, {2:d} minutes ago'.format(
            image_age_days,
            image_age_hours,
            image_age_minutes,
        )


class ModernAdminVirtualSkyContextService:
    def build_form_data(self, camera):
        camera_data = camera.data or {}

        return {
            'AZIMUTH_ANGLE'         : camera.az,
            'IMAGE_CIRCLE_DIAMETER' : camera_data.get('vs_image_circle_diameter', 3500),
            'LATITUDE_OFFSET'       : camera_data.get('vs_latitude_offset', 0.0),
            'LONGITUDE_OFFSET'      : camera_data.get('vs_longitude_offset', 0.0),
            'OFFSET_X'              : camera_data.get('vs_offset_x', 0.0),
            'OFFSET_Y'              : camera_data.get('vs_offset_y', 0.0),
            'MAGNITUDE'             : camera_data.get('vs_magnitude', 6.0),
            'CONSTELLATIONS'        : camera_data.get('vs_constellations', True),
            'CONSTELLATIONLABELS'   : camera_data.get('vs_constellationlabels', False),
            'SHOWSTARS'             : camera_data.get('vs_showstars', True),
            'SHOWSTARLABELS'        : camera_data.get('vs_showstarlabels', True),
            'SHOWPLANETS'           : camera_data.get('vs_showplanets', True),
            'SHOWPLANETLABELS'      : camera_data.get('vs_showplanetlabels', True),
        }
