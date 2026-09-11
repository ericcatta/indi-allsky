"""Frozen ConfigView display/encoding blocks from 4dbf79f2; preserve evaluation order."""
import json

def legacy_apply_full_config_form_display_fields(self, form_data):
    # ADU_ROI
    ADU_ROI = self.indi_allsky_config.get('ADU_ROI', [])
    if ADU_ROI is None:
        ADU_ROI = []
    elif isinstance(ADU_ROI, bool):
        ADU_ROI = []

    try:
        form_data['ADU_ROI_X1'] = ADU_ROI[0]
    except IndexError:
        form_data['ADU_ROI_X1'] = 0

    try:
        form_data['ADU_ROI_Y1'] = ADU_ROI[1]
    except IndexError:
        form_data['ADU_ROI_Y1'] = 0

    try:
        form_data['ADU_ROI_X2'] = ADU_ROI[2]
    except IndexError:
        form_data['ADU_ROI_X2'] = 0

    try:
        form_data['ADU_ROI_Y2'] = ADU_ROI[3]
    except IndexError:
        form_data['ADU_ROI_Y2'] = 0


    # SQM_ROI
    SQM_ROI = self.indi_allsky_config.get('SQM_ROI', [])
    if SQM_ROI is None:
        SQM_ROI = []
    elif isinstance(SQM_ROI, bool):
        SQM_ROI = []

    try:
        form_data['SQM_ROI_X1'] = SQM_ROI[0]
    except IndexError:
        form_data['SQM_ROI_X1'] = 0

    try:
        form_data['SQM_ROI_Y1'] = SQM_ROI[1]
    except IndexError:
        form_data['SQM_ROI_Y1'] = 0

    try:
        form_data['SQM_ROI_X2'] = SQM_ROI[2]
    except IndexError:
        form_data['SQM_ROI_X2'] = 0

    try:
        form_data['SQM_ROI_Y2'] = SQM_ROI[3]
    except IndexError:
        form_data['SQM_ROI_Y2'] = 0


    # IMAGE_CROP_ROI
    IMAGE_CROP_ROI = self.indi_allsky_config.get('IMAGE_CROP_ROI', [])
    if IMAGE_CROP_ROI is None:
        IMAGE_CROP_ROI = []
    elif isinstance(IMAGE_CROP_ROI, bool):
        IMAGE_CROP_ROI = []

    try:
        form_data['IMAGE_CROP_ROI_X1'] = IMAGE_CROP_ROI[0]
    except IndexError:
        form_data['IMAGE_CROP_ROI_X1'] = 0

    try:
        form_data['IMAGE_CROP_ROI_Y1'] = IMAGE_CROP_ROI[1]
    except IndexError:
        form_data['IMAGE_CROP_ROI_Y1'] = 0

    try:
        form_data['IMAGE_CROP_ROI_X2'] = IMAGE_CROP_ROI[2]
    except IndexError:
        form_data['IMAGE_CROP_ROI_X2'] = 0

    try:
        form_data['IMAGE_CROP_ROI_Y2'] = IMAGE_CROP_ROI[3]
    except IndexError:
        form_data['IMAGE_CROP_ROI_Y2'] = 0


    # Font color
    text_properties__font_color = self.indi_allsky_config.get('TEXT_PROPERTIES', {}).get('FONT_COLOR', [200, 200, 200])
    form_data['TEXT_PROPERTIES__FONT_COLOR'] = ','.join([str(x) for x in text_properties__font_color])

    # Cardinal directions color
    cardinal_dirs__font_color = self.indi_allsky_config.get('CARDINAL_DIRS', {}).get('FONT_COLOR', [200, 0, 0])
    form_data['CARDINAL_DIRS__FONT_COLOR'] = ','.join([str(x) for x in cardinal_dirs__font_color])

    # Sun orb color
    orb_properties__sun_color = self.indi_allsky_config.get('ORB_PROPERTIES', {}).get('SUN_COLOR', [200, 200, 100])
    form_data['ORB_PROPERTIES__SUN_COLOR'] = ','.join([str(x) for x in orb_properties__sun_color])

    # Moon orb color
    orb_properties__moon_color = self.indi_allsky_config.get('ORB_PROPERTIES', {}).get('MOON_COLOR', [128, 128, 128])
    form_data['ORB_PROPERTIES__MOON_COLOR'] = ','.join([str(x) for x in orb_properties__moon_color])

    # Border color
    image_border__color = self.indi_allsky_config.get('IMAGE_BORDER', {}).get('COLOR', [0, 0, 0])
    form_data['IMAGE_BORDER__COLOR'] = ','.join([str(x) for x in image_border__color])

    # Lightgraph colors
    lightgraph_overlay__day_color = self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('DAY_COLOR', [150, 150, 150])
    form_data['LIGHTGRAPH_OVERLAY__DAY_COLOR'] = ','.join([str(x) for x in lightgraph_overlay__day_color])

    lightgraph_overlay__dusk_color = self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('DUSK_COLOR', [200, 100, 60])
    form_data['LIGHTGRAPH_OVERLAY__DUSK_COLOR'] = ','.join([str(x) for x in lightgraph_overlay__dusk_color])

    lightgraph_overlay__night_color = self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('NIGHT_COLOR', [30, 30, 30])
    form_data['LIGHTGRAPH_OVERLAY__NIGHT_COLOR'] = ','.join([str(x) for x in lightgraph_overlay__night_color])

    lightgraph_overlay__moonmode_color = self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('MOONMODE_COLOR', [50, 50, 50])
    form_data['LIGHTGRAPH_OVERLAY__MOONMODE_COLOR'] = ','.join([str(x) for x in lightgraph_overlay__moonmode_color])

    lightgraph_overlay__hour_color = self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('HOUR_COLOR', [100, 15, 15])
    form_data['LIGHTGRAPH_OVERLAY__HOUR_COLOR'] = ','.join([str(x) for x in lightgraph_overlay__hour_color])

    lightgraph_overlay__border_color = self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('BORDER_COLOR', [1, 1, 1])
    form_data['LIGHTGRAPH_OVERLAY__BORDER_COLOR'] = ','.join([str(x) for x in lightgraph_overlay__border_color])

    lightgraph_overlay__now_color = self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('NOW_COLOR', [120, 120, 200])
    form_data['LIGHTGRAPH_OVERLAY__NOW_COLOR'] = ','.join([str(x) for x in lightgraph_overlay__now_color])

    lightgraph_overlay__font_color = self.indi_allsky_config.get('LIGHTGRAPH_OVERLAY', {}).get('FONT_COLOR', [150, 150, 150])
    form_data['LIGHTGRAPH_OVERLAY__FONT_COLOR'] = ','.join([str(x) for x in lightgraph_overlay__font_color])


    # Youtube
    youtube_tags = self.indi_allsky_config.get('YOUTUBE', {}).get('TAGS', [])
    form_data['YOUTUBE__TAGS_STR'] = ', '.join(youtube_tags)
    return form_data


def legacy_apply_full_config_form_encoded_fields(self, form_data):
    # FITS headers
    fitsheaders = self.indi_allsky_config.get('FITSHEADERS', [])

    try:
        form_data['FITSHEADERS__0__KEY'] = str(fitsheaders[0][0]).upper()
        form_data['FITSHEADERS__0__VAL'] = str(fitsheaders[0][1])
    except IndexError:
        form_data['FITSHEADERS__0__KEY'] = 'INSTRUME'
        form_data['FITSHEADERS__0__VAL'] = 'indi-allsky'

    try:
        form_data['FITSHEADERS__1__KEY'] = str(fitsheaders[1][0]).upper()
        form_data['FITSHEADERS__1__VAL'] = str(fitsheaders[1][1])
    except IndexError:
        form_data['FITSHEADERS__1__KEY'] = 'OBSERVER'
        form_data['FITSHEADERS__1__VAL'] = ''

    try:
        form_data['FITSHEADERS__2__KEY'] = str(fitsheaders[2][0]).upper()
        form_data['FITSHEADERS__2__VAL'] = str(fitsheaders[2][1])
    except IndexError:
        form_data['FITSHEADERS__2__KEY'] = 'SITE'
        form_data['FITSHEADERS__2__VAL'] = ''

    try:
        form_data['FITSHEADERS__3__KEY'] = str(fitsheaders[3][0]).upper()
        form_data['FITSHEADERS__3__VAL'] = str(fitsheaders[3][1])
    except IndexError:
        form_data['FITSHEADERS__3__KEY'] = 'OBJECT'
        form_data['FITSHEADERS__3__VAL'] = ''

    try:
        form_data['FITSHEADERS__4__KEY'] = str(fitsheaders[4][0]).upper()
        form_data['FITSHEADERS__4__VAL'] = str(fitsheaders[4][1])
    except IndexError:
        form_data['FITSHEADERS__4__KEY'] = 'NOTES'
        form_data['FITSHEADERS__4__VAL'] = ''


    # libcurl options as json text
    filetransfer__libcurl_options = self.indi_allsky_config.get('FILETRANSFER', {}).get('LIBCURL_OPTIONS', {'VERBOSE' : 0})
    form_data['FILETRANSFER__LIBCURL_OPTIONS'] = json.dumps(filetransfer__libcurl_options, indent=4)


    # INDI config as json text
    indi_config_defaults = self.indi_allsky_config.get('INDI_CONFIG_DEFAULTS', {})
    form_data['INDI_CONFIG_DEFAULTS'] = json.dumps(indi_config_defaults, indent=4)

    indi_config_day = self.indi_allsky_config.get('INDI_CONFIG_DAY', {})
    form_data['INDI_CONFIG_DAY'] = json.dumps(indi_config_day, indent=4)
    return form_data


