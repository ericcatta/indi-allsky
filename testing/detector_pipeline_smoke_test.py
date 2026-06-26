#!/usr/bin/env python3
import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from indi_allsky.detector_result import DetectorContract
from indi_allsky.detector_result import DetectorEvidence
from indi_allsky.detector_result import DetectorResult
from indi_allsky.detector_result import DetectorRunContext
from indi_allsky.detector_result import DetectorRunner
from indi_allsky.detector_result import build_detector_result_offline_report
from indi_allsky.detector_result import convert_detector_results_to_event_classifications_offline
from indi_allsky.detector_result import convert_detector_results_to_meteor_observations_offline
from indi_allsky.detector_result import render_detector_result_text_summary
from indi_allsky.scientific_frame import ScientificFrame
from indi_allsky.scientific_frame import build_scientific_frame_sequence


DEFAULT_BASE_DIR = Path('/tmp/indi-allsky-detector-pipeline-smoke')
DEFAULT_DATE = '2026-06-26'


class SyntheticDetector(DetectorContract):
    detector_id = 'synthetic_detector_pipeline_smoke'
    detector_version = 'smoke_v1'
    detector_type = 'synthetic_contract_test'
    supported_labels = ('meteor_candidate',)
    required_input_type = 'ScientificFrameSequence'

    def detect(self, input_sequence, context=None):
        frames = list(input_sequence.frames)
        return [
            DetectorResult(
                detector_id=self.detector_id,
                detector_version=self.detector_version,
                detector_type=self.detector_type,
                status='candidate',
                label='meteor_candidate',
                confidence=0.55,
                profile_id=input_sequence.profile_id,
                camera_id=input_sequence.camera_id,
                sequence_id=input_sequence.sequence_id,
                timeline_id=context.timeline_id if context else '',
                evidence=[
                    DetectorEvidence(
                        evidence_type='synthetic_line_signal',
                        frame_ids=[1001, 1002],
                        timestamps_utc=[frame.timestamp for frame in frames],
                        camera_id=input_sequence.camera_id,
                        profile_id=input_sequence.profile_id,
                        score=42.0,
                        confidence=0.55,
                        geometry={
                            'line': {
                                'x1': 10,
                                'y1': 20,
                                'x2': 120,
                                'y2': 220,
                            },
                        },
                        metrics={
                            'synthetic_frame_count': input_sequence.frame_count,
                        },
                        reasons=['synthetic_detector_pipeline_smoke'],
                        created_at='{0:s}T22:00:03+00:00'.format(DEFAULT_DATE),
                    ),
                ],
                reasons=['synthetic_detector_pipeline_smoke'],
                created_at='{0:s}T22:00:04+00:00'.format(DEFAULT_DATE),
            ),
        ]


def build_synthetic_sequence(date):
    return build_scientific_frame_sequence([
        ScientificFrame(
            timestamp='{0:s}T22:00:00+00:00'.format(date),
            camera_uuid='synthetic-camera-uuid',
            camera_id=2,
            profile_id='asi678mc',
            source_image_path='/synthetic/nonexistent/frame-1001.fits',
            detector_image_path='/synthetic/nonexistent/frame-1001.fits',
            detector_image_type='fits',
            fits_path='/synthetic/nonexistent/frame-1001.fits',
            bit_depth=16,
            width=3840,
            height=2160,
            exposure=0.021,
            gain=300.0,
            binning=1,
            is_lossless=True,
            is_calibrated=False,
        ),
        ScientificFrame(
            timestamp='{0:s}T22:00:02+00:00'.format(date),
            camera_uuid='synthetic-camera-uuid',
            camera_id=2,
            profile_id='asi678mc',
            source_image_path='/synthetic/nonexistent/frame-1002.fits',
            detector_image_path='/synthetic/nonexistent/frame-1002.fits',
            detector_image_type='fits',
            fits_path='/synthetic/nonexistent/frame-1002.fits',
            bit_depth=16,
            width=3840,
            height=2160,
            exposure=0.021,
            gain=300.0,
            binning=1,
            is_lossless=True,
            is_calibrated=False,
        ),
    ])


def cleanup(base_dir):
    if base_dir.exists():
        shutil.rmtree(base_dir)
        return True
    return False


def print_summary(summary):
    for key in (
            'detector_result_path',
            'event_classification_path',
            'meteor_observation_path',
            'total_results',
            'labels_count',
            'detector_summary_text',
            'classifications_written',
            'observations_written',
    ):
        value = summary.get(key)
        if isinstance(value, (dict, list)):
            value = json.dumps(value, sort_keys=True)
        print('{0:s}={1}'.format(key, value))


def run_smoke(base_dir, date):
    cleanup(base_dir)

    detector_result_dir = base_dir.joinpath('detector_results')
    event_classification_dir = base_dir.joinpath('event_classifications')
    meteor_observation_dir = base_dir.joinpath('meteor_observations')

    sequence = build_synthetic_sequence(date)
    context = DetectorRunContext.from_sequence(
        sequence,
        mode='offline_smoke',
        timeline_id='synthetic-timeline-smoke-v1',
        created_at='{0:s}T22:00:05+00:00'.format(date),
    )

    runner_summary = DetectorRunner(
        SyntheticDetector(),
        output_dir=detector_result_dir,
    ).run(sequence, context=context)

    detector_result_path = detector_result_dir.joinpath('{0:s}.jsonl'.format(date))
    report = build_detector_result_offline_report(detector_result_path)
    text_summary = render_detector_result_text_summary(report, date=date)

    classification_summary = convert_detector_results_to_event_classifications_offline(
        detector_result_path,
        output_dir=event_classification_dir,
    )
    meteor_summary = convert_detector_results_to_meteor_observations_offline(
        detector_result_path,
        output_dir=meteor_observation_dir,
    )

    classification_path = event_classification_dir.joinpath('{0:s}.jsonl'.format(date))
    meteor_path = meteor_observation_dir.joinpath('{0:s}.jsonl'.format(date))
    classification_rows = _read_jsonl(classification_path)
    meteor_rows = _read_jsonl(meteor_path)

    assert runner_summary['total_results'] == 1
    assert runner_summary['labels_count'] == {'meteor_candidate': 1}
    assert report['counts_by_label'] == {'meteor_candidate': 1}
    assert report['counts_by_detector_id'] == {'synthetic_detector_pipeline_smoke': 1}
    assert 'meteor_candidate=1' in text_summary
    assert classification_summary['classifications_written'] == 1
    assert meteor_summary['observations_written'] == 1
    assert classification_rows[0]['schema_version'] == 'event_classification_v1'
    assert classification_rows[0]['label'] == 'meteor_candidate'
    assert meteor_rows[0]['schema_version'] == 'meteor_observation_v1'
    assert meteor_rows[0]['status'] == 'shadow'
    assert meteor_rows[0]['validation_state'] == 'unknown'

    return {
        'detector_result_path': str(detector_result_path),
        'event_classification_path': str(classification_path),
        'meteor_observation_path': str(meteor_path),
        'total_results': runner_summary['total_results'],
        'labels_count': report['counts_by_label'],
        'detector_summary_text': text_summary.replace('\n', ' | '),
        'classifications_written': classification_summary['classifications_written'],
        'observations_written': meteor_summary['observations_written'],
    }


def _read_jsonl(path):
    return [
        json.loads(line)
        for line in path.read_text(encoding='utf-8').splitlines()
        if line.strip()
    ]


def main():
    parser = argparse.ArgumentParser(description='Run synthetic detector pipeline smoke test without real images.')
    parser.add_argument('--date', default=DEFAULT_DATE, help='Synthetic date, default: {0:s}'.format(DEFAULT_DATE))
    parser.add_argument('--output-dir', default=str(DEFAULT_BASE_DIR), help='Temporary output directory.')
    parser.add_argument('--cleanup', action='store_true', help='Remove synthetic smoke-test output before running.')
    args = parser.parse_args()

    base_dir = Path(args.output_dir)
    if args.cleanup:
        removed = cleanup(base_dir)
        print('cleanup_removed={0}'.format('true' if removed else 'false'))

    summary = run_smoke(base_dir, args.date)
    print('Detector pipeline smoke test OK')
    print_summary(summary)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
