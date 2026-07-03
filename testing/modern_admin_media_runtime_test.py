#!/usr/bin/env python3

import inspect
import sys
from datetime import datetime
from datetime import timedelta
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from indi_allsky.modern_admin_media_runtime import ModernAdminLatestCameraFramesRepository
from indi_allsky.modern_admin_media_runtime import ModernAdminMediaUrlNormalizer


class FakeField:
    def __eq__(self, value):
        return ('eq', value)


class FakeCamera:
    def __init__(self, camera_id, name):
        self.id = camera_id
        self.friendlyName = name
        self.name = name


class FakeImage:
    def __init__(self, camera_id=1, url='images/camera/latest.jpg', created=None):
        self.camera_id = camera_id
        self.url = url
        self.createDate = created or datetime(2026, 7, 3, 12, 0, 0)
        self.get_url_calls = list()

    def getUrl(self, s3_prefix='', local=True):
        self.get_url_calls.append({
            's3_prefix': s3_prefix,
            'local': local,
        })
        return self.url


class FakeQuery:
    def __init__(self, rows=None, first_row=None, fail=False):
        self.rows = rows or list()
        self.first_row = first_row
        self.fail = fail
        self.filter_calls = list()
        self.order_by_calls = list()
        self.limit_calls = list()

    def filter(self, expression):
        self.filter_calls.append(expression)
        return self

    def order_by(self, expression):
        self.order_by_calls.append(expression)
        return self

    def limit(self, limit):
        self.limit_calls.append(limit)
        return self

    def all(self):
        if self.fail:
            raise RuntimeError('query failed')
        return self.rows

    def first(self):
        if self.fail:
            raise RuntimeError('query failed')
        return self.first_row


def build_repository(camera_query=None, image_query=None, clock=None):
    return ModernAdminLatestCameraFramesRepository(
        camera_query=camera_query or FakeQuery(rows=[FakeCamera(1, 'IMX708 Wide')]),
        image_query=image_query or FakeQuery(first_row=FakeImage()),
        camera_id_field=FakeField(),
        image_order_by_expression='created-desc',
        camera_visible_expression='camera-visible',
        camera_order_by_expression='camera-id-asc',
        fallback_camera=FakeCamera(9, 'Fallback Camera'),
        clock=clock or (lambda: datetime(2026, 7, 3, 12, 5, 0)),
        s3_prefix='https://cdn.invalid',
        images_folder_url_builder=lambda path: '/images/{0:s}'.format(path),
    )


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def test_latest_camera_frames_queries_are_bounded_and_camera_filtered():
    camera_query = FakeQuery(rows=[
        FakeCamera(1, 'IMX708 Wide'),
        FakeCamera(2, 'ASI678MC'),
        FakeCamera(3, 'Hidden Extra'),
    ])
    image_query = FakeQuery(first_row=FakeImage(url='images/camera/latest.jpg'))
    repository = build_repository(camera_query=camera_query, image_query=image_query)

    frames = repository.get_latest_camera_frames()

    assert_true(len(frames) == 2, 'latest camera frames must be capped at two cameras')
    assert_true(camera_query.filter_calls == ['camera-visible'], 'camera query must apply visible-camera expression')
    assert_true(camera_query.order_by_calls == ['camera-id-asc'], 'camera query must preserve camera ordering')
    assert_true(camera_query.limit_calls == [2], 'camera query must be bounded')
    assert_true(image_query.filter_calls == [('eq', 1), ('eq', 2)], 'image query must filter each camera id')
    assert_true(image_query.order_by_calls == ['created-desc', 'created-desc'], 'image query must use latest-first ordering')
    assert_true(image_query.limit_calls == [1, 1], 'image lookup must be bounded per camera')
    assert_true(frames[0]['safe_image_url'] == '/images/camera/latest.jpg', 'relative images path must normalize through injected URL builder')
    assert_true(frames[0]['image_available'] is True, 'safe local image route must be marked available')


def test_latest_camera_frames_falls_back_to_active_camera_when_camera_query_empty():
    camera_query = FakeQuery(rows=[])
    image_query = FakeQuery(first_row=FakeImage(camera_id=9, url='/images/fallback/latest.jpg'))
    repository = build_repository(camera_query=camera_query, image_query=image_query)

    frames = repository.get_latest_camera_frames()

    assert_true(len(frames) == 1, 'fallback camera should be used when camera query has no rows')
    assert_true(frames[0]['camera_id'] == 9, 'fallback frame should use fallback camera id')
    assert_true(frames[0]['safe_image_url'] == '/images/fallback/latest.jpg', 'fallback frame should preserve safe local image route')


def test_latest_camera_frames_rejects_remote_and_unsafe_routes():
    repository = build_repository()

    unsafe_urls = (
        'https://example.invalid/latest.jpg',
        'http://example.invalid/latest.jpg',
        'images/../secret.jpg',
        '/other/latest.jpg',
        '/images/../secret.jpg',
        'file:///tmp/latest.jpg',
    )

    for unsafe_url in unsafe_urls:
        assert_true(
            repository.safe_image_url(FakeImage(url=unsafe_url)) is None,
            'unsafe URL must be rejected: {0:s}'.format(unsafe_url),
        )


def test_latest_camera_frames_handles_missing_rows_and_query_errors_safely():
    repository = build_repository(image_query=FakeQuery(first_row=None))
    frames = repository.get_latest_camera_frames()

    assert_true(frames[0]['image_available'] is False, 'missing image row should produce fallback frame')
    assert_true(frames[0]['safe_image_url'] is None, 'missing image row must not expose an URL')

    failing_repository = build_repository(image_query=FakeQuery(fail=True))
    frames = failing_repository.get_latest_camera_frames()

    assert_true(frames[0]['image_available'] is False, 'query errors should produce fallback frame')
    assert_true(frames[0]['source_status'] == 'Latest image metadata unavailable.', 'query errors should preserve safe status')


def test_latest_camera_frame_age_labels_are_stable():
    repository = build_repository(clock=lambda: datetime(2026, 7, 3, 12, 5, 0))

    assert_true(repository.age_label(datetime(2026, 7, 3, 12, 4, 45)) == '15 seconds ago', 'seconds age label changed')
    assert_true(repository.age_label(datetime(2026, 7, 3, 11, 50, 0)) == '15 minutes ago', 'minutes age label changed')
    assert_true(repository.age_label(datetime(2026, 7, 3, 9, 0, 0)) == '3 hours ago', 'hours age label changed')
    assert_true(repository.age_label(datetime(2026, 7, 3, 12, 6, 0)) == 'Not evaluated yet', 'future timestamps should be safe')
    assert_true(repository.age_label(None) == 'Not evaluated yet', 'missing timestamps should be safe')


def test_media_url_normalizer_preserves_existing_url_shapes():
    normalizer = ModernAdminMediaUrlNormalizer(
        images_folder_url_builder=lambda path: '/images/{0:s}'.format(path),
    )

    assert_true(normalizer.normalize_media_url(None) is None, 'None URLs should stay unavailable')
    assert_true(normalizer.normalize_media_url('') is None, 'empty URLs should stay unavailable')
    assert_true(normalizer.normalize_media_url('/images/camera/latest.jpg') == '/images/camera/latest.jpg', 'absolute app URLs should be preserved')
    assert_true(normalizer.normalize_media_url('https://example.invalid/media.jpg') == 'https://example.invalid/media.jpg', 'remote URLs should be preserved for media pages')
    assert_true(normalizer.normalize_media_url('http://example.invalid/media.jpg') == 'http://example.invalid/media.jpg', 'HTTP URLs should be preserved for media pages')
    assert_true(normalizer.normalize_media_url('images/camera/latest.jpg') == '/images/camera/latest.jpg', 'relative image URLs should use injected images route builder')
    assert_true(normalizer.normalize_media_url('custom/media.jpg') == 'custom/media.jpg', 'non-image relative URLs should preserve legacy shape')


def test_media_url_normalizer_supports_safe_local_image_profile():
    normalizer = ModernAdminMediaUrlNormalizer(
        images_folder_url_builder=lambda path: '/images/{0:s}'.format(path),
    )

    assert_true(normalizer.normalize_safe_local_image_url('images/camera/latest.jpg') == '/images/camera/latest.jpg', 'safe local image URL should be normalized')
    assert_true(normalizer.normalize_safe_local_image_url('/images/camera/latest.jpg') == '/images/camera/latest.jpg', 'safe absolute image URL should be preserved')
    assert_true(normalizer.normalize_safe_local_image_url('https://example.invalid/latest.jpg') is None, 'safe local profile must reject remote URLs')
    assert_true(normalizer.normalize_safe_local_image_url('/other/latest.jpg') is None, 'safe local profile must reject non-image routes')
    assert_true(normalizer.normalize_safe_local_image_url('/images/../secret.jpg') is None, 'safe local profile must reject traversal')


def test_modern_views_delegate_media_url_normalization_to_runtime_service():
    source = (REPO_ROOT / 'indi_allsky' / 'flask' / 'views.py').read_text(encoding='utf-8')

    assert_true('from ..modern_admin_media_runtime import ModernAdminMediaUrlNormalizer' in source, 'views must import Hybrid media URL normalizer')
    assert_true('def normalize_media_url(' not in source, 'views must not own inline media URL normalization')
    assert_true('ModernAdminMediaListView.normalize_media_url' not in source, 'views must not call legacy class-level URL normalization')
    assert_true('.getUrl(s3_prefix=self.s3_prefix, local=local)' in source, 'Classic getUrl adapter call should remain explicit and preserved')
    assert_true('.normalize_media_url(' in source, 'views should delegate final URL shaping to Hybrid runtime normalizer')


def test_media_runtime_service_has_no_flask_db_or_filesystem_access():
    import indi_allsky.modern_admin_media_runtime as module

    source = inspect.getsource(module)

    assert_true('flask' not in source.lower(), 'media runtime service must not import Flask')
    assert_true('db.session' not in source, 'media runtime service must not use db.session')
    assert_true('request' not in source, 'media runtime service must not read request state')
    assert_true('open(' not in source, 'media runtime service must not open files')
    assert_true('getFilesystemPath' not in source, 'media runtime service must not use filesystem path helpers')


def run_tests():
    test_latest_camera_frames_queries_are_bounded_and_camera_filtered()
    test_latest_camera_frames_falls_back_to_active_camera_when_camera_query_empty()
    test_latest_camera_frames_rejects_remote_and_unsafe_routes()
    test_latest_camera_frames_handles_missing_rows_and_query_errors_safely()
    test_latest_camera_frame_age_labels_are_stable()
    test_media_url_normalizer_preserves_existing_url_shapes()
    test_media_url_normalizer_supports_safe_local_image_profile()
    test_modern_views_delegate_media_url_normalization_to_runtime_service()
    test_media_runtime_service_has_no_flask_db_or_filesystem_access()
    print('Modern admin media runtime checks passed')


if __name__ == '__main__':
    run_tests()
