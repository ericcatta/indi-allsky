import math
from datetime import datetime, timedelta


IMAGE_LAG_LOOKBACK_HOURS = 3
IMAGE_LAG_ROW_LIMIT = 50


class ModernAdminCameraInfoService:
    arcsec_pix_factor = 1.2

    def __init__(self, cfa_map=None):
        self.cfa_map = cfa_map or {}


    def build_context(self, camera, privacy_mode=False):
        width, height, pixel_size, focal_length, focal_ratio, circle = (
            self.positive_measurement(getattr(camera, key, None)) for key in
            ('width', 'height', 'pixelSize', 'lensFocalLength', 'lensFocalRatio', 'lensImageCircle')
        )
        lens_aperture = focal_length / focal_ratio if focal_length and focal_ratio else None
        camera_width_mm = width * pixel_size / 1000.0 if width and pixel_size else None
        camera_height_mm = height * pixel_size / 1000.0 if height and pixel_size else None
        camera_diagonal_mm = (math.hypot(camera_width_mm, camera_height_mm)
                              if camera_width_mm and camera_height_mm else None)
        arcsec_pixel = pixel_size / focal_length * 206.2648 if pixel_size and focal_length else None
        image_circle_diameter = int(circle) if circle else None
        image_circle_diameter_mm = (image_circle_diameter * pixel_size / 1000.0
                                    if image_circle_diameter and pixel_size else None)
        deg_fov_width, deg_fov_height, deg_fov_diagonal = self.calculate_field_of_view(
            camera=camera,
            image_circle_diameter=image_circle_diameter,
            arcsec_pixel=arcsec_pixel,
        )

        return {
            'camera'                  : camera,
            'owner'                   : 'Private' if privacy_mode else camera.owner,
            'camera_cfa'              : self.cfa_map.get(camera.cfa, 'Unknown'),
            'lensAperture'            : lens_aperture,
            'camera_width_mm'         : camera_width_mm,
            'camera_height_mm'        : camera_height_mm,
            'camera_diagonal_mm'      : camera_diagonal_mm,
            'arcsec_pixel'            : arcsec_pixel,
            'dms_pixel'               : self.decdeg2dms(arcsec_pixel / 3600.0) if arcsec_pixel is not None else None,
            'arcsec_um'               : arcsec_pixel / pixel_size if arcsec_pixel is not None else None,
            'deg2_px'                 : (arcsec_pixel / 3600) ** 2 if arcsec_pixel is not None else None,
            'image_circle_diameter'   : image_circle_diameter,
            'image_circle_diameter_mm': image_circle_diameter_mm,
            'deg_fov_width'           : deg_fov_width,
            'deg_fov_height'          : deg_fov_height,
            'deg_fov_diagonal'        : deg_fov_diagonal,
        }


    def calculate_field_of_view(self, camera, image_circle_diameter, arcsec_pixel):
        width = self.positive_measurement(camera.width)
        height = self.positive_measurement(camera.height)
        diagonal = math.hypot(width, height) if width and height else None

        def field_of_view(dimension):
            if not dimension or not image_circle_diameter or arcsec_pixel is None:
                return None
            return min(image_circle_diameter, dimension) * arcsec_pixel * self.arcsec_pix_factor / 3600

        return tuple(field_of_view(dimension) for dimension in (width, height, diagonal))

    @staticmethod
    def positive_measurement(value):
        """Unknown sensor/lens metadata must not become a zero measurement."""
        if isinstance(value, (int, float)) and math.isfinite(value) and value > 0:
            return value
        return None


    def decdeg2dms(self, dd):
        is_positive = dd >= 0
        dd = abs(dd)
        minutes, seconds = divmod(dd * 3600, 60)
        degrees, minutes = divmod(minutes, 60)
        degrees = degrees if is_positive else -degrees
        return degrees, minutes, seconds


class ModernAdminImageLagPolicy:
    def __init__(self, lookback_hours=IMAGE_LAG_LOOKBACK_HOURS, row_limit=IMAGE_LAG_ROW_LIMIT):
        self.lookback_hours = lookback_hours
        self.row_limit = row_limit


    def window_start(self, timestamp_datetime):
        return timestamp_datetime - timedelta(hours=self.lookback_hours)

    def window_end(self, timestamp, camera_now, camera_time_offset):
        if not timestamp:
            return camera_now
        return datetime.fromtimestamp(timestamp) + timedelta(seconds=camera_time_offset)


class ModernAdminAduHistoryPolicy:
    """Seven camera-local days ending at now or an explicit navigation time."""

    def window_bounds(self, timestamp, camera_now, camera_time_offset):
        end = (datetime.fromtimestamp(timestamp) + timedelta(seconds=camera_time_offset)
               if timestamp else camera_now)
        return end - timedelta(days=7), end
