#!/usr/bin/env python3
"""Capture phase changes must not split one frame's archive/rendering context."""
from copy import deepcopy
from multiprocessing import Array
from types import SimpleNamespace
from hybrid_runtime_fixture import isolated_app

with isolated_app(multi_camera=True) as app, app.app_context():
    from indi_allsky.image import ImageWorker
    from indi_allsky.config import IndiAllSkyConfigBase
    from indi_allsky.archive_policy import ArchivePolicy

    def state(phase):
        return SimpleNamespace(position_av=Array('f', [46, 8, 200]),
            exposure_av=Array('f', [1]*8), gain_av=Array('f', [0]*8),
            binning_av=Array('i', [1]), sensors_temp_av=Array('f', [0]*60),
            sensors_user_av=Array('f', [0]*110), night_av=Array('i', phase),
            astro_av=Array('f', [0]*3))

    config = deepcopy(IndiAllSkyConfigBase().base_config)
    config.update(MULTI_CAMERA_CAPTURE_ENABLE=True,
        IMAGE_FOLDER=app.config['INDI_ALLSKY_IMAGE_FOLDER'],
        IMAGE_ARCHIVE={'NIGHT': 'fits', 'DAY': 'processed'})
    base, first, second = state([1, 0]), state([1, 0]), state([0, 0])
    worker = ImageWorker(1, config, None, None, None,
        base.position_av, base.exposure_av, base.gain_av, base.binning_av,
        base.sensors_temp_av, base.sensors_user_av, base.night_av, base.astro_av,
        camera_shared_state_map={'one': first, 'two': second})
    snapshot = worker.night_av
    assert worker.image_processor.night_av is snapshot
    assert worker._miscUpload.night_av is snapshot
    for profile, live, next_phase in [('one', first, [0, 0]), ('two', second, [1, 1])]:
        worker._select_shared_state(profile)
        worker._select_image_processor(profile, 1 if profile == 'one' else 2, False)
        before = snapshot[:]
        archive = ArchivePolicy.from_config(config, bool(snapshot[0]))
        live.night_av[:] = next_phase  # Capture changes while this frame is processed.
        assert snapshot == before
        assert worker.image_processor.night_av == before
        assert worker._miscUpload.night_av == before
        assert ArchivePolicy.from_config(config, bool(snapshot[0])).mode == archive.mode
        worker._select_shared_state(profile)  # Next frame picks up the transition.
        assert snapshot == next_phase and worker.night_av is snapshot
        assert worker.image_processor.night_av is snapshot
    worker.camera_shared_state_map = {}
    base.night_av[:] = [0, 0]
    worker._select_shared_state('default')
    assert snapshot == [0, 0]
    base.night_av[:] = [1, 1]
    assert snapshot == [0, 0]  # Single camera has the same isolation.
    worker._select_shared_state('default')
    assert snapshot == [1, 1]
    worker.camera_shared_state_map = {'default': second}
    worker._select_shared_state('unknown')
    assert snapshot == second.night_av[:]
print('Frame phase snapshot: actual worker, cached processors, uploader, archive, both transitions and fallback PASS')
