"""Authenticated FITS preview API, independent of frontend view classes."""
import base64
import math
from multiprocessing import Array

from flask import abort, current_app as app, jsonify, request
from flask_login import current_user, login_required
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException

from . import db
from .base_views import BaseView
from .forms import IndiAllskyImageProcessingForm
from .image_processing_config import REQUIRED_FIELDS, processing_config
from .models import IndiAllSkyDbFitsImageTable, IndiAllSkyDbDarkFrameTable, IndiAllSkyDbBadPixelMapTable
from .source_media_views import local_source_allowed, source_file_path
from ..exceptions import BadImage

FRAME_MODELS = {'light':IndiAllSkyDbFitsImageTable, 'dark':IndiAllSkyDbDarkFrameTable, 'bpm':IndiAllSkyDbBadPixelMapTable}


class JsonImageProcessingView(BaseView):
    methods = ['POST']
    decorators = [login_required]

    def dispatch_request(self):
        import cv2
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify(form_global=['Send a complete processing form.']), 400
        if any(isinstance(value,(dict,list)) for value in payload.values()):
            return jsonify(form_global=['Processing fields must contain scalar values.']), 400
        missing = set(REQUIRED_FIELDS).difference(payload)
        if missing:
            return jsonify(form_global=['Processing form is incomplete. Reload this page and try again.']), 400
        # File-selection privileges are checked before filesystem validators.
        if not app.config.get('LOGIN_DISABLED') and not current_user.is_admin:
            paths = {'IMAGE_EXTRA_TEXT':self.indi_allsky_config.get('IMAGE_EXTRA_TEXT',''),
                     'DETECT_MASK':self.indi_allsky_config.get('DETECT_MASK',''),
                     'TEXT_PROPERTIES__PIL_FONT_CUSTOM':self.indi_allsky_config.get('TEXT_PROPERTIES',{}).get('PIL_FONT_CUSTOM','')}
            if any(payload.get(key) not in ('',value) for key,value in paths.items()):
                return jsonify(form_global=['Only administrators may select a different server-side text, mask or font file.']), 403
        try:
            form = IndiAllskyImageProcessingForm(data=payload)
            valid = form.validate()
        except (TypeError,ValueError):
            return jsonify(form_global=['Processing parameters have invalid types.']), 400
        if not valid:
            return jsonify(dict(form.errors, form_global=['Please fix the highlighted processing parameters.'])), 400
        if any(isinstance(field.data,float) and not math.isfinite(field.data) for field in form):
            return jsonify(form_global=['Processing parameters must be finite numbers.']), 400
        try:
            return self.process(payload)
        except HTTPException as error:
            return jsonify(form_global=[error.description]), error.code
        except SQLAlchemyError:
            db.session.rollback()
            return jsonify(form_global=['Media metadata is temporarily unavailable. Try again later.']), 503
        except PermissionError:
            return jsonify(form_global=['The web service cannot read this source file.']), 403
        except FileNotFoundError:
            return jsonify(form_global=['A required source or calibration file is missing. Choose an available frame.']), 404
        except (BadImage, OSError, ValueError, TypeError, KeyError, cv2.error, ZeroDivisionError) as error:
            app.logger.warning('FITS preview failed: %s', type(error).__name__)
            return jsonify(form_global=['The preview could not be processed. Check the FITS file and processing parameters.']), 422

    def process(self, payload):
        import cv2
        from astropy.io import fits
        from ..processing import ImageProcessor
        from .image_processing_pipeline import process_preview
        try:
            camera_id, fits_id = int(payload['CAMERA_ID']), int(payload['FITS_ID'])
            if not 0 < camera_id <= 2**63-1 or not 0 < fits_id <= 2**63-1:
                raise ValueError()
        except (ValueError,TypeError):
            abort(400, description='Choose a valid camera and FITS frame.')
        model = FRAME_MODELS.get(payload['FRAME_TYPE'])
        if model is None:
            abort(400, description='Choose light, dark or bad-pixel-map frame type.')
        entry = model.query.filter_by(camera_id=camera_id,id=fits_id).first()
        if entry is None:
            abort(404, description='No matching FITS frame exists for this camera.')
        if not local_source_allowed(entry.camera,self.verify_admin_network):
            abort(403, description='Local FITS processing is unavailable under this camera’s media policy.')
        filename = source_file_path(entry,self.indi_allsky_config)
        config = processing_config(self.indi_allsky_config,payload)
        if payload['FRAME_TYPE'] != 'light' and config['IMAGE_STACK_COUNT'] > 1:
            abort(400, description='Stacking is available for light frames. Choose stack count 1 for dark frames or bad-pixel maps.')
        with fits.open(filename) as hdus:
            exposure = float(hdus[0].header.get('EXPTIME',0))
            gain = float(hdus[0].header.get('GAIN',0))
            binning = int(hdus[0].header.get('XBINNING',1))
        processor = ImageProcessor(config,
            Array('f',[entry.camera.latitude,entry.camera.longitude,entry.camera.elevation]),
            Array('f',[gain]),Array('i',[binning]),
            Array('f',[0.0]*60),Array('f',[0.0]*110),Array('i',[1,0]),Array('f',[0.0]*3))
        try:
            image, elapsed, messages = process_preview(processor,filename,exposure,gain,binning,entry,camera_id,config,bool(payload['DISABLE_PROCESSING']))
            if payload['OUTPUT_IMAGE_TYPE']=='png':
                extension,mime,parameter='.png','image/png',cv2.IMWRITE_PNG_COMPRESSION
                quality=config['IMAGE_FILE_COMPRESSION']['png']
            else:
                extension,mime,parameter='.jpg','image/jpeg',cv2.IMWRITE_JPEG_QUALITY
                quality=config['IMAGE_FILE_COMPRESSION']['jpg']
            success, encoded = cv2.imencode(extension,image,[parameter,quality])
            if not success:
                abort(422, description='The processed image could not be encoded.')
            return jsonify(image_b64=base64.b64encode(encoded.tobytes()).decode('ascii'),
                processing_elapsed_s=round(elapsed,3),message=', '.join(messages),
                mime_type=mime,width=image.shape[1],height=image.shape[0],camera_id=camera_id,fits_id=fits_id)
        finally:
            # The preview owns these image references; no worker shares them.
            for reference in processor.image_list:
                if reference is not None:
                    reference.hdulist.close()
            processor.image_list.clear()
