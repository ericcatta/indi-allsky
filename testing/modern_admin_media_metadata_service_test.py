#!/usr/bin/env python3

import sys
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from indi_allsky.modern_admin_media_metadata import ModernAdminKeogramMetadataService
from indi_allsky.modern_admin_media_metadata import ModernAdminStartrailVideoMetadataService


class FakeCameraIdField:
    def __eq__(self, value):
        return ('camera-id', value)


class FakeEntry:
    id = 17
    createDate = datetime(2026, 1, 2, 3, 4, 5)
    dayDate = '2026-01-02'
    camera_id = 2
    filename = '/unsafe/path/startrail-video.mp4'
    width = 1920
    height = 1080
    frames = 240
    framerate = 24.0
    fileSize = 1048576
    night = True
    uploaded = False
    success = True
    remote_url = ''
    s3_key = ''
    sync_id = None
    data = {'frames': 240, 'quality': 'metadata-only'}


class FakeRemoteEntry(FakeEntry):
    remote_url = 'https://example.invalid/video.mp4'
    s3_key = ''
    data = None


class FakeKeogramEntry(FakeEntry):
    filename = '/unsafe/path/keogram.jpg'
    frames = 120
    fileSize = 2048
    data = {'keogram': True}


class FakeQuery:
    def __init__(self, entries):
        self.entries = entries
        self.join_calls = list()
        self.filter_calls = list()
        self.order_by_calls = list()
        self.limit_calls = list()

    def join(self, relation):
        self.join_calls.append(relation)
        return self

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
        return self.entries


def build_service(query):
    return ModernAdminStartrailVideoMetadataService(
        query=query,
        camera_relation='camera-relation',
        camera_id_field=FakeCameraIdField(),
        camera_id=2,
        order_by_expression='created-desc',
    )


def build_keogram_service(query):
    return ModernAdminKeogramMetadataService(
        query=query,
        camera_relation='camera-relation',
        camera_id_field=FakeCameraIdField(),
        camera_id=2,
        order_by_expression='created-desc',
    )


def test_startrail_video_metadata_query_is_bounded_and_camera_filtered():
    query = FakeQuery([FakeEntry()])
    service = build_service(query)

    entries = service.list_entries(limit=100)

    assert entries == [query.entries[0]]
    assert query.join_calls == ['camera-relation']
    assert query.filter_calls == [('camera-id', 2)]
    assert query.order_by_calls == ['created-desc']
    assert query.limit_calls == [100]


def test_startrail_video_metadata_rows_preserve_context_shape():
    service = build_service(FakeQuery([]))

    rows = service.build_rows([FakeEntry()])

    assert rows == [{
        'id'         : 17,
        'created'    : '2026-01-02 03:04:05',
        'day_date'   : '2026-01-02',
        'camera_id'  : 2,
        'filename'   : 'startrail-video.mp4',
        'dimensions' : '1920 x 1080',
        'frames'     : 240,
        'framerate'  : '24 fps',
        'file_size'  : '1.0 MB',
        'timeofday'  : 'Night',
        'uploaded'   : 'No',
        'success'    : 'Yes',
        'source'     : 'Local DB entry',
        'sync_id'    : 'N/A',
        'metadata'   : 'Keys: 2',
    }]


def test_startrail_video_metadata_formats_remote_source_without_exposing_url():
    service = build_service(FakeQuery([]))

    row = service.build_row(FakeRemoteEntry())

    assert row['source'] == 'Remote URL recorded'
    assert 'http' not in str(row)
    assert '/unsafe/path' not in str(row)


def test_keogram_metadata_query_is_bounded_and_camera_filtered():
    query = FakeQuery([FakeKeogramEntry()])
    service = build_keogram_service(query)

    entries = service.list_entries(limit=100)

    assert entries == [query.entries[0]]
    assert query.join_calls == ['camera-relation']
    assert query.filter_calls == [('camera-id', 2)]
    assert query.order_by_calls == ['created-desc']
    assert query.limit_calls == [100]


def test_keogram_metadata_rows_preserve_context_shape():
    service = build_keogram_service(FakeQuery([]))

    rows = service.build_rows([FakeKeogramEntry()])

    assert rows == [{
        'id'         : 17,
        'created'    : '2026-01-02 03:04:05',
        'day_date'   : '2026-01-02',
        'camera_id'  : 2,
        'filename'   : 'keogram.jpg',
        'dimensions' : '1920 x 1080',
        'frames'     : 120,
        'file_size'  : '2.0 KB',
        'timeofday'  : 'Night',
        'uploaded'   : 'No',
        'success'    : 'Yes',
        'source'     : 'Local DB entry',
        'sync_id'    : 'N/A',
        'metadata'   : 'Keys: 1',
    }]


def test_keogram_metadata_formats_remote_source_without_exposing_url():
    service = build_keogram_service(FakeQuery([]))

    row = service.build_row(FakeRemoteEntry())

    assert row['source'] == 'Remote URL recorded'
    assert 'http' not in str(row)
    assert '/unsafe/path' not in str(row)


def test_startrail_video_metadata_service_has_no_flask_db_or_filesystem_access():
    import inspect
    import indi_allsky.modern_admin_media_metadata as module

    source = inspect.getsource(module)

    assert 'flask' not in source.lower()
    assert 'db.session' not in source
    assert 'request' not in source
    assert 'open(' not in source
    assert 'getFilesystemPath' not in source


def run_tests():
    test_startrail_video_metadata_query_is_bounded_and_camera_filtered()
    test_startrail_video_metadata_rows_preserve_context_shape()
    test_startrail_video_metadata_formats_remote_source_without_exposing_url()
    test_keogram_metadata_query_is_bounded_and_camera_filtered()
    test_keogram_metadata_rows_preserve_context_shape()
    test_keogram_metadata_formats_remote_source_without_exposing_url()
    test_startrail_video_metadata_service_has_no_flask_db_or_filesystem_access()
    print('Modern admin media metadata service checks passed')


if __name__ == '__main__':
    run_tests()
