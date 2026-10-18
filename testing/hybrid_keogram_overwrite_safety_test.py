#!/usr/bin/env python3
"""Generated-output overwrite keeps durable predecessors until publish."""
import argparse
from copy import deepcopy
from datetime import date, datetime
import hashlib
from pathlib import Path
from queue import Queue
from unittest.mock import patch

from sqlalchemy.exc import OperationalError

from hybrid_runtime_fixture import isolated_app
from hybrid_generation_fixture import seed_generation, seed_preview_frames


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(runtime_config):
    with isolated_app(runtime_config, multi_camera=True) as app:
        seed_generation(app)
        seed_preview_frames(app)
        from indi_allsky.flask import db
        from indi_allsky.flask.models import IndiAllSkyDbConfigTable as Config
        from indi_allsky.flask.models import IndiAllSkyDbCameraTable as Camera
        from indi_allsky.flask.models import IndiAllSkyDbKeogramTable as Keogram
        from indi_allsky.flask.models import IndiAllSkyDbStarTrailsTable as Startrail
        from indi_allsky.flask.models import IndiAllSkyDbStarTrailsVideoTable as StarVideo
        from indi_allsky.flask.models import IndiAllSkyDbThumbnailTable as Thumbnail
        from indi_allsky.flask.models import IndiAllSkyDbTaskQueueTable as Task
        from indi_allsky.flask.models import TaskQueueQueue as QueueName, TaskQueueState as State
        from indi_allsky.exceptions import TimelapseException
        from PIL import Image

        with patch('indi_allsky.flask.create_app', return_value=app):
            from indi_allsky.video import VideoWorker, KeogramGenerator, TimelapseGenerator
            from indi_allsky.generated_output_replacement import GeneratedOutputReplacement

        with app.app_context():
            config = deepcopy(db.session.get(Config, 1).data)
            config.update(
                FFMPEG_CODEC='libx264', FFMPEG_FRAMERATE=10,
                FFMPEG_EXTRA_OPTIONS='', FFMPEG_VFSCALE='',
                TIMELAPSE_SKIP_FRAMES=0, TIMELAPSE_OVERWRITE=True,
                KEOGRAM_LABEL=False, KEOGRAM_H_SCALE=100, KEOGRAM_V_SCALE=100,
                STARTRAILS_SUN_ALT_THOLD=91, STARTRAILS_MOONMODE_THOLD=False,
                STARTRAILS_MOON_ALT_THOLD=91, STARTRAILS_MOON_PHASE_THOLD=101,
                STARTRAILS_MAX_ADU=255, STARTRAILS_MASK_THOLD=255,
                STARTRAILS_MIN_STARS=0, STARTRAILS_TIMELAPSE=True,
                STARTRAILS_TIMELAPSE_MINFRAMES=250,
            )
            config['TIMELAPSE'].update(PRE_PROCESSOR='standard', USE_NIGHT_CONFIG=True,
                                        FFMPEG_REPORT=False)
            config['FILETRANSFER'] = {}
            config['S3UPLOAD'] = {'ENABLE': False}
            config['SYNCAPI'] = {'ENABLE': False}
            config['YOUTUBE'] = {}
            row = db.session.get(Config, 1)
            row.data = config
            db.session.commit()

        worker = VideoWorker(98, config, Queue(), Queue(), Queue(), [1, 0], [1])
        root = Path(app.config['INDI_ALLSKY_IMAGE_FOLDER']).resolve()
        fixed_now = datetime.now().replace(microsecond=0)
        token = int(fixed_now.timestamp())

        class FixedDateTime(datetime):
            @classmethod
            def now(cls, tz=None):
                if tz is None:
                    return cls.fromtimestamp(fixed_now.timestamp())
                return cls.fromtimestamp(fixed_now.timestamp(), tz=tz)

        with app.app_context():
            camera = db.session.get(Camera, 1)
            folder = worker._getVideoFolder(date.today(), camera)
            paths = {
                'keogram': folder / ('allsky-keogram_ccd1_%s_night_%d.jpg' % (date.today().strftime('%Y%m%d'), token)),
                'startrail': folder / ('allsky-startrail_ccd1_%s_night_%d.jpg' % (date.today().strftime('%Y%m%d'), token)),
                'startrail-video': folder / ('allsky-startrail_timelapse_ccd1_%s_night_%d.mp4' % (date.today().strftime('%Y%m%d'), token)),
            }
            Image.new('RGB', (64, 48), (3, 4, 5)).save(paths['keogram'])
            Image.new('RGB', (64, 48), (6, 7, 8)).save(paths['startrail'])
            paths['startrail-video'].write_bytes(b'durable-old-video')
            old_rows = {
                'keogram': Keogram(filename=str(paths['keogram'].relative_to(root)), camera_id=1,
                                   dayDate=date.today(), night=True, success=True, frames=9,
                                   fileSize=paths['keogram'].stat().st_size, data={}),
                'startrail': Startrail(filename=str(paths['startrail'].relative_to(root)), camera_id=1,
                                       dayDate=date.today(), night=True, success=True, frames=9,
                                       fileSize=paths['startrail'].stat().st_size, data={}),
                'startrail-video': StarVideo(filename=str(paths['startrail-video'].relative_to(root)), camera_id=1,
                                             dayDate=date.today(), night=True, success=True, frames=9,
                                             framerate=10, fileSize=paths['startrail-video'].stat().st_size,
                                             data={}),
            }
            db.session.add_all(old_rows.values())
            db.session.commit()
            old_ids = {kind: row.id for kind, row in old_rows.items()}
            old_hashes = {kind: digest(path) for kind, path in paths.items()}

            # Simulate a process death after candidate rows/files were committed.
            abandoned_path = folder / ('abandoned-%d.jpg' % token)
            abandoned_path.write_bytes(b'abandoned-candidate')
            abandoned = Keogram(filename=str(abandoned_path.relative_to(root)), camera_id=1,
                                 dayDate=date.today(), night=True, success=False, frames=0,
                                 fileSize=abandoned_path.stat().st_size,
                                 data={'_replacement_candidate': {'task_id': 999, 'token': token}})
            db.session.add(abandoned)
            db.session.commit()
            abandoned_id = abandoned.id

        def submit():
            with app.app_context():
                task = Task(queue=QueueName.VIDEO, state=State.QUEUED,
                            data={'action': 'generateKeogramStarTrails',
                                  'kwargs': {'timespec': date.today().strftime('%Y%m%d'),
                                             'night': True, 'camera_id': 1}})
                db.session.add(task)
                db.session.commit()
                task_id = task.id
                worker.processTask({'task_id': task_id, 'profile_id': 'test-profile-1', 'camera_id': 1})
                db.session.expire_all()
                return db.session.get(Task, task_id)

        def assert_old_unchanged():
            with app.app_context():
                for kind, model in (('keogram', Keogram), ('startrail', Startrail),
                                    ('startrail-video', StarVideo)):
                    row = db.session.get(model, old_ids[kind])
                    assert row is not None and row.success
                    path = Path(row.getFilesystemPath())
                    assert path.is_file() and digest(path) == old_hashes[kind]
                    assert model.query.filter_by(camera_id=1, dayDate=date.today(), night=True).count() == 1

        original_process = KeogramGenerator.processImage
        processed = []

        def fail_after_processing(generator, *args, **kwargs):
            original_process(generator, *args, **kwargs)
            processed.append(True)
            raise RuntimeError('render failed after first accepted frame')

        with patch('indi_allsky.video.datetime', FixedDateTime), \
                patch.object(KeogramGenerator, 'processImage', fail_after_processing):
            failed = submit()
        assert processed and failed.state == State.FAILED
        assert_old_unchanged()
        with app.app_context():
            assert db.session.get(Keogram, abandoned_id) is None
            assert not abandoned_path.exists()

        original_commit = GeneratedOutputReplacement._commit
        commit_calls = []

        def fail_publish_once(replacement):
            if not commit_calls:
                commit_calls.append(True)
                raise OperationalError('publish replacement', {}, RuntimeError('forced commit failure'))
            return original_commit(replacement)

        with patch('indi_allsky.video.datetime', FixedDateTime), \
                patch.object(GeneratedOutputReplacement, '_commit', fail_publish_once):
            commit_failed = submit()
        assert commit_failed.state == State.FAILED and commit_calls
        assert_old_unchanged()

        # Valid Keogram/Startrail candidates replace their predecessors. The
        # same-second old names force selection of a different filename token.
        with patch('indi_allsky.video.datetime', FixedDateTime):
            replaced = submit()
        assert replaced.state == State.SUCCESS
        with app.app_context():
            new_kg = Keogram.query.filter_by(camera_id=1).one()
            new_st = Startrail.query.filter_by(camera_id=1).one()
            old_video = db.session.get(StarVideo, old_ids['startrail-video'])
            assert new_kg.id != old_ids['keogram'] and new_st.id != old_ids['startrail']
            assert Path(new_kg.getFilesystemPath()).is_file() and Path(new_st.getFilesystemPath()).is_file()
            assert str(token + 1) in new_kg.filename and str(token + 1) in new_st.filename
            assert old_video is not None and digest(old_video.getFilesystemPath()) == old_hashes['startrail-video']
            assert 'existing output preserved' in replaced.data['generation_outcome']['outputs'][2]['reason']
            prior_startrail_id = new_st.id
            prior_startrail_hash = digest(new_st.getFilesystemPath())

        # A zero-eligible-frame retry replaces only the valid Keogram and keeps
        # the prior Startrail and Startrail video.
        worker.config['STARTRAILS_MAX_ADU'] = 0
        with patch('indi_allsky.video.datetime', FixedDateTime):
            partial = submit()
        assert partial.state == State.SUCCESS
        with app.app_context():
            saved_st = db.session.get(Startrail, prior_startrail_id)
            saved_video = db.session.get(StarVideo, old_ids['startrail-video'])
            assert saved_st is not None and digest(saved_st.getFilesystemPath()) == prior_startrail_hash
            assert saved_video is not None and digest(saved_video.getFilesystemPath()) == old_hashes['startrail-video']
            outcome = partial.data['generation_outcome']
            assert outcome['status'] == 'partial'
            assert outcome['outputs'][1]['record_id'] == prior_startrail_id
            assert 'existing output preserved' in outcome['outputs'][1]['reason']

        # An encoder failure is reported as failed while the old video remains;
        # it must not be misreported as a newly generated video.
        worker.config['STARTRAILS_MAX_ADU'] = 255
        worker.config['STARTRAILS_TIMELAPSE_MINFRAMES'] = 3
        with patch('indi_allsky.video.datetime', FixedDateTime), \
                patch.object(TimelapseGenerator, 'generate', side_effect=TimelapseException('forced encoder failure')):
            encoder_failed = submit()
        assert encoder_failed.state == State.FAILED
        with app.app_context():
            saved_video = db.session.get(StarVideo, old_ids['startrail-video'])
            assert saved_video is not None and digest(saved_video.getFilesystemPath()) == old_hashes['startrail-video']
            video_result = encoder_failed.data['generation_outcome']['outputs'][2]
            assert video_result['status'] == 'failed'
            assert video_result['reason'] == 'Generation failed; existing output preserved'
            assert StarVideo.query.filter_by(camera_id=1).count() == 1

            # A pending thumbnail transfer protects its parent generated output.
            startrail = Startrail.query.filter_by(camera_id=1).one()
            thumbnail_path = root / 'pending-startrail-thumbnail.jpg'
            thumbnail_path.write_bytes(b'thumbnail')
            thumbnail = Thumbnail(uuid='pending-startrail-thumbnail', filename=str(thumbnail_path.relative_to(root)),
                                  camera_id=1, fileSize=thumbnail_path.stat().st_size, data={})
            db.session.add(thumbnail)
            db.session.commit()
            startrail.thumbnail_uuid = thumbnail.uuid
            db.session.commit()
            transfer = Task(queue=QueueName.UPLOAD, state=State.QUEUED,
                            data={'action': 1, 'model': type(thumbnail).__name__, 'id': thumbnail.id})
            db.session.add(transfer)
            db.session.commit()
            protected_ids = (Keogram.query.filter_by(camera_id=1).one().id,
                             startrail.id, StarVideo.query.filter_by(camera_id=1).one().id)

        pending = submit()
        assert pending.state == State.FAILED and 'pending transfer' in pending.result
        with app.app_context():
            assert protected_ids == (Keogram.query.filter_by(camera_id=1).one().id,
                                     Startrail.query.filter_by(camera_id=1).one().id,
                                     StarVideo.query.filter_by(camera_id=1).one().id)
            assert thumbnail_path.is_file()

        assert worker.upload_q.empty()
        print('Keogram overwrite lifecycle: render/commit rollback, interrupted recovery, same-second collision, partial preservation, encoder failure, and transfer guard PASS')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-config', default='/etc/indi-allsky/flask.json')
    args = parser.parse_args()
    run(args.runtime_config)
