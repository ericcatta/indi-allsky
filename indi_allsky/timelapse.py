import os
import time
from pathlib import Path
import subprocess
import logging

from . import timelapse_preprocessor
from .exceptions import TimelapseException
from .timelapse_options import video_filter_arguments


logger = logging.getLogger('indi_allsky')



class TimelapseGenerator(object):

    ### System default
    ffmpeg_bin = 'ffmpeg'

    ### jellyfin-ffmpeg
    #ffmpeg_bin = '/usr/lib/jellyfin-ffmpeg/ffmpeg'


    def __init__(
        self,
        config,
        skip_frames=0,
        pre_processor_class='standard',
    ):
        self.config = config
        self.skip_frames = skip_frames

        self._codec = 'libx264'
        self._framerate = 25
        self._bitrate = '5000k'
        self._vf_scale = ''
        self._ffmpeg_extra_options = ''


        pp_class = getattr(timelapse_preprocessor, pre_processor_class)
        self._pre_processor = pp_class(self.config)


    @property
    def codec(self):
        return self._codec

    @codec.setter
    def codec(self, new_codec):
        self._codec = str(new_codec)

    @property
    def framerate(self):
        return self._framerate

    @framerate.setter
    def framerate(self, new_framerate):
        self._framerate = float(new_framerate)

    @property
    def bitrate(self):
        return self._bitrate

    @bitrate.setter
    def bitrate(self, new_bitrate):
        self._bitrate = str(new_bitrate)

    @property
    def vf_scale(self):
        return self._vf_scale

    @vf_scale.setter
    def vf_scale(self, new_vf_scale):
        self._vf_scale = str(new_vf_scale)

    @property
    def ffmpeg_extra_options(self):
        return self._ffmpeg_extra_options

    @ffmpeg_extra_options.setter
    def ffmpeg_extra_options(self, new_ffmpeg_extra_options):
        self._ffmpeg_extra_options = str(new_ffmpeg_extra_options)


    @property
    def pre_processor(self):
        return self._pre_processor


    def generate(self, video_file, file_list):
        video_file_p = Path(video_file)

        # Exclude empty files
        file_list_nonzero = filter(lambda p: p.stat().st_size != 0, file_list)

        # Sort by timestamp
        file_list_ordered = sorted(file_list_nonzero, key=lambda p: p.stat().st_mtime)


        if self.skip_frames:
            logger.warning('Skipping %d frames for timelapse', self.skip_frames)
            file_list_ordered = file_list_ordered[self.skip_frames:]


        # process images
        self.pre_processor.main(file_list_ordered)
        seqfolder = self.pre_processor.seqfolder


        start = time.time()

        cmd = self._ffmpeg_command(video_file_p, [
            '-f', 'image2', '-i', '{0:s}/%05d.{1:s}'.format(
                str(seqfolder), self.config['IMAGE_FILE_TYPE']),
        ])

        logger.info('FFmpeg command: %s', ' '.join(cmd))


        ffmpeg_env = dict()
        if self.config.get('TIMELAPSE', {}).get('FFMPEG_REPORT'):
            home_dir = Path(os.environ['HOME'])
            logger.warning('*** FFMPEG debug report will be generated in %s ***', home_dir)
            ffmpeg_env['FFREPORT'] = 'file={0:s}/ffmpeg-report-%t.log'.format(str(home_dir))


        try:
            ffmpeg_subproc = subprocess.run(
                cmd,
                env=ffmpeg_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                preexec_fn=lambda: os.nice(19),
                check=True
            )
            elapsed_s = time.time() - start
            logger.info('Timelapse generated in %0.4f s', elapsed_s)

            for line in ffmpeg_subproc.stdout.decode().split('\n'):
                logger.info('ffmpeg: %s', line)
        except subprocess.CalledProcessError as e:
            elapsed_s = time.time() - start

            logger.info('FFMPEG ran for %0.4f s', elapsed_s)
            logger.error('FFMPEG failed to generate timelapse, return code: %d', e.returncode)

            for line in e.stdout.decode().split('\n'):
                logger.error('ffmpeg: %s', line)

            ### Check if video file was created
            if video_file_p.is_file():
                logger.error('FFMPEG created broken video file, cleaning up')
                video_file_p.unlink()

            raise TimelapseException('FFMPEG return code %d', e.returncode)


        # set default permissions
        video_file_p.chmod(0o644)


    def _ffmpeg_command(self, video_file_p, input_arguments):
        cmd = [self.ffmpeg_bin]


        # add codec options
        if self.codec in ['h264_qsv']:
            ### Intel QSV
            cmd.extend(['-init_hw_device', 'qsv=hw', '-filter_hw_device', 'hw'])
        elif self.codec in ['h264_nvenc']:
            ### Nvidia NVENC
            #cmd.extend([])  # nothing to add currently
            pass
        elif self.codec in ['h264_vaapi']:
            ### AMD VAAPI
            #cmd.extend([])  # nothing to add currently
            pass


        cmd.extend([
            '-y',
            '-loglevel', 'level+error',
            '-r', '{0:0.2f}'.format(self.framerate),
        ])
        cmd.extend(input_arguments)
        cmd.extend([
            '-c:v', '{0:s}'.format(self.codec),
            '-b:v', '{0:s}'.format(self.bitrate),
            #'-filter:v', 'setpts=50*PTS',
            '-pix_fmt', 'yuv420p',
            '-movflags', '+faststart',
        ])


        cmd.extend(video_filter_arguments(self.config, self.vf_scale, self.ffmpeg_extra_options))


        # finally add filename
        cmd.append('{0:s}'.format(str(video_file_p)))

        return cmd

    def generate_entries(self, video_file, entries, media_root, fits_lookup):
        """Preserve the legacy path when display files exist; stream source frames."""
        from .generation_frames import read_generation_frame
        from .timelapse_stream import encode_stream
        import cv2

        eligible = []
        needs_source = False
        for entry in entries:
            path = Path(entry.getFilesystemPath())
            if path.exists():
                if path.stat().st_size:
                    eligible.append((entry, path))
            elif (entry.data or {}).get('render_source') is not None:
                eligible.append((entry, path))
                needs_source = True
            else:
                logger.error('File not found: %s', path)
        if not needs_source:
            return self.generate(video_file, [path for _, path in eligible])
        ordered = sorted(eligible, key=lambda item: (item[0].createDate, item[0].id))
        ordered = ordered[self.skip_frames:]
        if not ordered:
            raise TimelapseException('No frames remain after timelapse selection')
        wrap_args = None
        if hasattr(self.pre_processor, 'prepare'):
            wrap_args = self.pre_processor.prepare(len(ordered))

        def frames():
            for index, (entry, _) in enumerate(ordered):
                frame = read_generation_frame(entry, media_root, fits_lookup)
                if frame is None:
                    raise TimelapseException('A selected timelapse frame is no longer readable')
                _, pixels, _ = frame
                if wrap_args is not None:
                    pixels = self.pre_processor.wrap(index, None, None, *wrap_args,
                                                     image=pixels, return_pixels=True)
                ok, encoded = cv2.imencode('.png', pixels)
                if not ok:
                    raise TimelapseException('Unable to encode timelapse frame')
                yield encoded.tobytes()

        command = self._ffmpeg_command(Path(video_file),
            ['-f', 'image2pipe', '-vcodec', 'png', '-i', 'pipe:0'])
        env = {}
        if self.config.get('TIMELAPSE', {}).get('FFMPEG_REPORT'):
            env['FFREPORT'] = 'file={0:s}/ffmpeg-report-%t.log'.format(os.environ['HOME'])
        encode_stream(command, frames(), video_file, env)
