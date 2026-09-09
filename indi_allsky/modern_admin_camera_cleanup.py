"""Camera-scoped cleanup selection; filesystem effects remain shared adapters."""
from datetime import timedelta


IMAGE_FAMILIES = ('Image', 'FitsImage', 'RawImage', 'PanoramaImage')
OUTPUT_FAMILIES = ('Video', 'MiniVideo', 'Keogram', 'StarTrails', 'StarTrailsVideo', 'PanoramaVideo')
DAY_FAMILIES = IMAGE_FAMILIES + ('Video', 'Keogram', 'PanoramaVideo')
ACTION_FAMILIES = {
    'flush_images': IMAGE_FAMILIES,
    'flush_16min_images': ('Image',),
    'flush_timelapses': OUTPUT_FAMILIES,
    'flush_daytime': DAY_FAMILIES,
}

CLEANUP_ACTIONS = (
    ('flush_images', 'Delete all images', 'Images, FITS, RAW and panorama images, at every date.'),
    ('flush_16min_images', 'Delete recent images', 'Processed images from the last 16 minutes. FITS, RAW and panoramas are kept.'),
    ('flush_timelapses', 'Delete generated outputs', 'Timelapses, mini timelapses, keograms, startrails, startrail videos and panorama videos, at every date.'),
    ('flush_daytime', 'Delete daytime media', 'Daytime images, FITS, RAW, panoramas, timelapses, keograms and panorama videos. Mini timelapses and startrails are kept.'),
)


def build_cleanup_queries(command, camera_id, models, now):
    families = ACTION_FAMILIES[command]
    camera = models['Camera']
    result = []
    for family in families:
        table = models[family]
        query = table.query.join(table.camera).filter(camera.id == camera_id)
        if command == 'flush_daytime':
            query = query.filter(table.night == False)  # SQL boolean comparison, preserving legacy selection.
        elif command == 'flush_16min_images':
            query = query.filter(table.createDate >= now - timedelta(minutes=16))
        result.append((query.order_by(table.createDate.asc()), table))
    return result
