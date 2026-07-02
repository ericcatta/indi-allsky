import math


class ModernAdminCameraInfoService:
    arcsec_pix_factor = 1.2

    def __init__(self, cfa_map=None):
        self.cfa_map = cfa_map or {}


    def build_context(self, camera, privacy_mode=False):
        lens_aperture = camera.lensFocalLength / camera.lensFocalRatio
        camera_width_mm = camera.width * camera.pixelSize / 1000.0
        camera_height_mm = camera.height * camera.pixelSize / 1000.0
        camera_diagonal_mm = math.hypot(camera_width_mm, camera_height_mm)
        arcsec_pixel = camera.pixelSize / camera.lensFocalLength * 206.2648
        image_circle_diameter = int(camera.lensImageCircle)
        image_circle_diameter_mm = image_circle_diameter * camera.pixelSize / 1000.0
        deg_fov_width, deg_fov_height, deg_fov_diagonal = self.calculate_field_of_view(
            camera=camera,
            image_circle_diameter=image_circle_diameter,
            arcsec_pixel=arcsec_pixel,
        )

        return {
            'camera'                  : camera,
            'owner'                   : 'Private' if privacy_mode else camera.owner,
            'camera_cfa'              : self.cfa_map[camera.cfa],
            'lensAperture'            : lens_aperture,
            'camera_width_mm'         : camera_width_mm,
            'camera_height_mm'        : camera_height_mm,
            'camera_diagonal_mm'      : camera_diagonal_mm,
            'arcsec_pixel'            : arcsec_pixel,
            'dms_pixel'               : self.decdeg2dms(arcsec_pixel / 3600.0),
            'arcsec_um'               : arcsec_pixel / camera.pixelSize,
            'deg2_px'                 : (arcsec_pixel / 3600) ** 2,
            'image_circle_diameter'   : image_circle_diameter,
            'image_circle_diameter_mm': image_circle_diameter_mm,
            'deg_fov_width'           : deg_fov_width,
            'deg_fov_height'          : deg_fov_height,
            'deg_fov_diagonal'        : deg_fov_diagonal,
        }


    def calculate_field_of_view(self, camera, image_circle_diameter, arcsec_pixel):
        camera_diagonal = math.hypot(camera.width, camera.height)
        arcsec_fov_width = min(image_circle_diameter, camera.width) * arcsec_pixel * self.arcsec_pix_factor
        arcsec_fov_height = min(image_circle_diameter, camera.height) * arcsec_pixel * self.arcsec_pix_factor
        arcsec_fov_diagonal = min(image_circle_diameter, camera_diagonal) * arcsec_pixel * self.arcsec_pix_factor

        return (
            arcsec_fov_width / 3600,
            arcsec_fov_height / 3600,
            arcsec_fov_diagonal / 3600,
        )


    def decdeg2dms(self, dd):
        is_positive = dd >= 0
        dd = abs(dd)
        minutes, seconds = divmod(dd * 3600, 60)
        degrees, minutes = divmod(minutes, 60)
        degrees = degrees if is_positive else -degrees
        return degrees, minutes, seconds
