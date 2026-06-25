import sys
from dataclasses import FrozenInstanceError
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from indi_allsky.scientific_frame import SCIENTIFIC_FRAME_METADATA_VERSION
from indi_allsky.scientific_frame import ScientificFrame


def test_scientific_frame_minimal_creation():
    frame = ScientificFrame(
        timestamp='2026-06-25T20:00:00+00:00',
        camera_id=1,
    )

    assert frame.timestamp == '2026-06-25T20:00:00+00:00'
    assert frame.camera_id == 1
    assert frame.source_image_path is None
    assert frame.detector_image_path is None
    assert frame.metadata_version == SCIENTIFIC_FRAME_METADATA_VERSION


def test_scientific_frame_fits_source():
    frame = ScientificFrame(
        timestamp='2026-06-25T20:00:00+00:00',
        camera_uuid='camera-uuid',
        camera_id=2,
        source_image_path='/var/lib/indi-allsky/images/ccd_uuid/fits/20260625/night/25_20/ccd2_20260625_200000.fit',
        detector_image_path='/var/lib/indi-allsky/images/ccd_uuid/fits/20260625/night/25_20/ccd2_20260625_200000.fit',
        detector_image_type='fits',
        fits_path='/var/lib/indi-allsky/images/ccd_uuid/fits/20260625/night/25_20/ccd2_20260625_200000.fit',
        bit_depth=16,
        width=3840,
        height=2160,
        exposure=14.0,
        gain=220.0,
        binning=1,
        is_lossless=True,
        is_calibrated=True,
    )

    assert frame.detector_image_type == 'fits'
    assert frame.fits_path.endswith('.fit')
    assert frame.raw_path is None
    assert frame.is_lossless is True


def test_scientific_frame_raw_source():
    frame = ScientificFrame(
        source_image_path='/var/www/html/allsky/images/export/ccd_uuid/20260625/night/25_20/raw_ccd2_20260625_200000.tif',
        detector_image_path='/var/www/html/allsky/images/export/ccd_uuid/20260625/night/25_20/raw_ccd2_20260625_200000.tif',
        detector_image_type='tif',
        raw_path='/var/www/html/allsky/images/export/ccd_uuid/20260625/night/25_20/raw_ccd2_20260625_200000.tif',
        is_lossless=True,
    )

    assert frame.detector_image_type == 'tif'
    assert frame.fits_path is None
    assert frame.raw_path.endswith('.tif')


def test_scientific_frame_serialization():
    frame = ScientificFrame(
        timestamp='2026-06-25T20:00:00+00:00',
        camera_id=2,
        detector_image_type='fits',
        fits_path='/tmp/frame.fit',
    )
    data = frame.to_dict()

    assert data['timestamp'] == '2026-06-25T20:00:00+00:00'
    assert data['camera_id'] == 2
    assert data['detector_image_type'] == 'fits'
    assert data['fits_path'] == '/tmp/frame.fit'
    assert data['metadata_version'] == SCIENTIFIC_FRAME_METADATA_VERSION


def test_scientific_frame_from_frame_metadata_dict_compatibility():
    frame = ScientificFrame.from_frame_metadata({
        'timestamp': '2026-06-25T20:00:00+00:00',
        'camera_id': 2,
        'camera_uuid': 'camera-uuid',
        'exposure_us': 21686,
        'gain': 300.0,
        'fits_path': '/tmp/frame.fit',
        'detector_image_type': 'fits',
    })

    assert frame.timestamp == '2026-06-25T20:00:00+00:00'
    assert frame.camera_id == 2
    assert frame.camera_uuid == 'camera-uuid'
    assert frame.exposure == 0.021686
    assert frame.source_image_path == '/tmp/frame.fit'
    assert frame.detector_image_path == '/tmp/frame.fit'
    assert frame.detector_image_type == 'fits'


def test_scientific_frame_is_immutable():
    frame = ScientificFrame(camera_id=1)

    try:
        frame.camera_id = 2
    except FrozenInstanceError:
        return

    raise AssertionError('ScientificFrame must be immutable')


if __name__ == '__main__':
    test_scientific_frame_minimal_creation()
    test_scientific_frame_fits_source()
    test_scientific_frame_raw_source()
    test_scientific_frame_serialization()
    test_scientific_frame_from_frame_metadata_dict_compatibility()
    test_scientific_frame_is_immutable()
    print('scientific frame tests OK')
