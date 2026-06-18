import io
import shutil
from datetime import datetime
from collections import OrderedDict
import time
import tempfile
import json
import subprocess
import psutil
from pathlib import Path
import logging

from .indi import IndiClient
from .fake_indi import FakeIndiCcd

from .. import constants
from ..multicamera_diag import write_multicamera_diag

from ..exceptions import TimeOutException
from ..exceptions import BinModeException


logger = logging.getLogger('indi_allsky')


def _multi_camera_diag(message, *args):
    write_multicamera_diag(message, *args)



class IndiClientLibCameraGeneric(IndiClient):

    libcamera_exec = 'rpicam-still'
    libcamera_awb_modes = {
        'auto',
        'fixed',
        'daylight',
        'cloudy',
        'tungsten',
        'fluorescent',
        'indoor',
    }

    _sensor_temp_metadata_key = 'SensorTemperature'
    _analogue_gain_metadata_key = 'AnalogueGain'
    _digital_gain_metadata_key = 'DigitalGain'
    _ccm_metadata_key = 'ColourCorrectionMatrix'
    _awb_gains_metadata_key = 'ColourGains'
    _black_level_metadata_key = 'SensorBlackLevels'


    def __init__(self, *args, **kwargs):
        super(IndiClientLibCameraGeneric, self).__init__(*args, **kwargs)

        self.libcamera_process = None
        self.libcamera_output_f = None

        self._ccm = None

        self._awb_gains = None

        self._black_level = 0

        self.active_exposure = False
        self.current_exposure_file_p = None
        self.current_metadata_file_p = None
        self.exposureStartTime = 0.0
        self.processStartTime = 0.0
        self.exposureStartMonotonic = 0.0
        self.processStartMonotonic = 0.0
        self.libcamera_timeout = 0.0
        self._hybrid_awb_capture_control = None

        memory_info = psutil.virtual_memory()
        self.memory_total_mb = memory_info[0] / 1024.0 / 1024.0


        self.ccd_device_name = 'CHANGEME'


        # pick correct executable
        if shutil.which('rpicam-still'):
            self.ccd_driver_exec = 'rpicam-still'
        elif shutil.which('libcamera-still'):
            self.ccd_driver_exec = 'libcamera-still'
        else:
            logger.warning('rpicam-still command not found')
            self.ccd_driver_exec = self.libcamera_exec  # fallback


        # this will fallback to the original self.ccd_driver_exec
        logger.info('libcamera executable: %s', self.ccd_driver_exec)


        # override in subclass
        self.camera_info = {
            'width'         : 0,
            'height'        : 0,
            'pixel'         : 0.0,
            'min_gain'      : 0.0,
            'max_gain'      : 0.0,
            'min_binning'   : 0,
            'max_binning'   : 0,
            'min_exposure'  : 0.0,
            'max_exposure'  : 0.0,
            'cfa'           : 'CHANGEME',
            'bit_depth'     : 0,
        }


        self._binmode_options = {
            1 : '',
        }


    def _cmdHasOption(self, cmd, option):
        option_eq = '{0:s}='.format(option)
        for cmd_part in cmd:
            if cmd_part == option or str(cmd_part).startswith(option_eq):
                return True

        return False


    def _cmdOptionCount(self, cmd, option):
        option_eq = '{0:s}='.format(option)
        return sum(1 for cmd_part in cmd if cmd_part == option or str(cmd_part).startswith(option_eq))


    def _removeCmdOptions(self, cmd, options):
        normalized_cmd = []
        skip_next = False
        for idx, cmd_part in enumerate(cmd):
            if skip_next:
                skip_next = False
                continue

            if cmd_part in options:
                if idx + 1 < len(cmd) and not str(cmd[idx + 1]).startswith('--'):
                    skip_next = True
                continue

            if any(str(cmd_part).startswith('{0:s}='.format(option)) for option in options):
                continue

            normalized_cmd.append(cmd_part)

        return normalized_cmd


    def _multiCameraTimingDiagEnabled(self):
        return bool(getattr(self, 'images_only', False)) and bool(self.config.get('MULTI_CAMERA_TIMING_DIAG', False))


    def _libcameraAwbMode(self, night=True):
        libcamera_config = self.config.get('LIBCAMERA', {}) or {}
        awb_mode = str(libcamera_config.get('AWB_MODE', libcamera_config.get('awb_mode', '')) or '').strip().lower()
        if not awb_mode:
            if night:
                awb_enabled = bool(libcamera_config.get('AWB_ENABLE', True))
                awb_mode = str(libcamera_config.get('AWB', 'auto') or 'auto').strip().lower() if awb_enabled else 'fixed'
            else:
                awb_enabled = bool(libcamera_config.get('AWB_ENABLE_DAY', True))
                awb_mode = str(libcamera_config.get('AWB_DAY', 'auto') or 'auto').strip().lower() if awb_enabled else 'fixed'

        if awb_mode not in self.libcamera_awb_modes:
            logger.warning('Invalid libcamera AWB mode "%s"; using auto', awb_mode)
            return 'auto'

        return awb_mode


    def _libcameraAwbGainValue(self, key):
        libcamera_config = self.config.get('LIBCAMERA', {}) or {}
        try:
            gain = float(libcamera_config.get(key, libcamera_config.get(key.lower(), 1.0)))
        except (TypeError, ValueError):
            logger.warning('Invalid libcamera %s value; using 1.0', key)
            return 1.0

        if gain <= 0:
            logger.warning('Invalid libcamera %s value %0.4f; using 1.0', key, gain)
            return 1.0

        return gain


    def _processingMode(self):
        return str(self.config.get('PROCESSING_MODE', 'classic') or 'classic').strip().lower()


    def _hybridAwbEnabled(self):
        return self._processingMode() == 'hybrid'


    def _hybridAwbApplyMode(self):
        raw_apply_mode = self._hybridAwbRawApplyMode()
        apply_mode = str(raw_apply_mode or 'auto').strip().lower()
        if apply_mode not in ('auto', 'capture_driver', 'postprocess_rgb', 'disabled'):
            return 'auto'

        return apply_mode


    def _hybridAwbRawApplyMode(self):
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


    def _hybridAwbCaptureEnabled(self):
        if not self._hybridAwbEnabled():
            return False

        return self._hybridAwbApplyMode() in ('auto', 'capture_driver')


    def _hybridAwbCaptureDiagEnabled(self):
        return self._hybridAwbEnabled()


    def _clampHybridAwbGain(self, gain):
        return max(0.5, min(3.0, float(gain)))


    def _hybridAwbFallbackGains(self):
        return (
            self._clampHybridAwbGain(self._libcameraAwbGainValue('AWB_RED_GAIN')),
            self._clampHybridAwbGain(self._libcameraAwbGainValue('AWB_BLUE_GAIN')),
        )


    def _hybridAwbGains(self):
        red_gain, blue_gain = self._hybridAwbFallbackGains()
        hybrid_av = getattr(self, 'hybrid_av', None)
        if hybrid_av is None:
            return red_gain, blue_gain, 0, 'no-shared-state'

        try:
            with hybrid_av.get_lock():
                if hybrid_av[constants.HYBRID_AWB_INITIALIZED] < 0.5:
                    hybrid_av[constants.HYBRID_AWB_RED_GAIN_NEXT] = red_gain
                    hybrid_av[constants.HYBRID_AWB_BLUE_GAIN_NEXT] = blue_gain
                    hybrid_av[constants.HYBRID_AWB_INITIALIZED] = 1.0
                    hybrid_av[constants.HYBRID_AWB_SAMPLE_COUNT] = 0.0
                    hybrid_av[constants.HYBRID_AWB_STATUS] = 0.0

                red_gain = self._clampHybridAwbGain(hybrid_av[constants.HYBRID_AWB_RED_GAIN_NEXT])
                blue_gain = self._clampHybridAwbGain(hybrid_av[constants.HYBRID_AWB_BLUE_GAIN_NEXT])
                sample_count = int(hybrid_av[constants.HYBRID_AWB_SAMPLE_COUNT])
        except Exception as e:
            logger.error('Hybrid AWB shared state error: %s', str(e))
            red_gain, blue_gain = self._hybridAwbFallbackGains()
            return red_gain, blue_gain, 0, 'shared-state-error'

        return red_gain, blue_gain, sample_count, None


    def _hybridAwbCaptureControl(self):
        apply_mode = self._hybridAwbApplyMode()
        red_gain, blue_gain, sample_count, reason = self._hybridAwbGains()
        if apply_mode in ('auto', 'capture_driver'):
            return {
                'apply_mode'   : apply_mode,
                'backend'      : 'libcamera_capture',
                'awb_source'   : 'hybrid_runtime',
                'raw_apply_mode': self._hybridAwbRawApplyMode(),
                'awbgains_suppressed': False,
                'red_gain'     : red_gain,
                'blue_gain'    : blue_gain,
                'sample_count' : sample_count,
                'reason'       : reason,
            }

        return {
            'apply_mode'   : apply_mode,
            'backend'      : apply_mode,
            'awb_source'   : 'hybrid_runtime_diagnostic',
            'raw_apply_mode': self._hybridAwbRawApplyMode(),
            'awbgains_suppressed': apply_mode in ('postprocess_rgb', 'disabled'),
            'red_gain'     : red_gain,
            'blue_gain'    : blue_gain,
            'sample_count' : sample_count,
            'reason'       : reason,
        }


    def _normalizeHybridAwbCaptureCommand(self, cmd):
        if not self._hybridAwbEnabled():
            return cmd, None

        control = self._hybridAwbCaptureControl()
        normalized_cmd = self._removeCmdOptions(cmd, {'--awb', '--awbgains'})
        if not control.get('awbgains_suppressed'):
            normalized_cmd.extend([
                '--awbgains',
                '{0:0.4f},{1:0.4f}'.format(control['red_gain'], control['blue_gain']),
            ])
        return normalized_cmd, control


    def _logHybridAwbCaptureCommandDiag(self, cmd, control, exposure, exposure_us, gain, timeout):
        if not control or not self._hybridAwbCaptureDiagEnabled():
            return

        _multi_camera_diag(
            '[HYBRID_AWB_CAPTURE_DIAG][%s][camera_id=%s] command=%s argv=%r raw_apply_mode=%r apply_mode=%s backend=%s awb_source=%s awbgains_suppressed=%s awb_red=%0.4f awb_blue=%0.4f sample_count=%d shutter_us=%d requested_exposure_s=%0.8f gain=%0.2f start_monotonic=%0.6f exposure_period=%0.4f exposure_period_day=%0.4f timeout=%0.1fs has_awbgains=%s awbgains_count=%d has_awb=%s awb_count=%d has_timeout=%s has_immediate=%s has_nopreview=%s',
            getattr(self, 'profile_id', 'default'),
            getattr(self, 'camera_id', 'unknown'),
            ' '.join(cmd),
            cmd,
            control.get('raw_apply_mode'),
            control.get('apply_mode'),
            control.get('backend'),
            control.get('awb_source'),
            control.get('awbgains_suppressed'),
            control.get('red_gain'),
            control.get('blue_gain'),
            int(control.get('sample_count') or 0),
            exposure_us,
            float(exposure),
            float(gain),
            self.exposureStartMonotonic,
            float(self.config.get('EXPOSURE_PERIOD', 0.0)),
            float(self.config.get('EXPOSURE_PERIOD_DAY', 0.0)),
            timeout,
            self._cmdHasOption(cmd, '--awbgains'),
            self._cmdOptionCount(cmd, '--awbgains'),
            self._cmdHasOption(cmd, '--awb'),
            self._cmdOptionCount(cmd, '--awb'),
            self._cmdHasOption(cmd, '--timeout'),
            self._cmdHasOption(cmd, '--immediate'),
            self._cmdHasOption(cmd, '--nopreview'),
        )


    def _logHybridAwbCaptureEndDiag(self, process_exit_time, process_exit_monotonic, sync):
        control = getattr(self, '_hybrid_awb_capture_control', None)
        if not control or not self._hybridAwbCaptureDiagEnabled():
            return

        rpicam_elapsed_s = process_exit_time - self.exposureStartTime
        monotonic_elapsed_s = process_exit_monotonic - self.exposureStartMonotonic
        _multi_camera_diag(
            '[HYBRID_AWB_CAPTURE_DIAG][%s][camera_id=%s] process_end apply_mode=%s backend=%s awb_source=%s start_monotonic=%0.6f end_monotonic=%0.6f elapsed_monotonic=%0.4fs process_start_time=%0.6f process_exit_time=%0.6f elapsed=%0.4fs requested_exposure_s=%0.8f shutter_us=%d returncode=%s sync=%s timeout=%0.1fs',
            getattr(self, 'profile_id', 'default'),
            getattr(self, 'camera_id', 'unknown'),
            control.get('apply_mode'),
            control.get('backend'),
            control.get('awb_source'),
            self.exposureStartMonotonic,
            process_exit_monotonic,
            monotonic_elapsed_s,
            self.processStartTime,
            process_exit_time,
            rpicam_elapsed_s,
            float(self.exposure),
            int(float(self.exposure) * 1000000),
            self.libcamera_process.returncode,
            sync,
            self.libcamera_timeout,
        )


    def _appendLibcameraAwbOptions(self, cmd, night=True):
        if self._hybridAwbCaptureEnabled():
            red_gain, blue_gain, sample_count, reason = self._hybridAwbGains()
            cmd.extend(['--awbgains', '{0:g},{1:g}'.format(red_gain, blue_gain)])
            reason_s = '' if reason is None else ' reason={0:s}'.format(reason)
            _multi_camera_diag(
                '[HYBRID_AWB][%s][camera_id=%s] backend=libcamera_capture applied_red=%0.4f applied_blue=%0.4f sample_count=%d%s',
                getattr(self, 'profile_id', 'default'),
                self.camera_id if self.camera_id is not None else 'unknown',
                red_gain,
                blue_gain,
                sample_count,
                reason_s,
            )
            return

        awb_mode = self._libcameraAwbMode(night=night)
        if awb_mode == 'fixed':
            red_gain = self._libcameraAwbGainValue('AWB_RED_GAIN')
            blue_gain = self._libcameraAwbGainValue('AWB_BLUE_GAIN')
            cmd.extend(['--awbgains', '{0:g},{1:g}'.format(red_gain, blue_gain)])
            return

        cmd.extend(['--awb', awb_mode])


    @property
    def libcamera_bit_depth(self):
        return self.ccd_device.bit_depth

    @libcamera_bit_depth.setter
    def libcamera_bit_depth(self, new_libcamera_bit_depth):
        self.camera_info['bit_depth'] = int(new_libcamera_bit_depth)
        self.ccd_device.bit_depth = self.camera_info['bit_depth']


    def getCcdGain(self):
        return float(self.gain_av[constants.GAIN_CURRENT])


    def setCcdGain(self, new_gain_value):
        gain_f = float(round(new_gain_value, 2))  # limit gain to 2 decimals

        # Update shared gain value
        with self.gain_av.get_lock():
            self.gain_av[constants.GAIN_CURRENT] = gain_f

        self.gain = gain_f


    def setCcdBinning(self, bin_value):
        if not bin_value:
            # Assume default
            return


        # Update shared gin value
        with self.binning_av.get_lock():
            self.binning_av[constants.BINNING_CURRENT] = int(bin_value)


        self.binning = int(bin_value)


    def _getBinModeOptions(self, bin_value):
        try:
            option = self._binmode_options[int(bin_value)]
        except KeyError:
            raise BinModeException('Invalid bin mode for camera: {0:d}'.format(int(bin_value)))

        return option


    def setCcdExposure(self, exposure, gain, binning, sync=False, timeout=None, sqm_exposure=False):
        if self.active_exposure:
            return


        self.exposure = exposure
        self.sqm_exposure = sqm_exposure


        libcamera_camera_id = self.config.get('LIBCAMERA', {}).get('CAMERA_ID', 0)


        if self.night_av[constants.NIGHT_NIGHT]:
            # night
            image_type = self.config.get('LIBCAMERA', {}).get('IMAGE_FILE_TYPE', 'jpg')
        else:
            # day
            image_type = self.config.get('LIBCAMERA', {}).get('IMAGE_FILE_TYPE_DAY', 'jpg')


        if image_type == 'dng' and self.memory_total_mb <= 768:
            logger.warning('*** Capturing raw images (dng) with libcamera and less than 1gb of memory can result in out-of-memory errors ***')


        try:
            image_tmp_f = tempfile.NamedTemporaryFile(mode='w', suffix='.{0:s}'.format(image_type), delete=True)
            image_tmp_f.close()
            image_tmp_p = Path(image_tmp_f.name)

            metadata_tmp_f = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=True)
            metadata_tmp_f.close()
            metadata_tmp_p = Path(metadata_tmp_f.name)
        except OSError as e:
            logger.error('OSError: %s', str(e))
            return


        try:
            binmode_option = self._getBinModeOptions(int(binning))
        except BinModeException as e:
            logger.error('Invalid setting: %s', str(e))
            binmode_option = ''


        self.current_exposure_file_p = image_tmp_p
        self.current_metadata_file_p = metadata_tmp_p


        if self.gain != float(round(gain, 2)):
            self.setCcdGain(gain)

        if self.binning != int(binning):
            self.setCcdBinning(binning)


        exposure_us = int(exposure * 1000000)

        if image_type in ['dng']:
            cmd = [
                self.ccd_device.driver_exec,
                '--nopreview',
                '--camera', '{0:d}'.format(libcamera_camera_id),
                '--raw',
                '--denoise', 'off',
                '--gain', '{0:0.2f}'.format(self.gain_av[constants.GAIN_CURRENT]),
                '--shutter', '{0:d}'.format(exposure_us),
                '--metadata', str(metadata_tmp_p),
                '--metadata-format', 'json',
            ]
        elif image_type in ['jpg', 'png']:
            #logger.warning('RAW frame mode disabled due to low memory resources')
            cmd = [
                self.ccd_device.driver_exec,
                '--nopreview',
                '--camera', '{0:d}'.format(libcamera_camera_id),
                '--encoding', '{0:s}'.format(image_type),
                '--quality', '95',
                '--gain', '{0:0.2f}'.format(self.gain_av[constants.GAIN_CURRENT]),
                '--shutter', '{0:d}'.format(exposure_us),
                '--metadata', str(metadata_tmp_p),
                '--metadata-format', 'json',
            ]
        else:
            raise Exception('Invalid image type')



        if self.night_av[constants.NIGHT_NIGHT]:
            #  night

            if self.config.get('LIBCAMERA', {}).get('IMMEDIATE', True):
                cmd.insert(1, '--immediate')


            self._appendLibcameraAwbOptions(cmd, night=True)


            # CCM
            if self.config.get('LIBCAMERA', {}).get('CCM_DISABLE'):
                cmd.extend(['--ccm', '1,0,0,0,1,0,0,0,1'])

        else:
            # daytime

            if self.config.get('LIBCAMERA', {}).get('IMMEDIATE_DAY', True):
                cmd.insert(1, '--immediate')


            self._appendLibcameraAwbOptions(cmd, night=False)


            # CCM
            if self.config.get('LIBCAMERA', {}).get('CCM_DISABLE_DAY'):
                cmd.extend(['--ccm', '1,0,0,0,1,0,0,0,1'])


        # add --mode flags for binning
        if binmode_option:
            cmd.extend(binmode_option.split(' '))


        # extra options get added last
        if self.night_av[constants.NIGHT_NIGHT]:
            #  night
            # Add extra config options
            extra_options = self.config.get('LIBCAMERA', {}).get('EXTRA_OPTIONS')
            if extra_options:
                cmd.extend(extra_options.split(' '))

        else:
            # daytime

            # Add extra config options
            extra_options = self.config.get('LIBCAMERA', {}).get('EXTRA_OPTIONS_DAY')
            if extra_options:
                cmd.extend(extra_options.split(' '))

        cmd, self._hybrid_awb_capture_control = self._normalizeHybridAwbCaptureCommand(cmd)

        if self._hybridAwbEnabled() and self._cmdHasOption(cmd, '--immediate'):
            cmd = self._removeCmdOptions(cmd, {'--timeout'})
            cmd.extend(['--timeout', '1'])
        elif self._cmdHasOption(cmd, '--immediate') and not self._cmdHasOption(cmd, '--timeout'):
            cmd.extend(['--timeout', '1'])


        # Finally add output file
        cmd.extend(['--output', str(image_tmp_p)])


        ### testing an expoure that times out
        #cmd = [
        #    'sleep', '600',
        #]


        images_only = bool(getattr(self, 'images_only', False))
        self.libcamera_timeout = self._libcameraExposureTimeout()
        self.exposureStartTime = time.time()
        self.exposureStartMonotonic = time.monotonic()
        logger.info('image command: %s', ' '.join(cmd))
        if images_only:
            _multi_camera_diag(
                '[MULTI_CAMERA_DIAG][%s][camera_id=%s] libcamera command: %s',
                getattr(self, 'profile_id', 'default'),
                getattr(self, 'camera_id', 'unknown'),
                ' '.join(cmd),
            )
        self._logHybridAwbCaptureCommandDiag(cmd, self._hybrid_awb_capture_control, exposure, exposure_us, gain, self.libcamera_timeout)


        if images_only:
            # MULTI_CAMERA_DIAG: avoid an unread PIPE in the asynchronous
            # libcamera path. A verbose rpicam/libcamera process can block if
            # stdout fills before getCcdExposureStatus() reads it.
            self.libcamera_output_f = tempfile.TemporaryFile(mode='w+b')
            libcamera_stdout = self.libcamera_output_f
        else:
            self.libcamera_output_f = None
            libcamera_stdout = subprocess.PIPE

        timing_diag = self._multiCameraTimingDiagEnabled()
        if timing_diag:
            _multi_camera_diag(
                '[MULTI_CAMERA_TIMING][%s][camera_id=%s] rpicam_command requested_exposure_s=%0.8f shutter_us=%d timeout=%0.1fs command=%s',
                getattr(self, 'profile_id', 'default'),
                getattr(self, 'camera_id', 'unknown'),
                float(exposure),
                exposure_us,
                self.libcamera_timeout,
                ' '.join(cmd),
            )
            _multi_camera_diag(
                '[MULTI_CAMERA_TIMING][%s][camera_id=%s] rpicam_start exposure_start_time=%0.6f requested_exposure_s=%0.8f shutter_us=%d gain=%0.2f binning=%d image_type=%s libcamera_camera_id=%s timeout=%0.1fs',
                getattr(self, 'profile_id', 'default'),
                getattr(self, 'camera_id', 'unknown'),
                self.exposureStartTime,
                float(exposure),
                exposure_us,
                float(gain),
                int(binning),
                image_type,
                libcamera_camera_id,
                self.libcamera_timeout,
            )

        self.processStartTime = time.time()
        self.processStartMonotonic = time.monotonic()
        self.libcamera_process = subprocess.Popen(
            cmd,
            stdout=libcamera_stdout,
            stderr=subprocess.STDOUT,
        )

        self.active_exposure = True


        # Update shared exposure value
        with self.exposure_av.get_lock():
            self.exposure_av[constants.EXPOSURE_CURRENT] = float(exposure)


        if sync:
            try:
                self.libcamera_process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                logger.error('Exposure timeout')
                if images_only:
                    _multi_camera_diag(
                        '[MULTI_CAMERA_DIAG][%s][camera_id=%s] libcamera sync timeout timeout=%s; aborting process',
                        getattr(self, 'profile_id', 'default'),
                        getattr(self, 'camera_id', 'unknown'),
                        timeout,
                    )
                self.abortCcdExposure()
                raise TimeOutException('Timeout waiting for exposure')


            if self.libcamera_process.returncode != 0:
                # log errors
                stdout_lines = self._readLibcameraOutput()
                for line in stdout_lines:
                    logger.error('rpicam-still error: %s', line)

                # not returning, just log the error

            if timing_diag:
                process_exit_time = time.time()
                process_exit_monotonic = time.monotonic()
                rpicam_elapsed_s = process_exit_time - self.exposureStartTime
                _multi_camera_diag(
                    '[MULTI_CAMERA_TIMING][%s][camera_id=%s] rpicam_end process_start_time=%0.6f process_exit_time=%0.6f elapsed=%0.4fs requested_exposure_s=%0.8f shutter_us=%d returncode=%s sync=%s timeout=%0.1fs',
                    getattr(self, 'profile_id', 'default'),
                    getattr(self, 'camera_id', 'unknown'),
                    self.processStartTime,
                    process_exit_time,
                    rpicam_elapsed_s,
                    float(self.exposure),
                    int(float(self.exposure) * 1000000),
                    self.libcamera_process.returncode,
                    sync,
                    self.libcamera_timeout,
                )
            else:
                process_exit_time = time.time()
                process_exit_monotonic = time.monotonic()

            self._logHybridAwbCaptureEndDiag(process_exit_time, process_exit_monotonic, True)

            self.active_exposure = False

            self._processMetadata()

            self._closeLibcameraOutput()

            self._queueImage()
            self._resetLibcameraProcessState()


    def getCcdExposureStatus(self):
        # returns camera_ready, exposure_state
        if self.active_exposure and self._libcameraProcessTimedOut():
            timeout = self._libcameraExposureTimeout()
            elapsed = time.time() - self.exposureStartTime
            _multi_camera_diag(
                '[MULTI_CAMERA_DIAG][%s][camera_id=%s] libcamera async timeout elapsed=%0.1fs timeout=%0.1fs; aborting process',
                getattr(self, 'profile_id', 'default'),
                getattr(self, 'camera_id', 'unknown'),
                elapsed,
                timeout,
            )
            self.abortCcdExposure()
            return True, 'TIMEOUT'

        if self._libCameraProcessRunning():
            return False, 'BUSY'


        if self.active_exposure:
            # if we get here, that means the camera is finished with the exposure
            self.active_exposure = False


            if self.libcamera_process.returncode != 0:
                # log errors
                stdout_lines = self._readLibcameraOutput()
                for line in stdout_lines:
                    logger.error('rpicam-still error: %s', line)

                # not returning, just log the error

            if self._multiCameraTimingDiagEnabled():
                process_exit_time = time.time()
                process_exit_monotonic = time.monotonic()
                rpicam_elapsed_s = process_exit_time - self.exposureStartTime
                _multi_camera_diag(
                    '[MULTI_CAMERA_TIMING][%s][camera_id=%s] rpicam_end process_start_time=%0.6f process_exit_time=%0.6f elapsed=%0.4fs requested_exposure_s=%0.8f shutter_us=%d returncode=%s sync=%s timeout=%0.1fs',
                    getattr(self, 'profile_id', 'default'),
                    getattr(self, 'camera_id', 'unknown'),
                    self.processStartTime,
                    process_exit_time,
                    rpicam_elapsed_s,
                    float(self.exposure),
                    int(float(self.exposure) * 1000000),
                    self.libcamera_process.returncode,
                    False,
                    self.libcamera_timeout,
                )
            else:
                process_exit_time = time.time()
                process_exit_monotonic = time.monotonic()

            self._logHybridAwbCaptureEndDiag(process_exit_time, process_exit_monotonic, False)


            self._processMetadata()

            self._closeLibcameraOutput()

            self._queueImage()
            self._resetLibcameraProcessState()


        return True, 'READY'


    def _readLibcameraOutput(self):
        if self.libcamera_output_f:
            self.libcamera_output_f.seek(0)
            return self.libcamera_output_f.readlines()

        if self.libcamera_process and self.libcamera_process.stdout:
            return self.libcamera_process.stdout.readlines()

        return []


    def _closeLibcameraOutput(self):
        if not self.libcamera_output_f:
            return

        self.libcamera_output_f.close()
        self.libcamera_output_f = None


    def _resetLibcameraProcessState(self):
        self.libcamera_process = None
        self.current_exposure_file_p = None
        self.current_metadata_file_p = None
        self.exposureStartTime = 0.0


    def _libcameraExposureTimeout(self):
        exposure = float(getattr(self, 'exposure', 0.0) or 0.0)
        configured_timeout = float(self.config.get('CCD_EXPOSURE_TIMEOUT', 330))
        return max(configured_timeout, exposure + 30.0)


    def _libcameraProcessTimedOut(self):
        if not bool(getattr(self, 'images_only', False)):
            return False

        if not self.exposureStartTime:
            return False

        if not self._libCameraProcessRunning():
            return False

        return (time.time() - self.exposureStartTime) > self._libcameraExposureTimeout()


    def _processMetadata(self):
        # read metadata to get sensor temperature
        if self.current_metadata_file_p:
            try:
                with io.open(self.current_metadata_file_p, 'r', encoding='utf-8') as f_metadata:
                    metadata_dict = json.load(f_metadata, object_pairs_hook=OrderedDict)
            except FileNotFoundError as e:
                logger.error('Metadata file not found: %s', str(e))
                metadata_dict = dict()
            except PermissionError as e:
                logger.error('Permission erro: %s', str(e))
                metadata_dict = dict()
            except json.JSONDecodeError as e:
                logger.error('Error decoding json: %s', str(e))
                metadata_dict = dict()


        #logger.info('Metadata: %s', metadata_dict)


        try:
            self.current_metadata_file_p.unlink()
        except FileNotFoundError:
            pass


        ### Gain
        try:
            analogue_gain = float(metadata_dict[self._analogue_gain_metadata_key])
        except KeyError:
            #logger.error('libcamera camera analogue gain key not found')
            analogue_gain = 0.0
        except ValueError:
            #logger.error('Unable to parse libcamera analogue gain')
            analogue_gain = 0.0


        try:
            digital_gain = float(metadata_dict[self._digital_gain_metadata_key])
        except KeyError:
            #logger.error('libcamera camera digital gain key not found')
            digital_gain = 0.0
        except ValueError:
            #logger.error('Unable to parse libcamera digital gain')
            digital_gain = 0.0


        if analogue_gain:
            logger.info('libcamera reported gain: %0.2f/%0.2f', analogue_gain, digital_gain)


        ### Temperature
        try:
            self.ccd_temp = float(metadata_dict[self._sensor_temp_metadata_key])
        except KeyError:
            logger.error('libcamera camera temperature key not found')
        except ValueError:
            logger.error('Unable to parse libcamera camera temperature')


        ### Auto white balance
        # Only return these values when libcamera AWB is enabled
        if self.night_av[constants.NIGHT_NIGHT]:
            # night
            if self._libcameraAwbMode(night=True) != 'fixed':
                try:
                    awb_gains = metadata_dict[self._awb_gains_metadata_key]
                    self._awb_gains = [awb_gains[0], awb_gains[1]]
                    logger.info('libcamera color gains: Red: %0.2f, Blue: %0.2f', *self._awb_gains)
                except KeyError:
                    logger.error('libcamera sensor AWB key not found')
                    self._awb_gains = None
                except IndexError:
                    logger.error('Invalid color gain values')
                    self._awb_gains = None


                ### Color correction matrix
                #try:
                #    ccm = metadata_dict[self._ccm_metadata_key]
                #    self._ccm = [
                #        [ccm[8], ccm[7], ccm[6]],
                #        [ccm[5], ccm[4], ccm[3]],
                #        [ccm[2], ccm[1], ccm[0]],
                #    ]
                #except KeyError:
                #    logger.error('libcamera CCM key not found')
                #    self._ccm = None
                #except IndexError:
                #    logger.error('Invalid CCM values')
                #    self._ccm = None

            else:
                self._awb_gains = None
                #self._ccm = None

        else:
            # day
            if self._libcameraAwbMode(night=False) != 'fixed':
                try:
                    awb_gains = metadata_dict[self._awb_gains_metadata_key]
                    self._awb_gains = [awb_gains[0], awb_gains[1]]
                    logger.info('libcamera color gains: Red: %0.2f, Blue: %0.2f', *self._awb_gains)
                except KeyError:
                    logger.error('libcamera sensor AWB key not found')
                    self._awb_gains = None
                except IndexError:
                    logger.error('Invalid color gain values')
                    self._awb_gains = None


                ### Color correction matrix
                #try:
                #    ccm = metadata_dict[self._ccm_metadata_key]
                #    self._ccm = [
                #        [ccm[8], ccm[7], ccm[6]],
                #        [ccm[5], ccm[4], ccm[3]],
                #        [ccm[2], ccm[1], ccm[0]],
                #    ]
                #except KeyError:
                #    logger.error('libcamera CCM key not found')
                #    self._ccm = None
                #except IndexError:
                #    logger.error('Invalid CCM values')
                #    self._ccm = None

            else:
                self._awb_gains = None
                #self._ccm = None


        ### Black Level
        try:
            black_level = metadata_dict[self._black_level_metadata_key]
            self._black_level = black_level[0]  # Only going to use the first key for now
            logger.info('libcamera black level: %d', self._black_level)
        except KeyError:
            logger.error('libcamera sensor black level key not found')
            self._black_level = None
        except IndexError:
            logger.error('Invalid black level values')
            self._black_level = None



    def abortCcdExposure(self):
        logger.warning('Aborting exposure')

        self.active_exposure = False

        for _ in range(5):
            if not self._libCameraProcessRunning():
                break

            self.libcamera_process.terminate()
            time.sleep(0.5)
            continue


        if self._libCameraProcessRunning():
            self.libcamera_process.kill()
            self.libcamera_process.poll()  # close out the process

        self._closeLibcameraOutput()


        try:
            if self.current_exposure_file_p:
                self.current_exposure_file_p.unlink()
        except FileNotFoundError:
            pass


        try:
            if self.current_metadata_file_p:
                self.current_metadata_file_p.unlink()
        except FileNotFoundError:
            pass

        self._resetLibcameraProcessState()


    def _queueImage(self):
        exposure_elapsed_s = time.time() - self.exposureStartTime
        queue_time = time.time()

        exp_date = datetime.now()

        ### process data in worker
        jobdata = {
            'filename'    : str(self.current_exposure_file_p),
            'exposure'    : self.exposure,
            'gain'        : self.gain,
            'binning'     : self.binning,
            'sqm_exposure': self.sqm_exposure,
            'exp_time'    : datetime.timestamp(exp_date),  # datetime objects are not json serializable
            'exp_elapsed' : exposure_elapsed_s,
            'capture_start_time' : self.exposureStartTime,
            'queue_time'  : queue_time,
            'camera_id'   : self.camera_id,
            'profile_id'  : getattr(self, 'profile_id', 'default'),
            'profile_primary' : bool(getattr(self, 'profile_primary', True)),
            'images_only' : bool(getattr(self, 'images_only', False)),
            'profile_outputs' : getattr(self, 'profile_outputs', {}),
            'filename_t'  : self._filename_t,
            'libcamera_black_level' : self._black_level,
            'libcamera_awb_gains'   : self._awb_gains,
            #'libcamera_ccm'         : self._ccm,
        }

        if self._multiCameraTimingDiagEnabled():
            try:
                file_size = self.current_exposure_file_p.stat().st_size
            except (FileNotFoundError, AttributeError):
                file_size = 'missing'

            try:
                queue_depth = self.image_q.qsize()
            except NotImplementedError:
                queue_depth = 'unknown'

            _multi_camera_diag(
                '[MULTI_CAMERA_TIMING][%s][camera_id=%s] image_queue_push t=%0.6f capture_elapsed=%0.4fs file_size=%s queue_depth_before=%s filename=%s',
                getattr(self, 'profile_id', 'default'),
                getattr(self, 'camera_id', 'unknown'),
                queue_time,
                exposure_elapsed_s,
                file_size,
                queue_depth,
                str(self.current_exposure_file_p),
            )

        self.image_q.put(jobdata)


    def _libCameraProcessRunning(self):
        if not self.libcamera_process:
            return False

        # poll returns None when process is active, rc (normally 0) when finished
        poll = self.libcamera_process.poll()
        if isinstance(poll, type(None)):
            return True

        return False


    def findCcd(self, *args, **kwargs):
        new_ccd = FakeIndiCcd()
        new_ccd.device_name = self.ccd_device_name
        new_ccd.driver_exec = self.ccd_driver_exec

        new_ccd.width = self.camera_info['width']
        new_ccd.height = self.camera_info['height']
        new_ccd.pixel = self.camera_info['pixel']

        new_ccd.min_gain = self.camera_info['min_gain']
        new_ccd.max_gain = self.camera_info['max_gain']

        new_ccd.min_binning = self.camera_info['min_binning']
        new_ccd.max_binning = self.camera_info['max_binning']

        new_ccd.min_exposure = self.camera_info['min_exposure']
        new_ccd.max_exposure = self.camera_info['max_exposure']

        new_ccd.cfa = self.camera_info['cfa']
        new_ccd.bit_depth = self.camera_info['bit_depth']

        self.ccd_device = new_ccd

        return new_ccd


    def getCcdInfo(self):
        ccdinfo = dict()

        ccdinfo['CCD_EXPOSURE'] = dict()
        ccdinfo['CCD_EXPOSURE']['CCD_EXPOSURE_VALUE'] = {
            'current' : None,
            'min'     : self.ccd_device.min_exposure,
            'max'     : self.ccd_device.max_exposure,
            'step'    : None,
            'format'  : None,
        }

        ccdinfo['CCD_INFO'] = dict()
        ccdinfo['CCD_INFO']['CCD_MAX_X'] = dict()
        ccdinfo['CCD_INFO']['CCD_MAX_Y'] = dict()
        ccdinfo['CCD_INFO']['CCD_PIXEL_SIZE'] = {
            'current' : self.ccd_device.pixel,
            'min'     : self.ccd_device.pixel,
            'max'     : self.ccd_device.pixel,
            'step'    : None,
            'format'  : None,
        }

        ccdinfo['CCD_INFO']['CCD_PIXEL_SIZE_X'] = {
            'current' : self.ccd_device.pixel,
            'min'     : self.ccd_device.pixel,
            'max'     : self.ccd_device.pixel,
            'step'    : None,
            'format'  : None,
        }

        ccdinfo['CCD_INFO']['CCD_PIXEL_SIZE_Y'] = {
            'current' : self.ccd_device.pixel,
            'min'     : self.ccd_device.pixel,
            'max'     : self.ccd_device.pixel,
            'step'    : None,
            'format'  : None,
        }

        ccdinfo['CCD_INFO']['CCD_BITSPERPIXEL'] = {
            'current' : self.ccd_device.bit_depth,
            'min'     : self.ccd_device.bit_depth,
            'max'     : self.ccd_device.bit_depth,
            'step'    : None,
            'format'  : None,
        }

        ccdinfo['CCD_CFA'] = dict()
        ccdinfo['CCD_CFA']['CFA_TYPE'] = {
            'text' : self.ccd_device.cfa,
        }

        ccdinfo['CCD_FRAME'] = dict()
        ccdinfo['CCD_FRAME']['X'] = dict()
        ccdinfo['CCD_FRAME']['Y'] = dict()

        ccdinfo['CCD_FRAME']['WIDTH'] = {
            'current' : self.ccd_device.width,
            'min'     : self.ccd_device.width,
            'max'     : self.ccd_device.width,
            'step'    : None,
            'format'  : None,
        }

        ccdinfo['CCD_FRAME']['HEIGHT'] = {
            'current' : self.ccd_device.height,
            'min'     : self.ccd_device.height,
            'max'     : self.ccd_device.height,
            'step'    : None,
            'format'  : None,
        }

        ccdinfo['CCD_FRAME_TYPE'] = {
            'FRAME_LIGHT' : 1,
            'FRAME_BIAS'  : 0,
            'FRAME_DARK'  : 0,
            'FRAME_FLAT'  : 0,
        }

        ccdinfo['GAIN_INFO'] = {
            'current' : self.ccd_device.min_gain,
            'min'     : self.ccd_device.min_gain,
            'max'     : self.ccd_device.max_gain,
            'step'    : None,
            'format'  : None,
        }

        ccdinfo['BINNING_INFO'] = {
            'current' : self.ccd_device.min_binning,
            'min'     : self.ccd_device.min_binning,
            'max'     : self.ccd_device.max_binning,
            'step'    : None,
            'format'  : None,
        }


        return ccdinfo


    def enableCcdCooler(self):
        # not supported
        pass


    def disableCcdCooler(self):
        # not supported
        pass


    def getCcdTemperature(self):
        return self.ccd_temp


    def setCcdTemperature(self, *args, **kwargs):
        # not supported
        pass


    def setCcdScopeInfo(self, *args):
        # not supported
        pass


class IndiClientLibCameraImx477(IndiClientLibCameraGeneric):

    def __init__(self, *args, **kwargs):
        super(IndiClientLibCameraImx477, self).__init__(*args, **kwargs)

        self.ccd_device_name = 'libcamera_imx477'

        self.camera_info = {
            'width'         : 4056,
            'height'        : 3040,
            'pixel'         : 1.55,
            'min_gain'      : 1.0,
            'max_gain'      : 22.26,
            'min_binning'   : 1,
            'max_binning'   : 4,
            'min_exposure'  : 0.000114,
            'max_exposure'  : 694.0,
            'cfa'           : 'BGGR',
            'bit_depth'     : 16,
        }

        self._binmode_options = {
            #1 : '--mode 4056:3040:12',
            1 : '',
            2 : '--mode 2028:1520:12',
            4 : '--mode 1332:990:10',  # cropped
        }


class IndiClientLibCameraImx378(IndiClientLibCameraGeneric):
    # this model is almost identical to the imx477

    def __init__(self, *args, **kwargs):
        super(IndiClientLibCameraImx378, self).__init__(*args, **kwargs)

        self.ccd_device_name = 'libcamera_imx378'

        self.camera_info = {
            'width'         : 4056,
            'height'        : 3040,
            'pixel'         : 1.55,
            'min_gain'      : 1.0,
            'max_gain'      : 22.26,
            'min_binning'   : 1,
            'max_binning'   : 4,
            'min_exposure'  : 0.000114,
            'max_exposure'  : 694.0,
            'cfa'           : 'BGGR',
            'bit_depth'     : 16,
        }

        self._binmode_options = {
            #1 : '--mode 4056:3040:12',
            1 : '',
            2 : '--mode 2028:1520:12',
            4 : '--mode 1332:990:10',  # cropped
        }


class IndiClientLibCameraOv5647(IndiClientLibCameraGeneric):

    def __init__(self, *args, **kwargs):
        super(IndiClientLibCameraOv5647, self).__init__(*args, **kwargs)

        self.ccd_device_name = 'libcamera_ov5647'

        self.camera_info = {
            'width'         : 2592,
            'height'        : 1944,
            'pixel'         : 1.4,
            'min_gain'      : 1.0,
            'max_gain'      : 16.0,
            'min_binning'   : 1,
            'max_binning'   : 1,
            'min_exposure'  : 0.0001,
            'max_exposure'  : 6.0,
            'cfa'           : 'BGGR',  # unverified
            'bit_depth'     : 16,
        }

        self._binmode_options = {
            1 : '',
        }


class IndiClientLibCameraImx219(IndiClientLibCameraGeneric):

    def __init__(self, *args, **kwargs):
        super(IndiClientLibCameraImx219, self).__init__(*args, **kwargs)

        self.ccd_device_name = 'libcamera_imx219'

        self.camera_info = {
            'width'         : 3280,
            'height'        : 2464,
            'pixel'         : 1.12,
            'min_gain'      : 1.0,
            'max_gain'      : 16.0,
            'min_binning'   : 1,
            'max_binning'   : 2,
            'min_exposure'  : 0.0001,
            'max_exposure'  : 11.76,
            'cfa'           : 'BGGR',
            'bit_depth'     : 16,
        }

        self._binmode_options = {
            #1 : '--mode 3280:2464:10',
            1 : '',
            2 : '--mode 1640:1232:10',
        }


class IndiClientLibCameraImx519(IndiClientLibCameraGeneric):
    # this model is almost identical to the imx477

    def __init__(self, *args, **kwargs):
        super(IndiClientLibCameraImx519, self).__init__(*args, **kwargs)

        self.ccd_device_name = 'libcamera_imx519'

        self.camera_info = {
            'width'         : 4656,
            'height'        : 3496,
            'pixel'         : 1.22,
            'min_gain'      : 1.0,
            'max_gain'      : 16.0,
            'min_binning'   : 1,
            'max_binning'   : 4,
            'min_exposure'  : 0.000592,
            'max_exposure'  : 200.0,
            'cfa'           : 'RGGB',
            'bit_depth'     : 16,
        }

        self._binmode_options = {
            #1 : '--mode 4656:3496:10',
            1 : '',
            2 : '--mode 2328:1748:10',
            #4 : '--mode 1920x1080:10',  # cropped
            4 : '--mode 1280:720:10',  # cropped
        }


class IndiClientLibCamera64mpHawkeye(IndiClientLibCameraGeneric):

    def __init__(self, *args, **kwargs):
        super(IndiClientLibCamera64mpHawkeye, self).__init__(*args, **kwargs)

        self.ccd_device_name = 'libcamera_64mp_hawkeye'

        self.camera_info = {
            'width'         : 9152,
            'height'        : 6944,
            'pixel'         : 0.8,
            'min_gain'      : 1.0,
            'max_gain'      : 16.0,  # unverified
            'min_binning'   : 1,
            'max_binning'   : 1,
            'min_exposure'  : 0.0001,
            'max_exposure'  : 200.0,
            'cfa'           : 'RGGB',
            'bit_depth'     : 16,
        }

        self._binmode_options = {
            1 : '',
            #1 : '--mode 9152:6944',  # unverified
            #2 : '--mode 4624:3472',
            #4 : '--mode 2312:1736',
        }


class IndiClientLibCameraOv64a40OwlSight(IndiClientLibCameraGeneric):

    def __init__(self, *args, **kwargs):
        super(IndiClientLibCameraOv64a40OwlSight, self).__init__(*args, **kwargs)

        self.ccd_device_name = 'libcamera_64mp_owlsight'

        self.camera_info = {
            'width'         : 9152,
            'height'        : 6944,
            'pixel'         : 1.008,
            'min_gain'      : 1.0,
            'max_gain'      : 16.0,
            'min_binning'   : 1,
            'max_binning'   : 4,
            'min_exposure'  : 0.000580,
            'max_exposure'  : 910.0,
            'cfa'           : 'RGGB',
            'bit_depth'     : 16,
        }

        self._binmode_options = {
            1 : '',
            #1 : '--mode 9152:6944:10',
            2 : '--mode 4624:3472:10',  # bin modes do not work well, exposure is not linear
            4 : '--mode 2312:1736:10',
        }


class IndiClientLibCameraImx708(IndiClientLibCameraGeneric):

    def __init__(self, *args, **kwargs):
        super(IndiClientLibCameraImx708, self).__init__(*args, **kwargs)

        self.ccd_device_name = 'libcamera_imx708'

        self.camera_info = {
            'width'         : 4608,
            'height'        : 2592,
            'pixel'         : 1.4,
            'min_gain'      : 1.13,
            'max_gain'      : 16.0,
            'min_binning'   : 1,
            'max_binning'   : 4,
            'min_exposure'  : 0.000026,
            'max_exposure'  : 220.0,
            'cfa'           : 'BGGR',
            'bit_depth'     : 16,
        }

        self._binmode_options = {
            #1 : '--mode 4608:2592:10',
            1 : '',
            2 : '--mode 2304:1296:10',
            4 : '--mode 1536:864:10',  # cropped
        }


class IndiClientLibCameraImx296(IndiClientLibCameraGeneric):

    def __init__(self, *args, **kwargs):
        super(IndiClientLibCameraImx296, self).__init__(*args, **kwargs)

        self.ccd_device_name = 'libcamera_imx296_gs'

        self.camera_info = {
            'width'         : 1456,
            'height'        : 1088,
            'pixel'         : 3.45,
            'min_gain'      : 1.0,
            'max_gain'      : 251.18,
            'min_binning'   : 1,
            'max_binning'   : 1,
            'min_exposure'  : 0.016562,
            'max_exposure'  : 15.5,
            'cfa'           : None,  # mono
            'bit_depth'     : 16,
        }

        self._binmode_options = {
            #1 : '--mode 1456:1088:10',
            1 : '',
            # no bin2
        }


class IndiClientLibCameraImx296Color(IndiClientLibCameraGeneric):

    def __init__(self, *args, **kwargs):
        super(IndiClientLibCameraImx296Color, self).__init__(*args, **kwargs)

        self.ccd_device_name = 'libcamera_imx296_gs_color'

        self.camera_info = {
            'width'         : 1456,
            'height'        : 1088,
            'pixel'         : 3.45,
            'min_gain'      : 1.0,
            'max_gain'      : 16.0,  # verified
            'min_binning'   : 1,
            'max_binning'   : 1,
            'min_exposure'  : 0.0001,
            'max_exposure'  : 15.5,
            'cfa'           : 'RGGB',  # unverified
            'bit_depth'     : 16,
        }

        self._binmode_options = {
            #1 : '--mode 1456:1088:10',
            1 : '',
            # no bin2
        }


class IndiClientLibCameraImx290(IndiClientLibCameraGeneric):

    def __init__(self, *args, **kwargs):
        super(IndiClientLibCameraImx290, self).__init__(*args, **kwargs)

        self.ccd_device_name = 'libcamera_imx290'

        self.camera_info = {
            'width'         : 1920,
            'height'        : 1080,
            'pixel'         : 2.9,
            'min_gain'      : 1.0,
            'max_gain'      : 29.51,  # unverified
            'min_binning'   : 1,
            'max_binning'   : 2,
            'min_exposure'  : 0.000014,
            'max_exposure'  : 115.0,
            'cfa'           : 'GRBG',
            'bit_depth'     : 16,
        }

        self._binmode_options = {
            #1 : '--mode 1920:1080:12',
            1 : '',
            2 : '--mode 1280:720:12',  # cropped
        }


class IndiClientLibCameraImx462(IndiClientLibCameraGeneric):

    def __init__(self, *args, **kwargs):
        super(IndiClientLibCameraImx462, self).__init__(*args, **kwargs)

        self.ccd_device_name = 'libcamera_imx462'

        self.camera_info = {
            'width'         : 1920,
            'height'        : 1080,
            'pixel'         : 2.9,
            'min_gain'      : 1.0,
            'max_gain'      : 29.51,
            'min_binning'   : 1,
            'max_binning'   : 2,
            'min_exposure'  : 0.000014,
            'max_exposure'  : 115.0,
            'cfa'           : 'RGGB',
            'bit_depth'     : 16,
        }

        self._binmode_options = {
            #1 : '--mode 1920:1080:12',
            1 : '',
            2 : '--mode 1280:720:12',  # cropped
        }


class IndiClientLibCameraImx327(IndiClientLibCameraGeneric):

    def __init__(self, *args, **kwargs):
        super(IndiClientLibCameraImx327, self).__init__(*args, **kwargs)

        self.ccd_device_name = 'libcamera_imx327'

        self.camera_info = {
            'width'         : 1920,
            'height'        : 1080,
            'pixel'         : 2.9,
            'min_gain'      : 1.0,
            'max_gain'      : 29.51,
            'min_binning'   : 1,
            'max_binning'   : 1,
            'min_exposure'  : 0.000014,
            'max_exposure'  : 115.0,
            'cfa'           : 'RGGB',
            'bit_depth'     : 16,
        }

        self._binmode_options = {
            #1 : '--mode 1920:1080:12',
            1 : '',
            #2 : '--mode 1280:720:12',  # cropped
        }


class IndiClientLibCameraImx298(IndiClientLibCameraGeneric):

    def __init__(self, *args, **kwargs):
        super(IndiClientLibCameraImx298, self).__init__(*args, **kwargs)

        self.ccd_device_name = 'libcamera_imx298'

        self.camera_info = {
            'width'         : 4640,
            'height'        : 3472,
            'pixel'         : 1.12,
            'min_gain'      : 1.0,
            'max_gain'      : 16.0,  # unverified
            'min_binning'   : 1,
            'max_binning'   : 1,
            'min_exposure'  : 0.0001,
            'max_exposure'  : 200.0,
            'cfa'           : 'RGGB',  # unverified
            'bit_depth'     : 16,
        }

        self._binmode_options = {
            1 : '',
        }


class IndiClientLibCameraImx500(IndiClientLibCameraGeneric):

    def __init__(self, *args, **kwargs):
        super(IndiClientLibCameraImx500, self).__init__(*args, **kwargs)

        self.ccd_device_name = 'libcamera_imx500_ai'

        self.camera_info = {
            'width'         : 4056,
            'height'        : 3040,
            'pixel'         : 1.55,
            'min_gain'      : 1.0,
            'max_gain'      : 22.0,  # verified
            'min_binning'   : 1,
            'max_binning'   : 1,
            'min_exposure'  : 0.0002,
            'max_exposure'  : 200.0,
            'cfa'           : 'RGGB',  # verified
            'bit_depth'     : 16,
        }

        self._binmode_options = {
            1 : '',
        }


class IndiClientLibCameraImx283(IndiClientLibCameraGeneric):

    def __init__(self, *args, **kwargs):
        super(IndiClientLibCameraImx283, self).__init__(*args, **kwargs)

        self.ccd_device_name = 'libcamera_imx283'

        self.camera_info = {
            'width'         : 5472,
            'height'        : 3648,
            'pixel'         : 2.4,
            'min_gain'      : 1.0,
            'max_gain'      : 22.5,
            'min_binning'   : 1,
            'max_binning'   : 1,
            'min_exposure'  : 0.000058,
            'max_exposure'  : 129.0,
            'cfa'           : 'RGGB',  # verified
            'bit_depth'     : 16,
        }

        self._binmode_options = {
            1 : '',
        }


class IndiClientLibCameraImx678(IndiClientLibCameraGeneric):

    def __init__(self, *args, **kwargs):
        super(IndiClientLibCameraImx678, self).__init__(*args, **kwargs)

        self.ccd_device_name = 'libcamera_imx678'

        self.camera_info = {
            'width'         : 3840,
            'height'        : 2160,
            'pixel'         : 2.0,
            'min_gain'      : 1.0,
            'max_gain'      : 32.0,  # unverified
            'min_binning'   : 1,
            'max_binning'   : 1,
            'min_exposure'  : 0.000032,
            'max_exposure'  : 200.0,
            'cfa'           : 'RGGB',  # verified
            'bit_depth'     : 16,
        }

        self._binmode_options = {
            1 : '',
        }


class IndiClientLibCameraImx335(IndiClientLibCameraGeneric):

    def __init__(self, *args, **kwargs):
        super(IndiClientLibCameraImx335, self).__init__(*args, **kwargs)

        self.ccd_device_name = 'libcamera_imx335'

        self.camera_info = {
            'width'         : 2592,
            'height'        : 1944,
            'pixel'         : 2.0,
            'min_gain'      : 1.0,
            'max_gain'      : 1000.0,
            'min_binning'   : 1,
            'max_binning'   : 1,
            'min_exposure'  : 0.000007,
            'max_exposure'  : 1.0,
            'cfa'           : 'RGGB',
            'bit_depth'     : 16,
        }

        self._binmode_options = {
            1 : '',
        }
