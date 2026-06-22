import time
from pathlib import Path
import cv2
import numpy
import logging


logger = logging.getLogger('indi_allsky')


class IndiAllSkyStars(object):

    _distanceThreshold = 10


    def __init__(self, config, mask=None):
        self.config = config

        self._sqm_mask_dict = mask

        self._star_mask_dict = dict()
        for binning in self._sqm_mask_dict.keys():
            self._star_mask_dict[binning] = None


        self._detectionThreshold = self.config.get('DETECT_STARS_THOLD', 0.6)

        if self.config['IMAGE_FOLDER']:
            self.image_dir = Path(self.config['IMAGE_FOLDER']).absolute()
        else:
            self.image_dir = Path(__file__).parent.parent.joinpath('html', 'images').absolute()


        # start with a black image
        star_template = numpy.zeros([15, 15], dtype=numpy.uint8)

        # draw a white circle
        cv2.circle(
            img=star_template,
            center=(7, 7),
            radius=3,
            color=255,  # mono
            thickness=cv2.FILLED,
        )

        # blur circle to simulate a star
        self.star_template = cv2.blur(
            src=star_template,
            ksize=(2, 2),
        )

        self.star_template_w, self.star_template_h = self.star_template.shape[::-1]


    def detectObjects(self, original_data, binning):
        image_shape = original_data.shape[:2]

        if binning not in self._star_mask_dict:
            logger.warning('No star mask cache entry for binning %s; generating star mask', binning)
            self._star_mask_dict[binning] = None


        if isinstance(self._star_mask_dict[binning], type(None)):
            # This only needs to be done once if a mask is not provided
            self._generateStarMask(original_data, binning)

        star_mask = self._star_mask_dict[binning]
        if star_mask is None:
            logger.warning(
                'Star mask is not available for binning %s, image_shape=%s; using unmasked image',
                binning,
                image_shape,
            )
            masked_img = original_data
        elif star_mask.dtype not in (numpy.uint8, numpy.int8):
            logger.warning(
                'Star mask has incompatible dtype %s for binning %s, mask_shape=%s, image_shape=%s; using unmasked image',
                star_mask.dtype,
                binning,
                star_mask.shape,
                image_shape,
            )
            masked_img = original_data
        elif star_mask.shape[:2] != image_shape:
            logger.warning(
                'Star mask shape %s does not match image shape %s for binning %s; regenerating star mask',
                star_mask.shape,
                image_shape,
                binning,
            )
            self._star_mask_dict[binning] = None
            self._generateStarMask(original_data, binning)

            star_mask = self._star_mask_dict[binning]
            if star_mask is None or star_mask.dtype not in (numpy.uint8, numpy.int8) or star_mask.shape[:2] != image_shape:
                logger.warning(
                    'Regenerated star mask is still incompatible for binning %s, mask_shape=%s, image_shape=%s; using unmasked image',
                    binning,
                    None if star_mask is None else star_mask.shape,
                    image_shape,
                )
                masked_img = original_data
            else:
                masked_img = cv2.bitwise_and(original_data, original_data, mask=star_mask)
        else:
            masked_img = cv2.bitwise_and(original_data, original_data, mask=star_mask)

        if len(original_data.shape) == 2:
            # gray scale or bayered
            grey_img = masked_img
        else:
            # assume color
            grey_img = cv2.cvtColor(masked_img, cv2.COLOR_BGR2GRAY)


        sep_start = time.time()


        result = cv2.matchTemplate(grey_img, self.star_template, cv2.TM_CCOEFF_NORMED)
        result_filter = numpy.where(result >= self._detectionThreshold)

        blobs = list()
        for pt in zip(*result_filter[::-1]):
            for blob in blobs:
                if (abs(pt[0] - blob[0]) < self._distanceThreshold) and (abs(pt[1] - blob[1]) < self._distanceThreshold):
                    break

            else:
                # if none of the points are under the distance threshold, then add it
                blobs.append(pt)


        sep_elapsed_s = time.time() - sep_start
        logger.info('Detected %d stars in %0.4f s', len(blobs), sep_elapsed_s)

        self._drawCircles(original_data, blobs)

        return blobs


    def _generateStarMask(self, img, binning):
        logger.info('Generating mask based on SQM_ROI')


        sqm_mask = self._sqm_mask_dict.get(binning)
        if not isinstance(sqm_mask, type(None)):
            if sqm_mask.dtype in (numpy.uint8, numpy.int8) and sqm_mask.shape[:2] == img.shape[:2]:
                self._star_mask_dict[binning] = sqm_mask
                return

            logger.warning(
                'Ignoring incompatible SQM star mask for binning %s, mask_shape=%s, mask_dtype=%s, image_shape=%s',
                binning,
                sqm_mask.shape,
                sqm_mask.dtype,
                img.shape[:2],
            )
        elif binning not in self._sqm_mask_dict:
            logger.warning('No SQM mask cache entry for binning %s; generating central star mask', binning)


        image_height, image_width = img.shape[:2]

        # create a black background
        mask = numpy.zeros((image_height, image_width), dtype=numpy.uint8)

        sqm_roi = self.config.get('SQM_ROI', [])

        try:
            x1 = int(sqm_roi[0] / binning)
            y1 = int(sqm_roi[1] / binning)
            x2 = int(sqm_roi[2] / binning)
            y2 = int(sqm_roi[3] / binning)
        except IndexError:
            logger.warning('Using central ROI for star detection')
            sqm_fov_div = self.config.get('SQM_FOV_DIV', 4)
            x1 = int((image_width / 2) - (image_width / sqm_fov_div))
            y1 = int((image_height / 2) - (image_height / sqm_fov_div))
            x2 = int((image_width / 2) + (image_width / sqm_fov_div))
            y2 = int((image_height / 2) + (image_height / sqm_fov_div))

        # The white area is what we keep
        cv2.rectangle(
            img=mask,
            pt1=(x1, y1),
            pt2=(x2, y2),
            color=255,  # mono
            thickness=cv2.FILLED,
        )

        self._star_mask_dict[binning] = mask


    def _drawCircles(self, sep_data, blob_list):
        if not self.config.get('DETECT_DRAW'):
            return

        image_height, image_width = sep_data.shape[:2]

        color_bgr = list(self.config['TEXT_PROPERTIES']['FONT_COLOR'])
        color_bgr.reverse()

        logger.info('Draw circles around objects')
        for blob in blob_list:
            x, y = blob

            center = (
                int(x + (self.star_template_w / 2)) + 1,
                int(y + (self.star_template_h / 2)) + 1,
            )

            cv2.circle(
                img=sep_data,
                center=center,
                radius=6,
                color=tuple(color_bgr),
                #thickness=cv2.FILLED,
                thickness=1,
            )
