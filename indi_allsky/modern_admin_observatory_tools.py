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
