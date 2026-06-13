# Multi-Camera Runtime Plan

## 1. Current Capture Runtime State

The current indi-allsky runtime is built around one active capture configuration and one active capture camera per running service instance.

The main service is orchestrated by `indi_allsky/allsky.py`. `IndiAllSky.__init__()` loads one active `IndiAllSkyConfig`, stores it in `self.config`, and creates one set of shared state arrays and queues:

- `capture_q`
- `image_q`
- `video_q`
- `upload_q`
- `position_av`
- `exposure_av`
- `gain_av`
- `binning_av`
- `sensors_temp_av`
- `sensors_user_av`
- `night_av`
- `astro_av`

`IndiAllSky._startCaptureWorker()` starts exactly one `CaptureWorker`, passing the single global config and shared arrays. The matching `_startImageWorker()` and `_startVideoWorker()` also start one image worker and one video worker.

`indi_allsky/capture.py` then resolves the active backend from:

```text
config["CAMERA_INTERFACE"]
```

and creates one camera client from `indi_allsky.camera`. The same `CaptureWorker` connects to one INDI/libcamera backend, finds one CCD, registers or updates one camera row, sets one `DB_CAMERA_ID` state value, then captures frames for that one camera.

For Eric's real case, that means the current normal runtime can run either:

- Camera Module V3 Wide via `libcamera_imx708`
- ASI678MC via `CAMERA_INTERFACE=indi` and `INDI_CAMERA_NAME`

but not both simultaneously in one normal app instance.

## 2. Where Code Assumes One Active Camera

Important single-camera assumptions:

- `indi_allsky/allsky.py`
  - Loads one `IndiAllSkyConfig`.
  - Owns one `self.config`.
  - Starts one `CaptureWorker`.
  - Maintains one capture queue and one capture error queue.
  - Maintains one set of shared arrays for exposure, gain, binning, night state, astro state, and sensors.

- `indi_allsky/capture.py`
  - `CaptureWorker.__init__()` stores one config.
  - `_initialize()` reads one `CAMERA_INTERFACE`.
  - `_initialize()` calls `findCcd(camera_name=config.get("INDI_CAMERA_NAME"))`.
  - `_initialize()` sets one `self.camera_id`, `self.camera_name`, and `self.camera_server`.
  - `_miscDb.setState("DB_CAMERA_ID", camera.id)` stores one global active DB camera id.
  - Exposure cadence uses one `EXPOSURE_PERIOD`, `EXPOSURE_PERIOD_DAY`, `CCD_CONFIG`, `INDI_CONFIG_DEFAULTS`, `INDI_CONFIG_DAY`, and `LIBCAMERA` block.
  - Queue backpressure is based on one `image_q` depth.
  - SQM, focus mode, cooling, day/night transition, and reconfigure logic all operate on the one active camera.

- `indi_allsky/flask/base_views.py`
  - `BaseView.cameraSetup()` resolves one current camera.
  - Many views assume one `self.camera`.
  - The camera selector can browse multiple DB cameras, but the active runtime state remains single-camera.

- State keys
  - `STATUS`
  - `CAMERA_NAME`
  - `CAMERA_SERVER`
  - `DB_CAMERA_ID`
  - `CONFIG_ID`

These are global keys today. A simultaneous runtime would need per-camera or per-instance state keys.

## 3. DB And Media Already Multi-Camera

The database/media side is much closer to multi-camera than capture runtime.

Already camera-scoped:

- `IndiAllSkyDbCameraTable`
- image rows with `camera_id`
- video rows with `camera_id`
- mini timelapse rows with `camera_id`
- keogram rows with `camera_id`
- startrail rows with `camera_id`
- panorama rows with `camera_id`
- dark frames and bad pixel maps with `camera_id`
- upload tasks often carry `camera_id`

The video worker is already largely camera-aware. In `indi_allsky/video.py`, generation methods load the camera from `kwargs["camera_id"]` and query media joined through that camera. Capture queues generation jobs with explicit camera ids, for example:

- `generateVideo`
- `generateKeogramStarTrails`
- `generatePanoramaVideo`
- `expireData`
- `uploadAllskyEndOfNight`

This means the media model can store IMX708 and ASI678MC histories side by side. The current missing part is not storage; it is running two capture pipelines at the same time with isolated config and state.

## 4. Global Config Vs Per-Camera Config

Current config is a single JSON document stored as one active config row. It mixes several categories:

Global/site settings:

- location
- owner/site title
- time zone assumptions
- image folder
- upload provider credentials
- web/UI behavior
- cleanup retention defaults
- aurora/smoke/satellite data settings

Camera identity and driver settings:

- `CAMERA_INTERFACE`
- `INDI_SERVER`
- `INDI_PORT`
- `INDI_CAMERA_NAME`
- `LIBCAMERA.CAMERA_ID`
- `LIBCAMERA.*`
- `INDI_CONFIG_DEFAULTS`
- `INDI_CONFIG_DAY`

Camera behavior settings:

- exposure periods
- gains/binning
- day/night capture
- focus mode
- cooling
- SQM exposure
- image type/raw settings
- lens geometry
- virtual sky offsets
- panorama/fish2pano behavior

For simultaneous capture, config needs a split:

- one global config shared by the app
- one per-camera capture profile per active camera
- optional per-camera processing/output profile

The smallest compatible shape would be additive, not destructive:

```json
{
  "CAMERA_PROFILES": [
    {
      "id": "imx708-wide",
      "enabled": true,
      "camera_interface": "libcamera_imx708",
      "libcamera": {
        "camera_id": 0
      },
      "capture": {},
      "processing": {},
      "outputs": {}
    },
    {
      "id": "asi678mc",
      "enabled": true,
      "camera_interface": "indi",
      "indi": {
        "server": "localhost",
        "port": 7624,
        "camera_name": "ZWO CCD ASI678MC"
      },
      "capture": {},
      "processing": {},
      "outputs": {}
    }
  ]
}
```

Existing single-camera keys should continue to work as the default profile until migration is explicit.

## 5. Proposed Architecture For Simultaneous Capture

Recommended architecture:

```text
IndiAllSky main process
  |
  +-- shared global workers
  |     +-- ImageWorker(s)
  |     +-- VideoWorker
  |     +-- UploadWorker(s)
  |     +-- SensorWorker
  |
  +-- CaptureSupervisor
        |
        +-- CaptureWorker(camera_profile=IMX708)
        |
        +-- CaptureWorker(camera_profile=ASI678MC)
```

Key design rules:

- Keep one main service process.
- Add a capture supervisor rather than running independent full app instances.
- Run one `CaptureWorker` per enabled camera profile.
- Keep image/video/upload workers shared initially because queues already carry `camera_id`.
- Give every capture worker isolated config, isolated state, and isolated control queue.
- Keep global astro/location calculations shared where practical.
- Keep per-camera status in DB/misc state, not one global `STATUS`.

For Eric's IMX708 + ASI678MC case:

- IMX708 profile uses `libcamera_imx708` and `LIBCAMERA.CAMERA_ID`.
- ASI678MC profile uses `indi`, `INDI_SERVER`, `INDI_PORT`, `INDI_CAMERA_NAME`.
- Both workers write image jobs into the same `image_q`, but every job already includes `camera_id`.
- Queue backpressure must become per-camera or at least camera-aware, because a slow ASI processing path should not silently throttle IMX708 unless system-level pressure requires it.

## 6. Process And Worker Management Per Camera

New runtime concepts:

- `CaptureProfile`
  - Immutable-ish normalized view of one camera profile.
  - Built from global config plus per-camera overrides.

- `CaptureWorkerHandle`
  - Worker process
  - per-camera `capture_q`
  - per-camera `error_q`
  - restart counter
  - last heartbeat
  - camera profile id
  - DB camera id once known

- `CaptureSupervisor`
  - starts/stops/restarts capture workers
  - owns the map `{profile_id: CaptureWorkerHandle}`
  - dispatches per-camera commands
  - handles graceful shutdown
  - handles per-camera restart limits

Worker state should be isolated:

- exposure array per camera
- gain array per camera
- binning array per camera
- camera sensor temp per camera
- active camera id per camera
- capture status per camera

Shared state can remain global:

- location
- sun/moon alt
- night/day calculation
- upload queue
- video queue
- image processing queue, initially

The current `capture_q` command model can be extended by adding `profile_id` or by giving each capture worker its own queue. Per-worker queues are safer and clearer.

## 7. Synchronized Vs Individual Settings

Suggested split:

Synchronized/global:

- observatory location
- owner/site metadata
- time zone
- sun/moon day/night calculation
- global image folder root
- database
- upload credentials
- retention policy defaults
- aurora/smoke/Kp external data
- system status

Individual per camera:

- camera interface
- INDI server/port/name
- libcamera camera id
- exposure periods
- gain/binning defaults
- cooling settings
- focus mode
- SQM behavior
- image file type/raw mode
- bit depth
- lens name/focal length/focal ratio/image circle
- lens offsets
- rotation/flip/crop
- dark/bpm calibration selection
- processing profile
- upload enablement per asset type
- timelapse/keogram/startrail enablement

Potentially shared with override:

- night/day capture enablement
- daytime timelapse
- panorama/fish2pano
- chart custom slots
- VirtualSky rendering metadata
- overlay text/template

## 8. Optional Timelapse, Keogram, Startrail Per Camera

Generation should become per-camera, not globally all-or-nothing.

Current generation functions already receive `camera_id`, but the gating config is global:

- `TIMELAPSE_ENABLE`
- `DAYTIME_TIMELAPSE`
- `FISH2PANO.ENABLE`
- upload flags
- retention settings

Recommended per-camera profile fields:

```json
{
  "outputs": {
    "timelapse": true,
    "daytime_timelapse": true,
    "keogram": true,
    "startrail": true,
    "panorama": false,
    "upload_images": true,
    "upload_timelapse": false
  }
}
```

For Eric's IMX708 + ASI678MC:

- IMX708 Wide likely keeps full all-sky outputs: latest, timelapse, keogram, startrails, optional panorama.
- ASI678MC may initially capture latest/images only, with timelapse/keogram/startrail disabled until exposure cadence and framing are understood.

That avoids expensive duplicate video generation and reduces risk during first simultaneous capture tests.

## 9. Risks And Gradual Migration

Main risks:

- Resource contention on Pi 5
  - Two cameras can double I/O, CPU, memory, and storage pressure.
  - ASI FITS/raw paths may be heavier than IMX708 JPG paths.

- INDI/libcamera conflicts
  - INDI ASI and libcamera can coexist conceptually, but process startup, USB bandwidth, and driver stability need real testing.
  - Multiple INDI cameras on one server need device-name disambiguation.

- Global state collisions
  - `STATUS`, `DB_CAMERA_ID`, `CAMERA_NAME`, and `CAMERA_SERVER` are currently single values.
  - A second capture worker would overwrite them unless namespaced.

- Shared arrays are single-camera
  - exposure/gain/binning/sensor arrays cannot represent multiple active cameras.

- Queue backpressure
  - One slow pipeline can affect all cameras if image queue throttling remains global.

- Config migration
  - Existing installs must continue to boot with old single-camera config.
  - Classic admin must not be forced to understand all multi-camera fields immediately.

- UI expectations
  - Users may expect "active camera" to mean capture active, selected for browsing, or primary dashboard camera. These must become separate concepts.

Recommended migration style:

- Add new structures behind existing behavior.
- Keep single-camera mode as default.
- Add read-only diagnostics first.
- Add one optional second capture profile only after state namespacing exists.
- Keep destructive/config-writing actions explicit and reversible.

## 10. Small-Step Implementation Plan

### Step 1: Document And Inspect Runtime State

Add Modern Admin diagnostics showing:

- current active config id
- current `DB_CAMERA_ID`
- configured cameras
- detected libcamera devices
- detected INDI devices
- candidate profile identity

No runtime changes.

### Step 2: Introduce Profile Normalization Helper

Create a pure helper that converts current single-camera config into one normalized capture profile.

No behavior change.

Expected output:

```text
profile_id=default
camera_interface=libcamera_imx708
camera_id=0
enabled=true
```

### Step 3: Add Namespaced Capture State Model

Before running multiple workers, add a safe state structure:

```text
CAPTURE_PROFILES.default.STATUS
CAPTURE_PROFILES.default.DB_CAMERA_ID
CAPTURE_PROFILES.default.CAMERA_NAME
CAPTURE_PROFILES.default.CAMERA_SERVER
```

Keep writing legacy global keys from the primary profile for compatibility.

### Step 4: Refactor CaptureWorker To Accept A CaptureProfile

Change `CaptureWorker` initialization so it can receive:

- global config
- camera profile
- profile-specific shared arrays/state

Initially pass one profile derived from the current config. No multi-camera yet.

### Step 5: Add CaptureSupervisor With One Worker

Move single worker start/stop/restart into a supervisor but still run only one profile.

No user-visible behavior change.

### Step 6: Make Queued Jobs Carry Profile Id

Keep `camera_id`, add `profile_id` where useful.

Workers should continue using `camera_id` for DB/media queries.

### Step 7: Add Second Disabled Profile

Allow config to store a second profile, disabled by default.

For Eric:

- profile `imx708-wide`: current Camera Module V3 Wide
- profile `asi678mc`: ASI678MC INDI config

Still only one enabled capture profile.

### Step 8: Enable Two Capture Workers Behind Feature Flag

Add a guarded flag such as:

```json
"MULTI_CAMERA_CAPTURE_ENABLE": false
```

When false, behavior remains current.

When true, supervisor starts enabled profiles.

### Step 9: Per-Camera Output Toggles

Add per-profile output settings before broad use:

- capture images
- generate timelapse
- generate keogram
- generate startrail
- upload

Default second camera outputs should be conservative.

### Step 10: Eric Pilot Path

Pilot sequence:

1. Keep current IMX708 single-camera config as primary.
2. Register ASI678MC as a disabled INDI profile.
3. Confirm both profiles render in Modern Admin.
4. Enable ASI678MC capture with images-only output.
5. Watch CPU, memory, queue depth, storage, and camera-specific status.
6. Enable optional ASI timelapse only after stable overnight capture.

## Recommendation

Do not try to make the current single `CaptureWorker` juggle two cameras internally. The cleaner and safer path is one capture worker per camera profile, supervised by the main service, with shared image/video/upload workers kept initially.

This matches the current strengths of indi-allsky:

- DB and media are already camera-scoped.
- Processing jobs already carry `camera_id`.
- Existing single-camera behavior can remain the compatibility path.

The hard work is state/config isolation, not media storage.
