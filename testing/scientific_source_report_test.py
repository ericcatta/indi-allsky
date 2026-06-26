import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from indi_allsky.scientific_source_report import build_scientific_source_offline_report
from indi_allsky.scientific_source_report import render_scientific_source_text_summary


def _metadata(**overrides):
    data = {
        'frame_id': 42,
        'timestamp': '2026-06-26T22:00:00+00:00',
        'camera_id': 2,
        'camera_uuid': 'camera-uuid',
        'profile_id': 'asi678mc',
        'image_file_path': '/var/lib/indi-allsky/display.jpg',
        'display_image_path': '/var/lib/indi-allsky/display.jpg',
        'exposure_us': 21686,
        'gain': 300.0,
        'fits_path': None,
        'raw_path': None,
        'detector_image_type': None,
    }
    data.update(overrides)
    return data


def _write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as f_jsonl:
        for row in rows:
            if isinstance(row, str):
                f_jsonl.write(row)
            else:
                f_jsonl.write(json.dumps(row, sort_keys=True))
            f_jsonl.write('\n')


def test_scientific_source_report_missing_metadata_file_is_safe():
    with tempfile.TemporaryDirectory() as tmpdir:
        report = build_scientific_source_offline_report(Path(tmpdir).joinpath('missing.jsonl'))

    assert report['total_metadata_lines'] == 0
    assert report['malformed_lines'] == 0
    assert report['scientific_frames_total'] == 0
    assert report['frames_with_detector_path'] == 0
    assert report['missing_detector_files'] == 0


def test_scientific_source_report_counts_malformed_lines():
    with tempfile.TemporaryDirectory() as tmpdir:
        metadata_path = Path(tmpdir).joinpath('frame_metadata', '2026-06-26.jsonl')
        _write_jsonl(metadata_path, [
            _metadata(),
            'not-json',
            '[]',
        ])

        report = build_scientific_source_offline_report(metadata_path)

    assert report['total_metadata_lines'] == 3
    assert report['malformed_lines'] == 2
    assert report['scientific_frames_total'] == 1


def test_scientific_source_report_counts_rows_without_detector_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        metadata_path = Path(tmpdir).joinpath('frame_metadata.jsonl')
        _write_jsonl(metadata_path, [_metadata()])

        report = build_scientific_source_offline_report(metadata_path)

    assert report['frames_with_source_path'] == 0
    assert report['frames_with_detector_path'] == 0
    assert report['missing_source_path'] == 1
    assert report['missing_detector_path'] == 1


def test_scientific_source_report_fake_detector_path_missing_when_checked():
    with tempfile.TemporaryDirectory() as tmpdir:
        missing_fits = Path(tmpdir).joinpath('missing.fit')
        metadata_path = Path(tmpdir).joinpath('frame_metadata.jsonl')
        _write_jsonl(metadata_path, [_metadata(fits_path=str(missing_fits), detector_image_type='fits')])

        report = build_scientific_source_offline_report(metadata_path, check_files=True)

    assert report['frames_with_source_path'] == 1
    assert report['frames_with_detector_path'] == 1
    assert report['counts_by_detector_image_type'] == {'fits': 1}
    assert report['existing_detector_files'] == 0
    assert report['missing_detector_files'] == 1


def test_scientific_source_report_fake_detector_path_not_checked_when_disabled():
    with tempfile.TemporaryDirectory() as tmpdir:
        missing_fits = Path(tmpdir).joinpath('missing.fit')
        metadata_path = Path(tmpdir).joinpath('frame_metadata.jsonl')
        _write_jsonl(metadata_path, [_metadata(fits_path=str(missing_fits), detector_image_type='fits')])

        report = build_scientific_source_offline_report(metadata_path, check_files=False)

    assert report['frames_with_detector_path'] == 1
    assert report['existing_detector_files'] == 0
    assert report['missing_detector_files'] == 0
    assert report['unreadable_detector_files'] == 0


def test_scientific_source_report_counts_profile_camera_and_type():
    with tempfile.TemporaryDirectory() as tmpdir:
        metadata_path = Path(tmpdir).joinpath('frame_metadata.jsonl')
        _write_jsonl(metadata_path, [
            _metadata(camera_id=1, profile_id='imx708-wide', raw_path='/tmp/fake.raw', detector_image_type='raw'),
            _metadata(camera_id=2, profile_id='asi678mc', fits_path='/tmp/fake.fit', detector_image_type='fits'),
        ])

        report = build_scientific_source_offline_report(metadata_path, check_files=False)

    assert report['counts_by_profile_id'] == {'asi678mc': 1, 'imx708-wide': 1}
    assert report['counts_by_camera_id'] == {'1': 1, '2': 1}
    assert report['counts_by_detector_image_type'] == {'fits': 1, 'raw': 1}


def test_scientific_source_report_tolerates_fits_header_failure():
    with tempfile.TemporaryDirectory() as tmpdir:
        fake_fits = Path(tmpdir).joinpath('fake.fit')
        fake_fits.write_text('not a fits file', encoding='utf-8')
        metadata_path = Path(tmpdir).joinpath('frame_metadata.jsonl')
        _write_jsonl(metadata_path, [_metadata(fits_path=str(fake_fits), detector_image_type='fits')])

        report = build_scientific_source_offline_report(
            metadata_path,
            check_files=True,
            inspect_fits_headers=True,
        )

    assert report['existing_detector_files'] == 1
    assert report['missing_detector_files'] == 0
    assert report['fits_headers_read'] == 0
    assert report['fits_header_failures'] + report['fits_header_inspection_unavailable'] == 1


def test_scientific_source_text_summary_empty_report():
    summary = render_scientific_source_text_summary({}, date='2026-06-26')

    assert 'Scientific Source Summary - 2026-06-26' in summary
    assert 'Frames: 0' in summary
    assert 'FITS warnings' not in summary


def test_scientific_source_text_summary_populated_report():
    summary = render_scientific_source_text_summary({
        'scientific_frames_total': 2,
        'frames_with_detector_path': 2,
        'existing_detector_files': 1,
        'missing_detector_files': 1,
        'counts_by_detector_image_type': {'fits': 1, 'raw': 1},
        'counts_by_profile_id': {'asi678mc': 1, 'imx708-wide': 1},
        'counts_by_camera_id': {'1': 1, '2': 1},
        'fits_header_failures': 1,
        'fits_header_inspection_unavailable': 0,
        'malformed_lines': 1,
    })

    assert 'Frames: 2' in summary
    assert 'Detector paths: 2' in summary
    assert 'Existing files: 1' in summary
    assert 'Missing files: 1' in summary
    assert 'Types: fits=1, raw=1' in summary
    assert 'FITS warnings: failures=1, unavailable=0' in summary
    assert 'Warning: malformed JSONL lines: 1' in summary


if __name__ == '__main__':
    test_scientific_source_report_missing_metadata_file_is_safe()
    test_scientific_source_report_counts_malformed_lines()
    test_scientific_source_report_counts_rows_without_detector_path()
    test_scientific_source_report_fake_detector_path_missing_when_checked()
    test_scientific_source_report_fake_detector_path_not_checked_when_disabled()
    test_scientific_source_report_counts_profile_camera_and_type()
    test_scientific_source_report_tolerates_fits_header_failure()
    test_scientific_source_text_summary_empty_report()
    test_scientific_source_text_summary_populated_report()
    print('scientific source report tests OK')
