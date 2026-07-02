#!/usr/bin/env python3

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VIEWS_PATH = REPO_ROOT / 'indi_allsky/flask/views.py'
TEMPLATE_ROOT = REPO_ROOT / 'indi_allsky/flask/templates/modern_admin'
MODERN_ADMIN_CSS_PATH = REPO_ROOT / 'indi_allsky/flask/static/modern_admin/modern-admin.css'


CAMERA_FILTER_TEMPLATES = (
    'media_list.html',
    'loop.html',
    'startrail_videos.html',
    'keograms.html',
    'startrails.html',
    'mini_timelapses.html',
    'panoramas.html',
    'raw_images.html',
    'fits.html',
)


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def read_views():
    return VIEWS_PATH.read_text(encoding='utf-8')


def class_body(views_text, class_name):
    match = re.search(
        r'^class\s+{0:s}\([^)]*\):\n'.format(re.escape(class_name)),
        views_text,
        flags=re.MULTILINE,
    )
    if not match:
        return ''

    start = match.end()
    next_class = re.search(r'^class\s+\w+\(', views_text[start:], flags=re.MULTILINE)
    if not next_class:
        return views_text[start:]

    return views_text[start:start + next_class.start()]


def test_media_browse_boundary_owns_gallery_camera_filter_policy():
    body = class_body(read_views(), 'ModernAdminMediaBrowseView')

    assert_true('def get_media_camera_filters(self):' in body, 'media browse boundary must own shared camera filters')
    assert_true('def apply_media_camera_id_filter(self, query, camera_id_field):' in body, 'media browse boundary must support direct camera_id filters')
    assert_true("'All Cameras'" in body, 'shared camera filters must preserve Gallery default')
    assert_true("request.args.get('profile_id'" in body, 'shared camera filters must support profile_id')
    assert_true("request.args.get('camera_id', type=int)" in body, 'shared camera filters must support camera_id')


def test_media_list_uses_selected_camera_filter_instead_of_active_camera_only():
    body = class_body(read_views(), 'ModernAdminMediaListView')

    assert_true('self.add_media_camera_filter_context(context)' in body, 'media list pages must expose camera filter context')
    assert_true('self.apply_media_camera_filter(query)' in body, 'media list queries must use selected camera filter')
    assert_true('.filter(IndiAllSkyDbCameraTable.id == self.camera.id)' not in body, 'media list must not force active camera only')


def test_modern_loop_uses_media_camera_filter_context():
    body = class_body(read_views(), 'ModernAdminLoopView')
    template = (TEMPLATE_ROOT / 'loop.html').read_text(encoding='utf-8')

    assert_true('self.add_media_camera_filter_context(context)' in body, 'Modern Loop must expose camera filter context')
    assert_true("context['modern_admin_loop_camera_id']" in body, 'Modern Loop must expose selected camera id')
    assert_true("context['modern_admin_loop_camera_views']" in body, 'Modern Loop must expose per-camera loop views')
    assert_true('def get_loop_camera_views(self, selected_filter):' in body, 'Modern Loop must build all-camera loop views')
    assert_true('const modernAdminLoopCameras = {{ modern_admin_loop_camera_views | tojson }};' in template, 'Loop JS must receive per-camera loop views')
    assert_true("v='modern-loop-preview-layout-v3'" in template, 'Loop template must cache-bust the responsive layout CSS')
    assert_true('modern-admin-loop-preview-grid' in template, 'Loop template must use the dedicated responsive preview grid')
    assert_true('modern-admin-loop-preview-grid-multi' in template, 'Loop template must distinguish all-camera preview layout')
    assert_true('modern-admin-status-grid' not in template, 'Loop template must not reuse compact status widget grid')
    assert_true('modern-admin-status-card' not in template, 'Loop template must not reuse compact status widget cards')
    assert_true('data-loop-camera="{{ loop_camera.loop_id }}"' in template, 'Loop template must render one card per loop camera')
    assert_true("params.set('camera_id', loopCamera.camera_id);" in template, 'Loop JS must request each selected camera explicitly')


def test_json_loop_all_cameras_does_not_require_camera_id():
    body = class_body(read_views(), 'JsonImageLoopView')

    assert_true("camera_id = request.args.get('camera_id', type=int)" in body, 'JSON loop must accept missing camera_id for All Cameras')
    assert_true('if camera_id:' in body, 'JSON loop must keep camera-specific behavior when camera_id is selected')
    assert_true("camera_id = int(request.args['camera_id'])" not in body, 'JSON loop must not require camera_id')


def test_modern_loop_preview_layout_contains_media_without_forced_stretch():
    css = MODERN_ADMIN_CSS_PATH.read_text(encoding='utf-8')

    assert_true('grid-template-columns: repeat(auto-fit, minmax(min(100%, 460px), 1fr));' in css, 'Loop all-camera grid must allow two contained desktop columns')
    assert_true('overflow: hidden;' in css, 'Loop preview cards must contain media overflow')
    assert_true('.modern-admin-loop-preview-card .modern-admin-live-frame img' in css, 'Loop preview image rule must be explicit')
    assert_true('max-width: 100%;' in css, 'Loop preview image must be width-constrained')
    assert_true('max-height: 100%;' in css, 'Loop preview image must be height-constrained')
    assert_true('width: auto;' in css, 'Loop preview image must keep natural aspect ratio width')
    assert_true('height: auto;' in css, 'Loop preview image must keep natural aspect ratio height')


def test_generated_output_metadata_pages_expose_openable_media_products():
    views_text = read_views()
    expected_contexts = (
        ('ModernAdminMediaKeogramsView', 'keogram_entries', "media_kind='image'"),
        ('ModernAdminMediaStartrailsView', 'startrail_entries', "media_kind='image'"),
        ('ModernAdminMediaStartrailVideosView', 'startrail_video_entries', "media_kind='video'"),
        ('ModernAdminMediaMiniTimelapsesView', 'mini_timelapse_entries', "media_kind='video'"),
        ('ModernAdminMediaPanoramaView', 'panorama_entries', "media_kind='image'"),
    )

    for class_name, entry_name, media_kind in expected_contexts:
        body = class_body(views_text, class_name)
        assert_true("context['modern_admin_generated_media_items']" in body, '{0:s} must expose generated media items'.format(class_name))
        assert_true('self.build_generated_media_items({0:s}, {1:s})'.format(entry_name, media_kind) in body, '{0:s} must build media items from its DB rows'.format(class_name))

    include = "{% include 'modern_admin/_generated_media_strip.html' %}"
    for template_name in ('keograms.html', 'startrails.html', 'startrail_videos.html', 'mini_timelapses.html', 'panoramas.html'):
        text = (TEMPLATE_ROOT / template_name).read_text(encoding='utf-8')
        assert_true(include in text, '{0:s} must render generated media products'.format(template_name))


def test_media_metadata_services_use_selected_camera_filter():
    body = class_body(read_views(), 'ModernAdminMediaMetadataView')

    assert_true('self.add_media_camera_filter_context(context)' in body, 'metadata pages must expose camera filter context')
    assert_true(body.count('camera_id=self.get_selected_media_camera_id()') == 4, 'metadata services must use selected camera filter')
    assert_true('camera_relation=' not in body, 'generated-output metadata services must not require Camera joins')
    assert_true('IndiAllSkyDbKeogramTable.camera_id' in body, 'Keogram metadata must filter by direct camera_id')
    assert_true('IndiAllSkyDbStarTrailsTable.camera_id' in body, 'Startrail metadata must filter by direct camera_id')
    assert_true('camera_id=self.camera.id' not in body, 'metadata services must not force active camera only')


def test_inline_metadata_queries_use_shared_camera_filter():
    views_text = read_views()

    for class_name in ('ModernAdminMediaPanoramaView', 'ModernAdminMediaRawImagesView', 'ModernAdminFitsView'):
        body = class_body(views_text, class_name)
        assert_true('self.apply_media_camera_id_filter(' in body, '{0:s} must use shared direct camera_id filter'.format(class_name))
        assert_true('.filter(IndiAllSkyDbCameraTable.id == self.camera.id)' not in body, '{0:s} must not force active camera only'.format(class_name))


def test_media_detail_views_do_not_restrict_to_active_camera():
    views_text = read_views()

    for class_name in ('ModernAdminMediaImageDetailView', 'ModernAdminMediaVideoDetailView', 'ModernAdminFitsDetailView'):
        body = class_body(views_text, class_name)
        assert_true('.filter(IndiAllSkyDbCameraTable.id == self.camera.id)' not in body, '{0:s} must open rows selected from all-camera listings'.format(class_name))


def test_camera_filter_partial_is_available_on_camera_owned_media_pages():
    include = "{% include 'modern_admin/_media_camera_filter.html' %}"

    for template_name in CAMERA_FILTER_TEMPLATES:
        text = (TEMPLATE_ROOT / template_name).read_text(encoding='utf-8')
        assert_true(include in text, '{0:s} must render the shared camera filter'.format(template_name))


def run_tests():
    test_media_browse_boundary_owns_gallery_camera_filter_policy()
    test_media_list_uses_selected_camera_filter_instead_of_active_camera_only()
    test_modern_loop_uses_media_camera_filter_context()
    test_json_loop_all_cameras_does_not_require_camera_id()
    test_modern_loop_preview_layout_contains_media_without_forced_stretch()
    test_generated_output_metadata_pages_expose_openable_media_products()
    test_media_metadata_services_use_selected_camera_filter()
    test_inline_metadata_queries_use_shared_camera_filter()
    test_media_detail_views_do_not_restrict_to_active_camera()
    test_camera_filter_partial_is_available_on_camera_owned_media_pages()


if __name__ == '__main__':
    run_tests()
    print('modern admin media camera filter tests passed')
