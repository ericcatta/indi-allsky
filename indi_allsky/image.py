import os
import io
import json
import re
from pathlib import Path
from datetime import datetime
from datetime import timedelta
from datetime import timezone
import time
import functools
import tempfile
import shutil
import psutil
import subprocess
import copy
import signal
import logging
import traceback
#from pprint import pformat

from multiprocessing import Process
from multiprocessing import Queue
#from threading import Thread
import queue

import cv2
import numpy

from PIL import Image

from fractions import Fraction

from . import constants
from .auto_gain_controller import AutoGainController
from .auto_gain_runtime_state import AutoGainRuntimeStateStore
from .auto_gain_runtime_state import default_auto_gain_runtime_state_path
from .auto_exposure_controller import AutoExposureController
from .auto_meter import DEFAULT_AUTO_EXPOSURE_METERING_MODE
from .auto_meter import measure_auto_exposure
from .frame_metadata import FrameMetadata
from .frame_metadata import FrameMetadataWriter
from .frame_metadata import default_frame_metadata_path
from .multicamera_diag import write_multicamera_diag

from .processing import ImageProcessor
from .miscUpload import miscUpload
from .adsb import AdsbAircraftHttpWorker

from .flask import create_app
from .flask import db
from .flask.miscDb import miscDb

from .flask.models import TaskQueueState
from .flask.models import TaskQueueQueue
from .flask.models import IndiAllSkyDbCameraTable
from .flask.models import IndiAllSkyDbImageTable
from .flask.models import IndiAllSkyDbTaskQueueTable

from sqlalchemy import func
#from sqlalchemy.orm.exc import NoResultFound

from .exceptions import TimeOutException
from .exceptions import BadImage



app = create_app()

logger = logging.getLogger('indi_allsky')


def _multi_camera_diag(message, *args):
    write_multicamera_diag(message, *args)



class ImageWorker(Process):

    sqm_history_minutes = 30
    stars_history_minutes = 30

    auto_gain_exposure_cutoff_level_low = 80  # percent of max exposure


    def __init__(
        self,
        idx,
        config,
        error_q,
        image_q,
        upload_q,
        position_av,
        exposure_av,
        gain_av,
        binning_av,
        sensors_temp_av,
        sensors_user_av,
        night_av,
        astro_av,
        camera_shared_state_map=None,
        camera_config_map=None,
    ):
        super(ImageWorker, self).__init__()

        self.name = 'Image-{0:d}'.format(idx)

        self.base_config = config
        self.config = config
        self.camera_config_map = camera_config_map or {}
        # MULTI_CAMERA_PREP: default route context for the current
        # single-camera runtime. It is refreshed from each image_q payload.
        self.profile_id = 'default'
        self.current_camera_id = None
        self.adu_context_key = 'default:unknown'
        self._missing_profile_config_warned = set()
        self._missing_profile_shared_state_warned = set()

        self.error_q = error_q
        self.image_q = image_q
        self.upload_q = upload_q

        self.position_av = position_av
        self.exposure_av = exposure_av
        self.gain_av = gain_av
        self.binning_av = binning_av

        self.sensors_temp_av = sensors_temp_av  # 0 ccd_temp
        self.sensors_user_av = sensors_user_av
        self.night_av = night_av
        self.astro_av = astro_av
        self.hybrid_av = None
        self.camera_shared_state_map = camera_shared_state_map or {}

        self.filename_t = 'ccd{0:d}_{1:s}.{2:s}'

        self.adsb_worker = None
        self.adsb_worker_idx = 0
        self.adsb_aircraft_q = None
        self.adsb_aircraft_list = []

        self.adu_states = {}
        self.adu_state = self._new_adu_state()
        self.adu_states[self.adu_context_key] = self.adu_state
        self.auto_meter_context_key = self.adu_context_key
        self.auto_meter_states = {}
        self.auto_meter_states[self.auto_meter_context_key] = self._new_auto_meter_state()
        self.auto_exposure_controller = AutoExposureController()
        self.auto_gain_states = {}
        self.auto_gain_states[self.auto_meter_context_key] = self._new_auto_gain_state()
        self.auto_gain_controller = AutoGainController()
        self.hybrid_awb_backend_warned = set()
        self.processing_config_logged = set()
        self.asi_frame_stats_counts = {}
        self.generate_mask_base = True

        self.sqm_value = 0

        self.image_count = 0
        self.metadata_count = 0

        self.image_processor = ImageProcessor(
            self.config,
            self.position_av,
            self.gain_av,
            self.binning_av,
            self.sensors_temp_av,
            self.sensors_user_av,
            self.night_av,
            self.astro_av,
        )
        self.image_processors = {}

        self._miscDb = miscDb(self.config)
        self._miscUpload = miscUpload(
            self.config,
            self.upload_q,
            self.night_av,
        )


        self._gain_step = None  # legacy fallback, per-camera state is authoritative after context selection
        self.auto_gain_step_list = None  # list of fixed gain values
        self.auto_gain_exposure_cutoff_low = None
        self.auto_gain_exposure_cutoff_mid = None
        self.auto_gain_exposure_cutoff_high = None


        self.image_save_hook_process = None  # used for both pre- and post-hooks
        self.image_save_hook_process_start = 0
        self.pre_hook_datajson_name_p = None


        self.next_save_fits_offset = self.config.get('IMAGE_SAVE_FITS_PERIOD', 7200)
        self.next_save_fits_time = time.time() + self.next_save_fits_offset

        self._libcamera_raw = False

        if self.config.get('IMAGE_FOLDER'):
            self.image_dir = Path(self.config['IMAGE_FOLDER']).absolute()
        else:
            self.image_dir = Path(__file__).parent.parent.joinpath('html', 'images').absolute()


        varlib_folder = self.config.get('VARLIB_FOLDER', '/var/lib/indi-allsky')
        self.varlib_folder_p = Path(varlib_folder)
        self.frame_metadata_writer = FrameMetadataWriter(
            self.config.get('FRAME_METADATA_PATH', default_frame_metadata_path(self.varlib_folder_p))
        )
        self.auto_gain_runtime_state_store = AutoGainRuntimeStateStore(
            self.config.get('AUTO_GAIN_RUNTIME_STATE_PATH', default_auto_gain_runtime_state_path(self.varlib_folder_p)),
            max_age_seconds=self.config.get('AUTO_GAIN_RESTORE_MAX_AGE_SECONDS', 86400),
        )


        self._shutdown = False


    def _validate_profile_id(self, i_dict):
        # MULTI_CAMERA_PREP: accept a stable route id without changing image
        # routing. Missing/blank profile ids fall back to the legacy default.
        raw_profile_id = i_dict.get('profile_id', 'default')
        profile_id = str(raw_profile_id or 'default')

        if profile_id != raw_profile_id and raw_profile_id is not None:
            logger.warning('Invalid image profile_id, using default')
            return 'default'

        return profile_id


    def _set_queue_context(self, profile_id, camera_id):
        # MULTI_CAMERA_PREP: mirror the active image route on this worker and
        # on helpers that enqueue follow-up upload tasks.
        self.profile_id = profile_id
        self.current_camera_id = camera_id
        self._miscUpload.set_profile_context(profile_id, camera_id=camera_id)


    def _images_only_diag_enabled(self, images_only):
        return bool(images_only and self.config.get('MULTI_CAMERA_CAPTURE_ENABLE', False))


    def _images_only_diag(self, profile_id, camera_id, event, **kwargs):
        detail = ' '.join('{0:s}={1!s}'.format(k, v) for k, v in sorted(kwargs.items()))
        if detail:
            _multi_camera_diag(
                '[MULTI_CAMERA_DIAG][%s][camera_id=%s] %s %s',
                profile_id,
                camera_id,
                event,
                detail,
            )
        else:
            _multi_camera_diag(
                '[MULTI_CAMERA_DIAG][%s][camera_id=%s] %s',
                profile_id,
                camera_id,
                event,
            )


    def _new_image_processor(self):
        return ImageProcessor(
            self.config,
            self.position_av,
            self.gain_av,
            self.binning_av,
            self.sensors_temp_av,
            self.sensors_user_av,
            self.night_av,
            self.astro_av,
        )


    def _select_image_processor(self, profile_id, camera_id, images_only_diag):
        if not images_only_diag:
            return

        processor_key = '{0:s}:{1!s}'.format(profile_id, camera_id)
        try:
            processor = self.image_processors[processor_key]
            action = 'reuse'
        except KeyError:
            processor = self._new_image_processor()
            self.image_processors[processor_key] = processor
            action = 'create'

        self.image_processor = processor
        self._images_only_diag(
            profile_id,
            camera_id,
            'IMAGE_PROCESSOR_CONTEXT',
            action=action,
            processor_key=processor_key,
            processors=len(self.image_processors),
        )


    def _log_processing_config_once(self, profile_id, camera_id):
        processing_key = '{0:s}:{1!s}'.format(str(profile_id), camera_id)
        if processing_key in self.processing_config_logged:
            return

        self.processing_config_logged.add(processing_key)
        image_stretch_config = self.config.get('IMAGE_STRETCH') or {}
        logger.info(
            '[MULTI_CAMERA_PROCESSING_CONFIG][%s][camera_id=%s] camera_interface=%s cfa_pattern=%s ccd_bit_depth=%s auto_wb_day=%s auto_wb_night=%s wbr_day=%s wbg_day=%s wbb_day=%s gamma_day=%s image_stretch_daytime=%s daytime_contrast_enhance=%s daytime_grayscale=%s scnr_algorithm_day=%s hybrid_awb_backend=%s',
            profile_id,
            camera_id if camera_id is not None else 'unknown',
            self.config.get('CAMERA_INTERFACE'),
            self.config.get('CFA_PATTERN'),
            self.config.get('CCD_BIT_DEPTH'),
            self.config.get('AUTO_WB_DAY'),
            self.config.get('AUTO_WB'),
            self.config.get('WBR_FACTOR_DAY'),
            self.config.get('WBG_FACTOR_DAY'),
            self.config.get('WBB_FACTOR_DAY'),
            self.config.get('GAMMA_CORRECTION_DAY'),
            image_stretch_config.get('DAYTIME'),
            self.config.get('DAYTIME_CONTRAST_ENHANCE'),
            self.config.get('DAYTIME_GRAYSCALE'),
            self.config.get('SCNR_ALGORITHM_DAY'),
            self._hybrid_awb_backend(),
        )


    def _shape_for_diag(self, value):
        shape = getattr(value, 'shape', None)
        if shape is None:
            return None

        return 'x'.join(str(x) for x in shape)


    def _asi_frame_stats_should_log(self, profile_id, camera_id):
        camera_interface = str(self.config.get('CAMERA_INTERFACE') or '').lower()
        profile_match = str(profile_id or '').lower() == 'asi678mc'
        interface_match = camera_interface == 'indi' or camera_interface.startswith('indi_')

        if not profile_match and not interface_match:
            return False

        stats_key = '{0:s}:{1!s}'.format(str(profile_id or 'default'), camera_id)
        count = self.asi_frame_stats_counts.get(stats_key, 0) + 1
        self.asi_frame_stats_counts[stats_key] = count

        return count == 1 or count % 10 == 0


    def _asi_frame_stats_threshold(self, data, bit_depth=None):
        if numpy.issubdtype(data.dtype, numpy.integer):
            try:
                bit_depth_int = int(bit_depth or 0)
            except (TypeError, ValueError):
                bit_depth_int = 0

            if bit_depth_int > 8:
                max_value = float((2 ** bit_depth_int) - 1)
            else:
                max_value = float(numpy.iinfo(data.dtype).max)
        else:
            finite_max = float(numpy.nanmax(data)) if data.size else 0.0
            if finite_max <= 1.0:
                max_value = 1.0
            elif finite_max <= 255.0:
                max_value = 255.0
            elif bit_depth:
                try:
                    max_value = float((2 ** int(bit_depth)) - 1)
                except (TypeError, ValueError):
                    max_value = finite_max
            else:
                max_value = finite_max

        if max_value <= 255.0:
            return 250.0

        return max_value * (250.0 / 255.0)


    def _log_asi_frame_stats(self, enabled, stage, profile_id, camera_id, image, exposure=None, gain=None, binning=None, i_ref=None):
        if not enabled:
            return

        if image is None:
            logger.info(
                '[ASI_FRAME_STATS][%s][camera_id=%s] stage=%s status=skipped reason=no-image',
                profile_id,
                camera_id if camera_id is not None else 'unknown',
                stage,
            )
            return

        try:
            data = numpy.asarray(image)
            if data.size == 0:
                logger.info(
                    '[ASI_FRAME_STATS][%s][camera_id=%s] stage=%s status=skipped reason=empty-image shape=%s dtype=%s',
                    profile_id,
                    camera_id if camera_id is not None else 'unknown',
                    stage,
                    self._shape_for_diag(data),
                    data.dtype,
                )
                return

            if numpy.issubdtype(data.dtype, numpy.floating):
                samples = data[numpy.isfinite(data)]
            else:
                samples = data.reshape(-1)

            if samples.size == 0:
                logger.info(
                    '[ASI_FRAME_STATS][%s][camera_id=%s] stage=%s status=skipped reason=no-finite-samples shape=%s dtype=%s',
                    profile_id,
                    camera_id if camera_id is not None else 'unknown',
                    stage,
                    self._shape_for_diag(data),
                    data.dtype,
                )
                return

            image_bitpix = getattr(i_ref, 'image_bitpix', None)
            image_bayerpat = getattr(i_ref, 'image_bayerpat', None)
            detected_bit_depth = getattr(i_ref, 'detected_bit_depth', None)
            configured_bit_depth = self.config.get('CCD_BIT_DEPTH')
            bit_depth_for_threshold = configured_bit_depth or detected_bit_depth or image_bitpix
            threshold = self._asi_frame_stats_threshold(data, bit_depth=bit_depth_for_threshold)
            saturated_pct = (float(numpy.count_nonzero(samples >= threshold)) / float(samples.size)) * 100.0

            logger.info(
                '[ASI_FRAME_STATS][%s][camera_id=%s] stage=%s shape=%s dtype=%s min=%0.3f max=%0.3f mean=%0.3f median=%0.3f p95=%0.3f p99=%0.3f pct_ge_250_equiv=%0.3f threshold=%0.3f exposure=%s gain=%s binning=%s image_bitpix=%s detected_bit_depth=%s configured_bit_depth=%s processor_max_bit_depth=%s fits_bayerpat=%s config_cfa=%s camera_interface=%s',
                profile_id,
                camera_id if camera_id is not None else 'unknown',
                stage,
                self._shape_for_diag(data),
                data.dtype,
                float(numpy.min(samples)),
                float(numpy.max(samples)),
                float(numpy.mean(samples)),
                float(numpy.median(samples)),
                float(numpy.percentile(samples, 95.0)),
                float(numpy.percentile(samples, 99.0)),
                saturated_pct,
                threshold,
                exposure,
                gain,
                binning,
                image_bitpix,
                detected_bit_depth,
                configured_bit_depth,
                getattr(self.image_processor, 'max_bit_depth', None),
                image_bayerpat,
                self.config.get('CFA_PATTERN'),
                self.config.get('CAMERA_INTERFACE'),
            )
        except Exception as e:
            logger.warning(
                '[ASI_FRAME_STATS][%s][camera_id=%s] stage=%s status=error error=%s',
                profile_id,
                camera_id if camera_id is not None else 'unknown',
                stage,
                str(e),
            )


    def _processor_cache_diag(self, profile_id, camera_id, event, binning):
        processor = self.image_processor
        image_shape = self._shape_for_diag(getattr(processor, 'image', None))

        image_list_shapes = []
        for i_ref in getattr(processor, 'image_list', []):
            if not i_ref:
                continue

            image_list_shapes.append(self._shape_for_diag(getattr(i_ref, 'opencv_data', None)))

        detection_masks = getattr(processor, '_detection_mask_dict', None) or {}
        adu_masks = getattr(processor, '_adu_mask_dict', None) or {}
        image_circle_masks = getattr(processor, '_image_circle_alpha_mask_dict', None) or {}
        overlay_masks = getattr(processor, '_alpha_mask_dict', None) or {}

        self._images_only_diag(
            profile_id,
            camera_id,
            event,
            adu_mask_shape=self._shape_for_diag(adu_masks.get(binning)),
            detection_mask_shape=self._shape_for_diag(detection_masks.get(binning)),
            image_circle_mask_shape=self._shape_for_diag(image_circle_masks.get(binning)),
            image_list_shapes=','.join([s for s in image_list_shapes if s]) or None,
            image_shape=image_shape,
            logo_alpha_shape=self._shape_for_diag(overlay_masks.get(binning)),
        )


    def _auto_exposure_metering_mode(self):
        return str(self.config.get('AUTO_EXPOSURE_METERING_MODE', DEFAULT_AUTO_EXPOSURE_METERING_MODE) or DEFAULT_AUTO_EXPOSURE_METERING_MODE).strip().lower()


    def _auto_exposure_enabled(self):
        enabled = self.config.get('AUTO_EXPOSURE_ENABLED', False)
        if isinstance(enabled, bool):
            return enabled

        if isinstance(enabled, str):
            enabled_str = enabled.strip().lower()
            if enabled_str in ('1', 'true', 'yes', 'on', 'enabled'):
                return True
            if enabled_str in ('0', 'false', 'no', 'off', 'disabled'):
                return False

        return bool(enabled)


    def _new_auto_meter_state(self):
        return {
            'mode'            : None,
            'measured_value'  : None,
            'smoothed_value'  : None,
            'sample_count'    : 0,
            'excluded_pixels' : 0,
            'trend_count'     : 0,
            'trend_direction' : 'none',
            'last_decision'   : None,
        }


    def _new_auto_gain_state(self):
        return {
            'mode'               : None,
            'trend_count'        : 0,
            'trend_direction'    : 'none',
            'cooldown_remaining' : 0,
            'last_action'        : 'hold',
            'last_decision'      : None,
            'auto_gain_raised'   : False,
        }


    def _select_auto_meter_state(self, profile_id, camera_id, mode):
        auto_meter_key = self._adu_key(profile_id, camera_id)
        state = self.auto_meter_states.get(auto_meter_key)
        if state is None or state.get('mode') not in (None, mode):
            state = self._new_auto_meter_state()
            self.auto_meter_states[auto_meter_key] = state

        state['mode'] = mode
        self.auto_meter_context_key = auto_meter_key
        return state


    def _select_auto_gain_state(self, profile_id, camera_id, mode):
        auto_gain_key = self._adu_key(profile_id, camera_id)
        state = self.auto_gain_states.get(auto_gain_key)
        if state is None or state.get('mode') not in (None, mode):
            state = self._new_auto_gain_state()
            self.auto_gain_states[auto_gain_key] = state

        state['mode'] = mode
        return state


    def _update_auto_meter_state(self, profile_id, camera_id, result):
        alpha = 0.25
        state = self._select_auto_meter_state(profile_id, camera_id, result.mode)
        measured_value = float(result.measured_value)
        previous_smoothed = state.get('smoothed_value')
        if previous_smoothed is None:
            smoothed_value = measured_value
        else:
            smoothed_value = (float(previous_smoothed) * (1.0 - alpha)) + (measured_value * alpha)

        state['measured_value'] = measured_value
        state['smoothed_value'] = smoothed_value
        state['sample_count'] = int(result.sample_count)
        state['excluded_pixels'] = int(result.excluded_pixels)

        logger.info(
            '[AUTO_METER_STATE] profile=%s camera_id=%s mode=%s measured_value=%0.2f smoothed_value=%0.2f alpha=%0.2f sample_count=%d excluded_pixels=%d',
            profile_id,
            camera_id,
            result.mode,
            measured_value,
            smoothed_value,
            alpha,
            int(result.sample_count),
            int(result.excluded_pixels),
        )

        return state


    def _auto_exposure_runtime_float(self, runtime_next, runtime_current, fallback_value, fallback_source):
        for source, value in (
            ('runtime_next', runtime_next),
            ('runtime_current', runtime_current),
        ):
            try:
                runtime_value = float(value)
            except (TypeError, ValueError):
                continue

            if numpy.isfinite(runtime_value) and runtime_value >= 0.0:
                return runtime_value, source

        try:
            fallback_runtime_value = float(fallback_value)
        except (TypeError, ValueError):
            return None, 'missing'

        if numpy.isfinite(fallback_runtime_value):
            return fallback_runtime_value, fallback_source

        return None, 'missing'


    def _auto_exposure_config_float(self, key, default):
        try:
            value = float(self.config.get(key, default))
        except (TypeError, ValueError):
            return float(default)

        if not numpy.isfinite(value) or value <= 0.0:
            return float(default)

        return value


    def _auto_gain_config_float(self, key, default, allow_zero=False):
        try:
            value = float(self.config.get(key, default))
        except (TypeError, ValueError):
            return float(default)

        if not numpy.isfinite(value):
            return float(default)

        if value < 0.0 or (value == 0.0 and not allow_zero):
            return float(default)

        return value


    def _auto_gain_config_int(self, key, default):
        try:
            value = int(self.config.get(key, default))
        except (TypeError, ValueError):
            return int(default)

        if value <= 0:
            return int(default)

        return value


    def _auto_gain_config_bool(self, key, default=False):
        value = self.config.get(key, default)
        if isinstance(value, bool):
            return value

        if value is None:
            return bool(default)

        if isinstance(value, str):
            value_str = value.strip().lower()
            if value_str in ('1', 'true', 'yes', 'on', 'enabled'):
                return True
            if value_str in ('0', 'false', 'no', 'off', 'disabled'):
                return False

        return bool(value)


    def _auto_exposure_controller_inputs(self, mode):
        ccd_config = self.config.get('CCD_CONFIG') or {}
        is_day = not bool(self.night_av[constants.NIGHT_NIGHT])
        if self.night_av[constants.NIGHT_NIGHT]:
            target = self.config.get('TARGET_ADU', 75)
            exposure_min = self.exposure_av[constants.EXPOSURE_MIN_NIGHT]
            exposure_max = self.exposure_av[constants.EXPOSURE_MAX]
            if self.night_av[constants.NIGHT_MOONMODE]:
                mode_gain_config = ccd_config.get('MOONMODE') or {}
                gain_min = self.gain_av[constants.GAIN_MIN_MOONMODE]
                gain_max = self.gain_av[constants.GAIN_MAX_MOONMODE]
            else:
                mode_gain_config = ccd_config.get('NIGHT') or {}
                gain_min = self.gain_av[constants.GAIN_MIN_NIGHT]
                gain_max = self.gain_av[constants.GAIN_MAX_NIGHT]
        else:
            target = self.config.get('TARGET_ADU_DAY', 75)
            mode_gain_config = ccd_config.get('DAY') or {}
            exposure_min = self.exposure_av[constants.EXPOSURE_MIN_DAY]
            exposure_max = self.exposure_av[constants.EXPOSURE_MAX]
            gain_min = self.gain_av[constants.GAIN_MIN_DAY]
            gain_max = self.gain_av[constants.GAIN_MAX_DAY]

        allow_gain_control = True
        if is_day:
            allow_gain_control = self._auto_gain_enabled('day')

        exposure_runtime_current = self.exposure_av[constants.EXPOSURE_CURRENT]
        exposure_runtime_next = self.exposure_av[constants.EXPOSURE_NEXT]
        gain_runtime_current = self.gain_av[constants.GAIN_CURRENT]
        gain_runtime_next = self.gain_av[constants.GAIN_NEXT]

        current_exposure, source_exposure = self._auto_exposure_runtime_float(
            exposure_runtime_next,
            exposure_runtime_current,
            self.config.get('CCD_EXPOSURE_DEF'),
            'profile_default',
        )
        current_gain, source_gain = self._auto_exposure_runtime_float(
            gain_runtime_next,
            gain_runtime_current,
            mode_gain_config.get('GAIN'),
            'profile_gain',
        )

        return {
            'target'                   : target,
            'current_exposure'         : current_exposure,
            'current_gain'             : current_gain,
            'exposure_min'             : exposure_min,
            'exposure_max'             : exposure_max,
            'gain_min'                 : gain_min,
            'gain_max'                 : gain_max,
            'source_exposure'          : source_exposure,
            'source_gain'              : source_gain,
            'exposure_runtime_current' : exposure_runtime_current,
            'exposure_runtime_next'    : exposure_runtime_next,
            'gain_runtime_current'     : gain_runtime_current,
            'gain_runtime_next'        : gain_runtime_next,
            'is_day'                   : is_day,
            'allow_gain_control'       : allow_gain_control,
            'day_step_factor'          : self._auto_exposure_config_float('AUTO_EXPOSURE_DAY_STEP_FACTOR', 0.35),
            'day_min_step'             : self._auto_exposure_config_float('AUTO_EXPOSURE_DAY_MIN_STEP', 0.00025),
            'day_max_step'             : self._auto_exposure_config_float('AUTO_EXPOSURE_DAY_MAX_STEP', 0.005),
        }


    def _log_auto_exposure_decision_skipped(self, profile_id, camera_id, mode, reason):
        logger.info(
            '[AUTO_EXPOSURE_DECISION] profile=%s camera_id=%s mode=%s status=skipped reason=%s shadow=True',
            profile_id,
            camera_id,
            mode,
            reason,
        )


    def _log_auto_exposure_blocker(self, profile_id, camera_id, mode, decision):
        if decision.blocker == 'none':
            return

        logger.info(
            '[AUTO_EXPOSURE_BLOCKER] profile=%s camera_id=%s mode=%s blocker=%s action=%s reason=%s current_exposure=%0.8f proposed_exposure=%0.8f current_gain=%0.2f proposed_gain=%0.2f trend_active=%s trend_count=%d error=%+0.2f deadband=%0.2f shadow=%s',
            profile_id,
            camera_id,
            mode,
            decision.blocker,
            decision.action,
            decision.reason,
            decision.current_exposure,
            decision.proposed_exposure,
            decision.current_gain,
            decision.proposed_gain,
            decision.trend_active,
            decision.trend_count,
            decision.error,
            decision.deadband,
            decision.shadow,
        )


    def _decide_auto_exposure_shadow(self, profile_id, camera_id, result, state):
        smoothed_value = state.get('smoothed_value')
        if smoothed_value is None:
            self._log_auto_exposure_decision_skipped(profile_id, camera_id, result.mode, 'missing_smoothed_value')
            return None

        inputs = self._auto_exposure_controller_inputs(result.mode)
        missing_inputs = [
            key
            for key, value in inputs.items()
            if value is None and key not in (
                'source_exposure',
                'source_gain',
                'exposure_runtime_current',
                'exposure_runtime_next',
                'gain_runtime_current',
                'gain_runtime_next',
                'is_day',
                'allow_gain_control',
            )
        ]
        if missing_inputs:
            self._log_auto_exposure_decision_skipped(profile_id, camera_id, result.mode, 'missing_{0:s}'.format(','.join(missing_inputs)))
            return None

        try:
            target = float(inputs['target'])
            error = target - float(smoothed_value)
        except (TypeError, ValueError) as e:
            self._log_auto_exposure_decision_skipped(profile_id, camera_id, result.mode, str(e))
            return None

        trend_count = 0
        trend_direction = 'none'
        if abs(error) > self.auto_exposure_controller.inner_deadband:
            trend_direction = 'positive' if error > 0 else 'negative'
            if state.get('trend_direction') == trend_direction:
                trend_count = int(state.get('trend_count') or 0) + 1
            else:
                trend_count = 1

        state['trend_count'] = trend_count
        state['trend_direction'] = trend_direction

        try:
            decision = self.auto_exposure_controller.decide(
                smoothed_value=smoothed_value,
                current_exposure=inputs['current_exposure'],
                current_gain=inputs['current_gain'],
                exposure_min=inputs['exposure_min'],
                exposure_max=inputs['exposure_max'],
                gain_min=inputs['gain_min'],
                gain_max=inputs['gain_max'],
                target=inputs['target'],
                trend_count=trend_count,
                is_day=inputs['is_day'],
                day_step_factor=inputs['day_step_factor'],
                day_min_step=inputs['day_min_step'],
                day_max_step=inputs['day_max_step'],
                allow_gain_control=inputs['allow_gain_control'],
            )
        except (TypeError, ValueError) as e:
            self._log_auto_exposure_decision_skipped(profile_id, camera_id, result.mode, str(e))
            return None

        if abs(decision.error) > decision.deadband and decision.action != 'hold':
            state['trend_count'] = 0
            state['trend_direction'] = 'none'

        state['last_decision'] = decision
        self._log_auto_exposure_blocker(profile_id, camera_id, result.mode, decision)

        logger.info(
            '[AUTO_EXPOSURE_DECISION] profile=%s camera_id=%s mode=%s smoothed_value=%0.2f target=%0.2f error=%+0.2f deadband=%0.2f trend_count=%d trend_active=%s trend_direction=%s trend_step=%0.8f step_strategy=%s exposure_step=%0.8f day_step_factor=%0.5f day_min_step=%0.8f day_max_step=%0.8f allow_gain_control=%s action=%s reason=%s blocker=%s current_exposure=%0.8f proposed_exposure=%0.8f source_exposure=%s runtime_current_exposure=%0.8f runtime_next_exposure=%0.8f current_gain=%0.2f proposed_gain=%0.2f source_gain=%s runtime_current_gain=%0.2f runtime_next_gain=%0.2f shadow=%s',
            profile_id,
            camera_id,
            result.mode,
            smoothed_value,
            decision.target,
            decision.error,
            decision.deadband,
            decision.trend_count,
            decision.trend_active,
            decision.trend_direction,
            decision.trend_step,
            decision.step_strategy,
            decision.exposure_step,
            inputs['day_step_factor'],
            inputs['day_min_step'],
            inputs['day_max_step'],
            inputs['allow_gain_control'],
            decision.action,
            decision.reason,
            decision.blocker,
            decision.current_exposure,
            decision.proposed_exposure,
            inputs['source_exposure'],
            float(inputs['exposure_runtime_current']),
            float(inputs['exposure_runtime_next']),
            decision.current_gain,
            decision.proposed_gain,
            inputs['source_gain'],
            float(inputs['gain_runtime_current']),
            float(inputs['gain_runtime_next']),
            decision.shadow,
        )
        return decision


    def _log_auto_gain_decision_skipped(self, profile_id, camera_id, mode, reason):
        logger.info(
            '[AUTO_GAIN_DECISION] profile=%s camera_id=%s mode=%s status=skipped reason=%s shadow=True',
            profile_id,
            camera_id,
            mode,
            reason,
        )


    def _log_auto_gain_apply(self, profile_id, camera_id, decision, *, apply_enabled, status, reason, old_gain=None, new_gain=None, shadow=True):
        logger.info(
            '[AUTO_GAIN_APPLY] profile=%s camera_id=%s mode=%s apply_enabled=%s status=%s reason=%s blocker=%s action=%s old_gain=%0.2f new_gain=%0.2f current_exposure=%0.8f exposure_max=%0.8f trend_active=%s cooldown_remaining=%d auto_gain_raised=%s shadow=%s',
            profile_id,
            camera_id,
            decision.mode,
            apply_enabled,
            status,
            reason,
            decision.blocker,
            decision.action,
            decision.current_gain if old_gain is None else old_gain,
            decision.current_gain if new_gain is None else new_gain,
            decision.current_exposure,
            decision.exposure_max,
            decision.trend_active,
            decision.cooldown_remaining,
            decision.auto_gain_raised,
            shadow,
        )


    def _save_auto_gain_runtime_state(self, profile_id, camera_id, mode, gain, gain_min, gain_max, reason):
        try:
            self.auto_gain_runtime_state_store.save_gain(
                profile_id=profile_id,
                camera_id=camera_id,
                mode=mode,
                gain=gain,
                gain_min=gain_min,
                gain_max=gain_max,
                reason=reason,
            )
            logger.info(
                '[AUTO_GAIN_STATE_SAVE] profile=%s camera_id=%s mode=%s gain=%0.2f reason=%s path=%s',
                profile_id,
                camera_id,
                mode,
                float(gain),
                reason,
                self.auto_gain_runtime_state_store.state_path,
            )
        except Exception as e:
            logger.warning(
                '[AUTO_GAIN_STATE_SAVE] profile=%s camera_id=%s mode=%s gain=%s reason=%s status=failed error=%s path=%s',
                profile_id,
                camera_id,
                mode,
                gain,
                reason,
                str(e),
                self.auto_gain_runtime_state_store.state_path,
            )


    def _apply_auto_gain_decision(self, profile_id, camera_id, decision, state):
        apply_enabled = self._auto_gain_config_bool('AUTO_GAIN_APPLY_ENABLED', False)
        should_apply, reason = self.auto_gain_controller.should_apply(decision, apply_enabled=apply_enabled)
        if not should_apply:
            self._log_auto_gain_apply(
                profile_id,
                camera_id,
                decision,
                apply_enabled=apply_enabled,
                status='skipped',
                reason=reason,
                shadow=True,
            )
            return

        try:
            new_gain = self._clamp_auto_exposure_apply_value(
                decision.proposed_gain,
                decision.gain_min,
                decision.gain_max,
            )
            old_gain = float(self.gain_av[constants.GAIN_NEXT])

            with self.gain_av.get_lock():
                self.gain_av[constants.GAIN_NEXT] = float(new_gain)

            self._save_auto_gain_runtime_state(
                profile_id,
                camera_id,
                decision.mode,
                new_gain,
                decision.gain_min,
                decision.gain_max,
                'apply_applied',
            )

            self._log_auto_gain_apply(
                profile_id,
                camera_id,
                decision,
                apply_enabled=True,
                status='applied',
                reason=reason,
                old_gain=old_gain,
                new_gain=new_gain,
                shadow=False,
            )
        except Exception as e:
            self._log_auto_gain_apply(
                profile_id,
                camera_id,
                decision,
                apply_enabled=True,
                status='skipped',
                reason=str(e),
                shadow=True,
            )


    def _log_auto_gain_blocker(self, profile_id, camera_id, decision):
        if decision.blocker == 'none':
            return

        logger.info(
            '[AUTO_GAIN_BLOCKER] profile=%s camera_id=%s mode=%s blocker=%s action=%s reason=%s enabled=%s current_exposure=%0.8f exposure_max=%0.8f current_gain=%0.2f proposed_gain=%0.2f gain_min=%0.2f gain_max=%0.2f trend_active=%s trend_count=%d cooldown_remaining=%d error=%+0.2f deadband=%0.2f shadow=%s',
            profile_id,
            camera_id,
            decision.mode,
            decision.blocker,
            decision.action,
            decision.reason,
            decision.enabled,
            decision.current_exposure,
            decision.exposure_max,
            decision.current_gain,
            decision.proposed_gain,
            decision.gain_min,
            decision.gain_max,
            decision.trend_active,
            decision.trend_count,
            decision.cooldown_remaining,
            decision.error,
            decision.deadband,
            decision.shadow,
        )


    def _persist_frame_metadata(self, *, frame_id, timestamp, camera_id, profile_id, image_file_path, exposure, gain, capture_status='processed', error_message=''):
        try:
            state = self.auto_meter_states.get(self._adu_key(profile_id, camera_id), {})
            auto_exposure_decision = state.get('last_decision')
            auto_gain_state = self.auto_gain_states.get(self._adu_key(profile_id, camera_id), {})
            auto_gain_decision = auto_gain_state.get('last_decision')

            target_meter = None
            meter_error = None
            auto_exposure_action = 'unknown'
            auto_gain_action = 'unknown'
            decision_reason = ''

            if auto_exposure_decision is not None:
                target_meter = auto_exposure_decision.target
                meter_error = auto_exposure_decision.error
                auto_exposure_action = auto_exposure_decision.action
                decision_reason = auto_exposure_decision.reason

            if auto_gain_decision is not None:
                auto_gain_action = auto_gain_decision.action
                if not decision_reason:
                    decision_reason = auto_gain_decision.reason

            metadata = FrameMetadata(
                frame_id=int(frame_id),
                timestamp=timestamp,
                camera_id=int(camera_id),
                profile_id=str(profile_id),
                image_file_path=str(image_file_path),
                exposure_us=int(round(float(exposure) * 1000000.0)),
                gain=float(gain),
                meter_value_raw=self._optional_float(state.get('measured_value')),
                meter_value_smoothed=self._optional_float(state.get('smoothed_value')),
                target_meter=self._optional_float(target_meter),
                meter_error=self._optional_float(meter_error),
                auto_exposure_action=str(auto_exposure_action),
                auto_gain_action=str(auto_gain_action),
                decision_reason=str(decision_reason),
                capture_status=str(capture_status),
                error_message=str(error_message or ''),
                quality_score=0.0,
                quality_flags=[],
            )
            self.frame_metadata_writer.write(metadata)
        except Exception as e:
            logger.warning(
                '[FRAME_METADATA] profile=%s camera_id=%s frame_id=%s status=skipped reason=%s',
                profile_id,
                camera_id,
                frame_id,
                str(e),
            )


    def _optional_float(self, value):
        if value is None:
            return None

        try:
            value_float = float(value)
        except (TypeError, ValueError):
            return None

        if not numpy.isfinite(value_float):
            return None

        return value_float


    def _decide_auto_gain_shadow(self, profile_id, camera_id, result, meter_state):
        mode = self._auto_gain_mode()
        state = self._select_auto_gain_state(profile_id, camera_id, mode)
        smoothed_value = meter_state.get('smoothed_value')
        if smoothed_value is None:
            self._log_auto_gain_decision_skipped(profile_id, camera_id, mode, 'missing_smoothed_value')
            return None

        inputs = self._auto_exposure_controller_inputs(result.mode)
        missing_inputs = [
            key
            for key, value in inputs.items()
            if value is None and key not in (
                'source_exposure',
                'source_gain',
                'exposure_runtime_current',
                'exposure_runtime_next',
                'gain_runtime_current',
                'gain_runtime_next',
                'is_day',
                'allow_gain_control',
            )
        ]
        if missing_inputs:
            self._log_auto_gain_decision_skipped(profile_id, camera_id, mode, 'missing_{0:s}'.format(','.join(missing_inputs)))
            return None

        enabled = self._auto_gain_enabled(mode)
        deadband = self._auto_gain_config_float('AUTO_GAIN_DEADBAND', 10.0)
        trend_frames = self._auto_gain_config_int('AUTO_GAIN_TREND_FRAMES', 3)
        cooldown_frames = self._auto_gain_config_int('AUTO_GAIN_COOLDOWN_FRAMES', 2)
        gain_step_factor = self._auto_gain_config_float('AUTO_GAIN_STEP_FACTOR', 0.15)
        gain_min_step = self._auto_gain_config_float('AUTO_GAIN_MIN_STEP', 0.01)
        gain_max_step = self._auto_gain_config_float('AUTO_GAIN_MAX_STEP', 0.0, allow_zero=True)
        logger.info(
            '[AUTO_GAIN_STATE] profile=%s camera_id=%s mode=%s metering_mode=%s enabled=%s trend_count=%d trend_direction=%s convergence_frames=%d cooldown_remaining=%d last_action=%s auto_gain_raised=%s deadband=%0.2f trend_frames=%d cooldown_frames=%d gain_step_factor=%0.4f gain_min_step=%0.4f gain_max_step=%0.4f',
            profile_id,
            camera_id,
            mode,
            result.mode,
            enabled,
            int(state.get('trend_count') or 0),
            state.get('trend_direction', 'none'),
            int(state.get('convergence_frames') or 0),
            int(state.get('cooldown_remaining') or 0),
            state.get('last_action', 'hold'),
            bool(state.get('auto_gain_raised', False)),
            deadband,
            trend_frames,
            cooldown_frames,
            gain_step_factor,
            gain_min_step,
            gain_max_step,
        )

        try:
            decision = self.auto_gain_controller.decide(
                smoothed_value=smoothed_value,
                target=inputs['target'],
                mode=mode,
                enabled=enabled,
                current_exposure=inputs['current_exposure'],
                exposure_min=inputs['exposure_min'],
                exposure_max=inputs['exposure_max'],
                current_gain=inputs['current_gain'],
                gain_min=inputs['gain_min'],
                gain_max=inputs['gain_max'],
                state=state,
                deadband=deadband,
                trend_frames=trend_frames,
                cooldown_frames=cooldown_frames,
                gain_step_factor=gain_step_factor,
                gain_min_step=gain_min_step,
                gain_max_step=gain_max_step,
            )
        except (TypeError, ValueError) as e:
            self._log_auto_gain_decision_skipped(profile_id, camera_id, mode, str(e))
            return None

        state['last_decision'] = decision
        logger.info(
            '[AUTO_GAIN_DECISION] profile=%s camera_id=%s mode=%s metering_mode=%s enabled=%s action=%s reason=%s blocker=%s smoothed_value=%0.2f target=%0.2f error=%+0.2f deadband=%0.2f current_exposure=%0.8f proposed_exposure=%0.8f exposure_min=%0.8f exposure_max=%0.8f source_exposure=%s current_gain=%0.2f proposed_gain=%0.2f gain_min=%0.2f gain_max=%0.2f source_gain=%s trend_count=%d trend_active=%s trend_direction=%s convergence_frames=%d fine_convergence=%s convergence_mode=%s cooldown_remaining=%d auto_gain_raised=%s step=%0.4f step_strategy=%s shadow=%s',
            profile_id,
            camera_id,
            decision.mode,
            result.mode,
            decision.enabled,
            decision.action,
            decision.reason,
            decision.blocker,
            float(smoothed_value),
            decision.target,
            decision.error,
            decision.deadband,
            decision.current_exposure,
            decision.proposed_exposure,
            decision.exposure_min,
            decision.exposure_max,
            inputs['source_exposure'],
            decision.current_gain,
            decision.proposed_gain,
            decision.gain_min,
            decision.gain_max,
            inputs['source_gain'],
            decision.trend_count,
            decision.trend_active,
            decision.trend_direction,
            decision.convergence_frames,
            decision.fine_convergence,
            decision.convergence_mode,
            decision.cooldown_remaining,
            decision.auto_gain_raised,
            decision.step,
            decision.step_strategy,
            decision.shadow,
        )
        self._log_auto_gain_blocker(profile_id, camera_id, decision)
        self._apply_auto_gain_decision(profile_id, camera_id, decision, state)
        return decision


    def _clamp_auto_exposure_apply_value(self, value, minimum, maximum):
        value = float(value)
        minimum = float(minimum)
        maximum = float(maximum)
        if minimum > maximum:
            minimum, maximum = maximum, minimum

        return max(minimum, min(maximum, value))


    def _apply_auto_exposure_decision(self, profile_id, camera_id):
        if not self._auto_exposure_enabled():
            return

        try:
            state = self.auto_meter_states.get(self._adu_key(profile_id, camera_id))
            if not state:
                logger.info('[AUTO_EXPOSURE_APPLY] profile=%s camera_id=%s enabled=True status=skipped reason=missing_state shadow=False', profile_id, camera_id)
                return

            decision = state.get('last_decision')
            if decision is None:
                logger.info('[AUTO_EXPOSURE_APPLY] profile=%s camera_id=%s enabled=True status=skipped reason=missing_decision shadow=False', profile_id, camera_id)
                return

            smoothed_value = state.get('smoothed_value')
            if smoothed_value is None:
                logger.info('[AUTO_EXPOSURE_APPLY] profile=%s camera_id=%s enabled=True status=skipped reason=missing_smoothed_value shadow=False', profile_id, camera_id)
                return

            old_exposure = float(decision.current_exposure)
            old_gain = float(decision.current_gain)
            if decision.action == 'hold':
                logger.info(
                    '[AUTO_EXPOSURE_APPLY] profile=%s camera_id=%s mode=%s enabled=True status=skipped reason=hold action=hold old_exposure=%0.8f new_exposure=%0.8f old_gain=%0.2f new_gain=%0.2f target=%0.2f smoothed_value=%0.2f error=%+0.2f deadband=%0.2f decision_current_exposure=%0.8f decision_current_gain=%0.2f shadow=False',
                    profile_id,
                    camera_id,
                    state.get('mode'),
                    old_exposure,
                    old_exposure,
                    old_gain,
                    old_gain,
                    decision.target,
                    float(smoothed_value),
                    decision.error,
                    decision.deadband,
                    decision.current_exposure,
                    decision.current_gain,
                )
                return

            if self.night_av[constants.NIGHT_NIGHT]:
                exposure_min = self.exposure_av[constants.EXPOSURE_MIN_NIGHT]
                if self.night_av[constants.NIGHT_MOONMODE]:
                    gain_min = self.gain_av[constants.GAIN_MIN_MOONMODE]
                    gain_max = self.gain_av[constants.GAIN_MAX_MOONMODE]
                else:
                    gain_min = self.gain_av[constants.GAIN_MIN_NIGHT]
                    gain_max = self.gain_av[constants.GAIN_MAX_NIGHT]
            else:
                exposure_min = self.exposure_av[constants.EXPOSURE_MIN_DAY]
                gain_min = self.gain_av[constants.GAIN_MIN_DAY]
                gain_max = self.gain_av[constants.GAIN_MAX_DAY]

            new_exposure = self._clamp_auto_exposure_apply_value(
                decision.proposed_exposure,
                exposure_min,
                self.exposure_av[constants.EXPOSURE_MAX],
            )
            new_gain = self._clamp_auto_exposure_apply_value(decision.proposed_gain, gain_min, gain_max)
            old_gain_next = float(self.gain_av[constants.GAIN_NEXT])

            with self.exposure_av.get_lock():
                self.exposure_av[constants.EXPOSURE_NEXT] = float(new_exposure)
                self.exposure_av[constants.EXPOSURE_DELTA] = float(new_exposure - self.exposure_av[constants.EXPOSURE_CURRENT])

            with self.gain_av.get_lock():
                self.gain_av[constants.GAIN_NEXT] = float(new_gain)
                self.gain_av[constants.GAIN_DELTA] = float(new_gain - self.gain_av[constants.GAIN_CURRENT])

            if float(new_gain) != old_gain_next:
                self._save_auto_gain_runtime_state(
                    profile_id,
                    camera_id,
                    state.get('mode') or self._auto_gain_mode(),
                    new_gain,
                    gain_min,
                    gain_max,
                    'runtime_next_changed',
                )

            logger.info(
                '[AUTO_EXPOSURE_APPLY] profile=%s camera_id=%s mode=%s enabled=True action=%s old_exposure=%0.8f new_exposure=%0.8f old_gain=%0.2f new_gain=%0.2f target=%0.2f smoothed_value=%0.2f error=%+0.2f deadband=%0.2f decision_current_exposure=%0.8f decision_current_gain=%0.2f shadow=False',
                profile_id,
                camera_id,
                state.get('mode'),
                decision.action,
                old_exposure,
                new_exposure,
                old_gain,
                new_gain,
                decision.target,
                float(smoothed_value),
                decision.error,
                decision.deadband,
                decision.current_exposure,
                decision.current_gain,
            )
        except Exception as e:
            logger.info('[AUTO_EXPOSURE_APPLY] profile=%s camera_id=%s enabled=True status=skipped reason=%s shadow=False', profile_id, camera_id, str(e))


    def _meter_auto_exposure(self, profile_id, camera_id, binning):
        try:
            adu_masks = getattr(self.image_processor, '_adu_mask_dict', None) or {}
            result = measure_auto_exposure(
                self.image_processor.image,
                mask=adu_masks.get(binning),
                mode=self._auto_exposure_metering_mode(),
            )
            logger.info(
                '[AUTO_METER] profile=%s camera_id=%s mode=%s strategy=%s sample_count=%d measured_value=%0.2f excluded_pixels=%d status=%s',
                profile_id,
                camera_id,
                result.mode,
                result.strategy,
                result.sample_count,
                result.measured_value,
                result.excluded_pixels,
                result.status,
            )
            state = self._update_auto_meter_state(profile_id, camera_id, result)
            self._decide_auto_exposure_shadow(profile_id, camera_id, result, state)
            self._decide_auto_gain_shadow(profile_id, camera_id, result, state)
            return result
        except Exception as e:
            logger.warning('[AUTO_METER] profile=%s camera_id=%s mode=%s status=error error=%s', profile_id, camera_id, self._auto_exposure_metering_mode(), str(e))
            return None


    def _queue_upload_task(self, task, camera_id=None, profile_id=None):
        # MULTI_CAMERA_PREP: passive route metadata; FileUploader still loads
        # and executes the existing DB task by task_id.
        payload = {
            'task_id'    : task.id,
            'profile_id' : profile_id or self.profile_id,
        }

        if camera_id:
            payload['camera_id'] = camera_id

        self.upload_q.put(payload)


    def _new_adu_state(self):
        return {
            'target_adu_found'               : False,
            'current_adu_target'             : 0,
            'hist_adu'                       : [],
            'gain_step'                      : None,
            'auto_gain_step_list'            : None,
            'auto_gain_exposure_cutoff_low'  : None,
            'auto_gain_exposure_cutoff_mid'  : None,
            'auto_gain_exposure_cutoff_high' : None,
            'auto_gain_step_key'             : None,
            'generate_mask_base'             : True,
        }


    def _adu_key(self, profile_id, camera_id):
        profile_key = str(profile_id or 'default')
        camera_key = str(camera_id if camera_id is not None else 'unknown')
        return '{0:s}:{1:s}'.format(profile_key, camera_key)


    def _select_adu_state(self, profile_id, camera_id):
        adu_key = self._adu_key(profile_id, camera_id)
        try:
            self.adu_state = self.adu_states[adu_key]
        except KeyError:
            self.adu_state = self._new_adu_state()
            self.adu_states[adu_key] = self.adu_state

        self.adu_context_key = adu_key
        return adu_key


    def _select_profile_config(self, profile_id):
        if profile_id in self.camera_config_map:
            self.config = self.camera_config_map[profile_id]
            return

        self.config = self.camera_config_map.get('default', self.base_config)
        if profile_id not in ('default', None) and profile_id not in self._missing_profile_config_warned:
            self._missing_profile_config_warned.add(profile_id)
            logger.warning(
                '[MULTI_CAMERA_CONFIG][%s] profile config not found in ImageWorker map; using global/default config fallback',
                profile_id,
            )


    def _auto_gain_mode(self):
        if self.night_av[constants.NIGHT_NIGHT] == 1:
            if self.night_av[constants.NIGHT_MOONMODE] == 1:
                return 'moonmode'
            return 'night'

        return 'day'


    def _auto_gain_enabled(self, mode=None):
        ccd_config = self.config.get('CCD_CONFIG') or {}
        legacy_auto = bool(ccd_config.get('AUTO_GAIN_ENABLE', False))
        mode = mode or self._auto_gain_mode()
        if mode == 'day':
            return bool(ccd_config.get('AUTO_GAIN_ENABLE_DAY', legacy_auto))
        elif mode == 'moonmode':
            return bool(ccd_config.get('AUTO_GAIN_ENABLE_MOONMODE', legacy_auto))

        return bool(ccd_config.get('AUTO_GAIN_ENABLE_NIGHT', legacy_auto))


    def _auto_gain_limits(self, mode=None):
        mode = mode or self._auto_gain_mode()
        if mode == 'day':
            return (
                float(self.gain_av[constants.GAIN_MIN_DAY]),
                float(self.gain_av[constants.GAIN_MAX_DAY]),
            )
        elif mode == 'moonmode':
            return (
                float(self.gain_av[constants.GAIN_MIN_MOONMODE]),
                float(self.gain_av[constants.GAIN_MAX_MOONMODE]),
            )

        return (
            float(self.gain_av[constants.GAIN_MIN_NIGHT]),
            float(self.gain_av[constants.GAIN_MAX_NIGHT]),
        )


    def _select_shared_state(self, profile_id):
        shared_state = self.camera_shared_state_map.get(profile_id)
        if not shared_state:
            shared_state = self.camera_shared_state_map.get('default')
            if profile_id not in ('default', None) and profile_id not in self._missing_profile_shared_state_warned:
                self._missing_profile_shared_state_warned.add(profile_id)
                logger.warning(
                    '[MULTI_CAMERA_CONFIG][%s] shared state not found in ImageWorker map; using global/default shared state fallback',
                    profile_id,
                )
        if not shared_state:
            return

        self.position_av = shared_state.position_av
        self.exposure_av = shared_state.exposure_av
        self.gain_av = shared_state.gain_av
        self.binning_av = shared_state.binning_av
        self.sensors_temp_av = shared_state.sensors_temp_av
        self.sensors_user_av = shared_state.sensors_user_av
        self.night_av = shared_state.night_av
        self.astro_av = shared_state.astro_av
        self.hybrid_av = getattr(shared_state, 'hybrid_av', None)


    def _select_runtime_context(self, profile_id, camera_id):
        self._select_profile_config(profile_id)
        self._select_shared_state(profile_id)
        return self._select_adu_state(profile_id, camera_id)


    def _processing_mode(self):
        return str(self.config.get('PROCESSING_MODE', 'classic') or 'classic').strip().lower()


    def _hybrid_awb_enabled(self):
        return self._processing_mode() == 'hybrid'


    def _hybrid_awb_apply_mode(self):
        raw_apply_mode = self._hybrid_awb_raw_apply_mode()
        apply_mode = str(raw_apply_mode or 'auto').strip().lower()
        if apply_mode not in ('auto', 'capture_driver', 'postprocess_rgb', 'disabled'):
            return 'auto'

        return apply_mode


    def _hybrid_awb_raw_apply_mode(self):
        hybrid_config = self.config.get('HYBRID') or {}
        if not isinstance(hybrid_config, dict):
            hybrid_config = {}

        awb_config = hybrid_config.get('AWB') or {}
        if not isinstance(awb_config, dict):
            awb_config = {}

        if 'APPLY_MODE' in awb_config:
            return awb_config.get('APPLY_MODE')

        active_profile_id = self.config.get('MULTI_CAMERA_ACTIVE_PROFILE')
        profile_configs = self.config.get('MULTI_CAMERA', {}).get('profiles', [])
        if not active_profile_id or not isinstance(profile_configs, list):
            return None

        for profile_config in profile_configs:
            if not isinstance(profile_config, dict):
                continue

            profile_id = profile_config.get('profile_id') or profile_config.get('id')
            if str(profile_id) != str(active_profile_id):
                continue

            try:
                return profile_config.get('hybrid', {}).get('awb', {}).get('apply_mode')
            except AttributeError:
                return None

        return None


    def _hybrid_awb_backend(self):
        apply_mode = self._hybrid_awb_apply_mode()
        if apply_mode == 'disabled':
            return 'disabled_not_applied'

        if apply_mode == 'postprocess_rgb':
            return 'postprocess_rgb'

        camera_interface = str(self.config.get('CAMERA_INTERFACE', '') or '').strip().lower()
        if apply_mode == 'capture_driver':
            if camera_interface.startswith('libcamera'):
                return 'libcamera_capture'

            return 'unsupported_not_applied'

        if camera_interface.startswith('libcamera'):
            return 'libcamera_capture'

        if camera_interface == 'indi':
            return 'postprocess_rgb'

        return 'unsupported_not_applied'


    def _log_hybrid_awb_backend_warning(self, profile_id, camera_id, backend):
        if backend != 'unsupported_not_applied':
            return

        warning_key = '{0:s}:{1:s}:{2:s}'.format(
            str(profile_id),
            str(camera_id if camera_id is not None else 'unknown'),
            backend,
        )
        if warning_key in self.hybrid_awb_backend_warned:
            return

        self.hybrid_awb_backend_warned.add(warning_key)
        logger.warning(
            '[HYBRID_AWB][%s][camera_id=%s] measured values are not applied to capture backend=%s',
            profile_id,
            camera_id if camera_id is not None else 'unknown',
            backend,
        )


    def _hybrid_awb_postprocess_skip(self, profile_id, camera_id, reason):
        _multi_camera_diag(
            '[HYBRID_AWB][%s][camera_id=%s] backend=postprocess_rgb skipped reason=%s',
            profile_id,
            camera_id if camera_id is not None else 'unknown',
            reason,
        )


    def apply_hybrid_awb(self, profile_id, camera_id):
        if not self._hybrid_awb_enabled():
            return

        backend = self._hybrid_awb_backend()
        self._log_hybrid_awb_backend_warning(profile_id, camera_id, backend)

        if backend == 'libcamera_capture':
            return

        if backend == 'disabled_not_applied':
            _multi_camera_diag(
                '[HYBRID_AWB][%s][camera_id=%s] backend=disabled_not_applied skipped reason=apply-disabled',
                profile_id,
                camera_id if camera_id is not None else 'unknown',
            )
            return

        if backend == 'unsupported_not_applied':
            _multi_camera_diag(
                '[HYBRID_AWB][%s][camera_id=%s] backend=unsupported_not_applied skipped reason=no-apply-backend',
                profile_id,
                camera_id if camera_id is not None else 'unknown',
            )
            return

        if backend != 'postprocess_rgb':
            return

        try:
            image = getattr(self.image_processor, 'image', None)
            if image is None:
                self._hybrid_awb_postprocess_skip(profile_id, camera_id, 'no-image')
                return

            if image.ndim != 3 or image.shape[2] < 3:
                self._hybrid_awb_postprocess_skip(profile_id, camera_id, 'not-bgr')
                return

            if self.hybrid_av is None:
                self._hybrid_awb_postprocess_skip(profile_id, camera_id, 'no-shared-state')
                return

            with self.hybrid_av.get_lock():
                initialized = self.hybrid_av[constants.HYBRID_AWB_INITIALIZED] >= 0.5
                sample_count = int(self.hybrid_av[constants.HYBRID_AWB_SAMPLE_COUNT])
                red_gain = self._clamp_hybrid_awb_gain(self.hybrid_av[constants.HYBRID_AWB_RED_GAIN_NEXT])
                blue_gain = self._clamp_hybrid_awb_gain(self.hybrid_av[constants.HYBRID_AWB_BLUE_GAIN_NEXT])

            if not initialized or sample_count <= 0:
                self._hybrid_awb_postprocess_skip(profile_id, camera_id, 'not_initialized')
                return

            corrected_image = image.astype(numpy.float32, copy=True)
            corrected_image[:, :, 0] *= blue_gain
            corrected_image[:, :, 2] *= red_gain

            if numpy.issubdtype(image.dtype, numpy.integer):
                max_value = numpy.iinfo(image.dtype).max
                corrected_image = numpy.clip(corrected_image, 0, max_value).astype(image.dtype)
            elif numpy.issubdtype(image.dtype, numpy.floating):
                finite_max = float(numpy.nanmax(image))
                if not numpy.isfinite(finite_max) or finite_max <= 1.5:
                    max_value = 1.0
                elif finite_max <= 255.0:
                    max_value = 255.0
                elif finite_max <= 65535.0:
                    max_value = 65535.0
                else:
                    max_value = finite_max

                corrected_image = numpy.clip(corrected_image, 0.0, max_value).astype(image.dtype, copy=False)
            else:
                self._hybrid_awb_postprocess_skip(profile_id, camera_id, 'unsupported-dtype')
                return

            self.image_processor.image = corrected_image
            _multi_camera_diag(
                '[HYBRID_AWB][%s][camera_id=%s] backend=postprocess_rgb applied_red=%0.4f applied_blue=%0.4f sample_count=%d',
                profile_id,
                camera_id if camera_id is not None else 'unknown',
                red_gain,
                blue_gain,
                sample_count,
            )
        except Exception as e:
            logger.error('Hybrid AWB postprocess apply failed: %s', str(e))
            self._hybrid_awb_postprocess_skip(profile_id, camera_id, 'apply-error')


    def _clamp_hybrid_awb_gain(self, gain):
        return max(0.5, min(3.0, float(gain)))


    def _hybrid_awb_fallback_gains(self):
        libcamera_config = self.config.get('LIBCAMERA', {}) or {}

        try:
            red_gain = float(libcamera_config.get('AWB_RED_GAIN', libcamera_config.get('awb_red_gain', 1.0)))
        except (TypeError, ValueError):
            red_gain = 1.0

        try:
            blue_gain = float(libcamera_config.get('AWB_BLUE_GAIN', libcamera_config.get('awb_blue_gain', 1.0)))
        except (TypeError, ValueError):
            blue_gain = 1.0

        return (
            self._clamp_hybrid_awb_gain(red_gain),
            self._clamp_hybrid_awb_gain(blue_gain),
        )


    def _hybrid_awb_current_gains(self):
        red_gain, blue_gain = self._hybrid_awb_fallback_gains()
        if self.hybrid_av is None:
            return red_gain, blue_gain, 0

        with self.hybrid_av.get_lock():
            if self.hybrid_av[constants.HYBRID_AWB_INITIALIZED] < 0.5:
                self.hybrid_av[constants.HYBRID_AWB_RED_GAIN_NEXT] = red_gain
                self.hybrid_av[constants.HYBRID_AWB_BLUE_GAIN_NEXT] = blue_gain
                self.hybrid_av[constants.HYBRID_AWB_INITIALIZED] = 1.0
                self.hybrid_av[constants.HYBRID_AWB_SAMPLE_COUNT] = 0.0
                self.hybrid_av[constants.HYBRID_AWB_STATUS] = 0.0

            red_gain = self._clamp_hybrid_awb_gain(self.hybrid_av[constants.HYBRID_AWB_RED_GAIN_NEXT])
            blue_gain = self._clamp_hybrid_awb_gain(self.hybrid_av[constants.HYBRID_AWB_BLUE_GAIN_NEXT])
            sample_count = int(self.hybrid_av[constants.HYBRID_AWB_SAMPLE_COUNT])

        return red_gain, blue_gain, sample_count


    def _hybrid_awb_roi(self, image):
        adu_roi = self.config.get('ADU_ROI', [])
        if not isinstance(adu_roi, (list, tuple)) or len(adu_roi) != 4:
            return image

        image_height, image_width = image.shape[:2]
        try:
            x1 = max(0, min(image_width, int(adu_roi[0])))
            y1 = max(0, min(image_height, int(adu_roi[1])))
            x2 = max(0, min(image_width, int(adu_roi[2])))
            y2 = max(0, min(image_height, int(adu_roi[3])))
        except (TypeError, ValueError):
            return image

        if x2 <= x1 or y2 <= y1:
            return image

        return image[y1:y2, x1:x2]


    def _hybrid_awb_channel_stat(self, channel_values):
        if channel_values.size < 32:
            return None

        low, high = numpy.percentile(channel_values, (5, 95))
        clipped_values = channel_values[(channel_values >= low) & (channel_values <= high)]
        if clipped_values.size < 32:
            clipped_values = channel_values

        return float(numpy.median(clipped_values))


    def _hybrid_awb_skip(self, profile_id, camera_id, reason):
        backend = self._hybrid_awb_backend()
        self._log_hybrid_awb_backend_warning(profile_id, camera_id, backend)

        try:
            red_gain, blue_gain, sample_count = self._hybrid_awb_current_gains()
            if self.hybrid_av is not None:
                with self.hybrid_av.get_lock():
                    self.hybrid_av[constants.HYBRID_AWB_STATUS] = -1.0
        except Exception:
            red_gain, blue_gain = self._hybrid_awb_fallback_gains()
            sample_count = 0

        _multi_camera_diag(
            '[HYBRID_AWB][%s][camera_id=%s] skipped reason=%s backend=%s applied_red=%0.4f applied_blue=%0.4f sample_count=%d',
            profile_id,
            camera_id if camera_id is not None else 'unknown',
            reason,
            backend,
            red_gain,
            blue_gain,
            sample_count,
        )


    def update_hybrid_awb(self, profile_id, camera_id):
        if not self._hybrid_awb_enabled():
            return

        try:
            backend = self._hybrid_awb_backend()
            self._log_hybrid_awb_backend_warning(profile_id, camera_id, backend)

            image = getattr(self.image_processor, 'image', None)
            if image is None:
                self._hybrid_awb_skip(profile_id, camera_id, 'no-image')
                return

            if image.ndim != 3 or image.shape[2] < 3:
                self._hybrid_awb_skip(profile_id, camera_id, 'not-bgr')
                return

            if self.hybrid_av is None:
                self._hybrid_awb_skip(profile_id, camera_id, 'no-shared-state')
                return

            sample_image = self._hybrid_awb_roi(image[:, :, :3])
            sample_pixels = sample_image.shape[0] * sample_image.shape[1]
            if sample_pixels <= 0:
                self._hybrid_awb_skip(profile_id, camera_id, 'empty-roi')
                return

            stride = max(1, int((sample_pixels / 500000) ** 0.5))
            sample_image = sample_image[::stride, ::stride, :3]

            if numpy.issubdtype(sample_image.dtype, numpy.integer):
                max_value = float(numpy.iinfo(sample_image.dtype).max)
            else:
                max_value = float(numpy.nanmax(sample_image))
                if not numpy.isfinite(max_value) or max_value <= 0:
                    max_value = 1.0

            sample_float = sample_image.astype(numpy.float32, copy=False)
            pixel_max = numpy.nanmax(sample_float, axis=2)
            valid_mask = numpy.isfinite(sample_float).all(axis=2)
            valid_mask &= pixel_max > (max_value * 0.01)
            valid_mask &= pixel_max < (max_value * 0.98)

            sample_count = int(numpy.count_nonzero(valid_mask))
            if sample_count < 256:
                self._hybrid_awb_skip(profile_id, camera_id, 'insufficient-samples')
                return

            valid_pixels = sample_float[valid_mask]
            blue_stat = self._hybrid_awb_channel_stat(valid_pixels[:, 0])
            green_stat = self._hybrid_awb_channel_stat(valid_pixels[:, 1])
            red_stat = self._hybrid_awb_channel_stat(valid_pixels[:, 2])

            if not all((blue_stat, green_stat, red_stat)):
                self._hybrid_awb_skip(profile_id, camera_id, 'invalid-channel-stat')
                return

            measured_red = self._clamp_hybrid_awb_gain(green_stat / red_stat)
            measured_blue = self._clamp_hybrid_awb_gain(green_stat / blue_stat)

            old_red, old_blue, previous_sample_count = self._hybrid_awb_current_gains()
            applied_red = self._clamp_hybrid_awb_gain((old_red * 0.75) + (measured_red * 0.25))
            applied_blue = self._clamp_hybrid_awb_gain((old_blue * 0.75) + (measured_blue * 0.25))

            with self.hybrid_av.get_lock():
                self.hybrid_av[constants.HYBRID_AWB_RED_GAIN_NEXT] = applied_red
                self.hybrid_av[constants.HYBRID_AWB_BLUE_GAIN_NEXT] = applied_blue
                self.hybrid_av[constants.HYBRID_AWB_INITIALIZED] = 1.0
                self.hybrid_av[constants.HYBRID_AWB_SAMPLE_COUNT] = float(sample_count)
                self.hybrid_av[constants.HYBRID_AWB_STATUS] = 1.0

            _multi_camera_diag(
                '[HYBRID_AWB][%s][camera_id=%s] measured_red=%0.4f measured_blue=%0.4f backend=%s applied_red=%0.4f applied_blue=%0.4f sample_count=%d previous_sample_count=%d',
                profile_id,
                camera_id if camera_id is not None else 'unknown',
                measured_red,
                measured_blue,
                backend,
                applied_red,
                applied_blue,
                sample_count,
                previous_sample_count,
            )
        except Exception as e:
            logger.error('Hybrid AWB calculation failed: %s', str(e))
            self._hybrid_awb_skip(profile_id, camera_id, 'calculation-error')


    @property
    def libcamera_raw(self):
        return self._libcamera_raw

    @libcamera_raw.setter
    def libcamera_raw(self, new_libcamera_raw):
        self._libcamera_raw = bool(new_libcamera_raw)


    @property
    def gain_step(self):
        return self.adu_state.get('gain_step')

    @gain_step.setter
    def gain_step(self, new_gain_step):
        self.adu_state['gain_step'] = new_gain_step
        self._gain_step = new_gain_step


    @property
    def target_adu_found(self):
        return bool(self.adu_state.get('target_adu_found'))

    @target_adu_found.setter
    def target_adu_found(self, new_target_adu_found):
        self.adu_state['target_adu_found'] = bool(new_target_adu_found)


    @property
    def current_adu_target(self):
        return self.adu_state.get('current_adu_target', 0)

    @current_adu_target.setter
    def current_adu_target(self, new_current_adu_target):
        self.adu_state['current_adu_target'] = new_current_adu_target


    @property
    def hist_adu(self):
        return self.adu_state.setdefault('hist_adu', [])

    @hist_adu.setter
    def hist_adu(self, new_hist_adu):
        self.adu_state['hist_adu'] = new_hist_adu


    @property
    def generate_mask_base(self):
        return bool(self.adu_state.get('generate_mask_base'))

    @generate_mask_base.setter
    def generate_mask_base(self, new_generate_mask_base):
        self.adu_state['generate_mask_base'] = bool(new_generate_mask_base)


    @property
    def auto_gain_step_list(self):
        return self.adu_state.get('auto_gain_step_list')

    @auto_gain_step_list.setter
    def auto_gain_step_list(self, new_auto_gain_step_list):
        self.adu_state['auto_gain_step_list'] = new_auto_gain_step_list


    @property
    def auto_gain_exposure_cutoff_low(self):
        return self.adu_state.get('auto_gain_exposure_cutoff_low')

    @auto_gain_exposure_cutoff_low.setter
    def auto_gain_exposure_cutoff_low(self, new_auto_gain_exposure_cutoff_low):
        self.adu_state['auto_gain_exposure_cutoff_low'] = new_auto_gain_exposure_cutoff_low


    @property
    def auto_gain_exposure_cutoff_mid(self):
        return self.adu_state.get('auto_gain_exposure_cutoff_mid')

    @auto_gain_exposure_cutoff_mid.setter
    def auto_gain_exposure_cutoff_mid(self, new_auto_gain_exposure_cutoff_mid):
        self.adu_state['auto_gain_exposure_cutoff_mid'] = new_auto_gain_exposure_cutoff_mid


    @property
    def auto_gain_exposure_cutoff_high(self):
        return self.adu_state.get('auto_gain_exposure_cutoff_high')

    @auto_gain_exposure_cutoff_high.setter
    def auto_gain_exposure_cutoff_high(self, new_auto_gain_exposure_cutoff_high):
        self.adu_state['auto_gain_exposure_cutoff_high'] = new_auto_gain_exposure_cutoff_high


    def sighup_handler_worker(self, signum, frame):
        logger.warning('Caught HUP signal')

        # set flag for program to stop processes
        self._shutdown = True


    def sigterm_handler_worker(self, signum, frame):
        logger.warning('Caught TERM signal')

        # set flag for program to stop processes
        self._shutdown = True


    def sigint_handler_worker(self, signum, frame):
        logger.warning('Caught INT signal')

        # set flag for program to stop processes
        self._shutdown = True


    def sigalarm_handler_worker(self, signum, frame):
        raise TimeOutException()



    def run(self):
        # setup signal handling after detaching from the main process
        signal.signal(signal.SIGHUP, self.sighup_handler_worker)
        signal.signal(signal.SIGTERM, self.sigterm_handler_worker)
        signal.signal(signal.SIGINT, self.sigint_handler_worker)
        signal.signal(signal.SIGALRM, self.sigalarm_handler_worker)


        ### use this as a method to log uncaught exceptions
        try:
            self.saferun()
        except Exception as e:
            tb = traceback.format_exc()
            self.error_q.put((str(e), tb))
            raise e



    def saferun(self):
        #raise Exception('Test exception handling in worker')

        while True:
            try:
                i_dict = self.image_q.get(timeout=23)  # prime number
            except queue.Empty:
                continue


            if i_dict.get('stop'):
                self._shutdown = True


            if self._shutdown:
                self.image_processor.realtimeKeogramDataSave()

                logger.warning('Goodbye')

                return

            queue_pop_time = time.time()
            if self._images_only_diag_enabled(bool(i_dict.get('images_only', False))) and self.config.get('MULTI_CAMERA_TIMING_DIAG', False):
                profile_id = self._validate_profile_id(i_dict)
                camera_id = i_dict.get('camera_id', 'unknown')
                queue_time = i_dict.get('queue_time')
                capture_start_time = i_dict.get('capture_start_time')
                queue_wait_s = queue_pop_time - queue_time if queue_time else 0.0
                capture_to_pop_s = queue_pop_time - capture_start_time if capture_start_time else 0.0
                _multi_camera_diag(
                    '[MULTI_CAMERA_TIMING][%s][camera_id=%s] image_queue_pop t=%0.6f queue_wait=%0.4fs capture_to_pop=%0.4fs filename=%s',
                    profile_id,
                    camera_id,
                    queue_pop_time,
                    queue_wait_s,
                    capture_to_pop_s,
                    str(i_dict.get('filename')),
                )


            # new context for every task, reduces the effects of caching
            with app.app_context():
                try:
                    self.processImage(i_dict)
                except Exception as e:
                    if self._images_only_diag_enabled(bool(i_dict.get('images_only', False))):
                        profile_id = self._validate_profile_id(i_dict)
                        camera_id = i_dict.get('camera_id', 'unknown')
                        self._images_only_diag(
                            profile_id,
                            camera_id,
                            'IMAGE_EXCEPTION',
                            error=str(e),
                            error_type=e.__class__.__name__,
                            location='processImage',
                        )
                    raise


    def processImage(self, i_dict):
        import piexif

        ### Not using DB task queue for image processing to reduce database I/O
        #task_id = i_dict['task_id']

        #try:
        #    task = IndiAllSkyDbTaskQueueTable.query\
        #        .filter(IndiAllSkyDbTaskQueueTable.id == task_id)\
        #        .filter(IndiAllSkyDbTaskQueueTable.state == TaskQueueState.QUEUED)\
        #        .filter(IndiAllSkyDbTaskQueueTable.queue == TaskQueueQueue.IMAGE)\
        #        .one()

        #except NoResultFound:
        #    logger.error('Task ID %d not found', task_id)
        #    continue


        #task.setRunning()


        #filename = Path(task.data['filename'])
        #exposure = task.data['exposure']
        #gain = task.data['gain']
        #exp_date = datetime.fromtimestamp(task.data['exp_time'])
        #exp_elapsed = task.data['exp_elapsed']
        #camera_id = task.data['camera_id']
        #filename_t = task.data.get('filename_t')
        ###

        filename_p = Path(i_dict['filename'])
        exposure = i_dict['exposure']
        gain = i_dict['gain']
        binning = i_dict['binning']
        exp_date = datetime.fromtimestamp(i_dict['exp_time'])
        exp_elapsed = i_dict['exp_elapsed']
        camera_id = i_dict['camera_id']
        # MULTI_CAMERA: route id selects the per-camera ADU state and shared
        # exposure/gain arrays before any exposure recalculation runs.
        profile_id = self._validate_profile_id(i_dict)
        adu_context_key = self._select_runtime_context(profile_id, camera_id)
        self._set_queue_context(profile_id, camera_id)
        profile_outputs = i_dict.get('profile_outputs') or {}
        profile_primary = bool(i_dict.get('profile_primary', True))
        images_only = bool(i_dict.get('images_only', False))
        images_only_diag = self._images_only_diag_enabled(images_only)
        filename_t = i_dict.get('filename_t')
        sqm_exposure = i_dict.get('sqm_exposure')
        payload_start_time = time.time()
        queue_time = i_dict.get('queue_time')
        capture_start_time = i_dict.get('capture_start_time')
        queue_wait_s = payload_start_time - queue_time if queue_time else 0.0
        capture_to_processing_s = payload_start_time - capture_start_time if capture_start_time else 0.0
        logger.debug(
            'Image queue route: profile=%s camera_id=%s primary=%s images_only=%s',
            profile_id,
            camera_id,
            profile_primary,
            images_only,
        )
        if self.config.get('MULTI_CAMERA_CAPTURE_ENABLE', False):
            _multi_camera_diag(
                '[MULTI_CAMERA_ADU][%s][camera_id=%s] context=%s states=%d',
                profile_id,
                camera_id,
                adu_context_key,
                len(self.adu_states),
            )

        if images_only or profile_id != 'default':
            _multi_camera_diag(
                '[MULTI_CAMERA_DIAG][%s][camera_id=%s] Image queue route primary=%s images_only=%s',
                profile_id,
                camera_id,
                profile_primary,
                images_only,
            )

        if images_only_diag and self.config.get('MULTI_CAMERA_TIMING_DIAG', False):
            _multi_camera_diag(
                '[MULTI_CAMERA_TIMING][%s][camera_id=%s] processing_start t=%0.6f queue_wait=%0.4fs capture_to_processing=%0.4fs exp_elapsed=%0.4fs',
                profile_id,
                camera_id,
                payload_start_time,
                queue_wait_s,
                capture_to_processing_s,
                float(exp_elapsed),
            )

        if images_only_diag:
            input_exists = filename_p.exists()
            input_size = filename_p.stat().st_size if input_exists else 'missing'
            self._images_only_diag(
                profile_id,
                camera_id,
                'IMAGE_PAYLOAD_START',
                exp_time=i_dict.get('exp_time'),
                filename=str(filename_p),
                input_exists=input_exists,
                input_size=input_size,
                primary=profile_primary,
            )

        self._select_image_processor(profile_id, camera_id, images_only_diag)
        self._log_processing_config_once(profile_id, camera_id)
        asi_frame_stats_enabled = self._asi_frame_stats_should_log(profile_id, camera_id)

        # libcamera
        libcamera_black_level = i_dict.get('libcamera_black_level', 0)
        libcamera_awb_gains = i_dict.get('libcamera_awb_gains')
        libcamera_ccm = i_dict.get('libcamera_ccm')


        if self.config['CAMERA_INTERFACE'].startswith('libcamera_') or self.config['CAMERA_INTERFACE'].startswith('mqtt_'):
            if filename_p.suffix == '.dng':
                self.libcamera_raw = True
                self.image_processor.libcamera_raw = True
            else:
                self.libcamera_raw = False
                self.image_processor.libcamera_raw = False


        if filename_t:
            self.filename_t = filename_t


        if not filename_p.exists():
            logger.error('Frame not found: %s', filename_p)
            if images_only_diag:
                self._images_only_diag(profile_id, camera_id, 'IMAGE_PAYLOAD_ERROR', reason='input_missing', filename=str(filename_p))
            self._persist_frame_metadata(
                frame_id=0,
                timestamp=exp_date.astimezone(timezone.utc).isoformat(),
                camera_id=camera_id,
                profile_id=profile_id,
                image_file_path=filename_p,
                exposure=exposure,
                gain=gain,
                capture_status='input_missing',
                error_message='Frame not found',
            )
            #task.setFailed('Frame not found: {0:s}'.format(str(filename_p)))
            return


        image_size = filename_p.stat().st_size
        if image_size == 0:
            logger.error('Frame is empty: %s', filename_p)
            if images_only_diag:
                self._images_only_diag(profile_id, camera_id, 'IMAGE_PAYLOAD_ERROR', reason='input_empty', filename=str(filename_p))
            self._persist_frame_metadata(
                frame_id=0,
                timestamp=exp_date.astimezone(timezone.utc).isoformat(),
                camera_id=camera_id,
                profile_id=profile_id,
                image_file_path=filename_p,
                exposure=exposure,
                gain=gain,
                capture_status='input_empty',
                error_message='Frame is empty',
            )
            filename_p.unlink()
            return

        #logger.info('Image size: %0.2fMB', image_size / 1024 / 1024)


        camera = IndiAllSkyDbCameraTable.query\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .one()


        ### Special function: image is for SQM calculations only
        if sqm_exposure:
            self.process_sqm_exposure(filename_p, exposure, gain, binning, exp_date, exp_elapsed, camera, libcamera_black_level)
            return


        auto_gain_mode = self._auto_gain_mode()
        auto_gain_min, auto_gain_max = self._auto_gain_limits(auto_gain_mode)
        try:
            auto_gain_levels = max(2, int(self.config.get('CCD_CONFIG', {}).get('AUTO_GAIN_LEVELS', 5)))
        except (TypeError, ValueError):
            auto_gain_levels = 5
        auto_gain_step_key = (auto_gain_mode, auto_gain_min, auto_gain_max, auto_gain_levels)
        if isinstance(self.gain_step, type(None)) or self.adu_state.get('auto_gain_step_key') != auto_gain_step_key:
            # the gain steps cannot be calculated until the gain_av variable is populated
            gain_range = auto_gain_max - auto_gain_min

            self.gain_step = gain_range / (auto_gain_levels - 1)  # need divisions

            self.auto_gain_step_list = [float(round((self.gain_step * x) + auto_gain_min, 2)) for x in range(auto_gain_levels)]
            self.auto_gain_step_list[-1] = float(round(auto_gain_max, 2))  # replace last value, round is necessary
            self.adu_state['auto_gain_step_key'] = auto_gain_step_key


            self.auto_gain_exposure_cutoff_high = self.exposure_av[constants.EXPOSURE_MAX] - 0.5

            self.auto_gain_exposure_cutoff_low = self.exposure_av[constants.EXPOSURE_MAX] * (self.auto_gain_exposure_cutoff_level_low / 100)
            if self.exposure_av[constants.EXPOSURE_MAX] - self.auto_gain_exposure_cutoff_low > 10.0:
                self.auto_gain_exposure_cutoff_low = self.exposure_av[constants.EXPOSURE_MAX] - 10.0

            self.auto_gain_exposure_cutoff_mid = self.auto_gain_exposure_cutoff_high - ((self.auto_gain_exposure_cutoff_high - self.auto_gain_exposure_cutoff_low) / 2)


            if self._auto_gain_enabled(auto_gain_mode):
                logger.info('Gain Steps: %d @ %0.2f', auto_gain_levels, self.gain_step)
                logger.info('Gain Step list: %s', str(self.auto_gain_step_list))
                logger.info(
                    'Auto-Gain Exposure cutoff: Low: %0.2fs - Mid: %0.2fs - High: %0.2fs',
                    self.auto_gain_exposure_cutoff_low,
                    self.auto_gain_exposure_cutoff_mid,
                    self.auto_gain_exposure_cutoff_high,
                )


        processing_start = time.time()


        ### simulate performance degradation
        #time.sleep(30)


        ### start fetching ADSB info
        if self.config.get('ADSB', {}).get('ENABLE'):
            self.adsb_aircraft_q = Queue()
            self.adsb_worker_idx += 1
            self.adsb_worker = AdsbAircraftHttpWorker(
                self.adsb_worker_idx,
                self.config,
                self.adsb_aircraft_q,
                self.position_av,
            )
            self.adsb_worker.start()


        now = datetime.now()
        self.image_processor.update_astrometric_data(now)

        if images_only_diag:
            self._images_only_diag(profile_id, camera_id, 'IMAGE_PROCESSOR_START', filename=str(filename_p), input_size=image_size)

        try:
            i_ref = self.image_processor.add(
                filename_p,
                exposure,
                gain,
                binning,
                exp_date,
                exp_elapsed,
                camera,
            )
        except BadImage as e:
            logger.error('Bad Image: %s', str(e))
            if images_only_diag:
                self._images_only_diag(profile_id, camera_id, 'IMAGE_PROCESSOR_ERROR', error=str(e), error_type='BadImage')
            self._persist_frame_metadata(
                frame_id=0,
                timestamp=exp_date.astimezone(timezone.utc).isoformat(),
                camera_id=camera_id,
                profile_id=profile_id,
                image_file_path=filename_p,
                exposure=exposure,
                gain=gain,
                capture_status='bad_image',
                error_message=str(e),
            )
            filename_p.unlink()
            #task.setFailed('Bad Image: {0:s}'.format(str(filename_p)))
            return
        except Exception as e:
            if images_only_diag:
                self._images_only_diag(profile_id, camera_id, 'IMAGE_PROCESSOR_ERROR', error=str(e), error_type=e.__class__.__name__)
            raise

        if images_only_diag:
            self._images_only_diag(
                profile_id,
                camera_id,
                'IMAGE_PROCESSOR_END',
                camera_uuid=i_ref.camera_uuid,
                day_date=i_ref.day_date,
                exp_date=i_ref.exp_date,
            )
            self._processor_cache_diag(profile_id, camera_id, 'IMAGE_PROCESSOR_CACHE_AFTER_ADD', binning)
            self._images_only_diag(profile_id, camera_id, 'IMAGE_POST_PROCESS_START')

        self._log_asi_frame_stats(
            asi_frame_stats_enabled,
            'raw_fits_after_read_pre_debayer',
            profile_id,
            camera_id,
            i_ref.hdulist[0].data,
            exposure=exposure,
            gain=gain,
            binning=binning,
            i_ref=i_ref,
        )


        filename_p.unlink()  # original file is no longer needed


        self.image_count += 1


        #############################################################################################
        ### Image data at this stage may be uint16 (grayscale or BGR) or uint8 (grayscale or BGR) ###
        #############################################################################################


        if images_only:
            logger.debug('[MULTI_CAMERA_IMAGES_ONLY][%s][camera_id=%s] disabled FITS/raw/hooks/circular display/realtime keogram/longterm keogram/panorama/extra uploads', profile_id, camera_id)

        if not images_only:
            self.start_image_save_pre_hook(exposure, gain, binning)


        if not images_only and self.config.get('IMAGE_SAVE_FITS'):
            if self.config.get('IMAGE_SAVE_FITS_PRE_DARK'):
                logger.warning('Saving FITS without dark frame calibration')
                self.write_fit(i_ref, camera)


        # use original value if not defined
        if i_ref.libcamera_black_level:
            libcamera_black_level = i_ref.libcamera_black_level


        if images_only_diag:
            self._images_only_diag(profile_id, camera_id, 'IMAGE_CALIBRATE_START')

        self.image_processor.calibrate(libcamera_black_level=libcamera_black_level)


        self.image_processor.fix_holes_early()

        self._log_asi_frame_stats(
            asi_frame_stats_enabled,
            'after_calibration_bitdepth_pre_debayer',
            profile_id,
            camera_id,
            i_ref.hdulist[0].data,
            exposure=exposure,
            gain=gain,
            binning=binning,
            i_ref=i_ref,
        )

        if images_only_diag:
            self._images_only_diag(profile_id, camera_id, 'IMAGE_CALIBRATE_END')
            self._processor_cache_diag(profile_id, camera_id, 'IMAGE_PROCESSOR_CACHE_AFTER_CALIBRATE', binning)


        if not images_only and self.config.get('IMAGE_SAVE_FITS'):
            if not self.config.get('IMAGE_SAVE_FITS_PRE_DARK'):
                self.write_fit(i_ref, camera)


        self.image_processor.calculateJankySqm()


        self.image_processor.debayer()  # populates self.opencv_data

        self._log_asi_frame_stats(
            asi_frame_stats_enabled,
            'after_debayer_cfa',
            profile_id,
            camera_id,
            i_ref.opencv_data,
            exposure=exposure,
            gain=gain,
            binning=binning,
            i_ref=i_ref,
        )

        self.image_processor.stack()  # populates self.image


        image_height, image_width = self.image_processor.image.shape[:2]
        logger.info('Image: %d x %d', image_width, image_height)
        if images_only_diag:
            self._processor_cache_diag(profile_id, camera_id, 'IMAGE_PROCESSOR_CACHE_AFTER_STACK', binning)

        self._log_asi_frame_stats(
            asi_frame_stats_enabled,
            'before_hybrid_awb_postprocess',
            profile_id,
            camera_id,
            self.image_processor.image,
            exposure=exposure,
            gain=gain,
            binning=binning,
            i_ref=i_ref,
        )

        self.apply_hybrid_awb(profile_id, camera_id)

        self._log_asi_frame_stats(
            asi_frame_stats_enabled,
            'after_hybrid_awb_postprocess',
            profile_id,
            camera_id,
            self.image_processor.image,
            exposure=exposure,
            gain=gain,
            binning=binning,
            i_ref=i_ref,
        )

        self.update_hybrid_awb(profile_id, camera_id)


        ### IMAGE IS CALIBRATED ###


        ### EXIF tags ###
        exp_date_utc = exp_date.replace(tzinfo=timezone.utc)

        # Python 3.6, 3.7 does not support as_integer_ratio()
        focal_length_frac = Fraction(camera.lensFocalLength).limit_denominator()
        focal_length = (focal_length_frac.numerator, focal_length_frac.denominator)

        f_number_frac = Fraction(camera.lensFocalRatio).limit_denominator()
        f_number = (f_number_frac.numerator, f_number_frac.denominator)

        exposure_time_frac = Fraction(exposure).limit_denominator(max_denominator=31250)
        exposure_time = (exposure_time_frac.numerator, exposure_time_frac.denominator)

        zeroth_ifd = {
            piexif.ImageIFD.Model            : camera.name,
            piexif.ImageIFD.Software         : 'indi-allsky',
            piexif.ImageIFD.ExposureTime     : exposure_time,
        }
        exif_ifd = {
            piexif.ExifIFD.DateTimeOriginal  : exp_date_utc.strftime('%Y:%m:%d %H:%M:%S'),
            piexif.ExifIFD.LensModel         : camera.lensName,
            piexif.ExifIFD.LensSpecification : (focal_length, focal_length, f_number, f_number),
            piexif.ExifIFD.FocalLength       : focal_length,
            piexif.ExifIFD.FNumber           : f_number,
            #piexif.ExifIFD.ApertureValue  # this is not the Aperture size
        }


        if self.sensors_temp_av[constants.SENSOR_TEMP_CCD_TEMP] > -150:
            # Add temperature data
            temperature_frac = Fraction(self.sensors_temp_av[constants.SENSOR_TEMP_CCD_TEMP]).limit_denominator()
            exif_ifd[piexif.ExifIFD.Temperature] = (temperature_frac.numerator, temperature_frac.denominator)


        jpeg_exif_dict = {
            '0th'   : zeroth_ifd,
            'Exif'  : exif_ifd,
        }


        if not self.config.get('IMAGE_EXIF_PRIVACY'):
            if camera.owner:
                zeroth_ifd[piexif.ImageIFD.Copyright] = camera.owner


            if self.config.get('PRIVACY_MODE'):
                long_deg, long_min, long_sec = self.decdeg2dms(float(round(camera.longitude)))
                lat_deg, lat_min, lat_sec = self.decdeg2dms(float(round(camera.latitude)))
            else:
                long_deg, long_min, long_sec = self.decdeg2dms(camera.longitude)
                lat_deg, lat_min, lat_sec = self.decdeg2dms(camera.latitude)


            if long_deg < 0:
                long_ref = 'W'
            else:
                long_ref = 'E'

            if lat_deg < 0:
                lat_ref = 'S'
            else:
                lat_ref = 'N'

            gps_datestamp = exp_date_utc.strftime('%Y:%m:%d')
            gps_hour   = int(exp_date_utc.strftime('%H'))
            gps_minute = int(exp_date_utc.strftime('%M'))
            gps_second = int(exp_date_utc.strftime('%S'))

            gps_ifd = {
                piexif.GPSIFD.GPSVersionID       : (2, 2, 0, 0),
                piexif.GPSIFD.GPSDateStamp       : gps_datestamp,
                piexif.GPSIFD.GPSTimeStamp       : ((gps_hour, 1), (gps_minute, 1), (gps_second, 1)),
                piexif.GPSIFD.GPSLongitudeRef    : long_ref,
                piexif.GPSIFD.GPSLongitude       : ((int(abs(long_deg)), 1), (int(long_min), 1), (0, 1)),  # no seconds
                piexif.GPSIFD.GPSLatitudeRef     : lat_ref,
                piexif.GPSIFD.GPSLatitude        : ((int(abs(lat_deg)), 1), (int(lat_min), 1), (0, 1)),  # no seconds
                #piexif.GPSIFD.GPSAltitudeRef     : 0,  # 0 = above sea level, 1 = below
                #piexif.GPSIFD.GPSAltitude        : (0, 1),
            }

            jpeg_exif_dict['GPS'] = gps_ifd


        jpeg_exif = piexif.dump(jpeg_exif_dict)


        # only perform this processing if libcamera is set to raw mode
        if self.libcamera_raw:
            # These values come from libcamera
            if libcamera_awb_gains:
                logger.info('Overriding Red balance: %f', libcamera_awb_gains[0])
                logger.info('Overriding Blue balance: %f', libcamera_awb_gains[1])
                self.config['WBR_FACTOR'] = float(libcamera_awb_gains[0])
                self.config['WBB_FACTOR'] = float(libcamera_awb_gains[1])


            # Not quite working
            if libcamera_ccm:
                self.image_processor.apply_color_correction_matrix(libcamera_ccm)


        if not images_only and self.config.get('IMAGE_EXPORT_RAW'):
            self.export_raw_image(i_ref, camera, jpeg_exif=jpeg_exif)


        # Calculate ADU before stretch
        adu = self.image_processor.calculate_8bit_adu()

        self._log_asi_frame_stats(
            asi_frame_stats_enabled,
            'before_auto_meter',
            profile_id,
            camera_id,
            self.image_processor.image,
            exposure=exposure,
            gain=gain,
            binning=binning,
            i_ref=i_ref,
        )

        self._meter_auto_exposure(profile_id, camera_id, binning)
        # adu value may be updated below


        self.image_processor.denoise()

        self.image_processor.stretch()


        if self.config.get('CONTRAST_ENHANCE_16BIT'):
            if not self.night_av[constants.NIGHT_NIGHT] and self.config['DAYTIME_CONTRAST_ENHANCE']:
                # Contrast enhancement during the day
                self.image_processor.contrast_clahe_16bit()
            elif self.night_av[constants.NIGHT_NIGHT] and self.config['NIGHT_CONTRAST_ENHANCE']:
                # Contrast enhancement during night
                self.image_processor.contrast_clahe_16bit()


        self.image_processor.convert_16bit_to_8bit()

        #################################################################
        ### Image data at this stage will be uint8 (grayscale or BGR) ###
        #################################################################


        #with io.open('/tmp/indi_allsky_numpy.npy', 'w+b') as f_numpy:
        #    numpy.save(f_numpy, self.image_processor.image)
        #logger.info('Wrote Numpy data: /tmp/indi_allsky_numpy.npy')


        # adu calculate (before processing)
        if images_only_diag:
            self._images_only_diag(profile_id, camera_id, 'IMAGE_ADU_CALC_START', target_adu_found=self.target_adu_found)
            self._processor_cache_diag(profile_id, camera_id, 'IMAGE_PROCESSOR_CACHE_BEFORE_ADU', binning)

        adu, adu_average = self.calculate_exposure(adu, exposure, gain)
        self._apply_auto_exposure_decision(profile_id, camera_id)

        if images_only_diag:
            self._images_only_diag(
                profile_id,
                camera_id,
                'IMAGE_ADU_CALC_END',
                adu=adu,
                adu_average=adu_average,
                current_adu_target=self.current_adu_target,
                target_adu_found=self.target_adu_found,
            )


        # generate a new mask base once the target ADU is found
        # this should only only fire once per restart
        if images_only_diag:
            self._images_only_diag(
                profile_id,
                camera_id,
                'IMAGE_STABLE_CHECK',
                generate_mask_base=self.generate_mask_base,
                target_adu_found=self.target_adu_found,
            )

        if self.generate_mask_base and self.target_adu_found:
            self.generate_mask_base = False
            if images_only_diag:
                self._images_only_diag(profile_id, camera_id, 'IMAGE_STABLE_CHECK', action='write_mask_base_start')
            self.write_mask_base_img(self.image_processor.image)
            if images_only_diag:
                self._images_only_diag(profile_id, camera_id, 'IMAGE_STABLE_CHECK', action='write_mask_base_end')


        # line detection
        if self.night_av[constants.NIGHT_NIGHT] and self.config.get('DETECT_METEORS'):
            self.image_processor.detectLines()


        # star detection
        if self.night_av[constants.NIGHT_NIGHT] and self.config.get('DETECT_STARS', True):
            self.image_processor.detectStars()


        # additional draw code
        if self.config.get('DETECT_DRAW'):
            self.image_processor.drawDetections()


        # rotation
        self.image_processor.rotate_90()
        self.image_processor.rotate_angle()


        # verticle flip
        self.image_processor.flip_v()

        # horizontal flip
        self.image_processor.flip_h()


        # crop
        self.image_processor.crop_image()


        # green removal
        self.image_processor.scnr()


        # white balance
        self.image_processor.white_balance_mtf()
        self.image_processor.white_balance_manual_bgr()
        self.image_processor.white_balance_auto_bgr()


        # saturation
        self.image_processor.saturation_adjust()


        # gamma correction
        self.image_processor.apply_gamma_correction()


        # sharpening (unsharp mask)
        self.image_processor.sharpen()


        if not self.config.get('CONTRAST_ENHANCE_16BIT'):
            if not self.night_av[constants.NIGHT_NIGHT] and self.config['DAYTIME_CONTRAST_ENHANCE']:
                # Contrast enhancement during the day
                self.image_processor.contrast_clahe()
            elif self.night_av[constants.NIGHT_NIGHT] and self.config['NIGHT_CONTRAST_ENHANCE']:
                # Contrast enhancement during night
                self.image_processor.contrast_clahe()


        self.image_processor.colorize()

        ##################################################
        ### Image data at this stage will be uint8 BGR ###
        ##################################################


        if images_only or not profile_outputs.get('longterm_keogram', True):
            logger.debug('[%s][camera_id=%s] Long term keogram disabled for images-only profile', profile_id, camera_id)
            longterm_keogram_pixels = None
        else:
            longterm_keogram_pixels = self.save_longterm_keogram_data(exp_date, camera_id)


        self.image_processor.colormap()


        if images_only_diag:
            self._processor_cache_diag(profile_id, camera_id, 'IMAGE_PROCESSOR_CACHE_BEFORE_CIRCLE_MASK', i_ref.binning)

        self.image_processor.apply_image_circle_mask(i_ref.binning)


        if images_only or not profile_outputs.get('realtime_keogram', True):
            logger.debug('[%s][camera_id=%s] Realtime keogram disabled for images-only profile', profile_id, camera_id)
        else:
            self.image_processor.realtimeKeogramUpdate()


        if not images_only and profile_outputs.get('panorama', True) and self.config.get('FISH2PANO', {}).get('ENABLE'):
            if not self.image_count % self.config.get('FISH2PANO', {}).get('MODULUS', 2):
                pano_data = self.image_processor.fish2pano(i_ref.binning)


                if self.config.get('FISH2PANO', {}).get('ENABLE_CARDINAL_DIRS'):
                    pano_data = self.image_processor.fish2pano_cardinal_dirs_label(pano_data)


                self.write_panorama_img(pano_data, i_ref, camera, jpeg_exif=jpeg_exif)


        if not images_only and self.config.get('CIRCULAR_DISPLAY', {}).get('ENABLE'):
            if not self.config.get('FOCUS_MODE', False):
                circular_display_image = self.image_processor.circular_display(i_ref.binning)
                self.write_circular_display_img(circular_display_image, jpeg_exif=jpeg_exif)


        if images_only_diag:
            self._processor_cache_diag(profile_id, camera_id, 'IMAGE_PROCESSOR_CACHE_BEFORE_LOGO', i_ref.binning)

        self.image_processor.apply_logo_overlay(i_ref.binning)


        self.image_processor.scale_image()


        self.image_processor.add_border()

        self.image_processor.moon_overlay()

        self.image_processor.lightgraph_overlay()

        self.image_processor.image_overlay()

        self.image_processor.orb_image()

        self.image_processor.cardinal_dirs_label()

        if images_only_diag:
            self._images_only_diag(profile_id, camera_id, 'IMAGE_POST_PROCESS_END')


        # get ADS-B data
        if images_only_diag:
            self._images_only_diag(profile_id, camera_id, 'IMAGE_ADSB_CHECK', has_worker=bool(self.adsb_worker))

        if self.adsb_worker:
            try:
                self.adsb_aircraft_list = self.adsb_aircraft_q.get(timeout=5.0)
            except queue.Empty:
                self.adsb_aircraft_list = []

            self.adsb_aircraft_q.close()
            self.adsb_aircraft_q = None

            self.adsb_worker.join()
            self.adsb_worker = None

        if images_only_diag:
            self._images_only_diag(profile_id, camera_id, 'IMAGE_ADSB_DONE', aircraft=len(self.adsb_aircraft_list))


        # wait on the pre-hook to finish
        if images_only:
            custom_hook_data = {}
        else:
            custom_hook_data = self.wait_image_save_pre_hook()


        if images_only_diag:
            self._images_only_diag(profile_id, camera_id, 'IMAGE_LABEL_START')

        self.image_processor.label_image(adsb_aircraft_list=self.adsb_aircraft_list, custom_hook_data=custom_hook_data)

        if images_only_diag:
            self._images_only_diag(profile_id, camera_id, 'IMAGE_LABEL_END')


        processing_elapsed_s = time.time() - processing_start
        logger.info('Image processed in %0.4f s', processing_elapsed_s)
        post_processing_start = time.time()


        # need this after resizing and scaling
        final_height, final_width = self.image_processor.image.shape[:2]


        #task.setSuccess('Image processed')

        if images_only_diag:
            self._images_only_diag(profile_id, camera_id, 'IMAGE_STATUS_ELIGIBLE', primary=profile_primary)

        if profile_primary:
            if images_only_diag:
                self._images_only_diag(profile_id, camera_id, 'IMAGE_PRIMARY_BRANCH_START')
                self._images_only_diag(profile_id, camera_id, 'IMAGE_STATUS_JSON_START')

            try:
                self.write_status_json(i_ref, adu, adu_average)  # write json status file
            except Exception as e:
                if images_only_diag:
                    self._images_only_diag(profile_id, camera_id, 'IMAGE_STATUS_JSON_ERROR', error=str(e), error_type=e.__class__.__name__)
                raise

            if images_only_diag:
                self._images_only_diag(profile_id, camera_id, 'IMAGE_STATUS_JSON_END')
                self._images_only_diag(profile_id, camera_id, 'IMAGE_PRIMARY_BRANCH_END')
        else:
            logger.debug('[%s][camera_id=%s] Status json disabled for secondary profile', profile_id, camera_id)


        if not images_only and profile_outputs.get('realtime_keogram', True) and not isinstance(self.image_processor.realtime_keogram_data, type(None)):
            # keogram might be empty on dimension mismatch
            self.write_realtime_keogram(self.image_processor.realtime_keogram_trimmed, camera)


        diag_context = None
        if images_only_diag:
            diag_context = {
                'profile_id' : profile_id,
                'camera_id'  : camera_id,
                'images_only': images_only,
            }
            self._images_only_diag(profile_id, camera_id, 'IMAGE_WRITE_IMG_START', write_latest=profile_primary)

        try:
            latest_file, new_filename = self.write_img(
                self.image_processor.image,
                i_ref,
                camera,
                jpeg_exif=jpeg_exif,
                write_latest=profile_primary,
                diag_context=diag_context,
            )
        except Exception as e:
            if images_only_diag:
                self._images_only_diag(profile_id, camera_id, 'IMAGE_WRITE_IMG_ERROR', error=str(e), error_type=e.__class__.__name__)
            raise

        if images_only_diag:
            self._images_only_diag(
                profile_id,
                camera_id,
                'IMAGE_WRITE_IMG_RESULT',
                latest_file=str(latest_file) if latest_file else None,
                new_filename=str(new_filename) if new_filename else None,
            )

        if new_filename:
            if not images_only:
                self.start_image_save_post_hook(new_filename, exposure, gain, binning)

            image_metadata = {
                'type'            : constants.IMAGE,
                'createDate'      : int(exp_date.timestamp()),
                'dayDate'         : i_ref.day_date.strftime('%Y%m%d'),
                'utc_offset'      : exp_date.astimezone().utcoffset().total_seconds(),
                'exposure'        : exposure,
                'exp_elapsed'     : exp_elapsed,
                'gain'            : float(gain),
                'binmode'         : int(binning),
                'temp'            : self.sensors_temp_av[constants.SENSOR_TEMP_CCD_TEMP],
                'adu'             : adu,
                'stable'          : self.target_adu_found,
                'moonmode'        : bool(self.night_av[constants.NIGHT_MOONMODE]),
                'moonphase'       : self.image_processor.astrometric_data['moon_phase'],
                'night'           : bool(self.night_av[constants.NIGHT_NIGHT]),
                'adu_roi'         : self.config['ADU_ROI'],
                'calibrated'      : i_ref.calibrated,
                'sqm'             : i_ref.sqm_value,
                'stars'           : len(i_ref.stars),
                'detections'      : len(i_ref.lines),
                'process_elapsed' : processing_elapsed_s,
                'kpindex'         : i_ref.kpindex,
                'ovation_max'     : i_ref.ovation_max,
                'smoke_rating'    : i_ref.smoke_rating,
                'fileSize'        : new_filename.stat().st_size,
                'height'          : final_height,
                'width'           : final_width,
                'keogram_pixels'  : longterm_keogram_pixels,
                'camera_uuid'     : i_ref.camera_uuid,
            }


            image_add_data = {
                'uptime'            : i_ref.uptime,
                'kpindex'           : i_ref.kpindex,
                'ovation_max'       : i_ref.ovation_max,
                'aurora_mag_bt'     : i_ref.aurora_mag_bt,
                'aurora_mag_gsm_bz' : i_ref.aurora_mag_gsm_bz,
                'aurora_plasma_density' : i_ref.aurora_plasma_density,
                'aurora_plasma_speed'   : i_ref.aurora_plasma_speed,
                'aurora_plasma_temp'    : i_ref.aurora_plasma_temp,
                'aurora_n_hemi_gw'  : i_ref.aurora_n_hemi_gw,
                'aurora_s_hemi_gw'  : i_ref.aurora_s_hemi_gw,
                'camera_sqm_raw_mag' : self.image_processor.camera_sqm_raw_mag,
            }


            for i in range(60):
                v = self.sensors_temp_av[i]

                if self.config.get('TEMP_DISPLAY') == 'f':
                    v_temp = (v * 9.0 / 5.0) + 32
                elif self.config.get('TEMP_DISPLAY') == 'k':
                    v_temp = v + 273.15
                else:
                    v_temp = v

                image_add_data['sensor_temp_{0:d}'.format(i)] = v_temp


            for i in range(60):
                image_add_data['sensor_user_{0:d}'.format(i)] = self.sensors_user_av[i]

            for i in range(100, 110):
                image_add_data['sensor_user_{0:d}'.format(i)] = self.sensors_user_av[i]


            if self.adsb_aircraft_list:
                image_add_data['aircraft'] = list()

                for aircraft in self.adsb_aircraft_list:
                    image_add_data['aircraft'].append(aircraft)


            image_metadata['data'] = image_add_data


            if images_only_diag:
                self._images_only_diag(profile_id, camera_id, 'IMAGE_ADDIMAGE_START', filename=str(new_filename))

            try:
                image_entry = self._miscDb.addImage(
                    new_filename.relative_to(self.image_dir),
                    camera_id,
                    image_metadata,
                )
            except Exception as e:
                if images_only_diag:
                    self._images_only_diag(profile_id, camera_id, 'IMAGE_ADDIMAGE_ERROR', error=str(e), error_type=e.__class__.__name__, filename=str(new_filename))
                self._persist_frame_metadata(
                    frame_id=0,
                    timestamp=exp_date.astimezone(timezone.utc).isoformat(),
                    camera_id=camera_id,
                    profile_id=profile_id,
                    image_file_path=new_filename,
                    exposure=exposure,
                    gain=gain,
                    capture_status='db_error',
                    error_message=str(e),
                )
                raise

            if images_only_diag:
                self._images_only_diag(profile_id, camera_id, 'IMAGE_ADDIMAGE_OK', image_id=image_entry.id, filename=str(new_filename))

            self._persist_frame_metadata(
                frame_id=image_entry.id,
                timestamp=exp_date.astimezone(timezone.utc).isoformat(),
                camera_id=camera_id,
                profile_id=profile_id,
                image_file_path=new_filename,
                exposure=exposure,
                gain=gain,
                capture_status='processed',
            )


            image_thumbnail_metadata = {
                'type'       : constants.THUMBNAIL,
                'origin'     : constants.IMAGE,
                'createDate' : int(exp_date.timestamp()),
                'dayDate'    : i_ref.day_date.strftime('%Y%m%d'),
                'utc_offset' : exp_date.astimezone().utcoffset().total_seconds(),
                'night'      : bool(self.night_av[constants.NIGHT_NIGHT]),
                'camera_uuid': camera.uuid,
            }

            image_thumbnail_entry = self._miscDb.addThumbnail(
                image_entry,
                image_metadata,
                camera.id,
                image_thumbnail_metadata,
                numpy_data=self.image_processor.image,
            )


            # add fileSize to metadata
            image_thumbnail_metadata['fileSize'] = image_thumbnail_entry.fileSize


            # wait on the post-hook to finish
            if not images_only:
                self.wait_image_save_post_hook()
        else:
            # images not being saved
            reason = 'not_saved'
            if images_only_diag:
                reason = 'unknown'
                if self.config.get('FOCUS_MODE', False):
                    reason = 'focus_mode'
                elif not self.night_av[constants.NIGHT_NIGHT] and self.config['DAYTIME_CAPTURE'] and not self.config.get('DAYTIME_CAPTURE_SAVE', True):
                    reason = 'daytime_save_disabled'

                self._images_only_diag(profile_id, camera_id, 'IMAGE_WRITE_IMG_SKIPPED', reason=reason)

            image_entry = None
            image_metadata = {}
            image_thumbnail_entry = None
            image_thumbnail_metadata = {}
            self._persist_frame_metadata(
                frame_id=0,
                timestamp=exp_date.astimezone(timezone.utc).isoformat(),
                camera_id=camera_id,
                profile_id=profile_id,
                image_file_path=latest_file or '',
                exposure=exposure,
                gain=gain,
                capture_status=reason,
            )


        if latest_file:
            # build mqtt data
            mq_topic_latest = 'latest'

            mqtt_data = {
                'exp_date' : exp_date.strftime('%Y-%m-%d %H:%M:%S'),
                'exposure' : round(exposure, 6),
                'gain'     : round(gain, 2),
                'bin'      : int(binning),
                'temp'     : round(self.sensors_temp_av[constants.SENSOR_TEMP_CCD_TEMP], 1),
                'sunalt'   : round(self.image_processor.astrometric_data['sun_alt'], 1),
                'moonalt'  : round(self.image_processor.astrometric_data['moon_alt'], 1),
                'moonphase': round(self.image_processor.astrometric_data['moon_phase'], 1),
                'mooncycle': round(self.image_processor.astrometric_data['moon_cycle'], 1),
                'moonmode' : bool(self.night_av[constants.NIGHT_MOONMODE]),
                'night'    : bool(self.night_av[constants.NIGHT_NIGHT]),
                'sqm'      : round(i_ref.sqm_value, 1),
                'stars'    : len(i_ref.stars),
                'detections' : len(i_ref.lines),
                'latitude' : round(self.position_av[constants.POSITION_LATITUDE], 3),
                'longitude': round(self.position_av[constants.POSITION_LONGITUDE], 3),
                'elevation': int(self.position_av[constants.POSITION_ELEVATION]),
                'smoke_rating'  : constants.SMOKE_RATING_MAP_STR[i_ref.smoke_rating],
                'aircraft'      : len(self.adsb_aircraft_list),
                'sidereal_time' : self.image_processor.astrometric_data['sidereal_time'],
                'kpindex'       : round(i_ref.kpindex, 2),
                'ovation_max'   : int(i_ref.ovation_max),
                'aurora_mag_bt'     : round(i_ref.aurora_mag_bt, 2),
                'aurora_mag_gsm_bz' : round(i_ref.aurora_mag_gsm_bz, 2),
                'aurora_plasma_density' : round(i_ref.aurora_plasma_density, 2),
                'aurora_plasma_speed'   : round(i_ref.aurora_plasma_speed, 2),
                'aurora_plasma_temp'    : i_ref.aurora_plasma_temp,
                'aurora_n_hemi_gw'  : i_ref.aurora_n_hemi_gw,
                'aurora_s_hemi_gw'  : i_ref.aurora_s_hemi_gw,
                'camera_sqm_raw_mag' : self.image_processor.camera_sqm_raw_mag,
            }


            # publish cpu info
            cpu_info = psutil.cpu_times_percent()
            mqtt_data['cpu/user'] = round(cpu_info.user, 1)
            mqtt_data['cpu/system'] = round(cpu_info.system, 1)
            mqtt_data['cpu/nice'] = round(cpu_info.nice, 1)
            mqtt_data['cpu/iowait'] = round(cpu_info.iowait, 1)  # io wait is not true cpu usage, not including in total
            mqtt_data['cpu/total'] = round(cpu_info.user + cpu_info.system + cpu_info.nice, 1)


            # publish memory info
            memory_info = psutil.virtual_memory()
            memory_total = memory_info.total
            memory_free = memory_info.free

            mqtt_data['memory/user'] = round((memory_info.used / memory_total) * 100.0, 1)
            mqtt_data['memory/cached'] = round((memory_info.cached / memory_total) * 100.0, 1)
            mqtt_data['memory/total'] = round(100 - ((memory_free * 100) / memory_total), 1)


            # publish disk info
            fs_list = psutil.disk_partitions(all=False)

            for fs in fs_list:

                skip = False
                for p in ('/snap',):
                    if fs.mountpoint.startswith(p + '/'):
                        skip = True
                        break
                    elif fs.mountpoint == p:
                        skip = True
                        break

                if skip:
                    continue


                try:
                    disk_usage = psutil.disk_usage(fs.mountpoint)
                except PermissionError as e:
                    logger.error('PermissionError: %s', str(e))
                    continue

                if fs.mountpoint == '/':
                    mqtt_data['disk/root'] = round(disk_usage.percent, 1)  # hopefully there is not a /root filesystem
                    continue
                else:
                    # slash is included with filesystem name
                    mqtt_data['disk{0:s}'.format(fs.mountpoint)] = round(disk_usage.percent, 1)


            # publish temperature info
            temp_info = psutil.sensors_temperatures()

            system_temp_count = 0  # need index for shared sensor values
            for t_key in sorted(temp_info):  # always return the keys in the same order
                for i, t in enumerate(temp_info[t_key]):
                    if system_temp_count > 49:
                        # limit to 50
                        continue

                    temp_c = float(t.current)

                    if self.config.get('TEMP_DISPLAY') == 'f':
                        current_temp = (temp_c * 9.0 / 5.0) + 32
                    elif self.config.get('TEMP_DISPLAY') == 'k':
                        current_temp = temp_c + 273.15
                    else:
                        current_temp = temp_c


                    if not t.label:
                        # use index for label name
                        label = str(i)
                    else:
                        label = t.label

                    topic = 'temp/{0:s}/{1:s}'.format(t_key, label)

                    # no spaces, etc in topics
                    topic_sub = re.sub(r'[#+\$\*\>\.\ ]', '_', topic)

                    mqtt_data[topic_sub] = round(current_temp, 1)


                    # update share array
                    # temperatures always Celsius here
                    with self.sensors_temp_av.get_lock():
                        # index 0 is always ccd_temp
                        self.sensors_temp_av[10 + system_temp_count] = temp_c

                    system_temp_count += 1


            # system temp sensors
            for i in range(60):
                v = self.sensors_temp_av[i]

                if self.config.get('TEMP_DISPLAY') == 'f':
                    v_temp = (v * 9.0 / 5.0) + 32
                elif self.config.get('TEMP_DISPLAY') == 'k':
                    v_temp = v + 273.15
                else:
                    v_temp = v


                sensor_topic = 'sensor_temp_{0:d}'.format(i)
                mqtt_data[sensor_topic] = round(v_temp, 1)


            # user sensors
            for i in range(60):
                sensor_topic = 'sensor_user_{0:d}'.format(i)
                mqtt_data[sensor_topic] = round(self.sensors_user_av[i], 3)

            for i in range(100, 110):
                sensor_topic = 'sensor_user_{0:d}'.format(i)
                mqtt_data[sensor_topic] = round(self.sensors_user_av[i], 3)


            if new_filename:
                upload_filename = new_filename
            else:
                upload_filename = latest_file


            if images_only or not profile_outputs.get('extra_uploads', True):
                logger.debug('[%s][camera_id=%s] Extra uploads disabled for images-only profile', profile_id, camera_id)
            else:
                ### upload thumbnail first
                if image_thumbnail_entry:
                    self._miscUpload.syncapi_thumbnail(image_thumbnail_entry, image_thumbnail_metadata)  # syncapi before s3
                    self._miscUpload.s3_upload_thumbnail(image_thumbnail_entry, image_thumbnail_metadata)


                self._miscUpload.syncapi_image(image_entry, image_metadata)  # syncapi before s3
                self._miscUpload.s3_upload_image(image_entry, image_metadata)
                self._miscUpload.mqtt_publish_image(upload_filename, mq_topic_latest, mqtt_data)
                self._miscUpload.upload_image(image_entry)

                self.upload_metadata(i_ref, adu, adu_average)

        if images_only_diag and self.config.get('MULTI_CAMERA_TIMING_DIAG', False):
            post_processing_elapsed_s = time.time() - post_processing_start
            payload_elapsed_s = time.time() - payload_start_time
            _multi_camera_diag(
                '[MULTI_CAMERA_TIMING][%s][camera_id=%s] processing_end processing=%0.4fs post_processing=%0.4fs total_worker=%0.4fs queue_wait=%0.4fs capture_to_done=%0.4fs db_saved=%s latest_file=%s new_filename=%s',
                profile_id,
                camera_id,
                processing_elapsed_s,
                post_processing_elapsed_s,
                payload_elapsed_s,
                queue_wait_s,
                (time.time() - capture_start_time) if capture_start_time else 0.0,
                bool(new_filename),
                str(latest_file) if latest_file else None,
                str(new_filename) if new_filename else None,
            )


    def decdeg2dms(self, dd):
        is_positive = dd >= 0
        dd = abs(dd)
        minutes, seconds = divmod(dd * 3600, 60)
        degrees, minutes = divmod(minutes, 60)
        degrees = degrees if is_positive else -degrees
        return degrees, minutes, seconds


    def upload_metadata(self, i_ref, adu, adu_average):
        ### upload metadata
        if not self.config.get('FILETRANSFER', {}).get('UPLOAD_METADATA'):
            #logger.warning('Metadata uploading disabled')
            return

        if not self.config.get('FILETRANSFER', {}).get('UPLOAD_IMAGE'):
            logger.warning('Metadata uploading disabled when image upload is disabled')
            return


        self.metadata_count += 1

        metadata_remain = self.metadata_count % int(self.config['FILETRANSFER']['UPLOAD_IMAGE'])
        if metadata_remain != 0:
            #next_metadata = int(self.config['FILETRANSFER']['UPLOAD_IMAGE']) - image_metadata
            #logger.info('Next metadata upload in %d images (%d s)', next_metadata, int(self.config['EXPOSURE_PERIOD'] * next_metadata))
            return


        metadata = {
            'type'                : constants.METADATA,
            'device'              : i_ref.camera_name,
            'night'               : self.night_av[constants.NIGHT_NIGHT],
            'temp'                : self.sensors_temp_av[constants.SENSOR_TEMP_CCD_TEMP],
            'gain'                : i_ref.gain,
            'exposure'            : i_ref.exposure,
            'stable_exposure'     : int(self.target_adu_found),
            'target_adu'          : i_ref.target_adu,
            'current_adu_target'  : self.current_adu_target,
            'current_adu'         : adu,
            'adu_average'         : adu_average,
            'sqm'                 : i_ref.sqm_value,
            'stars'               : len(i_ref.stars),
            'time'                : i_ref.exp_date.strftime('%s'),
            'tz'                  : str(i_ref.exp_date.astimezone().tzinfo),
            'utc_offset'          : i_ref.exp_date.astimezone().utcoffset().total_seconds(),
            'sqm_data'            : self.getSqmData(i_ref.camera_id),
            'stars_data'          : self.getStarsData(i_ref.camera_id),
            'latitude'            : self.position_av[constants.POSITION_LATITUDE],
            'longitude'           : self.position_av[constants.POSITION_LONGITUDE],
            'elevation'           : int(self.position_av[constants.POSITION_ELEVATION]),
            'sidereal_time'       : self.image_processor.astrometric_data['sidereal_time'],
            'kpindex'             : i_ref.kpindex,
            'aurora_mag_bt'       : i_ref.aurora_mag_bt,
            'aurora_mag_gsm_bz'   : i_ref.aurora_mag_gsm_bz,
            'aurora_plasma_density' : i_ref.aurora_plasma_density,
            'aurora_plasma_speed'   : i_ref.aurora_plasma_speed,
            'aurora_plasma_temp'    : i_ref.aurora_plasma_temp,
            'aurora_n_hemi_gw'    : i_ref.aurora_n_hemi_gw,
            'aurora_s_hemi_gw'    : i_ref.aurora_s_hemi_gw,
            'ovation_max'         : i_ref.ovation_max,
            'smoke_rating'        : constants.SMOKE_RATING_MAP_STR[i_ref.smoke_rating],
            'aircraft'            : len(self.adsb_aircraft_list),
            'camera_sqm_raw_mag'  : self.image_processor.camera_sqm_raw_mag,
        }


        # system temp sensors
        for i in range(60):
            v = self.sensors_temp_av[i]

            if self.config.get('TEMP_DISPLAY') == 'f':
                v_temp = (v * 9.0 / 5.0) + 32
            elif self.config.get('TEMP_DISPLAY') == 'k':
                v_temp = v + 273.15
            else:
                v_temp = v


            sensor_topic = 'sensor_temp_{0:d}'.format(i)
            metadata[sensor_topic] = v_temp


        # user sensors
        for i in range(60):
            sensor_topic = 'sensor_user_{0:d}'.format(i)
            metadata[sensor_topic] = self.sensors_user_av[i]

        for i in range(100, 110):
            sensor_topic = 'sensor_user_{0:d}'.format(i)
            metadata[sensor_topic] = self.sensors_user_av[i]


        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8') as f_tmp_metadata:
            json.dump(
                metadata,
                f_tmp_metadata,
                indent=4,
                ensure_ascii=False,
            )

            tmp_metadata_name_p = Path(f_tmp_metadata.name)


        tmp_metadata_name_p.chmod(0o644)


        file_data_dict = {
            'timestamp'    : i_ref.exp_date,
            'ts'           : i_ref.exp_date,  # shortcut
            'day_date'     : i_ref.day_date,
            'ext'          : 'json',
            'camera_uuid'  : i_ref.camera_uuid,
            'camera_id'    : i_ref.camera_id,
        }


        if self.night_av[constants.NIGHT_NIGHT]:
            file_data_dict['timeofday'] = 'night'
            file_data_dict['tod'] = 'night'
        else:
            file_data_dict['timeofday'] = 'day'
            file_data_dict['tod'] = 'day'


        # Replace parameters in names
        remote_dir = self.config['FILETRANSFER']['REMOTE_METADATA_FOLDER'].format(**file_data_dict)
        remote_file = self.config['FILETRANSFER']['REMOTE_METADATA_NAME'].format(**file_data_dict)

        remote_file_p = Path(remote_dir).joinpath(remote_file)

        # tell worker to upload file
        jobdata = {
            'action'       : constants.TRANSFER_UPLOAD,
            'local_file'   : str(tmp_metadata_name_p),
            'remote_file'  : str(remote_file_p),
            'remove_local' : True,
        }

        upload_task = IndiAllSkyDbTaskQueueTable(
            queue=TaskQueueQueue.UPLOAD,
            state=TaskQueueState.QUEUED,
            data=jobdata,
        )
        db.session.add(upload_task)
        db.session.commit()

        # MULTI_CAMERA_PREP: passive route id; upload worker still loads task.
        self._queue_upload_task(upload_task, camera_id=i_ref.camera_id)


    def getSqmData(self, camera_id):
        now_minus_minutes = datetime.now() - timedelta(minutes=self.sqm_history_minutes)

        sqm_images = IndiAllSkyDbImageTable.query\
            .add_columns(
                func.max(IndiAllSkyDbImageTable.sqm).label('image_max_sqm'),
                func.min(IndiAllSkyDbImageTable.sqm).label('image_min_sqm'),
                func.avg(IndiAllSkyDbImageTable.sqm).label('image_avg_sqm'),
            )\
            .join(IndiAllSkyDbCameraTable)\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .filter(IndiAllSkyDbImageTable.createDate > now_minus_minutes)\
            .first()


        sqm_data = {
            'max' : sqm_images.image_max_sqm,
            'min' : sqm_images.image_min_sqm,
            'avg' : sqm_images.image_avg_sqm,
        }

        return sqm_data


    def getStarsData(self, camera_id):
        now_minus_minutes = datetime.now() - timedelta(minutes=self.stars_history_minutes)

        stars_images = IndiAllSkyDbImageTable.query\
            .add_columns(
                func.max(IndiAllSkyDbImageTable.stars).label('image_max_stars'),
                func.min(IndiAllSkyDbImageTable.stars).label('image_min_stars'),
                func.avg(IndiAllSkyDbImageTable.stars).label('image_avg_stars'),
            )\
            .join(IndiAllSkyDbCameraTable)\
            .filter(IndiAllSkyDbCameraTable.id == camera_id)\
            .filter(IndiAllSkyDbImageTable.createDate > now_minus_minutes)\
            .first()


        stars_data = {
            'max' : stars_images.image_max_stars,
            'min' : stars_images.image_min_stars,
            'avg' : stars_images.image_avg_stars,
        }

        return stars_data


    def write_fit(self, i_ref, camera):
        now_time = time.time()
        if now_time < self.next_save_fits_time:
            return

        self.next_save_fits_time = time.time() + self.next_save_fits_offset


        ### Do not write daytime image files if daytime capture is disabled
        if not self.night_av[constants.NIGHT_NIGHT] and not self.config.get('DAYTIME_CAPTURE_SAVE', True):
            return


        data = i_ref.hdulist[0].data
        image_height, image_width = data.shape[:2]


        if self.config.get('IMAGE_SAVE_FITS_COMPRESSED'):
            import gzip

            fits_image_buffer = io.BytesIO()
            i_ref.hdulist.writeto(fits_image_buffer)

            f_tmpfile = tempfile.NamedTemporaryFile(mode='w+b', delete=False, suffix='.fit.gz')
            f_tmpfile.write(gzip.compress(fits_image_buffer.getbuffer()))

            fits_ext = 'fit.gz'
        else:
            f_tmpfile = tempfile.NamedTemporaryFile(mode='w+b', delete=False, suffix='.fit')
            i_ref.hdulist.writeto(f_tmpfile)

            fits_ext = 'fit'


        f_tmpfile.close()


        tmpfile_p = Path(f_tmpfile.name)


        fits_size_bytes = tmpfile_p.stat().st_size
        logger.info('FITS image file size: %0.1f MB', fits_size_bytes / 1024 / 1024)


        date_str = i_ref.exp_date.strftime('%Y%m%d_%H%M%S')
        # raw light
        folder = self._getImageFolder(i_ref.exp_date, i_ref.day_date, camera, 'fits')
        filename = folder.joinpath(self.filename_t.format(
            i_ref.camera_id,
            date_str,
            fits_ext,  # defined above
        ))


        fits_metadata = {
            'type'       : constants.FITS_IMAGE,
            'createDate' : int(i_ref.exp_date.timestamp()),
            'dayDate'    : i_ref.day_date.strftime('%Y%m%d'),
            'utc_offset' : i_ref.exp_date.astimezone().utcoffset().total_seconds(),
            'exposure'   : i_ref.exposure,
            'gain'       : i_ref.gain,
            'binmode'    : i_ref.binning,
            'night'      : bool(self.night_av[constants.NIGHT_NIGHT]),
            'fileSize'   : fits_size_bytes,
            'height'     : image_height,
            'width'      : image_width,
            'camera_uuid': i_ref.camera_uuid,
        }

        fits_metadata['data'] = {
            'moonmode'        : bool(self.night_av[constants.NIGHT_MOONMODE]),
            'moonphase'       : self.image_processor.astrometric_data['moon_phase'],
            'sqm'             : i_ref.sqm_value,
            'stars'           : len(i_ref.stars),
            'detections'      : len(i_ref.lines),
            'kpindex'         : i_ref.kpindex,
            'ovation_max'     : i_ref.ovation_max,
            'smoke_rating'    : i_ref.smoke_rating,
            'aurora_mag_bt'     : i_ref.aurora_mag_bt,
            'aurora_mag_gsm_bz' : i_ref.aurora_mag_gsm_bz,
            'aurora_plasma_density' : i_ref.aurora_plasma_density,
            'aurora_plasma_speed'   : i_ref.aurora_plasma_speed,
            'aurora_plasma_temp'    : i_ref.aurora_plasma_temp,
            'aurora_n_hemi_gw'      : i_ref.aurora_n_hemi_gw,
            'aurora_s_hemi_gw'      : i_ref.aurora_s_hemi_gw,
            'camera_sqm_raw_mag'    : self.image_processor.camera_sqm_raw_mag,
        }

        fits_entry = self._miscDb.addFitsImage(
            filename.relative_to(self.image_dir),
            i_ref.camera_id,
            fits_metadata,
        )


        file_dir = filename.parent
        if not file_dir.exists():
            file_dir.mkdir(mode=0o755, parents=True)

        logger.info('fit filename: %s', filename)


        if filename.exists():
            logger.error('File exists: %s (skipping)', filename)
            tmpfile_p.unlink()
            return


        shutil.copy2(str(tmpfile_p), str(filename))
        filename.chmod(0o644)

        # set mtime to original exposure time
        #os.utime(str(filename), (i_ref.exp_date.timestamp(), i_ref.exp_date.timestamp()))

        tmpfile_p.unlink()


        self._miscUpload.s3_upload_fits(fits_entry, fits_metadata)
        self._miscUpload.upload_fits_image(fits_entry)


    def export_raw_image(self, i_ref, camera, jpeg_exif=None):
        if not self.config.get('IMAGE_EXPORT_RAW'):
            return

        if not self.config.get('IMAGE_EXPORT_FOLDER'):
            logger.error('IMAGE_EXPORT_FOLDER not defined')
            return


        ### Do not write daytime image files if daytime capture is disabled
        if not self.night_av[constants.NIGHT_NIGHT] and not self.config.get('DAYTIME_CAPTURE_SAVE', True):
            return


        f_tmpfile = tempfile.NamedTemporaryFile(mode='w+b', delete=False, suffix='.{0}'.format(self.config['IMAGE_EXPORT_RAW']))
        f_tmpfile.close()

        tmpfile_name = Path(f_tmpfile.name)


        data = i_ref.opencv_data

        image_height, image_width = data.shape[:2]
        max_bit_depth = self.image_processor.max_bit_depth

        if i_ref.image_bitpix == 8:
            # nothing to scale
            scaled_data = data
        elif i_ref.image_bitpix == 16:
            logger.info('Upscaling data from %d to 16 bit', max_bit_depth)
            shift_factor = 16 - max_bit_depth
            scaled_data = numpy.left_shift(data, shift_factor)
        else:
            raise Exception('Unsupported bit depth')


        #logger.info('Image type: %s', str(scaled_data.dtype))
        #logger.info('Image shape: %s', str(scaled_data.shape))


        if not self.config.get('IMAGE_EXPORT_FLIP_V'):
            scaled_data = self.image_processor._flip(scaled_data, 0)

        if not self.config.get('IMAGE_EXPORT_FLIP_H'):
            scaled_data = self.image_processor._flip(scaled_data, 1)


        write_img_start = time.time()

        if self.config['IMAGE_EXPORT_RAW'] in ('jpg', 'jpeg'):
            if i_ref.image_bitpix == 8:
                scaled_data_8 = scaled_data
            else:
                # jpeg has to be 8 bits
                logger.info('Resampling image from %d to 8 bits', i_ref.image_bitpix)

                #div_factor = int((2 ** max_bit_depth) / 255)
                #scaled_data_8 = (scaled_data / div_factor).astype(numpy.uint8)

                # shifting is 5x faster than division
                shift_factor = max_bit_depth - 8
                scaled_data_8 = numpy.right_shift(scaled_data, shift_factor).astype(numpy.uint8)

            if len(scaled_data_8.shape) == 2:
                img = Image.fromarray(scaled_data_8)
            else:
                img = Image.fromarray(cv2.cvtColor(scaled_data_8, cv2.COLOR_BGR2RGB))

            img.save(str(tmpfile_name), quality=self.config['IMAGE_FILE_COMPRESSION']['jpg'], exif=jpeg_exif)
        elif self.config['IMAGE_EXPORT_RAW'] in ('png',):
            # Pillow does not support 16-bit RGB data
            # opencv is faster than Pillow with PNG
            cv2.imwrite(str(tmpfile_name), scaled_data, [cv2.IMWRITE_PNG_COMPRESSION, self.config['IMAGE_FILE_COMPRESSION']['png']])
        elif self.config['IMAGE_EXPORT_RAW'] in ('jp2',):
            cv2.imwrite(str(tmpfile_name), scaled_data)
        elif self.config['IMAGE_EXPORT_RAW'] in ('webp',):
            cv2.imwrite(str(tmpfile_name), scaled_data, [cv2.IMWRITE_WEBP_QUALITY, 101])  # lossless
        elif self.config['IMAGE_EXPORT_RAW'] in ('tif', 'tiff'):
            # Pillow does not support 16-bit RGB data
            cv2.imwrite(str(tmpfile_name), scaled_data, [cv2.IMWRITE_TIFF_COMPRESSION, 5])  # LZW
        else:
            raise Exception('Unknown file type: %s', self.config['IMAGE_EXPORT_RAW'])

        write_img_elapsed_s = time.time() - write_img_start
        logger.info('Raw image written in %0.4f s', write_img_elapsed_s)



        export_dir = Path(self.config['IMAGE_EXPORT_FOLDER'])

        if self.night_av[constants.NIGHT_NIGHT]:
            timeofday_str = 'night'
        else:
            # daytime
            timeofday_str = 'day'


        day_folder = export_dir.joinpath(
            'ccd_{0:s}'.format(camera.uuid),
            '{0:s}'.format(i_ref.day_date.strftime('%Y%m%d')),
            timeofday_str,
        )

        if not day_folder.exists():
            day_folder.mkdir(mode=0o755, parents=True)


        hour_str = i_ref.exp_date.strftime('%d_%H')

        hour_folder = day_folder.joinpath('{0:s}'.format(hour_str))
        if not hour_folder.exists():
            hour_folder.mkdir(mode=0o755)


        date_str = i_ref.exp_date.strftime('%Y%m%d_%H%M%S')

        raw_filename_t = 'raw_{0:s}'.format(self.filename_t)
        filename = hour_folder.joinpath(raw_filename_t.format(
            i_ref.camera_id,
            date_str,
            self.config['IMAGE_EXPORT_RAW'],  # file suffix
        ))


        raw_metadata = {
            'type'       : constants.RAW_IMAGE,
            'createDate' : int(i_ref.exp_date.timestamp()),
            'dayDate'    : i_ref.day_date.strftime('%Y%m%d'),
            'utc_offset' : i_ref.exp_date.astimezone().utcoffset().total_seconds(),
            'exposure'   : i_ref.exposure,
            'gain'       : i_ref.gain,
            'binmode'    : i_ref.binning,
            'night'      : bool(self.night_av[constants.NIGHT_NIGHT]),
            'fileSize'   : tmpfile_name.stat().st_size,
            'height'     : image_height,
            'width'      : image_width,
            'camera_uuid': i_ref.camera_uuid,
        }

        raw_metadata['data'] = {
            'moonmode'        : bool(self.night_av[constants.NIGHT_MOONMODE]),
            'moonphase'       : self.image_processor.astrometric_data['moon_phase'],
            'sqm'             : i_ref.sqm_value,
            'stars'           : len(i_ref.stars),
            'detections'      : len(i_ref.lines),
            'kpindex'         : i_ref.kpindex,
            'ovation_max'     : i_ref.ovation_max,
            'smoke_rating'    : i_ref.smoke_rating,
            'aurora_mag_bt'     : i_ref.aurora_mag_bt,
            'aurora_mag_gsm_bz' : i_ref.aurora_mag_gsm_bz,
            'aurora_plasma_density' : i_ref.aurora_plasma_density,
            'aurora_plasma_speed'   : i_ref.aurora_plasma_speed,
            'aurora_plasma_temp'    : i_ref.aurora_plasma_temp,
            'aurora_n_hemi_gw'      : i_ref.aurora_n_hemi_gw,
            'aurora_s_hemi_gw'      : i_ref.aurora_s_hemi_gw,
            'camera_sqm_raw_mag'    : self.image_processor.camera_sqm_raw_mag,
        }

        try:
            raw_filename = filename.relative_to(self.image_dir)
        except ValueError:
            # raw exports may be outside the image path
            raw_filename = filename

        raw_entry = self._miscDb.addRawImage(
            raw_filename,
            i_ref.camera_id,
            raw_metadata,
        )


        logger.info('RAW filename: %s', filename)

        if filename.exists():
            logger.error('File exists: %s (skipping)', filename)
            tmpfile_name.unlink()
            return


        shutil.copy2(str(tmpfile_name), str(filename))
        filename.chmod(0o644)

        tmpfile_name.unlink()

        # set mtime to original exposure time
        #os.utime(str(filename), (i_ref.exp_date.timestamp(), i_ref.exp_date.timestamp()))

        self._miscUpload.s3_upload_raw(raw_entry, raw_metadata)
        self._miscUpload.upload_raw_image(raw_entry)


    def write_mask_base_img(self, data):
        logger.info('Generating new mask base')
        f_tmpfile = tempfile.NamedTemporaryFile(mode='w+b', delete=False, suffix='.png')
        f_tmpfile.close()

        tmpfile_name = Path(f_tmpfile.name)


        cv2.imwrite(str(tmpfile_name), data, [cv2.IMWRITE_PNG_COMPRESSION, self.config['IMAGE_FILE_COMPRESSION']['png']])

        mask_file = self.image_dir.joinpath('mask_base.png')

        try:
            mask_file.unlink()
        except FileNotFoundError:
            pass


        shutil.copy2(str(tmpfile_name), str(mask_file))
        mask_file.chmod(0o644)


        tmpfile_name.unlink()


    def write_focus_fit(self, data):
        from astropy.io import fits

        if len(data.shape) == 3:
            # swap axes for FITS
            data = numpy.swapaxes(data, 1, 0)
            data = numpy.swapaxes(data, 2, 0)


        # create a new fits container
        hdu = fits.PrimaryHDU(data)
        hdulist = fits.HDUList([hdu])

        hdu.update_header()  # populates BITPIX, NAXIS, etc

        hdulist[0].header['IMAGETYP'] = 'Light Frame'
        hdulist[0].header['INSTRUME'] = 'focus'


        f_tmpfile = tempfile.NamedTemporaryFile(mode='w+b', delete=False, suffix='.fit')
        hdulist.writeto(f_tmpfile)
        f_tmpfile.close()

        tmpfile_p = Path(f_tmpfile.name)


        focus_fit_p = self.image_dir.joinpath('focus.fit')


        try:
            focus_fit_p.unlink()
        except FileNotFoundError:
            pass


        shutil.copy2(str(tmpfile_p), str(focus_fit_p))
        focus_fit_p.chmod(0o644)


        # cleanup
        tmpfile_p.unlink()


    def write_focus_png(self, data):

        f_tmpfile = tempfile.NamedTemporaryFile(mode='w+b', delete=False, suffix='.png')
        f_tmpfile.close()

        tmpfile_p = Path(f_tmpfile.name)

        cv2.imwrite(str(tmpfile_p), data, [cv2.IMWRITE_PNG_COMPRESSION, self.config['IMAGE_FILE_COMPRESSION']['png']])


        focus_png_p = self.image_dir.joinpath('focus.png')


        try:
            focus_png_p.unlink()
        except FileNotFoundError:
            pass


        shutil.copy2(str(tmpfile_p), str(focus_png_p))
        focus_png_p.chmod(0o644)


        # cleanup
        tmpfile_p.unlink()


    def write_img(self, data, i_ref, camera, jpeg_exif=None, write_latest=True, diag_context=None):
        diag_context = diag_context or {}
        diag_enabled = bool(diag_context.get('images_only'))
        diag_profile_id = diag_context.get('profile_id', self.profile_id)
        diag_camera_id = diag_context.get('camera_id', i_ref.camera_id)

        f_tmpfile = tempfile.NamedTemporaryFile(mode='w+b', delete=False, suffix='.{0}'.format(self.config['IMAGE_FILE_TYPE']))
        f_tmpfile.close()

        tmpfile_name = Path(f_tmpfile.name)


        #write_img_start = time.time()

        # write to temporary file
        if self.config['IMAGE_FILE_TYPE'] in ('jpg', 'jpeg'):
            # opencv is faster but we have exif data
            img_rgb = Image.fromarray(cv2.cvtColor(data, cv2.COLOR_BGR2RGB))
            img_rgb.save(str(tmpfile_name), quality=self.config['IMAGE_FILE_COMPRESSION']['jpg'], exif=jpeg_exif)
        elif self.config['IMAGE_FILE_TYPE'] in ('png',):
            # exif does not appear to work with png
            #img_rgb = Image.fromarray(cv2.cvtColor(data, cv2.COLOR_BGR2RGB))
            #img_rgb.save(str(tmpfile_name), compress_level=self.config['IMAGE_FILE_COMPRESSION']['png'])

            # opencv is faster than Pillow with PNG
            cv2.imwrite(str(tmpfile_name), data, [cv2.IMWRITE_PNG_COMPRESSION, self.config['IMAGE_FILE_COMPRESSION']['png']])
        elif self.config['IMAGE_FILE_TYPE'] in ('webp',):
            img_rgb = Image.fromarray(cv2.cvtColor(data, cv2.COLOR_BGR2RGB))
            img_rgb.save(str(tmpfile_name), quality=90, lossless=False, exif=jpeg_exif)
        elif self.config['IMAGE_FILE_TYPE'] in ('tif', 'tiff'):
            # exif does not appear to work with tiff
            img_rgb = Image.fromarray(cv2.cvtColor(data, cv2.COLOR_BGR2RGB))
            img_rgb.save(str(tmpfile_name), compression='tiff_lzw')
        else:
            tmpfile_name.unlink()
            raise Exception('Unknown file type: %s', self.config['IMAGE_FILE_TYPE'])

        #write_img_elapsed_s = time.time() - write_img_start
        #logger.info('Image compressed in %0.4f s', write_img_elapsed_s)


        file_size_bytes = tmpfile_name.stat().st_size
        if file_size_bytes < 1024000:
            logger.info('Compressed image file size: %0.2f KB', file_size_bytes / 1024)
        else:
            logger.info('Compressed image file size: %0.2f MB', file_size_bytes / 1024 / 1024)


        latest_file = None
        if write_latest:
            ### Always write the latest file for web access
            latest_file = self.image_dir.joinpath('latest.{0:s}'.format(self.config['IMAGE_FILE_TYPE']))

            try:
                latest_file.unlink()
            except FileNotFoundError:
                pass


            shutil.copy2(str(tmpfile_name), str(latest_file))
            latest_file.chmod(0o644)


        ### disable timelapse images in focus mode
        if self.config.get('FOCUS_MODE', False):
            logger.warning('Focus mode enabled, not saving timelapse image')
            if diag_enabled:
                self._images_only_diag(diag_profile_id, diag_camera_id, 'IMAGE_WRITE_IMG_SKIP_REASON', reason='focus_mode')
            #self.write_focus_fit(data)
            #self.write_focus_png(data)
            tmpfile_name.unlink()
            return None, None


        ### Do not write daytime image files if daytime capture is disabled
        if diag_enabled:
            self._images_only_diag(
                diag_profile_id,
                diag_camera_id,
                'IMAGE_DAYTIME_SAVE_CHECK',
                daytime_capture=self.config['DAYTIME_CAPTURE'],
                daytime_capture_save=self.config.get('DAYTIME_CAPTURE_SAVE', True),
                night=bool(self.night_av[constants.NIGHT_NIGHT]),
            )

        if not self.night_av[constants.NIGHT_NIGHT] and self.config['DAYTIME_CAPTURE'] and not self.config.get('DAYTIME_CAPTURE_SAVE', True):
            logger.info('Daytime image save is disabled')
            if diag_enabled:
                self._images_only_diag(diag_profile_id, diag_camera_id, 'IMAGE_WRITE_IMG_SKIP_REASON', reason='daytime_save_disabled')
            tmpfile_name.unlink()
            return latest_file, None


        ### Write the timelapse file
        folder = self._getImageFolder(i_ref.exp_date, i_ref.day_date, camera, 'exposures')

        date_str = i_ref.exp_date.strftime('%Y%m%d_%H%M%S')
        filename = folder.joinpath(self.filename_t.format(i_ref.camera_id, date_str, self.config['IMAGE_FILE_TYPE']))

        #logger.info('Image filename: %s', filename)

        if diag_enabled:
            self._images_only_diag(
                diag_profile_id,
                diag_camera_id,
                'IMAGE_DUPLICATE_CHECK',
                exists=filename.exists(),
                final_filename=str(filename),
            )

        if filename.exists():
            logger.error('File exists: %s (skipping)', filename)
            if diag_enabled:
                self._images_only_diag(diag_profile_id, diag_camera_id, 'IMAGE_WRITE_IMG_SKIP_REASON', reason='final_filename_exists', final_filename=str(filename))
            tmpfile_name.unlink()
            return latest_file, None


        shutil.copy2(str(tmpfile_name), str(filename))
        filename.chmod(0o644)

        tmpfile_name.unlink()


        # set mtime to original exposure time
        #os.utime(str(filename), (i_ref.exp_date.timestamp(), i_ref.exp_date.timestamp()))

        #logger.info('Finished writing files')

        return latest_file, filename


    def write_status_json(self, i_ref, adu, adu_average):
        status = {
            'name'                : 'indi_json',
            'class'               : 'ccd',
            'device'              : i_ref.camera_name,
            'night'               : self.night_av[constants.NIGHT_NIGHT],
            'temp'                : self.sensors_temp_av[constants.SENSOR_TEMP_CCD_TEMP],
            'gain'                : i_ref.gain,
            'exposure'            : i_ref.exposure,
            'stable_exposure'     : int(self.target_adu_found),
            'target_adu'          : i_ref.target_adu,
            'current_adu_target'  : self.current_adu_target,
            'current_adu'         : adu,
            'adu_average'         : adu_average,
            'sqm'                 : i_ref.sqm_value,
            'stars'               : len(i_ref.stars),
            'detections'          : len(i_ref.lines),
            'time'                : i_ref.exp_date.strftime('%s'),
            'latitude'            : self.position_av[constants.POSITION_LATITUDE],
            'longitude'           : self.position_av[constants.POSITION_LONGITUDE],
            'elevation'           : int(self.position_av[constants.POSITION_ELEVATION]),
            'kpindex'             : i_ref.kpindex,
            'ovation_max'         : int(i_ref.ovation_max),
            'aurora_mag_bt'       : i_ref.aurora_mag_bt,
            'aurora_mag_gsm_bz'   : i_ref.aurora_mag_gsm_bz,
            'aurora_plasma_density' : i_ref.aurora_plasma_density,
            'aurora_plasma_speed'   : i_ref.aurora_plasma_speed,
            'aurora_plasma_temp'    : i_ref.aurora_plasma_temp,
            'aurora_n_hemi_gw'    : i_ref.aurora_n_hemi_gw,
            'aurora_s_hemi_gw'    : i_ref.aurora_s_hemi_gw,
            'smoke_rating'        : constants.SMOKE_RATING_MAP_STR[i_ref.smoke_rating],
            'aircraft'            : len(self.adsb_aircraft_list),
            'camera_sqm_raw_mag'  : self.image_processor.camera_sqm_raw_mag,
        }


        # system temp sensors
        for i in range(60):
            v = self.sensors_temp_av[i]

            if self.config.get('TEMP_DISPLAY') == 'f':
                v_temp = (v * 9.0 / 5.0) + 32
            elif self.config.get('TEMP_DISPLAY') == 'k':
                v_temp = v + 273.15
            else:
                v_temp = v


            sensor_topic = 'sensor_temp_{0:d}'.format(i)
            status[sensor_topic] = v_temp


        # user sensors
        for i in range(60):
            sensor_topic = 'sensor_user_{0:d}'.format(i)
            status[sensor_topic] = self.sensors_user_av[i]

        for i in range(100, 110):
            sensor_topic = 'sensor_user_{0:d}'.format(i)
            status[sensor_topic] = self.sensors_user_av[i]


        indi_allsky_status_p = self.varlib_folder_p.joinpath('indi_allsky_status.json')

        with io.open(str(indi_allsky_status_p), 'w', encoding='utf-8') as f_indi_status:
            json.dump(
                status,
                f_indi_status,
                indent=4,
                ensure_ascii=False,
            )

        indi_allsky_status_p.chmod(0o644)


    def _getImageFolder(self, exp_date, day_date, camera, type_folder):
        if self.night_av[constants.NIGHT_NIGHT]:
            # images should be written to previous day's folder until noon
            timeofday_str = 'night'
        else:
            # images should be written to current day's folder
            timeofday_str = 'day'


        day_folder = self.image_dir.joinpath(
            'ccd_{0:s}'.format(camera.uuid),
            type_folder,
            '{0:s}'.format(day_date.strftime('%Y%m%d')),
            timeofday_str,
        )

        if not day_folder.exists():
            day_folder.mkdir(mode=0o755, parents=True)

        hour_str = exp_date.strftime('%d_%H')

        hour_folder = day_folder.joinpath('{0:s}'.format(hour_str))
        if not hour_folder.exists():
            hour_folder.mkdir(mode=0o755)

        return hour_folder


    def write_panorama_img(self, pano_data, i_ref, camera, jpeg_exif=None):
        panorama_height, panorama_width = pano_data.shape[:2]

        f_tmpfile = tempfile.NamedTemporaryFile(mode='w+b', delete=False, suffix='.{0}'.format(self.config['IMAGE_FILE_TYPE']))
        f_tmpfile.close()

        tmpfile_name = Path(f_tmpfile.name)


        #write_img_start = time.time()

        # write to temporary file
        if self.config['IMAGE_FILE_TYPE'] in ('jpg', 'jpeg'):
            img_rgb = Image.fromarray(cv2.cvtColor(pano_data, cv2.COLOR_BGR2RGB))
            img_rgb.save(str(tmpfile_name), quality=self.config['IMAGE_FILE_COMPRESSION']['jpg'], exif=jpeg_exif)
        elif self.config['IMAGE_FILE_TYPE'] in ('png',):
            # exif does not appear to work with png
            #img_rgb = Image.fromarray(cv2.cvtColor(data, cv2.COLOR_BGR2RGB))
            #img_rgb.save(str(tmpfile_name), compress_level=self.config['IMAGE_FILE_COMPRESSION']['png'])

            # opencv is faster than Pillow with PNG
            cv2.imwrite(str(tmpfile_name), pano_data, [cv2.IMWRITE_PNG_COMPRESSION, self.config['IMAGE_FILE_COMPRESSION']['png']])
        elif self.config['IMAGE_FILE_TYPE'] in ('webp',):
            img_rgb = Image.fromarray(cv2.cvtColor(pano_data, cv2.COLOR_BGR2RGB))
            img_rgb.save(str(tmpfile_name), quality=90, lossless=False, exif=jpeg_exif)
        elif self.config['IMAGE_FILE_TYPE'] in ('tif', 'tiff'):
            # exif does not appear to work with tiff
            img_rgb = Image.fromarray(cv2.cvtColor(pano_data, cv2.COLOR_BGR2RGB))
            img_rgb.save(str(tmpfile_name), compression='tiff_lzw')
        else:
            tmpfile_name.unlink()
            raise Exception('Unknown file type: %s', self.config['IMAGE_FILE_TYPE'])

        #write_img_elapsed_s = time.time() - write_img_start
        #logger.info('Panorama image compressed in %0.4f s', write_img_elapsed_s)


        ### Always write the latest file for web access
        latest_pano_file = self.image_dir.joinpath('panorama.{0:s}'.format(self.config['IMAGE_FILE_TYPE']))

        try:
            latest_pano_file.unlink()
        except FileNotFoundError:
            pass


        shutil.copy2(str(tmpfile_name), str(latest_pano_file))
        latest_pano_file.chmod(0o644)


        ### disable timelapse images in focus mode
        if self.config.get('FOCUS_MODE', False):
            logger.warning('Focus mode enabled, not saving timelapse image')
            tmpfile_name.unlink()
            return


        ### Do not write daytime image files if daytime capture is disabled
        if not self.night_av[constants.NIGHT_NIGHT] and self.config['DAYTIME_CAPTURE'] and not self.config.get('DAYTIME_CAPTURE_SAVE', True):
            tmpfile_name.unlink()
            return


        ### Write the panorama file
        folder = self._getImageFolder(i_ref.exp_date, i_ref.day_date, camera, 'panoramas')


        panorama_filename_t = 'panorama_{0:s}'.format(self.filename_t)
        date_str = i_ref.exp_date.strftime('%Y%m%d_%H%M%S')
        filename = folder.joinpath(panorama_filename_t.format(i_ref.camera_id, date_str, self.config['IMAGE_FILE_TYPE']))

        #logger.info('Panorama filename: %s', filename)


        panorama_metadata = {
            'type'       : constants.PANORAMA_IMAGE,
            'createDate' : int(i_ref.exp_date.timestamp()),
            'dayDate'    : i_ref.day_date.strftime('%Y%m%d'),
            'utc_offset' : i_ref.exp_date.astimezone().utcoffset().total_seconds(),
            'exposure'   : i_ref.exposure,
            'gain'       : i_ref.gain,
            'binmode'    : i_ref.binning,
            'night'      : bool(self.night_av[constants.NIGHT_NIGHT]),
            'fileSize'   : latest_pano_file.stat().st_size,
            'height'     : panorama_height,
            'width'      : panorama_width,
            'camera_uuid': i_ref.camera_uuid,
        }

        panorama_metadata['data'] = {
            'moonmode'        : bool(self.night_av[constants.NIGHT_MOONMODE]),
            'moonphase'       : self.image_processor.astrometric_data['moon_phase'],
            'sqm'             : i_ref.sqm_value,
            'stars'           : len(i_ref.stars),
            'detections'      : len(i_ref.lines),
            'kpindex'         : i_ref.kpindex,
            'ovation_max'     : i_ref.ovation_max,
            'smoke_rating'    : i_ref.smoke_rating,
            'aurora_mag_bt'     : i_ref.aurora_mag_bt,
            'aurora_mag_gsm_bz' : i_ref.aurora_mag_gsm_bz,
            'aurora_plasma_density' : i_ref.aurora_plasma_density,
            'aurora_plasma_speed'   : i_ref.aurora_plasma_speed,
            'aurora_plasma_temp'    : i_ref.aurora_plasma_temp,
            'aurora_n_hemi_gw'      : i_ref.aurora_n_hemi_gw,
            'aurora_s_hemi_gw'      : i_ref.aurora_s_hemi_gw,
            'camera_sqm_raw_mag'    : self.image_processor.camera_sqm_raw_mag,
        }


        panorama_entry = self._miscDb.addPanoramaImage(
            filename.relative_to(self.image_dir),
            i_ref.camera_id,
            panorama_metadata,
        )


        if filename.exists():
            logger.error('File exists: %s (skipping)', filename)
            tmpfile_name.unlink()
            return


        shutil.copy2(str(tmpfile_name), str(filename))
        filename.chmod(0o644)

        tmpfile_name.unlink()


        # set mtime to original exposure time
        #os.utime(str(filename), (i_ref.exp_date.timestamp(), i_ref.exp_date.timestamp()))

        self._miscUpload.syncapi_panorama(panorama_entry, panorama_metadata)  # syncapi before s3
        self._miscUpload.s3_upload_panorama(panorama_entry, panorama_metadata)
        self._miscUpload.mqtt_publish_image(filename, 'panorama', {})
        self._miscUpload.upload_panorama(panorama_entry)


    def write_circular_display_img(self, circular_image_data, jpeg_exif=None):
        height, width = circular_image_data.shape[:2]

        f_tmpfile = tempfile.NamedTemporaryFile(mode='w+b', delete=False, suffix='.{0}'.format(self.config['IMAGE_FILE_TYPE']))
        f_tmpfile.close()

        tmpfile_name = Path(f_tmpfile.name)


        #write_img_start = time.time()

        # write to temporary file
        if self.config['IMAGE_FILE_TYPE'] in ('jpg', 'jpeg'):
            img_rgb = Image.fromarray(cv2.cvtColor(circular_image_data, cv2.COLOR_BGR2RGB))
            img_rgb.save(str(tmpfile_name), quality=self.config['IMAGE_FILE_COMPRESSION']['jpg'], exif=jpeg_exif)
        elif self.config['IMAGE_FILE_TYPE'] in ('png',):
            # exif does not appear to work with png
            #img_rgb = Image.fromarray(cv2.cvtColor(data, cv2.COLOR_BGR2RGB))
            #img_rgb.save(str(tmpfile_name), compress_level=self.config['IMAGE_FILE_COMPRESSION']['png'])

            # opencv is faster than Pillow with PNG
            cv2.imwrite(str(tmpfile_name), circular_image_data, [cv2.IMWRITE_PNG_COMPRESSION, self.config['IMAGE_FILE_COMPRESSION']['png']])
        elif self.config['IMAGE_FILE_TYPE'] in ('webp',):
            img_rgb = Image.fromarray(cv2.cvtColor(circular_image_data, cv2.COLOR_BGR2RGB))
            img_rgb.save(str(tmpfile_name), quality=90, lossless=False, exif=jpeg_exif)
        elif self.config['IMAGE_FILE_TYPE'] in ('tif', 'tiff'):
            # exif does not appear to work with tiff
            img_rgb = Image.fromarray(cv2.cvtColor(circular_image_data, cv2.COLOR_BGR2RGB))
            img_rgb.save(str(tmpfile_name), compression='tiff_lzw')
        else:
            tmpfile_name.unlink()
            raise Exception('Unknown file type: %s', self.config['IMAGE_FILE_TYPE'])

        #write_img_elapsed_s = time.time() - write_img_start
        #logger.info('Panorama image compressed in %0.4f s', write_img_elapsed_s)


        ### Always write the latest file for web access
        latest_circular_image_file = self.image_dir.joinpath('circular_display.{0:s}'.format(self.config['IMAGE_FILE_TYPE']))

        try:
            latest_circular_image_file.unlink()
        except FileNotFoundError:
            pass


        shutil.copy2(str(tmpfile_name), str(latest_circular_image_file))
        latest_circular_image_file.chmod(0o644)

        # cleanup
        tmpfile_name.unlink()


    def write_realtime_keogram(self, data, camera):
        if isinstance(data, type(None)):
            logger.warning('Realtime keogram data empty')
            return


        save_interval = self.config.get('REALTIME_KEOGRAM', {}).get('SAVE_INTERVAL', 25)
        if self.image_count % save_interval == 0:
            # store keogram data every X images
            self.image_processor.realtimeKeogramDataSave()


        keogram_height, keogram_width = data.shape[:2]

        # scale size
        h_scale_factor = int(self.config.get('KEOGRAM_H_SCALE', 100))
        v_scale_factor = int(self.config.get('KEOGRAM_V_SCALE', 33))
        new_width = int(keogram_width * h_scale_factor / 100)
        new_height = int(keogram_height * v_scale_factor / 100)

        #logger.info('Keogram: %d x %d', new_width, new_height)
        data = cv2.resize(data, (new_width, new_height), interpolation=cv2.INTER_AREA)

        data = self.image_processor.realtimeKeogramApplyLabels(data)

        f_tmpfile = tempfile.NamedTemporaryFile(mode='w+b', delete=False, suffix='.{0}'.format(self.config['IMAGE_FILE_TYPE']))
        f_tmpfile.close()

        tmpfile_name = Path(f_tmpfile.name)


        #write_img_start = time.time()

        # write to temporary file
        if self.config['IMAGE_FILE_TYPE'] in ('jpg', 'jpeg'):
            #img_rgb = Image.fromarray(cv2.cvtColor(data, cv2.COLOR_BGR2RGB))
            #img_rgb.save(str(tmpfile_name), quality=self.config['IMAGE_FILE_COMPRESSION']['jpg'])

            # opencv is faster
            cv2.imwrite(str(tmpfile_name), data, [cv2.IMWRITE_JPEG_QUALITY, self.config['IMAGE_FILE_COMPRESSION']['jpg']])
        elif self.config['IMAGE_FILE_TYPE'] in ('png',):
            # opencv is faster than Pillow with PNG
            cv2.imwrite(str(tmpfile_name), data, [cv2.IMWRITE_PNG_COMPRESSION, self.config['IMAGE_FILE_COMPRESSION']['png']])
        elif self.config['IMAGE_FILE_TYPE'] in ('webp',):
            img_rgb = Image.fromarray(cv2.cvtColor(data, cv2.COLOR_BGR2RGB))
            img_rgb.save(str(tmpfile_name), quality=90, lossless=False)
        elif self.config['IMAGE_FILE_TYPE'] in ('tif', 'tiff'):
            # exif does not appear to work with tiff
            img_rgb = Image.fromarray(cv2.cvtColor(data, cv2.COLOR_BGR2RGB))
            img_rgb.save(str(tmpfile_name), compression='tiff_lzw')
        else:
            tmpfile_name.unlink()
            raise Exception('Unknown file type: %s', self.config['IMAGE_FILE_TYPE'])

        #write_img_elapsed_s = time.time() - write_img_start
        #logger.info('Image compressed in %0.4f s', write_img_elapsed_s)


        ccd_folder = self.image_dir.joinpath('ccd_{0:s}'.format(camera.uuid))

        if not ccd_folder.exists():
            ccd_folder.mkdir(mode=0o755, parents=True)


        ### Always write the latest file for web access
        keogram_file = ccd_folder.joinpath('realtime_keogram.{0:s}'.format(self.config['IMAGE_FILE_TYPE']))

        try:
            keogram_file.unlink()
        except FileNotFoundError:
            pass


        shutil.copy2(str(tmpfile_name), str(keogram_file))
        keogram_file.chmod(0o644)

        tmpfile_name.unlink()

        self._miscUpload.upload_realtime_keogram(keogram_file, camera)


    def _log_adu_diag(self, adu, target_adu, adu_average=0.0):
        if not self.config.get('MULTI_CAMERA_CAPTURE_ENABLE', False):
            return

        _multi_camera_diag(
            '[MULTI_CAMERA_ADU][%s][camera_id=%s] key=%s adu=%s adu_average=%s target=%s current_target=%s stable=%s exposure_next=%s gain_next=%s hist_len=%d',
            self.profile_id,
            self.current_camera_id,
            self.adu_context_key,
            '{0:0.2f}'.format(float(adu)),
            '{0:0.2f}'.format(float(adu_average)),
            target_adu,
            self.current_adu_target,
            self.target_adu_found,
            '{0:0.8f}'.format(float(self.exposure_av[constants.EXPOSURE_NEXT])),
            '{0:0.2f}'.format(float(self.gain_av[constants.GAIN_NEXT])),
            len(self.hist_adu),
        )


    def calculate_exposure(self, adu, exposure, gain):
        if adu <= 0.0:
            # ensure we do not divide by zero
            logger.warning('Zero average, setting a default of 0.1')
            adu = 0.1


        if self.night_av[constants.NIGHT_NIGHT] == 1:
            target_adu = self.config['TARGET_ADU']
        else:
            target_adu = self.config['TARGET_ADU_DAY']


        # Brightness when the sun is in view (very short exposures) can change drastically when clouds pass through the view
        # Setting a deviation that is too short can cause exposure flapping
        if exposure < 0.001000:
            # DAY
            adu_dev = float(self.config.get('TARGET_ADU_DEV_DAY', 20))

            target_adu_min = target_adu - adu_dev
            target_adu_max = target_adu + adu_dev
            current_adu_target_min = self.current_adu_target - adu_dev
            current_adu_target_max = self.current_adu_target + adu_dev

            exp_scale_factor = 0.50  # scale exposure calculation
            history_max_vals = 6     # number of entries to use to calculate average
        else:
            # NIGHT
            adu_dev = float(self.config.get('TARGET_ADU_DEV', 10))

            target_adu_min = target_adu - adu_dev
            target_adu_max = target_adu + adu_dev
            current_adu_target_min = self.current_adu_target - adu_dev
            current_adu_target_max = self.current_adu_target + adu_dev

            exp_scale_factor = 1.0  # scale exposure calculation
            history_max_vals = 6    # number of entries to use to calculate average



        if not self.target_adu_found:
            self.recalculate_exposure(exposure, gain, adu, target_adu, target_adu_min, target_adu_max, exp_scale_factor)
            self._log_adu_diag(adu, target_adu)
            return adu, 0.0


        self.hist_adu.append(adu)
        self.hist_adu = self.hist_adu[(history_max_vals * -1):]  # remove oldest values, up to history_max_vals

        adu_average = functools.reduce(lambda a, b: a + b, self.hist_adu) / len(self.hist_adu)

        #logger.info('ADU average: %0.2f', adu_average)
        #logger.info('Current target ADU: %0.2f (%0.2f/%0.2f)', self.current_adu_target, current_adu_target_min, current_adu_target_max)
        #logger.info('Current ADU history: (%d) [%s]', len(self.hist_adu), ', '.join(['{0:0.2f}'.format(x) for x in self.hist_adu]))


        ### Need at least x values to continue
        if len(self.hist_adu) < history_max_vals:
            self._log_adu_diag(adu, target_adu, adu_average)
            return adu, 0.0


        ### only change exposure when 70% of the values exceed the max or minimum
        if adu_average > current_adu_target_max:
            logger.warning('ADU increasing beyond limits, recalculating next exposure')
            self.target_adu_found = False
        elif adu_average < current_adu_target_min:
            logger.warning('ADU decreasing beyond limits, recalculating next exposure')
            self.target_adu_found = False

        self._log_adu_diag(adu, target_adu, adu_average)

        return adu, adu_average


    def recalculate_exposure(self, exposure, gain, adu, target_adu, target_adu_min, target_adu_max, exp_scale_factor):
        # There might be a race condition here if there is a day/night change but self.target_adu_found == True

        # Until we reach a good starting point, do not calculate a moving average
        if adu <= target_adu_max and adu >= target_adu_min:
            logger.warning('Found target value for exposure')
            self.current_adu_target = copy.copy(adu)
            self.target_adu_found = True
            self.hist_adu = []
            return


        if self._auto_gain_enabled():
            # moonmode settings are ignored with auto-gain

            if self.night_av[constants.NIGHT_NIGHT] == 1:
                exposure_min = float(self.exposure_av[constants.EXPOSURE_MIN_NIGHT])
            else:
                exposure_min = float(self.exposure_av[constants.EXPOSURE_MIN_DAY])

            gain_min, gain_max = self._auto_gain_limits()
        else:
            if self.night_av[constants.NIGHT_NIGHT] == 1:
                exposure_min = float(self.exposure_av[constants.EXPOSURE_MIN_NIGHT])

                if self.night_av[constants.NIGHT_MOONMODE] == 1:
                    gain_min = float(self.gain_av[constants.GAIN_MIN_MOONMODE])
                    gain_max = float(self.gain_av[constants.GAIN_MAX_MOONMODE])
                else:
                    gain_min = float(self.gain_av[constants.GAIN_MIN_NIGHT])
                    gain_max = float(self.gain_av[constants.GAIN_MAX_NIGHT])

            else:
                exposure_min = float(self.exposure_av[constants.EXPOSURE_MIN_DAY])

                gain_min = float(self.gain_av[constants.GAIN_MIN_DAY])
                gain_max = float(self.gain_av[constants.GAIN_MAX_DAY])


        # Scale the exposure up and down based on targets
        if adu > target_adu_max:
            next_exposure = exposure - ((exposure - (exposure * (target_adu / adu))) * exp_scale_factor)
        elif adu < target_adu_min:
            next_exposure = exposure - ((exposure - (exposure * (target_adu / adu))) * exp_scale_factor)
        else:
            next_exposure = exposure


        # Do not exceed the exposure limits
        if next_exposure < exposure_min:
            next_exposure = float(exposure_min)
        elif next_exposure > self.exposure_av[constants.EXPOSURE_MAX]:
            next_exposure = float(self.exposure_av[constants.EXPOSURE_MAX])


        if self._auto_gain_enabled():
            try:
                auto_gain_idx = self.auto_gain_step_list.index(gain)
            except ValueError:
                # fallback to min if gain does not match
                logger.error('Current gain not found in list, reset to minimum gain')
                auto_gain_idx = 0


            if next_exposure == exposure:
                # no change
                #logger.warning('Auto-Gain - no changes')
                next_gain = gain
                exposure_delta = 0.0
                gain_delta = 0.0
            elif next_exposure > exposure:
                # exposure/gain needs to increase
                if gain == self.auto_gain_step_list[-1]:
                    # already at max gain, increase exposure
                    next_gain = gain
                    exposure_delta = next_exposure - exposure
                    gain_delta = 0.0
                    logger.info('Auto-Gain increasing exposure to %0.6f (%+0.8f) [max gain]', next_exposure, exposure_delta)
                else:
                    if exposure < self.auto_gain_exposure_cutoff_high:
                        # maintain gain, increase exposure
                        next_gain = gain
                        next_exposure = min(next_exposure, self.auto_gain_exposure_cutoff_high)  # prevent hitting max exposure
                        exposure_delta = next_exposure - exposure
                        gain_delta = 0.0
                        logger.info('Auto-Gain increasing exposure to %0.6f (%+0.8f) [maintain gain]', next_exposure, exposure_delta)
                    else:
                        # increase gain, maintain exposure
                        next_gain = self.auto_gain_step_list[auto_gain_idx + 1]
                        next_exposure = min(exposure, self.auto_gain_exposure_cutoff_high)  # prevent hitting max exposure
                        exposure_delta = 0.0
                        gain_delta = next_gain - gain
                        logger.info('Auto-Gain increasing gain to %0.2f (%+0.2f) [maintain exposure]', next_gain, gain_delta)

            else:
                # exposure/gain needs to decrease
                if gain == self.auto_gain_step_list[0]:
                    # already at minimum gain, decrease exposure
                    next_gain = gain
                    exposure_delta = next_exposure - exposure
                    gain_delta = 0.0
                    logger.info('Auto-Gain decreasing exposure to %0.6f (%+0.8f) [minimum gain]', next_exposure, exposure_delta)
                else:
                    if exposure > self.auto_gain_exposure_cutoff_low:
                        # maintain gain, decrease exposure
                        next_gain = gain
                        next_exposure = max(next_exposure, self.auto_gain_exposure_cutoff_low)
                        exposure_delta = next_exposure - exposure
                        gain_delta = 0.0
                        logger.info('Auto-Gain decreasing exposure to %0.6f (%+0.8f) [maintain gain]', next_exposure, exposure_delta)
                    else:
                        # decrease gain, maintain exposure
                        next_gain = self.auto_gain_step_list[auto_gain_idx - 1]
                        #next_exposure = max(exposure, self.auto_gain_exposure_cutoff_low)
                        next_exposure = max(exposure, self.auto_gain_exposure_cutoff_mid)
                        exposure_delta = 0.0
                        gain_delta = next_gain - gain
                        logger.info('Auto-Gain decreasing gain to %0.2f (%+0.2f) [maintain exposure)', next_gain, gain_delta)

        else:
            # just set the gain to the max for the current mode
            next_gain = gain_max
            exposure_delta = next_exposure - exposure
            gain_delta = 0.0


        # Do not exceed the gain limits
        if next_gain > gain_max:
            next_gain = gain_max
        elif next_gain < gain_min:
            next_gain = gain_min


        # Binning
        if self.night_av[constants.NIGHT_NIGHT] == 1:
            if self.night_av[constants.NIGHT_MOONMODE] == 1:
                next_binning = self.binning_av[constants.BINNING_MOONMODE]
            else:
                next_binning = self.binning_av[constants.BINNING_NIGHT]
        else:
            next_binning = self.binning_av[constants.BINNING_DAY]


        ### Check for exposure flapping
        # Flapping is defined when the exposure increases then immediately decreases (or the opposite)
        # and cannot find a stable value.  The result is the image brightness will flash
        if self.exposure_av[constants.EXPOSURE_DELTA] > 0 and exposure_delta < 0:
            # exposure is decreasing
            exposure_offset = exposure_delta / 2
            next_exposure -= exposure_offset  # offset will be negative
            exposure_delta -= exposure_offset

            logger.warning('DETECTED EXPOSURE FLAPPING - Attempting to mitigate by adjusting exposure by %+0.8fs', exposure_offset * -1)
        elif self.exposure_av[constants.EXPOSURE_DELTA] < 0 and exposure_delta > 0:
            # exposure is increasing
            exposure_offset = exposure_delta / 2
            next_exposure -= exposure_offset
            exposure_delta -= exposure_offset

            logger.warning('DETECTED EXPOSURE FLAPPING - Attempting to mitigate by adjusting exposure by %+0.8fs', exposure_offset * -1)


        logger.warning('New calculated exposure: %0.6fs (%+0.8f) @ gain %0.2f (%+0.2f) bin %d', next_exposure, exposure_delta, next_gain, gain_delta, next_binning)
        old_gain_next = float(self.gain_av[constants.GAIN_NEXT])
        with self.exposure_av.get_lock():
            self.exposure_av[constants.EXPOSURE_NEXT] = float(next_exposure)
            self.exposure_av[constants.EXPOSURE_DELTA] = float(exposure_delta)

        with self.gain_av.get_lock():
            self.gain_av[constants.GAIN_NEXT] = float(next_gain)
            self.gain_av[constants.GAIN_DELTA] = float(gain_delta)

        if float(next_gain) != old_gain_next:
            self._save_auto_gain_runtime_state(
                self.profile_id,
                self.camera_id,
                self._auto_gain_mode(),
                next_gain,
                gain_min,
                gain_max,
                'runtime_next_changed',
            )

        with self.binning_av.get_lock():
            self.binning_av[constants.BINNING_NEXT] = int(next_binning)


    def save_longterm_keogram_data(self, exp_date, camera_id):
        if self.image_processor.focus_mode:
            # disable processing in focus mode
            return

        if not self.config.get('LONGTERM_KEOGRAM', {}).get('ENABLE', True):
            logger.info('Long term keogram data disabled')
            return

        offset_x = self.config.get('LONGTERM_KEOGRAM', {}).get('OFFSET_X', 0)
        offset_y = self.config.get('LONGTERM_KEOGRAM', {}).get('OFFSET_Y', 0)

        image_height, image_width = self.image_processor.image.shape[:2]


        x = int(image_width / 2) + offset_x
        y = int(image_height / 2) - offset_y  # minus


        rgb_pixel_list = list()
        for p_y in range(5):
            pixel = self.image_processor.image[y + p_y, x]
            rgb_pixel_list.append([int(pixel[2]), int(pixel[1]), int(pixel[0])])  # bgr


        self._miscDb.add_long_term_keogram_data(
            exp_date,
            camera_id,
            rgb_pixel_list,
        )


        return rgb_pixel_list


    def start_image_save_pre_hook(self, exposure, gain, binning):
        if self.image_processor.focus_mode:
            return

        if not self.config.get('IMAGE_SAVE_HOOK_PRE'):
            return


        pre_save_hook_p = Path(self.config.get('IMAGE_SAVE_HOOK_PRE'))
        logger.info('Running image pre-save hook: %s', pre_save_hook_p)

        if not pre_save_hook_p.is_file():
            logger.error('Image pre-save script is not a file')
            return

        if pre_save_hook_p.stat().st_size == 0:
            logger.error('Image pre-save script is empty')
            return

        if not os.access(str(pre_save_hook_p), os.R_OK | os.X_OK):
            logger.error('Image pre-save script is not readable or executable')
            return


        # generate a tempfile for the data
        f_tmp_datajson = tempfile.NamedTemporaryFile(mode='w', delete=True, suffix='.json')
        f_tmp_datajson.close()

        self.pre_hook_datajson_name_p = Path(f_tmp_datajson.name)


        # Communicate sensor values as environment variables
        cmd_env = {
            'DATA_JSON': str(self.pre_hook_datajson_name_p),  # the file used for the json data is communicated via environment variable
            'EXPOSURE' : '{0:0.6f}'.format(exposure),
            'GAIN'     : '{0:0.2f}'.format(gain),
            'BIN'      : '{0:d}'.format(binning),
            'SUNALT'   : '{0:0.1f}'.format(self.image_processor.astrometric_data['sun_alt']),
            'MOONALT'  : '{0:0.1f}'.format(self.image_processor.astrometric_data['moon_alt']),
            'MOONPHASE': '{0:0.1f}'.format(self.image_processor.astrometric_data['moon_phase']),
            'MOONMODE' : '{0:d}'.format(int(bool(self.night_av[constants.NIGHT_MOONMODE]))),
            'NIGHT'    : '{0:d}'.format(int(self.night_av[constants.NIGHT_NIGHT])),
            'LATITUDE' : '{0:0.3f}'.format(self.position_av[constants.POSITION_LATITUDE]),
            'LONGITUDE': '{0:0.3f}'.format(self.position_av[constants.POSITION_LONGITUDE]),
            'ELEVATION': '{0:d}'.format(int(self.position_av[constants.POSITION_ELEVATION])),
        }


        # system temp sensors
        for i in range(60):
            v = self.sensors_temp_av[i]

            if self.config.get('TEMP_DISPLAY') == 'f':
                v_temp = (v * 9.0 / 5.0) + 32
            elif self.config.get('TEMP_DISPLAY') == 'k':
                v_temp = v + 273.15
            else:
                v_temp = v


            sensor_env_var = 'SENSOR_TEMP_{0:d}'.format(i)
            cmd_env[sensor_env_var] = '{0:0.3f}'.format(v_temp)


        # user sensors
        for i in range(60):
            sensor_env_var = 'SENSOR_USER_{0:d}'.format(i)
            cmd_env[sensor_env_var] = '{0:0.3f}'.format(self.sensors_user_av[i])

        for i in range(100, 110):
            sensor_env_var = 'SENSOR_USER_{0:d}'.format(i)
            cmd_env[sensor_env_var] = '{0:0.3f}'.format(self.sensors_user_av[i])


        cmd = [
            str(pre_save_hook_p),
        ]


        try:
            self.image_save_hook_process = subprocess.Popen(
                cmd,
                env=cmd_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )

            self.image_save_hook_process_start = time.time()
        except OSError:
            self.image_save_hook_process = None
            logger.error('Image pre-save script failed to execute')


    def start_image_save_post_hook(self, image_p, exposure, gain, binning):
        if self.image_processor.focus_mode:
            return

        if not self.config.get('IMAGE_SAVE_HOOK_POST'):
            return


        post_save_hook_p = Path(self.config.get('IMAGE_SAVE_HOOK_POST'))
        logger.info('Running image post-save hook: %s', post_save_hook_p)

        if not post_save_hook_p.is_file():
            logger.error('Image post-save script is not a file')
            return

        if post_save_hook_p.stat().st_size == 0:
            logger.error('Image post-save script is empty')
            return

        if not os.access(str(post_save_hook_p), os.R_OK | os.X_OK):
            logger.error('Image post-save script is not readable or executable')
            return


        # Communicate sensor values as environment variables
        hook_env = {
            'EXPOSURE' : '{0:0.6f}'.format(exposure),
            'GAIN'     : '{0:0.3f}'.format(gain),
            'BIN'      : '{0:d}'.format(binning),
            'SUNALT'   : '{0:0.1f}'.format(self.image_processor.astrometric_data['sun_alt']),
            'MOONALT'  : '{0:0.1f}'.format(self.image_processor.astrometric_data['moon_alt']),
            'MOONPHASE': '{0:0.1f}'.format(self.image_processor.astrometric_data['moon_phase']),
            'MOONMODE' : '{0:d}'.format(int(bool(self.night_av[constants.NIGHT_MOONMODE]))),
            'NIGHT'    : '{0:d}'.format(int(self.night_av[constants.NIGHT_NIGHT])),
            'LATITUDE' : '{0:0.3f}'.format(self.position_av[constants.POSITION_LATITUDE]),
            'LONGITUDE': '{0:0.3f}'.format(self.position_av[constants.POSITION_LONGITUDE]),
            'ELEVATION': '{0:d}'.format(int(self.position_av[constants.POSITION_ELEVATION])),
        }


        # system temp sensors
        for i in range(60):
            v = self.sensors_temp_av[i]

            if self.config.get('TEMP_DISPLAY') == 'f':
                v_temp = (v * 9.0 / 5.0) + 32
            elif self.config.get('TEMP_DISPLAY') == 'k':
                v_temp = v + 273.15
            else:
                v_temp = v


            sensor_env_var = 'SENSOR_TEMP_{0:d}'.format(i)
            hook_env[sensor_env_var] = '{0:0.3f}'.format(v_temp)


        # user sensors
        for i in range(60):
            sensor_env_var = 'SENSOR_USER_{0:d}'.format(i)
            hook_env[sensor_env_var] = '{0:0.3f}'.format(self.sensors_user_av[i])

        for i in range(100, 110):
            sensor_env_var = 'SENSOR_USER_{0:d}'.format(i)
            hook_env[sensor_env_var] = '{0:0.3f}'.format(self.sensors_user_av[i])


        cmd = [
            str(post_save_hook_p),
            str(image_p),
        ]


        try:
            self.image_save_hook_process = subprocess.Popen(
                cmd,
                env=hook_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )

            self.image_save_hook_process_start = time.time()
        except OSError:
            self.image_save_hook_process = None
            logger.error('Image post-save script failed to execute')


    def wait_image_save_pre_hook(self):
        if isinstance(self.image_save_hook_process, type(None)):
            return {}


        save_hook_timeout = self.config.get('IMAGE_SAVE_HOOK_TIMEOUT', 5)

        while self._processRunning(self.image_save_hook_process):
            now_time = time.time()
            if now_time - self.image_save_hook_process_start < save_hook_timeout:
                time.sleep(0.1)
                continue


            logger.error('Image pre-save script exceeded runtime')

            for _ in range(5):
                if not self._processRunning(self.image_save_hook_process):
                    break

                self.image_save_hook_process.terminate()
                time.sleep(0.25)
                continue


            if self._processRunning(self.image_save_hook_process):
                logger.error('Killing image pre-save script')
                self.image_save_hook_process.kill()
                self.image_save_hook_process.poll()  # close out process


            try:
                self.pre_hook_datajson_name_p.unlink()
            except FileNotFoundError:
                pass
            except PermissionError as e:
                logger.error('Unable to delete temp file: %s', str(e))


            return {}


        stdout, stderr = self.image_save_hook_process.communicate()
        hook_rc = self.image_save_hook_process.returncode

        if hook_rc == 0:
            try:
                with io.open(str(self.pre_hook_datajson_name_p), 'r', encoding='utf-8') as datajson_name_f:
                    hook_data = json.load(datajson_name_f)

                self.pre_hook_datajson_name_p.unlink()
            except json.JSONDecodeError as e:
                logger.error('Error decoding json: %s', str(e))
                self.pre_hook_datajson_name_p.unlink()
                hook_data = dict()
            except PermissionError as e:
                # cannot delete file
                logger.error(str(e))
                hook_data = dict()
            except FileNotFoundError as e:
                logger.error(str(e))
                hook_data = dict()
        else:
            logger.error('Image pre-save hook failed rc: %d', hook_rc)

            for line in stdout.decode().split('\n'):
                logger.error('Hook: %s', line)

            hook_data = dict()


            try:
                self.pre_hook_datajson_name_p.unlink()
            except FileNotFoundError:
                pass
            except PermissionError:
                pass


        self.image_save_hook_process = None


        # fetch these custom vars for image labels
        # all values should be str
        custom_hook_data = {
            'custom_1'  : hook_data.get('custom_1', ''),
            'custom_2'  : hook_data.get('custom_2', ''),
            'custom_3'  : hook_data.get('custom_3', ''),
            'custom_4'  : hook_data.get('custom_4', ''),
            'custom_5'  : hook_data.get('custom_5', ''),
            'custom_6'  : hook_data.get('custom_6', ''),
            'custom_7'  : hook_data.get('custom_7', ''),
            'custom_8'  : hook_data.get('custom_8', ''),
            'custom_9'  : hook_data.get('custom_9', ''),
        }


        return custom_hook_data


    def wait_image_save_post_hook(self):
        if isinstance(self.image_save_hook_process, type(None)):
            return


        save_hook_timeout = self.config.get('IMAGE_SAVE_HOOK_TIMEOUT', 5)

        while self._processRunning(self.image_save_hook_process):
            now_time = time.time()
            if now_time - self.image_save_hook_process_start < save_hook_timeout:
                time.sleep(0.1)
                continue


            logger.error('Image post-save script exceeded runtime')

            for _ in range(5):
                if not self._processRunning(self.image_save_hook_process):
                    break

                self.image_save_hook_process.terminate()
                time.sleep(0.25)
                continue


            if self._processRunning(self.image_save_hook_process):
                logger.error('Killing image post-save script')
                self.image_save_hook_process.kill()
                self.image_save_hook_process.poll()  # close out process

            return


        stdout, stderr = self.image_save_hook_process.communicate()
        hook_rc = self.image_save_hook_process.returncode

        if hook_rc != 0:
            logger.error('Image post-save hook failed rc: %d', hook_rc)

            for line in stdout.decode().split('\n'):
                logger.error('Hook: %s', line)


        self.image_save_hook_process = None


    def _processRunning(self, process):
        if not process:
            return False

        # poll returns None when process is active, rc (normally 0) when finished
        poll = process.poll()
        if isinstance(poll, type(None)):
            return True

        return False


    def process_sqm_exposure(self, filename_p, exposure, gain, binning, exp_date, exp_elapsed, camera, libcamera_black_level):
        logger.warning('Processing SQM exposure')

        try:
            i_ref = self.image_processor._add(
                filename_p,
                exposure,
                gain,
                binning,
                exp_date,
                exp_elapsed,
                camera,
            )
        except BadImage as e:
            logger.error('Bad Image: %s', str(e))
            filename_p.unlink()
            #task.setFailed('Bad Image: {0:s}'.format(str(filename_p)))
            return


        filename_p.unlink()


        # use original value if not defined
        if i_ref.libcamera_black_level:
            libcamera_black_level = i_ref.libcamera_black_level


        self.image_processor._calibrate(i_ref, libcamera_black_level=libcamera_black_level)


        mag_sqm, raw_mag, raw_adu = self.image_processor._calculateMagnitudeSqm(i_ref)


        logger.warning('Camera SQM Magnitude: %0.2f, Raw Magnitude: %0.2f, ADU: %0.2f', mag_sqm, raw_mag, raw_adu)
        with self.sensors_user_av.get_lock():
            self.sensors_user_av[constants.SENSOR_USER_CAMERA_SQM_MAG] = float(mag_sqm)
            self.sensors_user_av[constants.SENSOR_USER_CAMERA_SQM_ADU] = float(raw_adu)
