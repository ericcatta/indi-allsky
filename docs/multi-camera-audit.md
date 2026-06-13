# Multi-Camera Audit

Date: 2026-06-13

## Executive summary

indi-allsky already has strong multi-camera data modeling and browsing support: cameras are first-class database rows, media records belong to a camera, and the classic UI has a global camera selector that stores the selected camera in the Flask session.

That is not the same as official simultaneous capture from two local cameras in one normal install. The current runtime is centered on one active config, one main `indi-allsky` service, one capture worker, one selected camera interface, and one current capture camera id. Some background jobs iterate over all known cameras, and the UI can browse multiple camera histories, but the main capture pipeline is one-camera-at-a-time per app instance.

For Eric's Pi 5, Camera Module V3 Wide plus ASI678MC is best treated as a future multi-instance or supervisor problem, not as something the current UI should simply expose as "add second live camera" yet.

## Evidence inspected

- Camera model and relationships: `indi_allsky/flask/models.py`
- Camera selection/session behavior: `indi_allsky/flask/base_views.py`, `indi_allsky/flask/templates/base.html`, `indi_allsky/flask/views.py`
- Camera creation/update during capture: `indi_allsky/capture.py`, `indi_allsky/flask/miscDb.py`
- Main runtime/process model: `allsky.py`, `indi_allsky/allsky.py`, `service/indi-allsky.service`
- INDI/libcamera setup and service wiring: `setup.sh`, `service/indiserver.service`, `indi_allsky/config.py`
- Camera backends: `indi_allsky/camera/__init__.py`, `indi_allsky/camera/indi.py`, `indi_allsky/camera/libcamera.py`, `indi_allsky/camera/indi_passive.py`
- Classic UI: `indi_allsky/flask/templates/base.html`, `indi_allsky/flask/templates/cameras.html`, modern camera inventory work already present in `indi_allsky/flask/templates/modern_admin/cameras.html`

## 1. Is it already possible to use 2 cameras simultaneously?

Not as a normal supported single-install workflow.

What exists:

- The DB can store many cameras.
- Images, thumbnails, videos, FITS, raw images, darks, bad pixel maps, panoramas, keograms, star trails, and long-term keograms all carry `camera_id`.
- Classic UI can switch the selected camera in the session.
- Many views and forms filter by selected camera.
- Some periodic jobs iterate over all non-hidden cameras.
- `indi_passive` exists and is explicitly described in setup as connecting a second instance of indi-allsky to an existing indiserver.

What does not exist as a normal path:

- No built-in "two active local cameras" setup flow.
- No single config structure containing two independent camera profiles.
- No main runtime orchestration for two capture workers with separate camera configs.
- No service templates for two coordinated `indi-allsky` instances.
- No UI that distinguishes "selected camera for browsing" from "active capture process per camera".

The current capture process creates or updates one active DB camera, sets `self.camera_id`, sets `indiclient.camera_id`, and stores `DB_CAMERA_ID`. That is the current capture camera for that running instance.

## 2. Is Camera V3 Wide + ASI678MC together already possible?

Partially possible at the ecosystem level, but not cleanly supported as one standard indi-allsky install.

Camera V3 Wide:

- Supported through the libcamera backend, specifically `libcamera_imx708`.
- The config has one `CAMERA_INTERFACE` and one `LIBCAMERA.CAMERA_ID`.
- The libcamera backend calls `rpicam-still` or `libcamera-still` with `--camera <id>`.

ASI678MC:

- Listed as a supported ZWO camera in README.
- Uses the INDI path, usually through `indi_asi_ccd` or related ZWO INDI driver.
- The setup script supports INDI camera drivers and an indiserver service.

Together:

- They use different capture backends: libcamera direct/MQTT vs INDI/ZWO.
- A single config cannot express "run libcamera_imx708 and indi_asi_ccd as two independent active capture profiles".
- A single normal `indi-allsky.service` starts one app instance with one loaded config.
- Running both would require an advanced multi-instance arrangement, for example one instance for V3 Wide and another for ASI678MC, with separated config/state/runtime paths, ports, service names, pid files, and storage conventions.

This should be treated as experimental unless upstream already documents a precise multi-instance recipe outside the files inspected here.

## 3. How is it configured today?

Normal single-camera configuration:

1. Run setup and choose exactly one camera interface:
   - `indi` for USB astronomy cameras such as ZWO.
   - `libcamera_imx708` for Raspberry Pi Camera Module 3.
   - `mqtt_libcamera` for MQTT-controlled remote libcamera camera.
   - `indi_passive` for a second instance connecting to an existing indiserver.
2. The setup writes a single active config with:
   - `CAMERA_INTERFACE`
   - `INDI_SERVER`
   - `INDI_PORT`
   - `INDI_CAMERA_NAME`
   - `LIBCAMERA.CAMERA_ID` for libcamera.
3. If using INDI, setup creates one `indiserver.service` using one selected CCD driver plus telescope/GPS simulator options.
4. `indi-allsky.service` starts `allsky.py run`, which loads the latest config from the DB and starts one capture worker.
5. When capture connects, it creates or updates one `camera` DB row based on the connected camera name and metadata.
6. The UI can then browse media by selecting a camera from the sidebar selector.

Classic camera selection today is mostly browsing selection, not capture selection.

## 4. Current implementation limits

- Single active config: no list of camera profiles.
- Single service: `service/indi-allsky.service` starts one `allsky.py run`.
- Single PID lock: the app writes/locks one pid file by default, preventing accidental duplicate instances.
- Single capture worker per app instance: the main loop starts one `CaptureWorker`.
- Shared process state: status, watchdog, config id, current DB camera id, queues, and sensor arrays are global to the instance.
- Single selected backend: `CAMERA_INTERFACE` resolves to one camera client class.
- INDI discovery chooses a single CCD device: if `INDI_CAMERA_NAME` is not set, the first CCD is selected.
- libcamera selects one camera id via `LIBCAMERA.CAMERA_ID`.
- The UI's camera selector changes `session['camera_id']`; it does not start, stop, or switch capture hardware.
- Camera-specific settings are partly persisted on the camera row, but most operational settings still live in one global config.
- Names are important: camera rows are matched by `name`, `name_alt1`, or `name_alt2`; duplicate device names can cause ambiguity.
- Generated assets and upload names include `camera_id` in many templates, which is good, but operational state is still not clearly per-camera in the UI.

## 5. UX problems identified

- The sidebar says "Cameras Available", but that means known/browsable cameras, not necessarily cameras currently capturing.
- The camera selector looks like a hardware selector but behaves like a viewing/session selector.
- Classic UI does not clearly distinguish:
  - known camera,
  - selected camera,
  - latest connected camera,
  - currently captured camera,
  - offline historical camera.
- Capture status is global-looking even though browsing can switch cameras.
- Multi-camera records exist, but adding/configuring a camera is not a product flow.
- There is no "camera profile" concept in UI.
- There is no safe explanation for mixed backend setups such as "Pi CSI + ZWO USB".
- If a user sees Camera V3 Wide and ASI678MC in the inventory, the UI could imply both can run together even though the runtime does not provide that as a simple path.

## 6. Simplest path for Eric

For a fresh Pi 5, choose one active camera first.

Recommended simplest path:

1. Install and validate Camera Module V3 Wide as the first camera using `libcamera_imx708`.
2. Use Modern Admin camera inventory to show the active camera, driver, latest image age, and storage/media status.
3. Treat ASI678MC as a separate evaluation path:
   - stop/reconfigure the same install to `indi` + ZWO driver for testing, or
   - use a second isolated install/instance only if Eric is comfortable with advanced service separation.
4. Do not promise simultaneous capture in the Modern Admin UI yet.
5. Add UX labels such as "Selected for viewing" and "Captured by this instance" before exposing any future multi-camera controls.

If Eric specifically needs both cameras running at once now, the least invasive experimental route is likely two isolated indi-allsky instances, not a UI feature:

- one libcamera instance for V3 Wide,
- one INDI/ZWO instance for ASI678MC,
- separate config DB/runtime paths,
- separate service names and pid files,
- separate image roots or very carefully separated camera folders,
- one shared or separate web UI only after the data model and service management are understood.

That should be treated as advanced and tested on disposable data first.

## 7. Best long-term path

The clean long-term design is a real camera profile and capture-instance model.

Recommended architecture direction:

- Introduce explicit camera profiles:
  - name,
  - backend type,
  - driver/interface,
  - INDI server/port/camera name or libcamera camera id,
  - image/config overrides,
  - enabled/disabled,
  - capture role.
- Separate "camera inventory" from "capture instance".
- Track active capture process per profile.
- Move operational status from global state toward per-camera or per-instance state.
- Add a supervisor layer that can start/stop/reload one capture worker per enabled profile.
- Keep media tables camera-linked as they already are.
- Add UI language:
  - Active capture,
  - Available,
  - Offline,
  - Selected for viewing,
  - Managed by another instance.
- Support safe mixed backend setups explicitly:
  - local libcamera,
  - local INDI,
  - remote/MQTT libcamera,
  - passive INDI.
- Build Modern Admin camera management around read-only discovery first, then safe start/stop controls later.

## Existing support summary

Strong:

- Multi-camera DB schema.
- Per-camera media relationships.
- Per-camera media browsing.
- Session-based camera selection.
- Camera inventory data already usable for Modern Admin.
- Setup supports many camera backends.
- `indi_passive` hints at advanced multi-instance use.

Weak or missing:

- Simultaneous local capture from two cameras in one standard instance.
- Per-camera config profiles.
- Per-camera service/process supervision.
- Clear UX for active vs selected vs historical cameras.
- Safe setup path for Camera V3 Wide plus ASI678MC together.

## Recommendation

For Eric now: do not try to make the Modern Admin "Add Camera" flow start two cameras yet. Use it first as a camera inventory and status surface.

Short term:

- Keep one active capture camera per install.
- Make Modern Admin accurately label the active camera and historical/available cameras.
- Add documentation/UI warnings that camera selection is browsing selection unless a future capture profile system exists.

Medium term:

- Prototype a read-only "capture instances" page that reports the current service, config id, DB camera id, camera interface, INDI host/port, and latest frame per camera.

Long term:

- Add first-class capture profiles and a supervisor.
- Only then expose "run V3 Wide and ASI678MC together" as a supported UI workflow.
