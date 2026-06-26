import json
from collections import Counter
from pathlib import Path

from .scientific_frame_provider import ScientificFrameProvider


def build_scientific_source_offline_report(
        frame_metadata_path,
        max_rows=None,
        check_files=True,
        inspect_fits_headers=True,
):
    rows, malformed_lines, total_lines = _load_jsonl_rows(frame_metadata_path, max_rows=max_rows)
    provider = ScientificFrameProvider()

    profile_counter = Counter()
    camera_counter = Counter()
    detector_type_counter = Counter()
    fits_shape_counter = Counter()
    fits_bitpix_counter = Counter()

    frames_with_source_path = 0
    frames_with_detector_path = 0
    existing_detector_files = 0
    missing_detector_files = 0
    unreadable_detector_files = 0
    fits_headers_read = 0
    fits_header_failures = 0
    fits_header_inspection_unavailable = 0

    for row in rows:
        frame = provider.from_frame_metadata(row)
        _count_value(profile_counter, frame.profile_id)
        _count_value(camera_counter, frame.camera_id)
        _count_value(detector_type_counter, frame.detector_image_type)

        if frame.source_image_path:
            frames_with_source_path += 1
        if frame.detector_image_path:
            frames_with_detector_path += 1

        if not check_files or not frame.detector_image_path:
            continue

        detector_path = Path(frame.detector_image_path)
        if not detector_path.exists():
            missing_detector_files += 1
            continue

        if not detector_path.is_file():
            unreadable_detector_files += 1
            continue

        try:
            with detector_path.open('rb'):
                pass
        except OSError:
            unreadable_detector_files += 1
            continue

        existing_detector_files += 1

        if inspect_fits_headers and frame.detector_image_type in ('fits', 'fits.gz'):
            header_info = _inspect_fits_header(detector_path)
            if header_info['status'] == 'ok':
                fits_headers_read += 1
                _count_value(fits_shape_counter, header_info.get('shape'))
                _count_value(fits_bitpix_counter, header_info.get('bitpix'))
            elif header_info['status'] == 'unavailable':
                fits_header_inspection_unavailable += 1
            else:
                fits_header_failures += 1

    scientific_frames_total = len(rows)
    return {
        'total_metadata_lines': total_lines,
        'malformed_lines': malformed_lines,
        'scientific_frames_total': scientific_frames_total,
        'frames_with_source_path': frames_with_source_path,
        'frames_with_detector_path': frames_with_detector_path,
        'missing_source_path': scientific_frames_total - frames_with_source_path,
        'missing_detector_path': scientific_frames_total - frames_with_detector_path,
        'counts_by_profile_id': dict(sorted(profile_counter.items())),
        'counts_by_camera_id': dict(sorted(camera_counter.items())),
        'counts_by_detector_image_type': dict(sorted(detector_type_counter.items())),
        'existing_detector_files': existing_detector_files,
        'missing_detector_files': missing_detector_files,
        'unreadable_detector_files': unreadable_detector_files,
        'fits_headers_read': fits_headers_read,
        'fits_header_failures': fits_header_failures,
        'fits_header_inspection_unavailable': fits_header_inspection_unavailable,
        'counts_by_fits_shape': dict(sorted(fits_shape_counter.items())),
        'counts_by_fits_bitpix': dict(sorted(fits_bitpix_counter.items())),
    }


def render_scientific_source_text_summary(report, date=None):
    report = report or {}
    lines = []

    title = 'Scientific Source Summary'
    if date:
        title = '{0:s} - {1:s}'.format(title, _string_value(date))
    lines.append(title)
    lines.append('Frames: {0:d}'.format(_int_value(report.get('scientific_frames_total'))))
    lines.append('Detector paths: {0:d}'.format(_int_value(report.get('frames_with_detector_path'))))
    lines.append('Existing files: {0:d}'.format(_int_value(report.get('existing_detector_files'))))
    lines.append('Missing files: {0:d}'.format(_int_value(report.get('missing_detector_files'))))

    detector_types = _dict_value(report.get('counts_by_detector_image_type'))
    if detector_types:
        lines.append('Types: {0:s}'.format(_format_counts(detector_types)))

    profile_counts = _dict_value(report.get('counts_by_profile_id'))
    if profile_counts:
        lines.append('Profiles: {0:s}'.format(_format_counts(profile_counts)))

    camera_counts = _dict_value(report.get('counts_by_camera_id'))
    if camera_counts:
        lines.append('Cameras: {0:s}'.format(_format_counts(camera_counts)))

    fits_warnings = _int_value(report.get('fits_header_failures')) + _int_value(report.get('fits_header_inspection_unavailable'))
    if fits_warnings:
        lines.append(
            'FITS warnings: failures={0:d}, unavailable={1:d}'.format(
                _int_value(report.get('fits_header_failures')),
                _int_value(report.get('fits_header_inspection_unavailable')),
            )
        )

    malformed_lines = _int_value(report.get('malformed_lines'))
    if malformed_lines:
        lines.append('Warning: malformed JSONL lines: {0:d}'.format(malformed_lines))

    return '\n'.join(lines)


def _load_jsonl_rows(path, max_rows=None):
    if not path:
        return [], 0, 0

    path = Path(path)
    if not path.exists() or not path.is_file():
        return [], 0, 0

    rows = []
    malformed = 0
    total = 0
    max_rows = int(max_rows) if max_rows is not None else None
    with path.open('r', encoding='utf-8') as f_jsonl:
        for line in f_jsonl:
            line = line.strip()
            if not line:
                continue
            if max_rows is not None and total >= max_rows:
                break
            total += 1
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                malformed += 1
                continue
            if isinstance(row, dict):
                rows.append(row)
            else:
                malformed += 1
    return rows, malformed, total


def _inspect_fits_header(path):
    try:
        from astropy.io import fits
    except ImportError:
        return {'status': 'unavailable'}

    try:
        header = fits.getheader(path, 0)
    except Exception:
        return {'status': 'failed'}

    width = header.get('NAXIS1')
    height = header.get('NAXIS2')
    bitpix = header.get('BITPIX')
    shape = ''
    if width and height:
        shape = '{0:d}x{1:d}'.format(int(width), int(height))

    return {
        'status': 'ok',
        'shape': shape,
        'bitpix': bitpix,
    }


def _count_value(counter, value):
    value = _string_value(value)
    if value:
        counter[value] += 1


def _string_value(value):
    if value is None:
        return ''
    return str(value)


def _dict_value(value):
    if value is None:
        return {}
    return dict(value)


def _int_value(value):
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _format_counts(counts):
    return ', '.join(
        '{0:s}={1:d}'.format(_string_value(key), _int_value(value))
        for key, value in sorted(_dict_value(counts).items())
    )
