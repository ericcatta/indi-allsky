"""Shared frame rendering stages for capture and source-backed derivatives.

The caller supplies a prepared processor and the acquisition context. These stages
never meter exposure, persist files, update keograms or enqueue output tasks.
Their boundaries preserve capture's existing intermediate consumers and order.
"""
from . import constants

def render_tone(processor, config, night_av):
    processor.denoise()

    processor.stretch()


    if config.get('CONTRAST_ENHANCE_16BIT'):
        if not night_av[constants.NIGHT_NIGHT] and config['DAYTIME_CONTRAST_ENHANCE']:
            # Contrast enhancement during the day
            processor.contrast_clahe_16bit()
        elif night_av[constants.NIGHT_NIGHT] and config['NIGHT_CONTRAST_ENHANCE']:
            # Contrast enhancement during night
            processor.contrast_clahe_16bit()


    processor.convert_16bit_to_8bit()


def render_geometry_and_color(processor, config, night_av):
    # rotation
    processor.rotate_90()
    processor.rotate_angle()


    # verticle flip
    processor.flip_v()

    # horizontal flip
    processor.flip_h()


    # crop
    processor.crop_image()


    # green removal
    processor.scnr()


    # white balance
    processor.white_balance_mtf()
    processor.white_balance_manual_bgr()
    processor.white_balance_auto_bgr()


    # saturation
    processor.saturation_adjust()


    # gamma correction
    processor.apply_gamma_correction()


    # sharpening (unsharp mask)
    processor.sharpen()


    if not config.get('CONTRAST_ENHANCE_16BIT'):
        if not night_av[constants.NIGHT_NIGHT] and config['DAYTIME_CONTRAST_ENHANCE']:
            # Contrast enhancement during the day
            processor.contrast_clahe()
        elif night_av[constants.NIGHT_NIGHT] and config['NIGHT_CONTRAST_ENHANCE']:
            # Contrast enhancement during night
            processor.contrast_clahe()


    processor.colorize()


def render_presentation(processor, binning):
    processor.apply_logo_overlay(binning)


    processor.scale_image()


    processor.add_border()

    processor.moon_overlay()

    processor.lightgraph_overlay()

    processor.image_overlay()

    processor.orb_image()

    processor.cardinal_dirs_label()


