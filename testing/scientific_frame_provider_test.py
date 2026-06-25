import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from indi_allsky.scientific_frame_provider import ScientificFrameProvider


def _metadata(**kwargs):
    data = {
        'timestamp': '2026-06-25T20:00:00+00:00',
        'camera_id': 2,
        'camera_uuid': 'camera-uuid',
        'display_image_path': '/var/lib/indi-allsky/images/ccd2.jpg',
        'image_file_path': '/var/lib/indi-allsky/images/ccd2.jpg',
        'exposure_us': 21686,
        'gain': 300.0,
    }
    data.update(kwargs)
    return data


def test_provider_single_metadata_with_fits_source():
    provider = ScientificFrameProvider()
    frame = provider.from_frame_metadata(_metadata(
        fits_path='/var/lib/indi-allsky/images/ccd_uuid/fits/20260625/night/25_20/ccd2_20260625_200000.fit',
        raw_path='/var/www/html/allsky/images/export/ccd_uuid/20260625/night/25_20/raw_ccd2_20260625_200000.tif',
    ))

    assert frame.source_image_path.endswith('.fit')
    assert frame.detector_image_path.endswith('.fit')
    assert frame.detector_image_type == 'fits'
    assert frame.fits_path.endswith('.fit')
    assert frame.raw_path.endswith('.tif')


def test_provider_single_metadata_with_raw_fallback():
    provider = ScientificFrameProvider()
    frame = provider.from_frame_metadata(_metadata(
        raw_path='/var/www/html/allsky/images/export/ccd_uuid/20260625/night/25_20/raw_ccd2_20260625_200000.tif',
    ))

    assert frame.source_image_path.endswith('.tif')
    assert frame.detector_image_path.endswith('.tif')
    assert frame.detector_image_type == 'tif'
    assert frame.fits_path is None


def test_provider_metadata_with_no_scientific_source():
    provider = ScientificFrameProvider()
    frame = provider.from_frame_metadata(_metadata())

    assert frame.source_image_path is None
    assert frame.detector_image_path is None
    assert frame.detector_image_type is None


def test_provider_list_conversion_preserves_order():
    provider = ScientificFrameProvider()
    frames = provider.from_frame_metadata_list([
        _metadata(camera_id=1, fits_path='/tmp/one.fit'),
        _metadata(camera_id=2, raw_path='/tmp/two.tif'),
        _metadata(camera_id=3),
    ])

    assert [frame.camera_id for frame in frames] == [1, 2, 3]
    assert frames[0].source_image_path == '/tmp/one.fit'
    assert frames[1].source_image_path == '/tmp/two.tif'
    assert frames[2].source_image_path is None


def test_provider_does_not_promote_display_image_to_source():
    provider = ScientificFrameProvider()
    frame = provider.from_frame_metadata(_metadata(
        display_image_path='/var/lib/indi-allsky/images/display-only.jpg',
        image_file_path='/var/lib/indi-allsky/images/display-only.jpg',
    ))

    assert frame.source_image_path is None
    assert frame.detector_image_path is None


if __name__ == '__main__':
    test_provider_single_metadata_with_fits_source()
    test_provider_single_metadata_with_raw_fallback()
    test_provider_metadata_with_no_scientific_source()
    test_provider_list_conversion_preserves_order()
    test_provider_does_not_promote_display_image_to_source()
    print('scientific frame provider tests OK')
