"""Dedicated records and URL variants for Hybrid detail-page discovery."""
def seed_detail_pages(app):
    from hybrid_operations_fixture import seed_operations
    from hybrid_source_media_fixture import seed_source_media
    from hybrid_generation_fixture import seed_generation
    from hybrid_generated_media_fixture import seed_generated_media
    seed_operations(app)
    seed_source_media(app)
    seed_generation(app)
    seed_generated_media(app)


def detail_parameters(endpoint, camera):
    from indi_allsky.flask.views import ModernAdminUploadDetailView, ModernAdminLogDetailView
    name = endpoint.removeprefix('indi_allsky.')
    camera_fields = {
        'modern_admin_media_image_detail_view': 'image_id',
        'modern_admin_media_video_detail_view': 'video_id',
        'modern_admin_fits_detail_view': 'fits_id',
        'modern_admin_task_detail_view': 'task_id',
    }
    if name in camera_fields:
        return [{camera_fields[name]: camera}]
    if name == 'modern_admin_upload_detail_view':
        return [{'provider_slug': value} for value in ModernAdminUploadDetailView.provider_configs]
    if name == 'modern_admin_log_detail_view':
        return [{'log_name': value} for value in ModernAdminLogDetailView.log_sources]
    if name == 'modern_admin_user_detail_view':
        return [{'user_id': 1}, {'user_id': 2}]
    if name == 'modern_admin_config_restore_detail_view':
        return [{'config_id': 1}]
    if name == 'modern_admin_notification_detail_view':
        return [{'notification_id': value} for value in (1, 2, 3)]
    return None
