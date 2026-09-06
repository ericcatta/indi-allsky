"""Shared FITS preview pipeline; scientific stage order retained from the existing handler."""
import time
from datetime import datetime
from astropy.io import fits
from .models import IndiAllSkyDbFitsImageTable, IndiAllSkyDbCameraTable
from .source_media_views import source_file_path

def process_preview(image_processor, filename_p, exposure, gain, binning, fits_entry, camera_id, p_config, disable_processing):
    processing_start = time.time()

    message_list = list()

    if disable_processing:
        # just return original image with no processing

        # use mtime for date
        image_date = datetime.fromtimestamp(filename_p.stat().st_mtime)

        image_processor.add(
            filename_p,
            exposure,
            gain,
            binning,
            image_date,
            0.0,
            fits_entry.camera,
        )

        image_processor.debayer()  # populates self.opencv_data

        image_processor.stack()  # populates self.image

        image_processor.convert_16bit_to_8bit()

        # rotation
        image_processor.rotate_90()
        image_processor.rotate_angle()

        # verticle flip
        image_processor.flip_v()

        # horizontal flip
        image_processor.flip_h()

        image_processor.colorize()

        message_list.append('Unprocessed image')

    else:
        if p_config['IMAGE_STACK_COUNT'] > 1:
            fits_image_query = IndiAllSkyDbFitsImageTable.query\
                .join(IndiAllSkyDbFitsImageTable.camera)\
                .filter(IndiAllSkyDbCameraTable.id == camera_id)\
                .filter(IndiAllSkyDbFitsImageTable.id != fits_entry.id)\
                .filter(IndiAllSkyDbFitsImageTable.createDate < fits_entry.createDate)\
                .order_by(IndiAllSkyDbFitsImageTable.createDate.desc())\
                .limit(p_config['IMAGE_STACK_COUNT'] - 1)

            for f_image in fits_image_query:
                f_image_p = source_file_path(f_image, p_config)

                # use mtime for date
                pre_image_date = datetime.fromtimestamp(f_image_p.stat().st_mtime)

                with fits.open(f_image_p) as alt_hdulist:
                    alt_exposure = float(alt_hdulist[0].header.get('EXPTIME', 0))
                    alt_gain = float(alt_hdulist[0].header.get('GAIN', 0))
                    alt_binning = int(alt_hdulist[0].header.get('XBINNING', 1))

                i_ref_2 = image_processor.add(
                    f_image_p,
                    alt_exposure,
                    alt_gain,
                    alt_binning,
                    pre_image_date,
                    0.0,
                    f_image.camera,
                )

                image_processor._calibrate(i_ref_2)
                i_ref_2.opencv_data = image_processor._debayer(i_ref_2)  # update opencv_data



        # use mtime for date
        image_date = datetime.fromtimestamp(filename_p.stat().st_mtime)

        image_processor.update_astrometric_data(image_date)

        # add image after preloading other images
        i_ref = image_processor.add(
            filename_p,
            exposure,
            gain,
            binning,
            datetime.now(),
            0.0,
            fits_entry.camera,
        )

        if p_config['IMAGE_STACK_COUNT'] > 1:
            message_list.append('Stacked {0:d} images (requested {1:d})'.format(
                sum(reference is not None for reference in image_processor.image_list), p_config['IMAGE_STACK_COUNT']))

        image_processor.calibrate()

        image_processor.fix_holes_early()

        image_processor.debayer()  # populates self.opencv_data

        image_processor.stack()  # populates self.image

        image_processor.denoise()

        image_processor.stretch()

        if p_config['NIGHT_CONTRAST_ENHANCE']:
            if p_config.get('CONTRAST_ENHANCE_16BIT'):
                image_processor.contrast_clahe_16bit()

                message_list.append('16-bit CLAHE')

        image_processor.convert_16bit_to_8bit()

        if p_config.get('IMAGE_ROTATE'):
            image_processor.rotate_90()

        # rotation
        if p_config.get('IMAGE_ROTATE_ANGLE'):
            image_processor.rotate_angle()

        # verticle flip
        if p_config.get('IMAGE_FLIP_V'):
            image_processor.flip_v()

        # horizontal flip
        if p_config.get('IMAGE_FLIP_H'):
            image_processor.flip_h()

        # crop
        image_processor.crop_image()

        # green removal
        image_processor.scnr()

        # white balance
        image_processor.white_balance_mtf()
        image_processor.white_balance_manual_bgr()
        image_processor.white_balance_auto_bgr()

        # saturation
        image_processor.saturation_adjust()

        # gamma correction
        image_processor.apply_gamma_correction()

        # sharpening (unsharp mask)
        image_processor.sharpen()

        if p_config['NIGHT_CONTRAST_ENHANCE']:
            if not p_config.get('CONTRAST_ENHANCE_16BIT'):
                image_processor.contrast_clahe()

                message_list.append('CLAHE Contrast Enhance')

        image_processor.colorize()

        image_processor.colormap()

        image_processor.apply_image_circle_mask(i_ref.binning)

        if not p_config.get('FISH2PANO', {}).get('ENABLE'):
            image_processor.add_border()

            image_processor.moon_overlay()

            image_processor.lightgraph_overlay()

            image_processor.cardinal_dirs_label()

            if p_config['IMAGE_LABEL_SYSTEM']:
                image_processor.label_image()

        else:
            # no labels if converting to panorama
            pano_data = image_processor.fish2pano(i_ref.binning)

            if p_config.get('FISH2PANO', {}).get('FLIP_H'):
                pano_data = image_processor._flip(pano_data, 1)

            if p_config.get('FISH2PANO', {}).get('ENABLE_CARDINAL_DIRS'):
                pano_data = image_processor.fish2pano_cardinal_dirs_label(pano_data)

            image_processor.image = pano_data

    processing_elapsed_s = time.time() - processing_start
    return image_processor.image, processing_elapsed_s, message_list
