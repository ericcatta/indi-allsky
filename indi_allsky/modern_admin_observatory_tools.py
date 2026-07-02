class ModernAdminSqmSummaryService:
    def build_context(self, image_data, sqm_summary):
        return {
            'modern_admin_sqm'        : image_data.get('sqm', 0.0),
            'modern_admin_stars'      : image_data.get('stars', 0),
            'modern_admin_moon_phase' : image_data.get('moon_phase', 0.0),
            'modern_admin_sqm_summary': sqm_summary,
        }
