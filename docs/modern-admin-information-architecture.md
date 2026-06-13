# Modern Admin Information Architecture

This document defines the intended product structure for the future Modern Admin. The goal is to keep the modern UI coherent and user-facing while preserving Classic Admin as the complete fallback for advanced configuration, maintenance, and risky controls.

Modern Admin should feel like an observatory control surface, not a database console. Pages should be organized around user outcomes: seeing the sky, understanding camera health, managing storage, publishing data, checking observatory conditions, maintaining the system, and applying updates.

## Current Surfaces

Classic Admin currently exposes a broad technical navigation:

- Latest and Loop
- Media: Gallery, Images, Timelapses, Mini-Timelapses, Panorama, Panorama Loop, Realtime Keogram, Long Term Keogram, FITS Viewer
- Info: SQM, Charts, Sensor Panel, Dark Library, ADU History, Image Lag, File Space Usage, Camera Info
- Tools: VirtualSky, Camera Simulator, Astropanel, Generate, Focus, FITS Processing, Image Circle Helper, Mask Base, Log, Support Info
- System: Config, Network, Drives, GPIO Control, System Info
- Hidden/admin routes: Cameras, Tasks, Notifications, Users

Modern Admin currently has:

- `/indi-allsky/modern-admin`: dashboard with latest image, selected camera identity, capture status, storage, upload placeholder, recent events placeholder, and Classic Admin link.
- `/indi-allsky/modern-admin/cameras`: read-only camera inventory with active camera, camera cards, last image age, and future Add/Configure placeholders.

## Product Principles

- Keep the top-level structure small.
- Prefer human concepts over implementation names.
- Show a calm overview first; put details one click deeper.
- Keep write actions separate from status reading.
- Leave complex, destructive, or expert workflows in Classic Admin until they have a deliberate modern design.
- Every Modern Admin section should provide a visible path back to Classic Admin.

## Top-Level Navigation

Recommended top-level navigation:

1. Dashboard
2. Cameras
3. Storage
4. Uploads
5. Observatory
6. System
7. Updates

## Dashboard

Purpose:

Dashboard is the daily landing page. It should answer: Is the system alive? Is the active camera capturing? Is the latest image fresh? Is anything urgent?

Real data already available:

- Latest image URL via `TemplateView.latest_image_entry` and `getUrl()`.
- Latest image age and timestamp.
- Selected camera name/friendly name.
- Camera driver/interface.
- Capture status normalized from `get_indi_allsky_status()`.
- Image filesystem storage capacity via `psutil.disk_usage()`.

Data still missing:

- Human-friendly health summary.
- Recent event stream.
- Upload/sync state.
- Storage warning thresholds.
- Capture cadence and expected next frame time.
- Clear distinction between camera health, capture health, and web app health.

Candidate future actions:

- Open Cameras.
- Open Storage.
- Open Uploads.
- Acknowledge low-risk notifications.
- Pause/resume capture only after a dedicated safety design.

Should stay in Classic Admin initially:

- Full Config.
- Manual GPIO controls.
- Service restart/shutdown/reboot controls.
- FITS processing and generation tools.
- User administration.

## Cameras

Purpose:

Cameras is the product-facing inventory and health view for camera devices. It should answer: Which camera is active? What cameras are known? Are they available? When did each last produce an image?

Real data already available:

- Current selected camera from session setup.
- Non-hidden camera rows from `IndiAllSkyDbCameraTable`.
- Camera friendly name/name.
- Camera driver/interface.
- Active camera state.
- Per-camera latest image age from `IndiAllSkyDbImageTable`.
- Capture status for the active camera.

Data still missing:

- True per-camera online/offline state.
- Camera detection/discovery status.
- Camera capability summary.
- Friendly camera model separate from driver.
- Sensor size, resolution, pixel size as product-facing details.
- Last connection time phrased for humans.

Candidate future actions:

- Add Camera.
- Configure Camera.
- Rename Camera.
- Select Active Camera.
- Test Capture.
- View Camera Details.

Should stay in Classic Admin initially:

- Driver-level configuration.
- Advanced camera simulator controls.
- Image circle helper.
- Mask base editor.
- Focus controls.
- Any add/edit/delete camera action until validation and rollback behavior are designed.

## Storage

Purpose:

Storage explains where images and videos live, how much space remains, and whether retention is safe.

Real data already available:

- Filesystem capacity, used, free, and percent used for configured image storage via `psutil.disk_usage()`.
- Classic File Space Usage route with database aggregate media sizes by day/type.
- Existing image/video database rows with file sizes.
- Existing configured image folder.

Data still missing:

- Product-level retention summary.
- Days remaining estimate.
- Per-camera storage usage.
- Breakdown by images, timelapses, panoramas, raw, FITS, thumbnails.
- Storage warning/critical thresholds.
- External drive health and mount stability.

Candidate future actions:

- Open retention settings.
- Review large media groups.
- Export/download storage report.
- Open Classic File Space Usage.
- Later: safe cleanup recommendations, but not automatic deletion at first.

Should stay in Classic Admin initially:

- Actual file deletion.
- Drive manager mount/unmount actions.
- Config changes affecting retention.
- Raw/FITS cleanup flows.
- Any destructive bulk operation.

## Uploads

Purpose:

Uploads shows whether images and videos are leaving the device successfully. It should answer: Is remote publishing working? What is queued, failed, or stale?

Real data already available:

- Config contains upload and sync-related settings.
- SyncAPI routes exist.
- File transfer/upload modules exist.
- Task queue models exist.
- Classic config includes upload-related sections.

Data still missing:

- Human-friendly upload destination summary.
- Last successful upload.
- Queue depth.
- Failure reason.
- Per-target status.
- Transfer bandwidth/retry state.
- Remote storage destination health.

Candidate future actions:

- View upload targets.
- Test connection.
- Retry failed uploads.
- Pause/resume upload queue.
- Open target-specific settings.

Should stay in Classic Admin initially:

- Credential editing.
- S3/GCS/OCI advanced config.
- SyncAPI secrets.
- YouTube authorization/revoke.
- Any destructive queue manipulation.

## Observatory

Purpose:

Observatory groups environmental and sky-context information: sensors, sky quality, weather, smoke, aurora, moon/sun, and visibility context.

Real data already available:

- SQM view.
- Charts.
- Sensor Panel.
- AstroPanel.
- VirtualSky.
- Aurora, smoke, astrometric, sun/moon status helpers in existing views.
- Latest image metadata includes sensor-style fields.

Data still missing:

- Unified observatory health summary.
- Sensor freshness indicators.
- Weather provider state.
- Forecast summary.
- Human-friendly sky condition assessment.
- Site identity/location card.

Candidate future actions:

- View sensor details.
- Open charts.
- Open VirtualSky.
- Open AstroPanel.
- Configure observatory location after design.

Should stay in Classic Admin initially:

- Sensor configuration.
- Location/config editing.
- VirtualSky helper controls.
- Image circle and mask tools.
- Advanced weather provider settings.

## System

Purpose:

System explains the health of the device and services without exposing users to every low-level control by default.

Real data already available:

- System Info page.
- Service status endpoints and system controls in classic views.
- Logs.
- Support Info.
- Network Manager.
- Drive Manager.
- Task queue.
- Notifications.
- User info/users.

Data still missing:

- Modern health summary.
- Service health normalized for humans.
- CPU/memory/temperature overview as product cards.
- Network identity/status summary.
- Log severity summary.
- User-safe diagnostic bundle flow.

Candidate future actions:

- View logs.
- Download support bundle.
- Open network details.
- Open drive details.
- Review notifications.
- View task queue.

Should stay in Classic Admin initially:

- Reboot/shutdown.
- Service restart controls.
- Network changes.
- Drive mount/unmount.
- GPIO control.
- User management.
- Advanced logs and raw system info.

## Updates

Purpose:

Updates should explain software version, update availability, and maintenance posture without surprising the user.

Real data already available:

- Version module.
- Upgrade service template.
- README/update guidance.
- Existing support/system info routes can expose version context.

Data still missing:

- Current git/ref state.
- Upstream/fork comparison.
- Update availability check.
- Last update time.
- Migration status.
- Safe release notes summary.

Candidate future actions:

- Check for updates.
- Review current version.
- View update notes.
- Start guided update only after a robust safety design.

Should stay in Classic Admin initially:

- Actual upgrade execution.
- Migration repair.
- Manual git operations.
- Service restarts tied to updates.

## Classic Admin Boundary

Classic Admin remains the source of truth for full functionality. Modern Admin should initially link to Classic Admin for advanced workflows rather than duplicating them.

Keep in Classic Admin until explicitly redesigned:

- Full configuration editor.
- Any action that writes config.
- Camera add/edit/delete.
- Capture generation jobs.
- Focus control.
- GPIO control.
- Network changes.
- Drive mount/unmount.
- Service restart/reboot/shutdown.
- User administration.
- Credential management.
- Upload secrets and OAuth flows.
- Bulk deletion or cleanup.

## Suggested Build Order

1. Stabilize Dashboard read-only cards.
2. Finish Cameras as read-only inventory and detail pages.
3. Add Storage read-only page using filesystem and media aggregate data.
4. Add Uploads read-only status.
5. Add Observatory overview from existing sensors/sky helpers.
6. Add System health overview with links to classic diagnostics.
7. Add Updates read-only version/status page.
8. Design write actions one by one, with Classic Admin as fallback.

## Naming Guidance

Use product language:

- Dashboard, Cameras, Storage, Uploads, Observatory, System, Updates.
- Active Camera, Latest Image, Last Image, Available Cameras.
- Storage Remaining, Upload Health, Observatory Conditions.

Avoid top-level technical labels:

- Config.
- Task Queue.
- AJAX.
- GPIO.
- Driver tables.
- Raw database names.

Those concepts can remain in Classic Admin or appear as secondary metadata where useful.
