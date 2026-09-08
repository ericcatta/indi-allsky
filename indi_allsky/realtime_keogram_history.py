"""Validate persisted realtime columns and their matching timestamp sequence."""


def load_realtime_keogram_history(data_path, metadata_path):
    import numpy

    with open(data_path, 'rb') as stream:
        data = numpy.load(stream, allow_pickle=False)
    with open(metadata_path, 'rb') as stream:
        metadata = numpy.load(stream, allow_pickle=False)
    if not isinstance(data, numpy.ndarray) or not isinstance(metadata, numpy.ndarray):
        raise ValueError('Realtime history must contain NumPy arrays')
    if data.ndim not in (2, 3) or not data.shape[0] or not data.shape[1]:
        raise ValueError('Realtime history contains no image columns')
    if metadata.ndim != 2 or metadata.shape != (1, data.shape[1]):
        raise ValueError('Realtime history columns and timestamps do not match')
    if metadata.dtype.kind not in 'ui':
        raise ValueError('Realtime history timestamps must be integers')
    return data, metadata[0]
