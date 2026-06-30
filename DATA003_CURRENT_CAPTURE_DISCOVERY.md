# DATA003 - Current Capture Status Discovery

## Scope

This discovery looks for an existing, read-only source for **Current Capture Status**.

Desired metadata:

- capture running / idle / paused / error / unknown;
- last capture time if already available safely;
- current camera/profile if already available safely;
- day/night capture mode if already available safely;
- cadence if already available safely;
- recent capture error status if already persisted safely.

Out of scope:

- camera connection;
- INDI/libcamera calls;
- process probing;
- hardware checks;
- filesystem reads;
- polling;
- image/media generation;
- runtime actions.

## Candidate 1 - `BaseView.get_indi_allsky_status()`

**Source**

Existing status helper backed by persisted indi-allsky state.

**Location**

- `indi_allsky/flask/base_views.py`
- `BaseView.get_indi_allsky_status()`

**Status types covered**

- `REMOTE`
- `UNKNOWN`
- `DOWN`
- `FOCUS MODE`
- `RUNNING`
- `SLEEPING`
- `RELOADING`
- `STARTING`
- `STOPPING`
- `STOPPED`
- `PAUSED`
- `NO CAMERA`
- `CAMERA ERROR`
- `NO INDISERVER`

**Used by**

- Classic/JSON status context.
- Modern Admin shell indirectly through `ModernAdminView.get_capture_status_label()`.

**Pros**

- Already exists.
- Uses persisted state (`WATCHDOG`, `STATUS`) rather than camera probing.
- Does not connect to camera hardware.
- Covers more capture/runtime states than a simple latest-frame timestamp.
- Already normalized by Modern Admin into `Running`, `Idle`, `Paused`, `Unknown`.
- Good candidate for "is capture working?" at product level.

**Cons**

- Returns HTML-formatted status strings, not a clean domain value.
- Reads misc state through the existing DB/misc state layer.
- Contains an old notification side effect branch after watchdog checks, although that branch appears unreachable because an earlier identical watchdog check returns first.
- Does not provide last capture time, next frame, cadence, or profile.
- Needs a sanitizing adapter before Product UI use.

**Risk**

Medium.

The data is useful and bounded, but the source is not currently a clean product contract. It must be normalized into safe enum-like values and must not expose HTML.

**Suitable for Product UI?**

YES, with audit/adapter guards.

**Reason**

It is the best existing source for current runtime capture state because it reflects persisted indi-allsky status without hardware checks or filesystem reads.

## Candidate 2 - `ModernAdminView.get_capture_status_label()`

**Source**

Modern Admin normalization wrapper over `get_indi_allsky_status()`.

**Location**

- `indi_allsky/flask/views.py`
- `ModernAdminView.get_capture_status_label()`

**Status types covered**

- `Running`
- `Idle`
- `Paused`
- `Unknown`

**Used by**

- Modern Admin dashboard context as `modern_admin_capture_status`.

**Pros**

- Already removes HTML tags from the status helper.
- Already maps low-level statuses into a product-ish label.
- Read-only.
- No filesystem access.
- No camera/hardware probing.

**Cons**

- Loses important error distinctions such as `NO CAMERA`, `CAMERA ERROR`, `NO INDISERVER`, and `DOWN`.
- Still depends on the HTML status helper.
- Does not expose evidence/source fields.
- Not framework-free.

**Risk**

Low to medium.

The current label is safe but too lossy for a Product UI contract.

**Suitable for Product UI?**

CONDITIONAL.

**Reason**

Useful as evidence of the desired mapping, but a future adapter should normalize from the underlying status source rather than reuse this lossy label directly.

## Candidate 3 - Camera Model Capture Flags

**Source**

Camera DB row fields.

**Location**

- `indi_allsky/flask/models.py`
- `IndiAllSkyDbCameraTable`
- fields: `daytime_capture`, `daytime_capture_save`, `capture_pause`, `local`, camera identity fields.

**Status types covered**

- capture pause configured for the camera;
- daytime capture enabled/disabled;
- daytime save enabled/disabled;
- local/remote camera mode;
- current camera identity.

**Used by**

- `BaseView.cameraSetup()`.
- latest-image/status logic.
- Modern Admin and settings pages.

**Pros**

- DB metadata only.
- Already loaded into request context in many views.
- Good for explaining whether capture is intentionally paused or gated by day mode.
- No camera probing.
- No filesystem.

**Cons**

- Configuration/state metadata, not live capture health.
- Does not prove capture is currently producing frames.
- Day/night behavior also requires phase context.
- Profile identity may require additional model/config context.

**Risk**

Low.

**Suitable for Product UI?**

YES, as supporting context.

**Reason**

Good for current capture policy and pause state, but insufficient as the only source for current status.

## Candidate 4 - Latest Image DB Metadata

**Source**

Latest image row metadata already used in modern/dashboard/latest image contexts.

**Location**

- `IndiAllSkyDbImageTable`
- `BaseView.latest_image_entry`
- `JsonLatestImageView`
- `ModernAdminView` latest image context.

**Status types covered**

- last frame timestamp;
- image age;
- camera id;
- capture metadata such as exposure/gain/binning where present.

**Used by**

- Classic latest image views.
- Modern Admin dashboard.
- DATA001 latest frame metadata.

**Pros**

- Canonical latest frame metadata source.
- Already integrated safely for DATA001.
- Can help infer whether capture produced a recent frame.
- Bounded query pattern already exists in Product UI.

**Cons**

- Not a capture service/status source by itself.
- A stale latest frame could mean pause, day gate, service down, camera error, remote save disabled, or no recent images.
- Existing view helpers often mix metadata with URLs, filesystem, or latest image routing.
- Must not reuse image URL helpers.

**Risk**

Medium.

**Suitable for Product UI?**

YES, as supporting evidence only.

**Reason**

Useful for "last capture time" but not enough to decide running/idle/error without the persisted status source.

## Candidate 5 - `/ajax/status_update` / Status Text Context

**Source**

JSON status endpoint/context that combines `get_indi_allsky_status()` with status text and extra web text.

**Location**

- `indi_allsky/flask/views.py`
- `AjaxStatusUpdateView`
- `BaseView.get_context()`

**Status types covered**

- user-facing status text;
- web extra text;
- page status fragments.

**Used by**

- Classic/shared status UI.

**Pros**

- Existing user-facing status source.
- Already used in production UI.

**Cons**

- Produces presentation-oriented text/HTML.
- Not a clean domain/source contract.
- May include extra context not appropriate for Product UI.
- Endpoint reuse would couple Product UI to shared AJAX behavior.

**Risk**

Medium.

**Suitable for Product UI?**

NO.

**Reason**

Good evidence of existing behavior, but Product UI should consume sanitized source data, not AJAX response text.

## Candidate 6 - Modern Capture Service Status Helper

**Source**

Systemd service status helper.

**Location**

- `indi_allsky/flask/views.py`
- `get_modern_admin_capture_service_status()`

**Status types covered**

- systemd `active` / `failed` / stopped-ish state;
- service running boolean;
- start/stop labels for existing control UI.

**Used by**

- Modern Admin shell/topbar/service controls.
- `/modern-admin/capture/service`.

**Pros**

- Clear service-level status.
- Already used by Modern Admin.
- Could explain whether the capture service unit is active.

**Cons**

- Calls `systemctl --user is-active` through subprocess.
- Runtime process/service probing is explicitly out of scope for DATA003 discovery target.
- Includes toggle labels/action concepts that are not Product UI read-only status.
- Does not prove camera is capturing frames.

**Risk**

High for DATA003.

**Suitable for Product UI?**

NO for the first current capture status integration.

**Reason**

It violates the "no process/service probing" spirit for this phase. It may be useful later for Observatory readiness, not Now current capture status.

## Candidate 7 - Frame Metadata Analytics

**Source**

Frame metadata files and analytics helpers.

**Location**

- `indi_allsky/frame_metadata_analytics.py`
- `FrameMetadataAnalytics`
- `ModernAdminView.get_modern_admin_dashboard_context()`

**Status types covered**

- latest metadata per camera;
- recent frames;
- exposure/gain/meter;
- quality/decision statistics.

**Used by**

- Modern Admin dashboard.

**Pros**

- Rich capture metadata.
- Can provide recent frame and quality context.
- Already used for dashboard cards.

**Cons**

- Reads metadata directories/files.
- Potentially scans recent history.
- More than one bounded data point.
- Not appropriate for DATA003 first integration.

**Risk**

High for this phase.

**Suitable for Product UI?**

NO for DATA003.

**Reason**

Useful future analytics source, but violates the no-filesystem/no-heavy requirement for current capture status.

## Candidate 8 - Task Queue

**Source**

Task queue DB table.

**Location**

- `indi_allsky/flask/models.py`
- `IndiAllSkyDbTaskQueueTable`
- Modern task queue views.

**Status types covered**

- queued/running/success/failed/expired task state;
- queue name;
- task action;
- task result/message.

**Used by**

- Modern and Classic task queue pages.
- Generation/upload/action workflows.

**Pros**

- Persisted DB source.
- Useful for background jobs.
- Can reveal recent generation/upload failures.

**Cons**

- Does not represent the main capture loop status.
- `data` and `result` can contain arbitrary action/error payloads.
- More useful for generation/automation status than capture status.

**Risk**

Medium.

**Suitable for Product UI?**

NO for current capture status.

**Reason**

It may support future Observatory/Automation status, but not the primary "is capture running?" question.

## Candidate 9 - Latest Image JSON Logic

**Source**

Latest image JSON view logic.

**Location**

- `indi_allsky/flask/views.py`
- `JsonLatestImageView.get_objects()`

**Status types covered**

- no image for 15 minutes;
- capture paused;
- daytime capture disabled;
- latest image available.

**Used by**

- Classic/latest image frontend.

**Pros**

- Encodes useful product messages.
- Already handles capture pause and day capture gates.

**Cons**

- Mixes status with image URL construction.
- Reads filesystem in focus/daytime-unsaved branches.
- Uses request args and presentation messages.
- Not cleanly reusable for Product UI.

**Risk**

High.

**Suitable for Product UI?**

NO.

**Reason**

Good behavioral evidence, but unsafe as a Product UI data source because it mixes metadata with URL/filesystem behavior.

## Best Source Recommendation

There is **no single complete source** for Current Capture Status.

Recommended future approach: **composite, with one primary source**.

Primary source:

- `BaseView.get_indi_allsky_status()` / persisted misc state (`WATCHDOG`, `STATUS`).

Supporting sources:

- current camera row fields (`capture_pause`, `daytime_capture`, `daytime_capture_save`, `local`, camera label);
- DATA001 latest frame metadata for last capture timestamp/age;
- existing `context['night']` for day/night phase.

Do not use for first integration:

- systemd service helper;
- frame metadata analytics directories;
- latest image JSON view;
- AJAX status response;
- task queue;
- filesystem-derived latest image checks.

## Why Composite Is Required

`get_indi_allsky_status()` can answer whether the capture process appears running, sleeping, paused, stopped, down, or in camera error state. It cannot explain capture policy gates or last frame recency.

Camera row flags explain intentional capture policy. Latest frame metadata explains recent output from the capture loop. Phase context explains day/night interpretation.

Together they can answer:

- is capture believed to be running?
- is capture intentionally paused?
- is day capture disabled?
- when did the latest frame metadata arrive?
- is the current phase day/night/unknown?

This should be designed as a bounded adapter in the next audit/adapter phase, not wired directly from presentation helpers.

## Main Risks

- `get_indi_allsky_status()` returns HTML and must be normalized.
- It uses misc DB state and may have legacy notification behavior in unreachable or edge branches.
- Latest frame timestamp is evidence of recent capture, not proof of current service health.
- Camera flags are configuration state, not live runtime status.
- Service status helper is tempting but should be avoided for DATA003 because it probes systemd.
- Filesystem-based latest image logic must not be reused.

## Discovery Verdict

**Composite source recommended.**

Best primary source: persisted indi-allsky status via `BaseView.get_indi_allsky_status()` / misc state.

Best supporting sources:

- current camera DB fields;
- DATA001 latest frame metadata;
- existing phase context.

Next step should be a DATA003 audit that defines:

- allowed status values;
- allowed camera fields;
- allowed latest-frame evidence fields;
- forbidden HTML/presentation text;
- no service probing;
- no filesystem access;
- no process checks;
- fallback behavior.
