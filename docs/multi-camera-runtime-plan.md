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

## 11. Implementation Roadmap

### MVP Multi-Camera

The MVP is the smallest runtime change that can capture from Eric's Camera Module V3 Wide and ASI678MC at the same time without breaking existing single-camera installs.

MVP definition:

- Existing single-camera config continues to boot unchanged.
- Multi-camera capture is disabled by default.
- A normalized default capture profile is derived from the current config.
- A second optional capture profile can be stored for ASI678MC.
- When `MULTI_CAMERA_CAPTURE_ENABLE` is false, the service starts one capture worker exactly as today.
- When enabled for the pilot, the service starts:
  - one `CaptureWorker` for IMX708/libcamera
  - one `CaptureWorker` for ASI678MC/INDI
- Each capture worker has isolated:
  - capture queue
  - error queue
  - exposure state
  - gain state
  - binning state
  - camera temp/state
  - status namespace
- Shared image/video/upload workers remain shared for the MVP.
- ASI678MC starts with images-only output:
  - no timelapse
  - no keogram
  - no startrails
  - no panorama
  - optional upload disabled by default
- IMX708 remains the primary/dashboard camera and keeps existing output behavior.

MVP success criteria:

- IMX708 continues producing latest image, normal media, and existing outputs.
- ASI678MC produces image rows under its own DB camera id.
- Both camera histories are visible in Modern Admin media/camera views.
- A failure in ASI678MC capture does not stop IMX708 capture.
- A failure in IMX708 capture does not stop ASI678MC capture.
- Existing classic admin behavior remains usable for the primary camera.

### Step 1: Add Capture Profile Normalization

Difficulty: Low

Risk: Low

Dependencies: None

Add a pure helper that converts the current active config into a single normalized capture profile. This should not change runtime behavior.

Example output:

```json
{
  "profile_id": "default",
  "primary": true,
  "enabled": true,
  "camera_interface": "libcamera_imx708",
  "indi": {
    "server": "localhost",
    "port": 7624,
    "camera_name": ""
  },
  "libcamera": {
    "camera_id": 0
  },
  "outputs": {
    "inherit_global": true
  }
}
```

Why first:

- It creates a compatibility bridge.
- It lets tests assert that current config maps cleanly into a future profile.
- It does not require new workers, DB migrations, or UI changes.

### Step 2: Add Read-Only Runtime Profile Diagnostics

Difficulty: Low

Risk: Low

Dependencies: Step 1

Expose the normalized active profile in Modern Admin read-only diagnostics.

Show:

- profile id
- interface
- DB camera id if known
- INDI host/port/name
- libcamera camera id
- whether profile is primary
- whether profile is enabled

No write path yet.

### Step 3: Namespace Capture State Without Changing Behavior

Difficulty: Medium

Risk: Medium

Dependencies: Step 1

Introduce a profile-aware state naming helper.

Current global state:

```text
STATUS
DB_CAMERA_ID
CAMERA_NAME
CAMERA_SERVER
```

New namespaced state:

```text
CAPTURE_PROFILES.default.STATUS
CAPTURE_PROFILES.default.DB_CAMERA_ID
CAPTURE_PROFILES.default.CAMERA_NAME
CAPTURE_PROFILES.default.CAMERA_SERVER
```

Compatibility requirement:

- The default/primary profile still writes the legacy global keys.
- Existing UI and classic admin continue reading old keys until migrated.

This prevents a future second capture worker from overwriting global active camera state.

### Step 4: Split Shared Arrays Into Profile State Objects

Difficulty: Medium

Risk: Medium

Dependencies: Step 3

Create a small structure for per-camera shared runtime values:

- exposure
- gain
- binning
- camera temperature slots
- camera user sensor slots
- capture status

Keep global shared arrays for:

- location
- sun altitude
- moon altitude
- moon phase
- day/night state if treated as observatory-wide

For the first refactor, still instantiate only one profile state object for the default camera.

### Step 5: Refactor CaptureWorker Constructor

Difficulty: Medium

Risk: Medium

Dependencies: Steps 1, 3, 4

Change `CaptureWorker` so it receives:

- global config
- capture profile
- profile runtime state
- per-profile capture queue
- per-profile error queue

The worker should build an effective config internally by merging:

```text
global config + capture profile overrides
```

Behavior must remain identical with one default profile.

### Step 6: Introduce CaptureSupervisor Running One Worker

Difficulty: Medium

Risk: Medium

Dependencies: Step 5

Move start/stop/restart logic for capture into a `CaptureSupervisor`.

Initially:

- supervisor owns one profile
- supervisor starts one `CaptureWorker`
- supervisor exposes one active worker handle
- supervisor mirrors current shutdown behavior

No simultaneous capture yet.

This step makes multi-worker orchestration possible without changing the number of workers.

### Step 7: Add Disabled Secondary Profile Storage

Difficulty: Medium

Risk: Medium

Dependencies: Step 1

Add config support for optional `CAMERA_PROFILES`, but keep it disabled by default.

For Eric:

```json
{
  "profile_id": "asi678mc",
  "primary": false,
  "enabled": false,
  "camera_interface": "indi",
  "indi": {
    "server": "localhost",
    "port": 7624,
    "camera_name": "ZWO CCD ASI678MC"
  },
  "outputs": {
    "capture_images": true,
    "timelapse": false,
    "keogram": false,
    "startrail": false,
    "panorama": false,
    "upload": false
  }
}
```

Modern Admin can write this later, but the first runtime step can load it read-only or from manual config.

### Step 8: Make Queues And Commands Profile-Aware

Difficulty: Medium

Risk: Medium

Dependencies: Steps 5, 6

Use one capture queue per capture worker.

Add `profile_id` to queue payloads where useful, especially for:

- manual pause/resume
- reload/reconfigure
- SQM frame request
- status/debug commands

Continue relying on `camera_id` for media processing and DB queries.

### Step 9: Add Feature Flag For Multiple Capture Workers

Difficulty: Medium

Risk: High

Dependencies: Steps 3, 4, 5, 6, 7, 8

Add a guarded config flag:

```json
"MULTI_CAMERA_CAPTURE_ENABLE": false
```

When false:

- current behavior remains single-camera.

When true:

- supervisor starts all enabled profiles.
- each profile gets one capture worker.
- image/video/upload workers stay shared.

This is the first step that actually changes runtime concurrency.

### Step 10: Pilot IMX708 + ASI678MC Images-Only

Difficulty: Medium

Risk: High

Dependencies: Step 9

Pilot settings:

- IMX708:
  - primary profile
  - existing outputs unchanged

- ASI678MC:
  - secondary profile
  - images only
  - no timelapse
  - no keogram
  - no startrails
  - no panorama
  - no upload by default

Monitor:

- process health per capture profile
- image queue depth
- processing latency per camera
- storage growth
- CPU/memory
- USB errors
- INDI disconnects
- libcamera failures

Rollback:

- set `MULTI_CAMERA_CAPTURE_ENABLE=false`
- restart service
- default single-camera behavior resumes

## 12. MVP Images-Only Implementation Plan

This section defines the first practical implementation target for simultaneous IMX708 + ASI678MC capture. It is intentionally narrower than the long-term architecture: capture still runs inside one indi-allsky service, no DB schema changes are required, no Modern Admin UI changes are required, and default behavior stays single-camera.

### Feature Flag

Add one top-level feature flag, default off:

```json
"MULTI_CAMERA_CAPTURE_ENABLE": false
```

Behavior:

- `false`: start exactly one `CaptureWorker`, using the first/default `CaptureProfile`, preserving current runtime behavior.
- `true`: start one `CaptureWorker` per enabled capture profile, but only for profiles explicitly marked enabled.

The flag should be treated as experimental. It should not be enabled automatically by camera registration, config migration, or Modern Admin camera switching.

### Proposed Config Format

The MVP should keep the current single-camera config as the source of truth for normal installs and add an optional `MULTI_CAMERA` section. If the section is missing or the feature flag is off, runtime behavior remains unchanged.

Example shape:

```json
{
  "MULTI_CAMERA_CAPTURE_ENABLE": false,
  "MULTI_CAMERA": {
    "profiles": [
      {
        "profile_id": "imx708-wide",
        "enabled": true,
        "primary": true,
        "label": "Camera Module V3 Wide",
        "camera_interface": "libcamera_imx708",
        "camera_name": "libcamera_imx708",
        "camera_id_hint": 0,
        "libcamera": {
          "camera_id": 0
        },
        "outputs": {
          "images": true,
          "timelapse": true,
          "keogram": true,
          "realtime_keogram": true,
          "longterm_keogram": true,
          "startrails": true,
          "panorama": true,
          "extra_uploads": true
        }
      },
      {
        "profile_id": "asi678mc",
        "enabled": false,
        "primary": false,
        "label": "ASI678MC",
        "camera_interface": "indi",
        "camera_name": "ZWO CCD ASI678MC",
        "indi": {
          "server": "localhost",
          "port": 7625,
          "camera_name": "ZWO CCD ASI678MC"
        },
        "outputs": {
          "images": true,
          "timelapse": false,
          "keogram": false,
          "realtime_keogram": false,
          "longterm_keogram": false,
          "startrails": false,
          "panorama": false,
          "extra_uploads": false
        }
      }
    ]
  }
}
```

Notes:

- `profile_id` is the runtime routing key.
- `camera_id` from the DB remains the media ownership key.
- `primary=true` identifies the camera that preserves existing dashboard/latest-output expectations.
- `enabled=true` means the profile may be started when the feature flag is on.
- The secondary ASI678MC profile should remain disabled until Eric intentionally enables the experiment.

### Profiles For Eric's MVP

Primary profile:

- `profile_id`: `imx708-wide`
- interface: `libcamera_imx708`
- camera: Raspberry Pi Camera Module V3 Wide / IMX708
- output behavior: unchanged from the current working setup
- purpose: keep the existing all-sky workflow stable

Secondary profile:

- `profile_id`: `asi678mc`
- interface: `indi`
- camera: `ZWO CCD ASI678MC`
- INDI host/port: `localhost:7625`
- output behavior: images only
- purpose: prove simultaneous capture and DB/media separation without enabling expensive generated products

### Disabled In The First MVP

For the secondary ASI678MC profile, keep these disabled:

- timelapse
- mini timelapse
- keogram
- realtime keogram
- longterm keogram
- startrails
- panorama
- panorama loop
- extra upload tasks
- automatic end-of-night generated products

The primary IMX708 profile can keep existing behavior. The MVP should not attempt to make every generated product multi-camera-safe in the first simultaneous capture test.

### Image Routing

The first MVP should route images using metadata that already exists or has been prepared:

- `profile_id`: stable runtime profile id, used by worker logs and future routing
- `camera_id`: DB camera id, used for media ownership and queries

Capture flow:

```text
CaptureWorker(profile_id=imx708-wide) -> image_q payload with profile_id + camera_id
CaptureWorker(profile_id=asi678mc)    -> image_q payload with profile_id + camera_id
ImageWorker                           -> stores/updates image rows by camera_id
```

`ImageWorker` may remain shared for the MVP. It should validate `profile_id`, log it, and continue using `camera_id` for DB/media operations. This keeps processing serialized and avoids starting two independent image processing pipelines too early.

### Avoiding Mixing In Gallery And Images

The DB/media model already links image rows to `camera_id`. The MVP should rely on that and avoid any new global latest-image assumption for the secondary camera.

Rules:

- Gallery and Images must always filter or label by `camera_id` when a camera context is selected.
- The primary dashboard/latest image can continue to use the primary camera.
- Secondary ASI678MC images should appear under their own camera identity.
- Any "all cameras" view must show camera labels clearly.
- Do not infer camera ownership from file path alone.
- Do not merge secondary camera images into primary latest-image widgets unless explicitly requested later.

If an existing page cannot safely distinguish cameras, keep it primary-camera-only for the MVP rather than mixing records.

### Rollback Plan

Safe rollback should be config-only:

1. Set `"MULTI_CAMERA_CAPTURE_ENABLE": false`.
2. Ensure the ASI678MC profile has `"enabled": false`.
3. Restart `indi-allsky`.
4. Confirm only the IMX708 `CaptureWorker` starts.
5. Leave existing ASI678MC DB camera rows and images in place; do not delete media or DB rows.
6. Stop the ASI678MC `indiserver` user service if it is not needed.

Expected result:

- IMX708 behavior returns to the current single-camera path.
- Previously captured ASI678MC media remains visible historically where camera-aware pages support it.
- No schema rollback is required.

### Raspberry Test Plan

Pre-flight:

1. Confirm current IMX708 single-camera capture works with the feature flag off.
2. Confirm ASI678MC is visible via `indi_getprop` against `localhost:7625`.
3. Confirm ASI678MC has a DB camera row and appears in Modern Admin Cameras.
4. Confirm enough free disk space for two image streams.

Dry run:

1. Add the `MULTI_CAMERA` config section with ASI678MC disabled.
2. Keep `"MULTI_CAMERA_CAPTURE_ENABLE": false`.
3. Restart `indi-allsky`.
4. Confirm runtime behavior is unchanged.

Feature-flag test:

1. Enable `"MULTI_CAMERA_CAPTURE_ENABLE": true`.
2. Enable only the IMX708 profile first.
3. Restart `indi-allsky`.
4. Confirm behavior is still equivalent to current single-camera capture.

Two-camera images-only test:

1. Start the ASI678MC `indiserver` user service on port `7625`.
2. Enable the ASI678MC profile with images-only outputs.
3. Restart `indi-allsky`.
4. Confirm logs show two capture profiles and two capture workers.
5. Confirm both workers enqueue image payloads with distinct `profile_id` values.
6. Confirm both cameras write image rows with distinct `camera_id` values.
7. Confirm Gallery/Images do not mix camera identities.
8. Watch CPU, memory, queue depth, storage growth, USB errors, INDI disconnects, and libcamera errors for at least one short daytime test.

Overnight pilot:

1. Keep ASI678MC generated products disabled.
2. Keep uploads for ASI678MC disabled.
3. Let IMX708 continue full normal output.
4. Verify in the morning that IMX708 generated products remain correct and ASI678MC has only image records.

Failure criteria:

- IMX708 capture stops or loses normal generated products.
- `ImageWorker` crashes or queue depth grows without recovery.
- Gallery/Images mix cameras without labels.
- ASI678MC disconnects repeatedly and restarts destabilize the primary profile.

On failure, use the rollback plan immediately.

### Step 11: Per-Camera Output Toggles

Difficulty: Medium

Risk: Medium

Dependencies: Step 10

Make generation gates per-camera:

- timelapse
- daytime timelapse
- keogram
- startrail
- panorama
- upload images
- upload videos

Default secondary camera outputs remain off until explicitly enabled.

### Step 12: Per-Camera Queue Backpressure

Difficulty: High

Risk: High

Dependencies: Step 10

Current backpressure watches one shared `image_q` depth. With two capture workers, queue pressure should not blindly penalize both cameras in the same way.

Add camera-aware queue metrics:

- pending images per `camera_id`
- processing latency per `camera_id`
- dropped/skipped frame counters per profile
- optional per-profile delay adjustment

This is important if ASI678MC produces heavier FITS/raw frames while IMX708 produces lighter JPG frames.

### Step 13: Modern Admin Runtime Control

Difficulty: Medium

Risk: Medium

Dependencies: Steps 9-12

Add safe controls after the runtime model is stable:

- enable/disable secondary profile
- view profile status
- restart one capture profile
- pause one capture profile
- keep global service restart as fallback

Do not add destructive camera deletion as part of this phase.

## 12. Shared Vs Per-Camera Responsibilities

### Can Be Shared Between Cameras

- geolocation:
  - latitude
  - longitude
  - elevation
  - timezone

- observatory state:
  - sun altitude
  - moon altitude
  - moon phase
  - day/night calculation, unless a camera has intentional horizon overrides

- storage root:
  - `IMAGE_FOLDER`
  - database
  - common media folder layout

- upload infrastructure:
  - credentials
  - remote host/bucket
  - upload workers
  - retry logic
  - queue mechanics

- processing workers, initially:
  - shared `ImageWorker`
  - shared `VideoWorker`
  - shared upload workers

- notifications framework:
  - notification table
  - delivery/display mechanisms
  - global system warnings

- external environmental data:
  - aurora/Kp
  - smoke
  - satellite/TLE data
  - weather-like observatory context

- retention defaults:
  - can be shared initially with optional per-camera overrides later

### Must Be Per-Camera

- identity:
  - profile id
  - camera DB id
  - camera name
  - driver/interface
  - INDI host/port/name
  - libcamera camera id
  - future USB path/device id

- capture state:
  - status
  - last frame time
  - last error
  - reconnect count
  - capture pause
  - queue delay/backpressure

- exposure behavior:
  - exposure min/default/max
  - night/day exposure period
  - gain
  - binning
  - cooling
  - camera-specific INDI properties
  - libcamera options

- image output behavior:
  - image file type
  - raw/FITS enablement
  - bit depth
  - debayer/CFA assumptions
  - rotation/flip/crop

- calibration:
  - dark frames
  - bad pixel maps
  - black level
  - camera-specific processing profile

- optical metadata:
  - lens name
  - focal length
  - focal ratio
  - image circle
  - lens offsets
  - panorama parameters
  - VirtualSky offsets

- generated products:
  - timelapse
  - mini timelapse
  - keogram
  - startrails
  - panorama
  - panorama loop

- upload decisions:
  - upload images
  - upload videos
  - upload FITS/raw
  - upload generated products

## 13. Complexity Summary

| Step | Description | Difficulty | Risk |
| --- | --- | --- | --- |
| 1 | Capture profile normalization | Low | Low |
| 2 | Read-only profile diagnostics | Low | Low |
| 3 | Namespaced capture state | Medium | Medium |
| 4 | Per-profile runtime state objects | Medium | Medium |
| 5 | CaptureWorker accepts profile | Medium | Medium |
| 6 | CaptureSupervisor with one worker | Medium | Medium |
| 7 | Disabled secondary profile storage | Medium | Medium |
| 8 | Profile-aware queues/commands | Medium | Medium |
| 9 | Feature flag for multiple workers | Medium | High |
| 10 | IMX708 + ASI678MC images-only pilot | Medium | High |
| 11 | Per-camera output toggles | Medium | Medium |
| 12 | Per-camera queue backpressure | High | High |
| 13 | Modern Admin runtime controls | Medium | Medium |

Overall complexity: High.

Reason: the DB/media model is already camera-aware, but runtime state, config, process supervision, and shared arrays are strongly single-camera.

## 14. Final Recommendation

The first code change should be Step 1: add a pure capture profile normalization helper.

Recommended first change:

```text
Create a helper that derives one default CaptureProfile from the current active config.
Use it in read-only diagnostics or tests only.
Do not change CaptureWorker behavior yet.
```

Why this is safest:

- It does not change runtime behavior.
- It creates the language and data shape needed for every later step.
- It lets Eric validate IMX708 and ASI678MC profile identity before any concurrent capture starts.
- It gives Modern Admin a safe place to show future multi-camera runtime concepts.
- It avoids touching service startup, queues, shared arrays, or capture loops too early.

Do not start by adding a second `CaptureWorker`. That would run directly into global state collisions (`DB_CAMERA_ID`, `STATUS`, shared exposure/gain/binning arrays) before the compatibility path is ready.
