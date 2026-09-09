"""Field selections for focused views of the unchanged Full Config editor."""
from fnmatch import fnmatchcase

SETTINGS_DOMAINS = {
    'storage': ('Storage', ('HEALTHCHECK__DISK_USAGE', 'VARLIB_FOLDER', 'IMAGE_FOLDER', 'IMAGE_EXPORT_FOLDER', 'IMAGE_*EXPIRE_DAYS', 'TIMELAPSE_EXPIRE_DAYS', 'FILETRANSFER__REMOTE_DB_BACKUP_FOLDER')),
    'analytics': ('Analytics', ('CHARTS__CUSTOM_SLOT_*', 'ADU_ROI_*', 'ADU_FOV_DIV', 'SQM_ROI_*', 'SQM_FOV_DIV', 'CAMERA_SQM__*')),
    'acquisition-save': ('Acquisition and Save', ('DAYTIME_CAPTURE', 'IMAGE_FILE_*', 'LIBCAMERA__IMAGE_FILE_TYPE*', 'PYCURL_CAMERA__IMAGE_FILE_TYPE', 'IMAGE_SAVE_*', 'IMAGE_EXPORT_RAW', 'FITSHEADERS__*', 'IMAGE_FOLDER', 'IMAGE_RAW_EXPIRE_DAYS', 'IMAGE_FITS_EXPIRE_DAYS')),
    'fits-source': ('FITS and Source', ('IMAGE_SAVE_FITS*', 'IMAGE_EXPORT_RAW', 'FILETRANSFER__UPLOAD_RAW', 'FILETRANSFER__UPLOAD_FITS', 'S3UPLOAD__UPLOAD_FITS', 'FITSHEADERS__*', 'IMAGE_FITS_EXPIRE_DAYS', 'IMAGE_RAW_EXPIRE_DAYS', 'IMAGE_FOLDER', 'IMAGE_EXPORT_FOLDER')),
}


def settings_domain_context(slug, field_names):
    domain = SETTINGS_DOMAINS.get(slug)
    if domain is None:
        return {'settings_domain_title': None, 'settings_domain_fields': []}
    title, patterns = domain
    return {'settings_domain_title': title, 'settings_domain_fields': [
        name for name in field_names if any(fnmatchcase(name, pattern) for pattern in patterns)
    ]}
