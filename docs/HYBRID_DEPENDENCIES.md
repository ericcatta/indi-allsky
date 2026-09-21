# Hybrid dependency review

Reviewed 21 September 2026 against source `a9e41451` and installed runtime `7d9e49f9`. Classic removal does not make shared backend packages obsolete. The 47 active core requirements were traced to direct imports, indirect/plugin consumers, tools or retained build compatibility. No package was removed or upgraded.

[Detailed consumer evidence](../testing/evidence/hybrid-core-dependency-review-20260921.json).

| Package | Retained purpose |
| --- | --- |
| astropy | [indi_allsky/camera/indi.py](../indi_allsky/camera/indi.py), [indi_allsky/camera/indi_accumulator.py](../indi_allsky/camera/indi_accumulator.py) |
| photutils | [indi_allsky/protection_masks.py](../indi_allsky/protection_masks.py) |
| pyerfa | Installed astropy declares pyerfa>=2.0.1.1. |
| numpy | [indi_allsky/aurora.py](../indi_allsky/aurora.py), [indi_allsky/auto_meter.py](../indi_allsky/auto_meter.py) |
| opencv-python-headless | [indi_allsky/auto_meter.py](../indi_allsky/auto_meter.py), [indi_allsky/camera/test_cameras.py](../indi_allsky/camera/test_cameras.py) |
| scipy | [examples/DENOISE PR TEST ENVIRONMENT/test_pr_real_image.py](../examples/DENOISE%20PR%20TEST%20ENVIRONMENT/test_pr_real_image.py) |
| ccdproc | [indi_allsky/darks.py](../indi_allsky/darks.py) |
| scikit-image | Installed ccdproc and astroalign require scikit-image. |
| astroalign | [indi_allsky/stack.py](../indi_allsky/stack.py) |
| bottleneck | Installed astropy/stats/nanfunctions.py and ccdproc/combiner.py import bottleneck. |
| python-dateutil | [indi_allsky/camera/indi.py](../indi_allsky/camera/indi.py) |
| ephem | [indi_allsky/capture.py](../indi_allsky/capture.py), [indi_allsky/flask/astropanel_views.py](../indi_allsky/flask/astropanel_views.py) |
| skyfield | [indi_allsky/flask/system_context_views.py](../indi_allsky/flask/system_context_views.py) |
| paramiko | [indi_allsky/filetransfer/paramiko_sftp.py](../indi_allsky/filetransfer/paramiko_sftp.py) |
| pycurl | [indi_allsky/camera/pycurl_camera.py](../indi_allsky/camera/pycurl_camera.py), [indi_allsky/filetransfer/pycurl_ftp.py](../indi_allsky/filetransfer/pycurl_ftp.py) |
| Pillow | [indi_allsky/flask/forms.py](../indi_allsky/flask/forms.py), [indi_allsky/flask/miscDb.py](../indi_allsky/flask/miscDb.py) |
| piexif | [indi_allsky/image.py](../indi_allsky/image.py), [indi_allsky/keogram.py](../indi_allsky/keogram.py) |
| imageio | testing/image/gif.py and testing/libcamera/fake_libcamera-still; installed scikit-image also requires it. |
| imageio-ffmpeg | Installed imageio/plugins/ffmpeg.py imports imageio_ffmpeg; retain supported imageio video I/O. |
| simplejpeg | [indi_allsky/darks.py](../indi_allsky/darks.py), [indi_allsky/flask/miscDb.py](../indi_allsky/flask/miscDb.py) |
| cython | Declared build tool in platform manifests. No application import; fresh builds across supported architectures were not tested, so removal is not justified by frontend retirement. |
| rawpy | [indi_allsky/darks.py](../indi_allsky/darks.py), [indi_allsky/processing.py](../indi_allsky/processing.py) |
| pygifsicle | testing/image/gif.py uses pygifsicle.optimize for the optional GIF optimization function. |
| gunicorn | [indi_allsky/flask/system_context_views.py](../indi_allsky/flask/system_context_views.py) |
| inotify | service/gunicorn.conf.py explicitly sets reload_engine=inotify. |
| psutil | [indi_allsky/allsky.py](../indi_allsky/allsky.py), [indi_allsky/backup.py](../indi_allsky/backup.py) |
| Flask | [indi_allsky/flask/__init__.py](../indi_allsky/flask/__init__.py), [indi_allsky/flask/actionapi_views.py](../indi_allsky/flask/actionapi_views.py) |
| Flask-SQLAlchemy | [indi_allsky/flask/__init__.py](../indi_allsky/flask/__init__.py) |
| Flask-Migrate | [indi_allsky/flask/__init__.py](../indi_allsky/flask/__init__.py) |
| Flask-WTF | [indi_allsky/flask/__init__.py](../indi_allsky/flask/__init__.py), [indi_allsky/flask/forms.py](../indi_allsky/flask/forms.py) |
| Flask-Login | [indi_allsky/flask/__init__.py](../indi_allsky/flask/__init__.py), [indi_allsky/flask/auth_views.py](../indi_allsky/flask/auth_views.py) |
| werkzeug | [indi_allsky/flask/image_processing_views.py](../indi_allsky/flask/image_processing_views.py), [indi_allsky/flask/views.py](../indi_allsky/flask/views.py) |
| is-safe-url | [indi_allsky/flask/auth_views.py](../indi_allsky/flask/auth_views.py) |
| certifi | Installed requests and skyfield declare certifi as a dependency. |
| cryptography | [indi_allsky/config.py](../indi_allsky/config.py), [indi_allsky/flask/miscDb.py](../indi_allsky/flask/miscDb.py) |
| dbus-python | [indi_allsky/capture.py](../indi_allsky/capture.py), [indi_allsky/drive_manager.py](../indi_allsky/drive_manager.py) |
| paho-mqtt | [indi_allsky/camera/libcamera_mqtt.py](../indi_allsky/camera/libcamera_mqtt.py), [indi_allsky/devices/dew_heaters/dewHeaterMqtt.py](../indi_allsky/devices/dew_heaters/dewHeaterMqtt.py) |
| setuptools-rust | Declared build tool in platform manifests. No application import; fresh source builds were not tested, so removal is not justified by frontend retirement. |
| bcrypt | Installed paramiko requires bcrypt>=3.2; testing/benchmark/hash_bench.py also uses it. |
| passlib | [indi_allsky/flask/actionapi_views.py](../indi_allsky/flask/actionapi_views.py), [indi_allsky/flask/auth_views.py](../indi_allsky/flask/auth_views.py) |
| prettytable | [indi_allsky/config.py](../indi_allsky/config.py), [misc/indi_list_cameras.py](../misc/indi_list_cameras.py) |
| lxml | [indi_allsky/smoke.py](../indi_allsky/smoke.py) |
| shapely | [indi_allsky/smoke.py](../indi_allsky/smoke.py) |
| requests-toolbelt | [indi_allsky/filetransfer/requests_syncapi_v1.py](../indi_allsky/filetransfer/requests_syncapi_v1.py) |
| pytz | Installed skyfield/timelib.py imports pytz.timezone. |
| mysql-connector-python | docker/start_gunicorn.sh and docker/start_indi_allsky.sh select mysql+mysqlconnector SQLAlchemy URIs; misc/convert_db.py also supports it. |
| PyWavelets | [indi_allsky/denoise.py](../indi_allsky/denoise.py) |

## Installed dependency check

`pip check` reports one metadata mismatch: Blinka requires the distribution `RPi.GPIO`, while this Raspberry Pi5 uses `rpi-lgpio0.6`, which provides the `RPi.GPIO` module. Both setup and unattended upgrade explicitly perform this replacement on the relevant Debian/aarch64 platforms. Do not install the old distribution over the working replacement merely to silence the checker. This is an explained nonzero result, not a green `pip check`.

## Installer and verification limits

All11 requirement-file paths referenced by the inspected installers/Dockerfiles resolve. Bash syntax passes for setup, unattended upgrade, web-only setup and both Docker application launch scripts. These checks do not prove clean installation on every OS/architecture.

Optional device and cloud integrations remain supported; unavailable hardware has not been exercised. Build tools Cython and setuptools-rust are retained because their removal requires clean-build evidence on supported platforms. Backend resource/concurrency review and the remaining acceptance work are separate from this package review.
