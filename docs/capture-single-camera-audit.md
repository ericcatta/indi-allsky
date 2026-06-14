# Capture Single-Camera Runtime Audit

This audit identifies places where the current capture runtime assumes one active camera. It is focused on the path needed before any safe IMX708 + ASI678MC simultaneous capture work.

## Summary

The database and media layers already support many camera-scoped records through `camera_id`, but the runtime service is still single-camera in its process model, shared arrays, global state keys, and active config access.

The most important blockers are:

- one `CaptureWorker`
- one active config object
- one `capture_q`
- one set of exposure/gain/binning arrays
- one set of camera sensor arrays
- one global `DB_CAMERA_ID`
- one global `STATUS`
- image processing reading a global `CAMERA_INTERFACE`

## Assumptions

| Area | File | Function/Class | What It Assumes | Why It Blocks Multi-Camera | Risk | Minimal Refactor |
| --- | --- | --- | --- | --- | --- | --- |
| Main config ownership | `indi_allsky/allsky.py` | `IndiAllSky.__init__` | Loads one `IndiAllSkyConfig` into `self.config`. | All workers receive the same active camera config. There is no profile list or per-camera effective config. | Medium | Add a pure `CaptureProfile` normalization helper that derives one default profile from `self.config` without changing behavior. |
| Capture process count | `indi_allsky/allsky.py` | `_startCaptureWorker` | Starts one `CaptureWorker` and stores it as `self.capture_worker`. | There is no map of workers per camera/profile. A second camera would need a second worker lifecycle. | High | Introduce a `CaptureSupervisor` wrapper that initially manages one worker. |
| Capture queue ownership | `indi_allsky/allsky.py` | `__init__`, `_startCaptureWorker`, `_stopCaptureWorker` | Creates one `self.capture_q` and sends stop/control commands to one worker. | Commands such as stop/settime cannot target a specific camera. | Medium | Replace direct queue ownership with per-profile queue handles while preserving the existing single queue for default profile. |
| Capture error ownership | `indi_allsky/allsky.py` | `_startCaptureWorker` | Reads one `capture_error_q`. | One failed worker would be treated as the capture failure for the whole service. | Medium | Store one error queue per capture profile. Keep global behavior for primary profile. |
| Shared exposure state | `indi_allsky/allsky.py` | `__init__` | Creates one `exposure_av` array. | IMX708 and ASI678MC need independent current/next/min/max/SQM exposure state. | High | Create a `CaptureRuntimeState` object per profile. Initially contains the existing arrays for default profile. |
| Shared gain state | `indi_allsky/allsky.py` | `__init__` | Creates one `gain_av` array. | Cameras have different gain ranges and next gain decisions. | High | Move gain array into per-profile runtime state. |
| Shared binning state | `indi_allsky/allsky.py` | `__init__` | Creates one `binning_av` array. | ASI and libcamera binning support can differ. | Medium | Move binning array into per-profile runtime state. |
| Shared camera temp/sensor slots | `indi_allsky/allsky.py` | `__init__` | Creates one `sensors_temp_av` and one `sensors_user_av`. | Slot 0 is camera temp and camera SQM/ADU slots are camera-specific. Multiple workers would overwrite each other. | High | Split camera-specific sensor slots per profile; keep observatory/system/environment slots shared. |
| Shared day/night state | `indi_allsky/allsky.py`, `indi_allsky/capture.py` | `night_av`, `detectNight`, `reconfigureCcd` | One `night_av` drives day/night and moonmode. | Day/night is observatory-wide, but reconfigure side effects are camera-specific. Multiple workers writing the same array can race. | Medium | Make astro/day-night calculation global read-only; each profile reacts to it locally. |
| Shared astro state | `indi_allsky/allsky.py`, `indi_allsky/capture.py` | `astro_av`, `detectNight` | One worker computes and writes sun/moon values. | Multiple capture workers would duplicate writes and logs. | Low/Medium | Move sun/moon calculation to main/sensor/global state, or designate only primary profile writer. |
| Single capture worker config | `indi_allsky/capture.py` | `CaptureWorker.__init__` | Stores one `self.config`. | Worker cannot know which camera profile it belongs to or which settings are global vs per-camera. | Medium | Pass `global_config` plus `capture_profile`; build an effective per-camera config. |
| Camera backend selection | `indi_allsky/capture.py` | `_initialize` | Uses `config["CAMERA_INTERFACE"]` once to choose one camera client. | Only one backend is active per service instance. | High | Make backend selection use `capture_profile.camera_interface`. |
| INDI endpoint selection | `indi_allsky/capture.py` | `_initialize` | Uses one `INDI_SERVER`, `INDI_PORT`, and `INDI_CAMERA_NAME`. | ASI678MC needs its own INDI identity while IMX708 uses libcamera. | High | Move INDI connection settings into capture profile; keep old keys as default profile source. |
| libcamera identity | `indi_allsky/capture.py`, `indi_allsky/camera/libcamera.py` | `_initialize`, libcamera client classes | Uses one `LIBCAMERA.CAMERA_ID` and one libcamera interface. | Multiple CSI cameras require per-profile camera id/interface. | Medium | Move `LIBCAMERA.CAMERA_ID` and libcamera options into profile overrides. |
| Active DB camera id | `indi_allsky/capture.py` | `_initialize` | Sets `self.camera_id` and writes `_miscDb.setState("DB_CAMERA_ID", camera.id)`. | A second capture worker would overwrite the same global active camera state. | High | Add namespaced state such as `CAPTURE_PROFILES.<profile_id>.DB_CAMERA_ID`; primary profile may also write legacy key. |
| Camera name/server state | `indi_allsky/capture.py` | `_initialize` | Writes `CAMERA_NAME` and `CAMERA_SERVER` global state. | Multiple workers would overwrite each other; UI would show whichever wrote last. | High | Namespace state by profile. Keep legacy keys for primary camera only. |
| Global capture status | `indi_allsky/allsky.py`, `indi_allsky/capture.py` | `_startup`, `_initialize`, exception paths | Writes one `STATUS`. | One camera can be healthy while another is disconnected. Global status cannot represent partial failure. | High | Add per-profile status and aggregate service status. |
| Capture loop transition actions | `indi_allsky/capture.py` | `saferun` | On day/night transitions, generates outputs for `self.camera_id`. | Logic is per-camera but controlled by one worker/state. It will work per worker only after state isolation. | Medium | Keep generation per worker, but gate outputs with per-profile output settings. |
| Timelapse flag | `indi_allsky/capture.py` | `self.generate_timelapse_flag` | One boolean per worker today because there is one worker. | Safe if each camera has its own worker; unsafe if a single worker handles many cameras. | Low if one worker per camera | Do not multiplex cameras inside one worker. Preserve per-worker flag. |
| Queue backpressure | `indi_allsky/capture.py` | `saferun` | Uses total `image_q.qsize()` to slow one camera. | With two cameras, a heavy ASI queue can throttle IMX708 or vice versa. | High | Add per-camera queue metrics later; for MVP start with global safety throttle and monitor. |
| Focus mode | `indi_allsky/capture.py` | `CaptureWorker.__init__`, `saferun` | One global `FOCUS_MODE` changes cadence. | Focusing ASI should not force IMX708 into focus cadence. | Medium | Move focus mode to per-profile capture settings. |
| SQM cadence | `indi_allsky/capture.py` | `CAMERA_SQM` fields, SQM exposure path | One camera SQM setting and one SQM timer. | ASI and IMX708 may have different SQM suitability and exposure. | Medium | Make `CAMERA_SQM` per-profile; disable on secondary MVP profile. |
| CCD config | `indi_allsky/capture.py` | `reconfigureCcd` | Uses one `INDI_CONFIG_DEFAULTS`, `INDI_CONFIG_DAY`, cooling config, gain/binning config. | Different devices need different INDI properties and gain/exposure ranges. | High | Move CCD/INDI config blocks into per-profile overrides. |
| Day/night output gates | `indi_allsky/capture.py` | `_generateDayTimelapse`, `_generateNightTimelapse`, `_generateDayKeogram`, `_generateNightKeogram` | Uses global `TIMELAPSE_ENABLE`, `DAYTIME_TIMELAPSE`, `FISH2PANO.ENABLE`. | Secondary camera may need images-only while primary keeps full all-sky products. | Medium | Add per-profile output toggles before enabling second worker broadly. |
| Service lifecycle | `indi_allsky/allsky.py` | main loop start/stop/reload | Starts/stops capture, image, video, upload workers as one bundle. | Per-camera restart/pause is impossible. One camera failure tends to restart whole capture path. | High | Add `CaptureSupervisor` with per-profile worker handles; keep image/video/upload global. |
| Reload behavior | `indi_allsky/allsky.py` | config reload path around `self._reload` | Reload replaces one `self.config`. | Multi-camera needs compare/reload profile set and restart only affected capture workers. | High | First support reload of one default profile; later diff profiles. |
| Manual main tasks | `indi_allsky/allsky.py` | manual task routing around `TaskQueueQueue.MAIN` | Some tasks send commands to one `capture_q`. | Manual capture commands cannot target camera/profile. | Medium | Add optional `profile_id` to task data and route to profile queue. |
| Location update | `indi_allsky/allsky.py`, `indi_allsky/capture.py` | `updateConfigLocation` | Updates global config and one camera row. | Location is observatory-wide, but camera row updates need target camera semantics. | Low/Medium | Keep global location; update all active/local camera rows or primary only explicitly. |
| Image worker config | `indi_allsky/image.py` | `ImageWorker.__init__` | Receives one global config and shared arrays. | Processing options may differ per camera, but worker only knows global config. | High | Include profile/effective processing config in image job or lookup by `camera_id`. |
| Image worker raw/libcamera detection | `indi_allsky/image.py` | `processImage` | Checks global `config["CAMERA_INTERFACE"]` to decide libcamera raw handling. | ASI and IMX708 jobs in same queue can need different handling. | High | Put camera interface/raw flags in image job metadata; stop using global `CAMERA_INTERFACE` for per-image decisions. |
| Image filename template cache | `indi_allsky/image.py` | `self.filename_t` | Worker mutates `self.filename_t` from image job. | Shared worker processing multiple cameras can leak one camera's template into another job if job lacks template. | Medium | Require `filename_t` in every image job or make it local to `processImage`. |
| ImageProcessor config | `indi_allsky/image.py`, `indi_allsky/processing.py` | `ImageWorker.__init__`, `ImageProcessor` | One `ImageProcessor` is constructed from one config and shared arrays. | Rotation, crop, lens geometry, denoise, overlays, FISH2PANO, calibration can differ per camera. | High | Create per-camera/per-job processing config or processor cache keyed by profile/camera id. |
| Realtime keogram state | `indi_allsky/image.py`, `indi_allsky/processing.py` | `ImageProcessor.realtimeKeogramDataSave`, realtime keogram data | Processor state is worker-wide. | Realtime keogram accumulation can mix cameras if shared. | High | Store realtime keogram state per camera id. |
| ADU/stars/SQM histories | `indi_allsky/image.py` | `hist_adu`, `getSqmData`, `getStarsData` | Some histories are worker instance fields, while DB queries are camera-scoped. | Worker-wide in-memory histories can mix cameras. | Medium | Key in-memory histories by camera id. |
| Metadata/upload naming | `indi_allsky/image.py`, `miscUpload.py` | metadata upload jobs | Uses camera id/uuid in filenames but global upload config. | Upload credentials can be shared, but upload enablement and remote naming may need per-camera overrides. | Medium | Keep upload workers shared, but pass per-camera upload flags/templates in job data. |
| Video worker config | `indi_allsky/video.py` | `VideoWorker.__init__`, generation methods | Receives one global config. | Queries are camera-scoped, but generation gates/templates are global. | Medium | Keep video worker shared; make task data include per-camera output config when needed. |
| Task queue state | `models.py`, `allsky.py`, `capture.py`, `video.py`, `miscUpload.py` | `IndiAllSkyDbTaskQueueTable.data` | Tasks often carry `camera_id`, but not `profile_id`. | `camera_id` is enough after DB row exists, but startup/reconfigure tasks may need profile identity before camera registration. | Medium | Add optional `profile_id` to task data; do not require schema migration if JSON data is enough. |
| Misc DB current camera helper | `indi_allsky/flask/miscDb.py` | `getCurrentCameraId` | Reads global `DB_CAMERA_ID`. | Cannot represent multiple active cameras. | High | Add `getCurrentCameraId(profile_id=None)` compatibility path; use namespaced state when profile is supplied. |
| Current camera UI | `indi_allsky/flask/base_views.py` | `cameraSetup`, `getLatestCamera`, camera selector | One selected `self.camera` per request/session. | UI can browse cameras, but runtime status is not per active profile. | Medium | Separate "selected for browsing" from "capturing profile status". |
| Notifications | `allsky.py`, `capture.py`, `image.py` | notification keys such as `image_queue_depth`, `no_camera`, `no_indiserver` | Keys are global and can collide across cameras. | One camera's failure can overwrite/suppress another's notification. | Medium | Prefix notification keys with profile id for capture-specific issues. |
| PID/service model | `indi_allsky/allsky.py` | `write_pid`, service start | One service process and one PID lock. | This is acceptable for supervised multi-camera; not a blocker if workers are child processes. | Low | Keep one service process; do not run multiple full app instances as MVP. |

## Pipeline Notes

### Capture Pipeline

The capture path is the hardest part because it owns camera connection, exposure cadence, day/night transitions, and current camera state. It should become profile-aware before any second camera worker starts.

Minimum safe direction:

- keep one `CaptureWorker` per camera
- do not make one worker multiplex multiple cameras
- isolate per-camera queues and arrays
- keep DB/media writes using `camera_id`

### Image Processing Pipeline

The image pipeline is already fed with `camera_id`, filename, exposure, gain, binning, and other per-frame values. That is promising.

The blockers are worker-wide/global config decisions:

- global `CAMERA_INTERFACE`
- global processing settings
- global `ImageProcessor`
- worker-wide realtime keogram/ADU state

Minimum safe direction:

- include camera interface and processing profile in each image job
- make processing state keyed by `camera_id`
- keep one shared image queue initially

### Video/Generated Media Pipeline

Video and generated media tasks are already largely camera-scoped through `camera_id`.

The main missing piece is per-camera output gating:

- primary IMX708 can keep timelapse/keogram/startrails
- ASI678MC should start images-only

Minimum safe direction:

- keep one video worker initially
- pass output settings in task data or resolve from camera profile

### Task Queue

The task queue can carry arbitrary JSON data, so it can likely support `profile_id` without a schema migration.

Use:

```json
{
  "camera_id": 12,
  "profile_id": "asi678mc"
}
```

`camera_id` remains the durable media/DB identity. `profile_id` identifies runtime worker/profile.

## First 5 Safe Changes

1. Add a pure capture profile normalizer.
   - No runtime behavior change.
   - Converts current config into a `default` profile.
   - Enables tests and Modern Admin diagnostics.

2. Add profile-aware state key helpers.
   - No behavior change if default profile still writes legacy keys.
   - Example: `capture_state_key(profile_id, "DB_CAMERA_ID")`.

3. Introduce a `CaptureRuntimeState` container for existing arrays.
   - Initially wrap existing arrays only.
   - Do not allocate multiple states yet.

4. Refactor `CaptureWorker.__init__` to accept optional `capture_profile` and `runtime_state`.
   - Default arguments preserve current behavior.
   - Worker still runs one camera.

5. Make image job metadata carry camera interface/profile id.
   - Add fields to queue payload only.
   - Do not change processing behavior until the field is present and observable.

## What Not To Touch Yet

- Do not start a second `CaptureWorker` yet.
- Do not change systemd service layout.
- Do not run two full indi-allsky app instances as the official plan.
- Do not change DB schema until profile/state compatibility is proven.
- Do not migrate classic admin config UI yet.
- Do not make output generation per-camera until capture state is isolated.
- Do not change image processing algorithms while making runtime structural changes.
- Do not enable ASI678MC timelapse/keogram/startrails in the first simultaneous capture test.

## Recommended First Code Change

The first implementation should be a no-behavior-change helper:

```text
derive_capture_profiles(config) -> [CaptureProfile]
```

It should produce exactly one default profile from the current config. The rest of the multi-camera work should build on that shape.

That is the safest first move because it creates the future runtime contract without touching service lifecycle, queues, workers, DB schema, or processing behavior.
