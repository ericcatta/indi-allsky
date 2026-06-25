from .scientific_frame import ScientificFrame


class ScientificFrameProvider:
    """Offline/read-only converter from frame metadata to ScientificFrame.

    The provider prepares future sequence-oriented access to scientific frames
    without reading files, querying the database, or promoting display images to
    detector input.
    """

    def from_frame_metadata(self, frame_metadata):
        return ScientificFrame.from_frame_metadata(self._scientific_metadata(frame_metadata))

    def from_frame_metadata_list(self, frame_metadata_list):
        return [
            self.from_frame_metadata(frame_metadata)
            for frame_metadata in frame_metadata_list
        ]

    def _scientific_metadata(self, frame_metadata):
        fits_path = self._value(frame_metadata, 'fits_path')
        raw_path = self._value(frame_metadata, 'raw_path')
        source_image_path = fits_path or raw_path or None
        detector_image_path = source_image_path
        detector_image_type = None

        if fits_path:
            detector_image_type = self._value(frame_metadata, 'detector_image_type') or self._fits_type(fits_path)
        elif raw_path:
            detector_image_type = self._value(frame_metadata, 'detector_image_type') or self._raw_type(raw_path)

        data = self._as_dict(frame_metadata)
        data['source_image_path'] = source_image_path
        data['detector_image_path'] = detector_image_path
        data['detector_image_type'] = detector_image_type
        return data

    def _as_dict(self, frame_metadata):
        if isinstance(frame_metadata, dict):
            return dict(frame_metadata)

        to_dict = getattr(frame_metadata, 'to_dict', None)
        if callable(to_dict):
            return dict(to_dict())

        return dict(getattr(frame_metadata, '__dict__', {}))

    def _value(self, frame_metadata, name):
        if isinstance(frame_metadata, dict):
            return frame_metadata.get(name)
        return getattr(frame_metadata, name, None)

    def _fits_type(self, fits_path):
        fits_path_str = str(fits_path).lower()
        if fits_path_str.endswith('.gz'):
            return 'fits.gz'
        return 'fits'

    def _raw_type(self, raw_path):
        raw_path_str = str(raw_path).rsplit('.', 1)
        if len(raw_path_str) == 2 and raw_path_str[1]:
            return raw_path_str[1].lower()
        return None
