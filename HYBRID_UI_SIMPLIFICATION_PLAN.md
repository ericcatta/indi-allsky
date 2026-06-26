# HYBRID UI SIMPLIFICATION PLAN

Audit date: 2026-06-26

Scope: documentation-only audit for Modern UI consolidation and future Classic UI
removal. No code, route, template, config, asset, schema or runtime change is made
by this document.

## 1. Executive Summary

Hybrid AllSky currently contains two UI worlds:

- Classic UI: the inherited indi-allsky interface under root-level routes such as
  `/config`, `/gallery`, `/imageviewer`, `/system`, `/focus`, `/processing`,
  `/generate`, `/network`, `/drives`, `/tasks`, `/users` and many AJAX/JSON
  helpers.
- Modern UI: the newer `/modern-admin` experience, with a modern shell,
  multi-camera/profile operation, Camera Settings, Modern Full Settings,
  metadata analytics, quality score, environmental awareness and Event Foundation
  diagnostics.

The Modern UI is already the operational center for Hybrid-specific work:
multi-camera, camera profiles, profile-first acquisition settings, Auto Exposure,
Auto Gain, Hybrid AWB, metadata analytics, dashboard quality summaries,
Environmental Awareness, Event Foundation diagnostics and scientific source
readiness are all designed around Modern Admin concepts.

Classic UI cannot be removed safely yet. It still owns or directly exposes many
operational surfaces: full legacy config editing, image/FITS/video viewers,
manual timelapse generation, image processing tools, focus, GPIO, network/drive
management, users, notifications, task queue, YouTube auth, and several public
or external routes. Modern Admin wraps some of these using `safe_controls.html`
or subclasses of legacy views, so parity is partial rather than complete.

Realistic removal status:

- Modern-first direction is clear.
- Hybrid-specific settings should continue moving to Modern profile-first pages.
- Classic removal is blocked by missing parity for several admin tools and by
  unknown external use of legacy routes/API.
- The safe path is: map, finish parity, redesign settings, add deprecation
  layer, then remove in micro-steps.

## 2. Current UI Architecture

### Classic UI Structure

Classic UI is mostly registered in `indi_allsky/flask/views.py` through
`bp_allsky.add_url_rule(...)` near the end of the file. It uses:

- base template: `indi_allsky/flask/templates/base.html`
- classic CSS: `indi_allsky/flask/static/css/style.css`
- shared libraries: Bootstrap, jQuery, DataTables, Chart.js, PhotoSwipe,
  VirtualSky, Astropanel assets
- inline page JavaScript embedded directly in most legacy templates
- WTForms monolithic config form in `indi_allsky/flask/forms.py`

Classic UI routes include public views, media viewers, generator tools,
configuration, system/admin pages and hidden maintenance pages.

### Modern UI Structure

Modern UI is rooted at `/modern-admin` in `indi_allsky/flask/views.py`.
Important Modern classes include:

- `ModernAdminView`
- `ModernAdminCamerasView`
- `ModernAdminCameraAddView`
- `ModernAdminStorageView`
- `ModernAdminUploadsView`
- `ModernAdminObservatoryView`
- `ModernAdminSystemView`
- `ModernAdminSettingsInventoryView`
- `ModernAdminFullSettingsView`
- `ModernAdminCameraSettingsView`
- `ModernAdminCaptureSettingsView`
- `ModernAdminMediaListView`
- `ModernAdminMediaGalleryView`

Modern UI templates live under `indi_allsky/flask/templates/modern_admin/`.
Modern styling is centralized in
`indi_allsky/flask/static/modern_admin/modern-admin.css`.

Modern UI currently uses three patterns:

1. Native Modern pages, for example dashboard, cameras, camera settings, media
   list, storage, settings inventory.
2. Modern wrappers around legacy view logic via `ModernAdminContextMixin`.
3. Safe control wrappers via `modern_admin/safe_controls.html` for pages that
   are not yet truly ported.

### Main Route Families

| Family | Classic examples | Modern examples | Notes |
| --- | --- | --- | --- |
| Latest/public image | `/`, `/index_img`, `/loop`, `/raw`, `/panorama` | `/modern-admin`, `/modern-admin/loop` | Modern dashboard uses metadata and latest DB image context. Public root still Classic. |
| Media | `/gallery`, `/imageviewer`, `/fitsimageviewer`, `/videoviewer` | `/modern-admin/media/*` | Modern media list is read-only and profile/camera filter aware. |
| Config | `/config`, `/ajax/config`, `/config/list`, `/config/restore` | `/modern-admin/settings/*` | Modern has inventory/full/capture/camera settings but still shares backend concepts. |
| Camera/admin | `/camera`, `/lag`, `/adu`, `/darks`, `/mask`, `/camerasimulator` | `/modern-admin/cameras/*` | Mixed native Modern and legacy wrappers. |
| Observatory | `/sqm`, `/charts`, `/sensor_panel`, `/astropanel`, `/virtualsky`, `/realtime_keogram`, `/longtermkeogram` | `/modern-admin/observatory/*` | Some Modern pages reuse classic JSON/data sources. |
| System/tools | `/system`, `/log`, `/support`, `/network`, `/drives`, `/manual_gpio`, `/focus`, `/processing` | `/modern-admin/system/*`, `/modern-admin/tools/*` | Several are wrappers/safe controls, not full native ports. |
| Background/API | `/ajax/*`, `/js/*`, `/sync/v1/*`, `/action/*` | Mixed use | Must not remove until consumers are mapped. |

### API Dependencies

Classic and Modern share several APIs:

- `/js/charts` is used by Classic charts and Modern charts.
- `/js/log` backs Classic and Modern log surfaces.
- `/js/support` backs support pages.
- `/ajax/status_update` remains a shared status source.
- `/ajax/config` remains the save endpoint for Classic config and Modern full
  settings patterns.
- `/sync/v1/*` appears external/sync-facing and must be treated separately from
  UI cleanup.

## 3. Classic UI Inventory

Status meanings:

- `ported`: Modern equivalent appears native and covers the core use case.
- `partial`: Modern equivalent exists but wraps legacy logic, has reduced scope,
  or lacks full parity.
- `missing`: no clear Modern equivalent found.
- `obsolete`: likely no longer central to Hybrid, but must be verified.
- `unknown`: usage or parity cannot be established from static audit alone.

| Classic page | Route Flask | Template | JS/CSS associated | Functionality | Modern equivalent | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Public/latest image | `/`, `/index_img`, `/index_canvas`, `/js/latest` | `index_img.html`, `index_canvas.html` | `base.html`, inline JS | Public/latest image display | `/modern-admin` dashboard for admin; public clean page still not equivalent | partial |
| Latest panorama/raw | `/panorama*`, `/raw*`, `/js/latest_panorama`, `/js/latest_rawimage` | `index_img.html`, `index_canvas.html` | inline JS | Latest panorama/raw display | Modern media categories include panorama/FITS; raw parity unclear | partial |
| Image loop | `/loop*`, `/js/loop` | `loop_img.html`, `loop_canvas.html` | inline JS | Loop latest images | `/modern-admin/loop` wraps loop view | partial |
| Panorama/raw loops | `/looppanorama*`, `/loopraw*` | `loop_img.html`, `loop_canvas.html` | inline JS | Loop panorama/raw media | Modern media read-only categories; no full loop parity confirmed | partial |
| Realtime keogram | `/realtime_keogram` | `realtime_keogram.html` | inline JS | Realtime keogram display | `/modern-admin/observatory/realtime-keogram` | partial |
| SQM | `/sqm` | `sqm.html` | inline JS | SQM view | `/modern-admin/observatory/sqm` | partial |
| Charts | `/charts`, `/js/charts` | `chart.html` | Chart.js, inline JS | Sensor/ADU charts | `/modern-admin/observatory/charts`, dashboard 24h analytics | partial |
| Image viewer | `/imageviewer`, `/ajax/imageviewer`, `/ajax/exclude` | `imageviewer.html` | inline JS | DB image browsing/exclude | Modern media gallery read-only | partial |
| FITS viewer | `/fitsimageviewer`, `/ajax/fitsimageviewer`, `/fits2jpeg` | `fitsimageviewer.html` | inline JS | FITS browsing/conversion | Modern media FITS list only | partial |
| Gallery | `/gallery`, `/ajax/gallery` | `gallery.html` | PhotoSwipe, inline JS | Media gallery | `/modern-admin/media/gallery` | ported for core browsing; advanced parity unknown |
| Video viewer | `/videoviewer`, `/ajax/videoviewer` | `videoviewer.html` | inline JS | Timelapse/video browsing | `/modern-admin/media/timelapses` | partial |
| Mini video viewer | `/minivideoviewer`, `/ajax/minivideoviewer` | `minivideoviewer.html` | inline JS | Mini timelapse browsing | `/modern-admin/media/mini-timelapses` | partial |
| Media object views | `/view_image`, `/view_keogram`, `/view_startrail`, `/view_raw`, `/watch_*` | `view_image.html`, `watch_video.html` | clipboard JS | Open/download individual media | Modern media opens read-only URLs | partial |
| Timelapse generator | `/generate`, `/ajax/generate` | `generate.html` | DataTables, inline JS | Manual timelapse generation | `/modern-admin/tools/generate` safe control wrapper | partial |
| Mini timelapse generator | `/minigenerate`, `/ajax/minigenerate` | `mini_generate.html` | inline JS | Manual mini timelapse generation | no clear native Modern page | missing |
| Full config | `/config`, `/ajax/config` | `config.html` | huge inline JS | Monolithic settings editor | `/modern-admin/settings/full` | partial |
| Config list/download/restore | `/config/list`, `/config/download`, `/config/restore`, `/ajax/config/restore` | `config_list.html`, `config_restore.html` | DataTables/inline JS | Config history/export/restore | Modern inventory/full settings partly; restore parity unclear | partial |
| System info | `/system`, `/ajax/system`, `/ajax/settime`, `/ajax/settimezone`, `/ajax/indiserver` | `system.html` | inline JS | System/admin controls | `/modern-admin/system`, `/modern-admin/system/info` | partial |
| Focus | `/focus`, `/js/focus`, `/ajax/focuscontroller` | `focus.html` | Chart.js, inline JS | Focus graph/controller | `/modern-admin/tools/focus` safe control wrapper | partial |
| Manual GPIO | `/manual_gpio`, `/ajax/manual_gpio` | `manual_gpio.html` | inline JS | GPIO control | `/modern-admin/system/gpio-control` safe control wrapper | partial |
| Log | `/log`, `/js/log`, `/log/*_download` | `log.html` | inline JS | Log view/download | `/modern-admin/system/log` | partial |
| Support | `/support`, `/js/support` | `support_info.html` | clipboard JS | Support bundle | `/modern-admin/system/support` | partial |
| User profile | `/user`, `/ajax/user` | `user.html` | inline JS | Current user settings | no clear Modern native page | missing |
| Users | `/users` | `users.html` | DataTables | User admin | no clear Modern native page | missing |
| Notifications | `/notifications`, `/ajax/notification` | `notifications.html` | DataTables | Notification admin | no clear Modern native page | missing |
| Astro panel | `/astropanel`, `/ajax/astropanel` | `astropanel.html` | Astropanel assets | Astronomy panel | `/modern-admin/observatory/astropanel` | partial |
| Image processing | `/processing`, `/js/processing` | `imageprocessing.html` | inline JS | FITS/image processing tool | `/modern-admin/tools/process-fits` safe control wrapper | partial |
| Long-term keogram | `/longtermkeogram`, `/js/longtermkeogram` | `longterm_keogram.html` | inline JS | Long-term keogram | `/modern-admin/observatory/long-term-keogram` | partial |
| Camera/lens | `/camera` | `cameraLens.html` | inline JS | Camera/lens info | `/modern-admin/cameras/info` | partial |
| Lag | `/lag` | `lag.html` | DataTables | Image lag | `/modern-admin/cameras/image-lag` | partial |
| ADU history | `/adu` | `adu.html` | DataTables | ADU history | `/modern-admin/cameras/adu-history` | partial |
| Darks | `/darks` | `darks.html` | DataTables | Dark library | `/modern-admin/cameras/dark-library` | partial |
| Mask | `/mask` | `mask.html` | inline JS | Mask base | `/modern-admin/cameras/mask-base` | partial |
| Camera simulator | `/camerasimulator` | `camera_simulator.html` | clipboard/inline JS | Simulator controls | `/modern-admin/tools/camera-simulator` safe control wrapper | partial |
| Image circle helper | `/imagecirclehelper` | `imagecirclehelper.html` | inline JS | Circle helper | `/modern-admin/tools/image-circle-helper` safe control wrapper | partial |
| File space usage | `/filespaceusage` | `filespaceusage.html` | DataTables | Storage usage | `/modern-admin/storage/file-space-usage` | partial |
| Network | `/network`, `/ajax/network` | `network.html` | inline JS | Network management | `/modern-admin/system/network` safe control wrapper | partial |
| Drives | `/drives`, `/ajax/drives` | `drive_manager.html` | DataTables/inline JS | Drive management | `/modern-admin/storage/drives` safe control wrapper | partial |
| VirtualSky | `/virtualsky` | `virtualsky.html` | VirtualSky assets | Sky map | `/modern-admin/observatory/virtualsky` | partial |
| Task queue | `/tasks` | `taskqueue.html` | DataTables | Queue inspection | no clear Modern native page | missing |
| Cameras hidden page | `/cameras` | `cameras.html` | DataTables | DB camera list | `/modern-admin/cameras` | partial |
| YouTube OAuth | `/youtube/*`, `/ajax/uploadyoutube` | none/direct | external OAuth | YouTube upload auth | no clear Modern native page | missing |

## 4. Modern UI Inventory

| Modern page | Route/API used | Functionality | Dependencies | Classic coverage |
| --- | --- | --- | --- | --- |
| Dashboard | `/modern-admin` | Camera cards, latest images, 24h analytics, quality, nightly summary, metadata health, Event Foundation runtime/read-only diagnostics, Sky Awareness | FrameMetadata JSONL, analytics modules, camera DB, event JSONL/runtime state | Exceeds Classic for Hybrid analytics; not public-page replacement |
| Cameras | `/modern-admin/cameras` | Multi-camera status, profile list, enable/disable, links to camera settings/media | `MULTI_CAMERA`, DB camera rows, profile config | Exceeds Classic camera list for Hybrid profiles |
| Add Camera | `/modern-admin/cameras/add`, `/modern-admin/cameras/detect-indi`, `/modern-admin/cameras/start-indi` | Camera detection and new active config | INDI/libcamera detection helpers, config DB | Partial replacement for legacy camera setup |
| Camera Settings | `/modern-admin/settings/cameras` | Profile-first Hybrid, Driver/Connection, Acquisition, Lens/Optics, Save & Sync | `MULTI_CAMERA.profiles[n]`, profile resolver semantics | Exceeds Classic for Hybrid acquisition; not full config parity |
| Capture Settings | `/modern-admin/settings/capture` | Global capture settings with legacy fallback messaging | global config, multi-camera awareness | Partial replacement for Classic config capture section |
| Full Settings | `/modern-admin/settings/full` | Modern searchable config editor preserving profile-operated fields | `IndiAllskyConfigForm`, config save path, profile field protection | Partial replacement for `/config`; still complex |
| Settings Inventory | `/modern-admin/settings` | Settings overview/inventory | field metadata | New Modern navigation layer |
| Media Gallery | `/modern-admin/media/gallery`, `/modern-admin/media/gallery/page` | Infinite scroll gallery, camera/profile filter | image DB, profile/camera filters | Core gallery mostly ported |
| Media categories | `/modern-admin/media/images`, `/timelapses`, `/mini-timelapses`, `/panorama`, `/panorama-loop`, `/fits` | Read-only media lists | media DB | Partial replacement for viewers |
| Storage | `/modern-admin/storage`, `/modern-admin/storage/file-space-usage`, `/modern-admin/storage/drives` | Storage overview and wrappers | filesystem usage, legacy drive manager | Partial |
| Uploads | `/modern-admin/uploads` | Upload status/config placeholder | upload config | Partial/missing compared with Classic/legacy upload config |
| Observatory | `/modern-admin/observatory/*` | SQM, charts, sensor panel, astropanel, virtualsky, realtime/long-term keogram | legacy data sources, Chart.js, VirtualSky | Partial wrappers/native mix |
| System | `/modern-admin/system/*` | System status/info/support/log/config/network/GPIO | system views, logs, safe controls | Partial |
| Tools | `/modern-admin/tools/*` | Generate, focus, process FITS, simulator, image circle helper | mostly legacy tools through `safe_controls.html` | Partial |
| Updates | `/modern-admin/updates` | Update/status page | app/version context | Modern-only/partial |
| Classic placeholder | `/modern-admin/classic/<classic_page>` | Bridge/placeholder for not-yet-ported pages | none | Transitional only |

## 5. Feature Porting Matrix

| Feature | Classic | Modern | Profile-aware | Multicamera-aware | Scientific/explainability aware | Porting status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Camera settings | yes, global-heavy | yes, Camera Settings | yes | yes | partial | ported for Hybrid core | Modern is the source of truth for profile operation. |
| Image settings | yes | partial via Full/Capture/Camera Settings | partial | partial | partial | partial | Display/scientific split needs UX consolidation. |
| Exposure | yes, global | yes, profile-first | yes | yes | decision logs | ported | Global `CCD_EXPOSURE_*` should become legacy fallback. |
| Gain | yes, global | yes, profile-first | yes | yes | decision logs | ported | Auto Gain UI is modern-profile centered. |
| AWB | yes/global legacy | yes, Hybrid/profile | yes | yes | logs | ported for Hybrid core | CFA/Debayer profile-specific and non-syncable. |
| Camera profiles | no equivalent | yes | yes | yes | yes | ported | Core Hybrid concept. |
| Multicamera | no/limited | yes | yes | yes | yes | ported | Classic camera pages are not enough for Hybrid. |
| Metadata | no | yes dashboard/health | yes | yes | yes | ported | Modern dashboard consumes JSONL analytics. |
| Analytics | charts legacy | yes 24h/nightly | yes | yes | yes | ported/partial | Modern has Hybrid analytics; Classic charts still richer in custom chart config. |
| Quality | no | yes | yes | yes | yes | ported | Quality score/flags are Modern-visible. |
| Environmental Awareness | no | yes read-only | yes | yes | yes | ported v1 | Sky condition/cloud/trend/condensation shown read-only. |
| Event Foundation | no | yes diagnostics | yes | yes | yes | ported v0 | No runtime action; read-only diagnostics. |
| Scientific Source Layer | no | partial docs/config/report planned | yes | yes | yes | partial | Needs UX for source persistence modes and offline report visibility. |
| System/status | yes | yes | n/a | partial | no | partial | Modern wraps/reuses many legacy pages. |
| Logs | yes | yes | n/a | n/a | no | partial | Modern log reuses legacy source. |
| Config editor | yes | yes | partial | partial | partial | partial | Modern Full Settings exists; user-facing settings architecture still needs redesign. |
| Timelapse | yes | partial media/generate wrapper | partial | partial | no | partial | Multicamera generation recently repaired; UI parity still needs validation. |
| Keogram | yes | partial | partial | partial | no | partial | Realtime/long-term keogram have Modern observatory pages. |
| Startrail | yes media/view | partial media/view | partial | partial | no | partial | Generation/status parity unclear. |
| Upload/network/storage | yes | partial | mostly global | partial | no | partial | Modern storage exists; network/drives are safe controls. |
| User/admin/auth | yes | missing/partial | n/a | n/a | no | missing | Users/current user pages need Modern parity. |
| Task queue | yes hidden | missing | n/a | n/a | no | missing | Important for operations; should be ported before removal. |
| YouTube auth | yes | missing | n/a | n/a | no | missing | External integration; verify usage. |

## 6. Configuration Audit

This is a static audit. "Read locations" are summarized from visible code and
known Hybrid work; exact runtime use should be verified before removal.

| Setting/group | Defined in | Read by | UI exposing it | Classification | Modern equivalent | Future proposal |
| --- | --- | --- | --- | --- | --- | --- |
| `MULTI_CAMERA` / `profiles` | `indi_allsky/config.py`, config DB | `capture_profiles.py`, `capture.py`, `image.py`, Modern views | Modern Cameras/Camera Settings, Full Settings | still useful | Modern profile editor | Keep; make first-class Basic/Advanced UI. |
| `CCD_CONFIG.*GAIN`, `CCD_EXPOSURE_*` | `config.py`, `forms.py` | capture/image controllers and resolver fallback | Classic config, Modern Full/Capture | duplicated/legacy fallback | profile `gain`, `auto_exposure`, limits | Keep as fallback; label Legacy fallback in Modern. |
| `TARGET_ADU*` global | `config.py`, `forms.py` | resolver fallback/controllers | Classic config, Modern Full | duplicated/legacy fallback | profile `target_adu.*` | Keep fallback; prefer profile UI. |
| `AUTO_GAIN_*` global | config/runtime | resolver/controller fallback | Modern Full/Camera Settings partly | duplicated | profile auto gain settings | Move daily operation to Camera Settings; globals Developer/Legacy. |
| `AUTO_EXPOSURE_*` global | config/runtime | resolver/controller fallback | Modern Camera Settings/Full | duplicated | profile auto exposure settings | Keep safe defaults; expose profile values. |
| `CFA_PATTERN`, `CCD_BIT_DEPTH`, WB fields | config/forms/profile processing | resolver/image processing | Camera Settings and Full | still useful but duplicated | profile `processing` | Keep profile-first; global fallback Developer. |
| `IMAGE_SAVE_FITS*`, `IMAGE_EXPORT_RAW` | `config.py`, `forms.py`, image processing | `image.py`, frame metadata | Classic config, Modern Full | still useful/needs clarification | future Scientific Source section | Redesign as Never/Periodic/Every frame/Event-window buffered. |
| `FRAME_METADATA_PATH`, rotation | config/runtime | `frame_metadata.py`, analytics | Modern Full | still useful | future Metadata/Storage section | Keep; expose simple storage status. |
| `EVENT_CANDIDATE_TRIGGERS` | `config.py`, `forms.py`, Modern settings | image shadow integration/dashboard | Modern Full | still useful but Developer | Event Foundation settings | Keep disabled by default; Developer/Experimental. |
| `TIMELAPSE_*`, `DAYTIME_TIMELAPSE` | config/forms | capture/allsky/video | Classic config, Modern Full/Media | still useful | future Media Products section | Keep; add profile-aware explanations. |
| `REALTIME_KEOGRAM`, `LONGTERM_KEOGRAM` | config/forms | keogram views/tasks | Classic config, Modern observatory | still useful but advanced | Observatory/Products | Advanced. |
| `STARTRAILS_*` | config/forms | startrail generation | Classic config, Modern Full/Media | still useful | Media Products | Advanced. |
| `FISH2PANO`, panorama settings | config/forms | processing/panorama views | Classic config, Modern media partial | optional/advanced | Panorama section | Keep Advanced; not Basic. |
| Upload groups `FILETRANSFER`, `S3UPLOAD`, `SYNCAPI`, `YOUTUBE` | config/forms/sync/youtube | upload workers/API/OAuth | Classic config, Modern uploads placeholder | still useful but duplicated/confusing | future Uploads/Reporting | Redesign by destination/provider. |
| `WEB_*`, public display settings | config/forms/templates | public pages/templates | Classic config | needs migration | future Public Page settings | Port before Classic removal. |
| `IMAGE_STRETCH`, `IMAGE_CIRCLE_MASK`, overlay/text settings | config/forms/processing | image processing/rendering | Classic config, Modern Full/Camera Settings partial | needs clarification | Display Rendering section | Explain display vs scientific source. |
| `DETECT_METEORS`, `DETECT_*` legacy | config/forms/detectLines | processing/detection legacy | Classic config/Full | legacy-only/needs verification | future Detector section should not call it real meteor detection | Keep hidden/Developer until audited against scientific source. |
| Hooks `IMAGE_SAVE_HOOK_*`, `CAPTURE_HOOK_*` | config/forms | capture/image runtime | Classic config/Full | dangerous to remove | Developer | Keep; external scripts may depend on them. |
| Network/drive/GPIO settings | config/forms/views | system tools | Classic pages, Modern safe controls | still useful | System/Hardware | Port before removal. |
| User/auth settings | models/forms/auth views | auth system | Classic users/user/login | still useful | future Modern User/Admin | Must port before removal. |

## 7. Proposed Settings Architecture

### Basic

Daily-use settings only. These should use user-facing Hybrid concepts, not raw
legacy key names.

- Active camera/profile selector.
- Camera Profile overview: enabled, primary, friendly name, interface.
- Acquisition per profile:
  - exposure mode and limits;
  - gain mode and limits;
  - target meter/ADU;
  - day/night/moon mode policy;
  - Auto Exposure and Auto Gain status.
- Scientific Source mode:
  - Never;
  - Periodic;
  - Every frame;
  - Event-window buffered (disabled until implemented, with clear warning).
- Display rendering:
  - image file type/quality;
  - overlay on/off;
  - stretch display on/off;
  - mask/crop basics.
- Storage health and retention summary.
- Dashboard/reporting summary toggles.

### Advanced

Useful settings that should not be part of routine operation.

- CFA/Debayer/bit depth/WB per profile.
- Hybrid AWB apply mode.
- Timelapse/keogram/startrail product settings.
- Realtime/long-term keogram.
- Panorama/Fish2Pano.
- Metadata path/rotation details.
- Upload destination settings.
- SQM/camera SQM.
- Sensor panel/custom chart labels.
- Scientific source period/compression/raw type.
- Profile Save & Sync with hardware-specific warnings.

### Developer

Diagnostics, compatibility, experiments and risky knobs.

- Legacy global fallback values (`CCD_EXPOSURE_*`, global `TARGET_ADU*`,
  global gain/AWB values).
- Event Candidate trigger enable/rate limit.
- Detector/offline report paths.
- Legacy `DETECT_METEORS`/line detection settings.
- Hooks and custom scripts.
- Queue internals.
- Raw JSON config editor.
- Debug masks/outlines.
- Config import/restore and migrations.

### Principles for the Redesign

- Profile-first: operational camera behavior lives in selected camera profile.
- Multicamera-first: no setting should ambiguously apply to only one camera.
- Modern-first: Classic pages are compatibility surfaces, not the main workflow.
- Scientific-first: source images and display renderings are separate concepts.
- Explainability-first: dangerous or fallback settings must say why they exist.

## 8. Flask Route Audit

### Still Necessary

- Public/latest routes: `/`, `/latestimage`, `/latestthumbnail`,
  `/latesttimelapse`, related redirects.
- Media serving fallback: `/images/<path:path>`.
- Auth: `/login`, `/logout`.
- Sync API: `/sync/v1/*`.
- Action API: `/action/pause`, `/action/unpause`.
- Modern Admin: `/modern-admin*`.
- Current shared JSON endpoints used by Modern wrappers: `/js/charts`, `/js/log`,
  `/js/support`, `/ajax/status_update`.

### Duplicate or Overlapping

| Classic route | Modern route | Status |
| --- | --- | --- |
| `/gallery`, `/ajax/gallery` | `/modern-admin/media/gallery`, `/modern-admin/media/gallery/page` | Duplicate/Modern mostly ready. |
| `/videoviewer` | `/modern-admin/media/timelapses` | Overlap; viewer controls parity unknown. |
| `/minivideoviewer` | `/modern-admin/media/mini-timelapses` | Overlap; parity unknown. |
| `/fitsimageviewer` | `/modern-admin/media/fits` | Partial; FITS conversion/viewer not fully Modern. |
| `/charts` | `/modern-admin/observatory/charts`, dashboard charts | Overlap; Classic custom chart set richer. |
| `/log` | `/modern-admin/system/log` | Partial duplicate. |
| `/system` | `/modern-admin/system`, `/modern-admin/system/info` | Partial duplicate. |
| `/camera`, `/lag`, `/adu`, `/darks`, `/mask` | `/modern-admin/cameras/*` | Partial duplicate. |
| `/config` | `/modern-admin/settings/full`, `/modern-admin/settings/capture`, `/modern-admin/settings/cameras` | Duplicate but not removable yet. |

### Classic-only / Candidate for Future Removal After Porting

- `/users`, `/user`
- `/notifications`
- `/tasks`
- `/minigenerate`
- `/youtube/*`
- `/network`, `/drives` only after Modern native parity exists
- `/manual_gpio`, `/focus`, `/processing`, `/imagecirclehelper` only after
  safe-controls wrappers are replaced or intentionally retained

### Modern-only

- `/modern-admin`
- `/modern-admin/cameras/add`
- `/modern-admin/settings/cameras`
- `/modern-admin/settings/capture`
- `/modern-admin/settings/full`
- `/modern-admin/media/gallery/page`
- `/modern-admin/capture/service`
- `/modern-admin/classic/<classic_page>`
- `/modern-admin/mode/<mode>`

### Compatibility Hold

- `/ajax/*` and `/js/*` endpoints must not be removed until consumer mapping is
  automated. Some may be used by both Classic and Modern or by external scripts.

## 9. Template Audit

### Legacy Templates Still Used

All root templates registered directly in `views.py` are still used unless route
traffic proves otherwise:

- `base.html`
- `index_img.html`, `index_canvas.html`
- `loop_img.html`, `loop_canvas.html`
- `gallery.html`
- `imageviewer.html`, `fitsimageviewer.html`, `videoviewer.html`,
  `minivideoviewer.html`
- `view_image.html`, `watch_video.html`
- `generate.html`, `mini_generate.html`
- `config.html`, `config_list.html`, `config_restore.html`
- `system.html`, `log.html`, `support_info.html`
- `focus.html`, `manual_gpio.html`, `imageprocessing.html`
- `cameraLens.html`, `lag.html`, `adu.html`, `darks.html`, `mask.html`
- `camera_simulator.html`, `imagecirclehelper.html`
- `filespaceusage.html`, `network.html`, `drive_manager.html`
- `astropanel.html`, `virtualsky.html`, `sensor_panel.html`, `sqm.html`,
  `realtime_keogram.html`, `longterm_keogram.html`
- `user.html`, `users.html`, `notifications.html`, `taskqueue.html`

### Modern Templates

- `modern_admin/index.html`
- `modern_admin/cameras.html`
- `modern_admin/camera_add.html`
- `modern_admin/settings_cameras.html`
- `modern_admin/settings_capture.html`
- `modern_admin/settings_full.html`
- `modern_admin/settings_inventory.html`
- `modern_admin/media_list.html`
- `modern_admin/storage.html`
- `modern_admin/uploads.html`
- `modern_admin/observatory.html`
- `modern_admin/system.html`
- `modern_admin/*` wrappers for charts, log, support, SQM, sensor panel,
  astropanel, virtualsky, realtime/long-term keogram, dark library, mask,
  safe controls.

### Candidate Future Removals

Only after Modern parity and route deprecation:

- `config.html` after Basic/Advanced/Developer settings and raw Developer config
  editor are stable.
- `gallery.html`, `imageviewer.html`, `videoviewer.html` after Modern media
  parity includes all needed operations.
- `taskqueue.html`, `users.html`, `notifications.html` only after Modern pages
  exist.
- `network.html`, `drive_manager.html`, `manual_gpio.html`, `focus.html`,
  `imageprocessing.html` only after safe-controls wrappers are replaced or
  explicitly preserved.

### Risks

- Inline JavaScript is embedded in templates, so deleting templates also deletes
  behavior.
- Some Modern templates wrap legacy views; removing the legacy template/class may
  break Modern pages.
- External bookmarks/scripts may use Classic URLs.

## 10. JavaScript / CSS Audit

### Classic Assets

- `indi_allsky/flask/static/css/style.css`: primary Classic styling.
- `bootstrap/*`: Classic base and login; may also remain useful generally.
- `js/jquery-3.7.1.min.js`: Classic base dependency.
- `js/indi-allsky-tabs.js`: Classic tab behavior.
- `DataTables/*`: Classic tables for config list, ADU, notifications, users,
  tasks, filespace, cameras, generate, drive manager, darks.
- `photoswipe/*`: Classic gallery.
- `virtualsky/*`: Classic and Modern VirtualSky.
- `astropanel/*`: Classic and Modern Astropanel.
- `html2canvas/*`: VirtualSky.
- `js/clipboard.min.js`: support/view/watch pages.
- `js/chart.umd.js`: Classic charts, focus and Modern charts/dashboard.

### Modern Assets

- `indi_allsky/flask/static/modern_admin/modern-admin.css`: Modern shell and
  all Modern UI styling.
- Modern templates still use inline JavaScript heavily.
- Modern charts use `js/chart.umd.js`.
- Modern media/gallery currently uses custom inline JS, not PhotoSwipe.

### Shared Assets

- Chart.js.
- VirtualSky assets.
- Astropanel assets.
- Bootstrap may remain used by Classic and login.
- Logo/favicon/static images.

### Candidate Cleanup

- DataTables may become removable after Classic table pages are replaced.
- PhotoSwipe may become removable if Modern gallery is final and Classic gallery
  is removed.
- `static/css/style.css` may become removable after Classic UI and login styling
  are modernized or separated.
- Many inline scripts should be extracted only after parity, not during removal.

## 11. API Duplication Audit

| Endpoint | Consumer Classic | Consumer Modern | Data | Overlap | Proposal |
| --- | --- | --- | --- | --- | --- |
| `/ajax/status_update` | Classic base/status | likely shared shell/status | runtime status | shared | Keep until Modern has dedicated stable status API. |
| `/js/charts` | `chart.html` | `modern_admin/charts.html` | chart datasets | shared | Keep; later rename to `/api/analytics/charts`. |
| `/js/log` | `log.html` | Modern log wrapper | log lines | shared | Keep; later route under `/api/system/log`. |
| `/js/support` | `support_info.html` | Modern support wrapper | support info | shared | Keep. |
| `/ajax/config` | Classic config | Modern full settings | config save | shared/critical | Keep; later split safe profile settings from raw config save. |
| `/ajax/gallery` | Classic gallery | Modern uses its own media page route | media rows | overlap | Prefer Modern page API after parity. |
| `/ajax/imageviewer` | Classic image viewer | no clear Modern use | image rows/actions | classic-only | Candidate after Modern media parity. |
| `/ajax/fitsimageviewer` | Classic FITS viewer | Modern FITS list partial | FITS rows | partial | Keep until FITS review/source UX is complete. |
| `/ajax/videoviewer` | Classic video viewer | Modern media list partial | video rows | partial | Keep until Modern video tools complete. |
| `/ajax/generate` | Classic generate | Modern safe control | task creation | shared via wrapper | Keep until native Modern generation exists. |
| `/ajax/network`, `/ajax/drives`, `/ajax/manual_gpio` | Classic tools | Modern safe controls | system controls | shared/wrapped | Keep. |
| `/sync/v1/*` | external sync | none/indirect | media sync CRUD | not UI duplicate | Do not remove as UI cleanup. |
| `/action/*` | external/action callers | none/indirect | pause/unpause | not UI duplicate | Keep. |

## 12. Obsolete / Legacy Candidates

### Safer Future Removal Candidates

These look removable only after Modern parity and route usage logging:

- Classic gallery/media viewer templates.
- DataTables dependency if no Modern/native pages need it.
- PhotoSwipe dependency if Classic gallery is removed.
- Classic config UI after Basic/Advanced/Developer settings are complete.

### Removable Only After Porting

- Users/current user pages.
- Notifications page/API.
- Task queue page.
- YouTube auth controls.
- Manual mini timelapse generation.
- Network/drives/GPIO/focus/image processing tools currently wrapped by Modern
  safe controls.

### Maintain Temporarily

- Public latest image/loop routes.
- Redirect routes like `/latestimage`, `/latesttimelapse`.
- Sync API and action API.
- Shared `/js/*` and `/ajax/*` endpoints consumed by Modern wrappers.
- Legacy global config keys as resolver fallbacks.

### Verify Manually

- `DETECT_METEORS` and legacy line detection settings: do not expose as real
  meteor detector.
- Panorama and mini-timelapse product usage.
- YouTube upload usage.
- External scripts using `/ajax/*`, `/latest*`, `/sync/v1/*`.

### Do Not Touch Now

- Config DB schema.
- Auth/session model.
- Sync API.
- Capture/image/video runtime.
- Profile resolver fallback keys.
- Public media URLs.

## 13. Risk Analysis

- UI regression: Modern wrappers still depend on legacy classes and endpoints.
- Configuration loss: monolithic `/config` can edit settings not yet present in
  Modern Basic/Advanced pages.
- Existing users: some users may rely on Classic URLs, bookmarks or habits.
- External automation: scripts may call `/latest*`, `/ajax/*`, `/sync/v1/*` or
  `/action/*`.
- Profile/camera ambiguity: removing global fallbacks before migration could
  break single-camera or old configs.
- Multicamera mismatch: Classic pages may be camera-global while Modern is
  profile-first; porting must not mix cameras.
- Scientific source confusion: FITS/RAW/display settings can be destructive if
  explained poorly.
- Upload/reporting integrations: storage/network/upload settings are spread
  across Classic config and Modern placeholders.
- Inline JS coupling: Classic behavior is embedded in templates, not isolated
  modules.
- Route naming compatibility: public media and redirect routes are likely used
  externally.

## 14. Recommended Roadmap

### Phase 0 - Audit Only

Current phase. Maintain this document as the source of truth for UI
simplification candidates.

### Phase 1 - Safe Visibility Mapping

- Add a non-invasive route/template/API inventory command or test.
- Log Modern-vs-Classic route traffic optionally.
- Add a Classic-to-Modern map in documentation.
- Mark Modern wrappers as `native`, `wrapped`, or `placeholder`.

### Phase 2 - Complete Modern Parity

Port missing operational pages:

1. Task queue.
2. Users/current user.
3. Notifications.
4. YouTube/upload auth.
5. Native generation controls for timelapse/keogram/startrail.
6. Native focus/GPIO/network/drives/process-FITS if still required.
7. FITS/source review and scientific source diagnostics.

### Phase 3 - Settings Redesign

- Implement Basic / Advanced / Developer information architecture.
- Move Hybrid operations out of raw full settings into profile-aware pages.
- Keep raw full settings as Developer fallback.
- Label legacy fallback fields explicitly.

### Phase 4 - Deprecation Layer

- Add non-breaking warnings in Classic UI.
- Add Modern links from Classic pages.
- Add optional admin setting to default to Modern.
- Document external route compatibility guarantees.

### Phase 5 - Legacy Removal

- Remove one Classic page family at a time only after parity and usage logging.
- Keep redirects where external URLs matter.
- Keep Sync/API routes independent from UI removal.

### Phase 6 - Cleanup

- Remove unused templates.
- Remove unused JS/CSS libraries.
- Simplify duplicated view classes and APIs.
- Clean config form groups that are truly migrated or obsolete.

## 15. First Safe Micro-Step

Recommended first micro-step:

Add a documentation-backed UI inventory test/report that introspects Flask
routes and emits a table with:

- route;
- endpoint;
- view class;
- template;
- UI family (`classic`, `modern`, `api`, `public`, `sync`, `action`);
- migration status (`native-modern`, `modern-wrapper`, `classic-only`,
  `shared-api`, `external-api`, `unknown`).

Why this first:

- No behavior change.
- No code removal.
- Reversible.
- Verifiable in CI or manually.
- Creates the safety net needed before deprecation.
- Prevents accidental deletion of a route still used by Modern wrappers.

Acceptance criteria:

- Running the report lists every route registered by `bp_allsky`,
  `bp_auth_allsky`, `bp_syncapi_allsky` and `bp_actionapi_allsky`.
- The report identifies Modern routes and Classic routes consistently.
- Unknowns are explicit.
- No UI behavior changes.

## 16. Final Answers

### 1. Quanto manca realmente per eliminare la Classic UI?

Non poco. Modern Admin e' gia' il centro operativo Hybrid, ma Classic UI non e'
ancora eliminabile perche' molte superfici sono ancora mancanti o solo avvolte:
task queue, users, notifications, YouTube/upload auth, network/drives/GPIO,
focus, image processing, full media/FITS viewer parity, manual generation tools
and raw public pages.

La rimozione completa richiede prima Modern parity, poi deprecation/usage
mapping, poi rimozione per famiglie di route.

### 2. Quale dovrebbe essere il primo micro-step sicuro?

Creare una mappa automatica e documentata Classic -> Modern per
route/template/API, senza rimuovere nulla. Deve distinguere Modern native,
Modern wrapper, Classic-only, shared API ed external API.

### 3. In quale ordine conviene fare il porting?

1. Operational visibility: task queue, logs/status parity, route inventory.
2. User/admin/notification pages.
3. Media and generation parity: image/FITS/video/generate workflows.
4. System tools: focus, GPIO, network, drives, process FITS.
5. Settings redesign: Basic / Advanced / Developer.
6. Public page strategy.
7. Deprecation and removal.

### 4. Quali parti del progetto diventeranno piu' semplici dopo questa pulizia?

- Configurazione: meno duplicazione tra globali legacy e profili.
- UI maintenance: meno template con inline JS e meno route duplicate.
- Asset pipeline: possibile rimozione di DataTables/PhotoSwipe/legacy CSS dove
  non piu' necessari.
- Operational workflows: una sola Modern UI profile-first invece di due mondi.
- Scientific source UX: concetti FITS/RAW/display/overlay piu' chiari.
- Event/Detector future work: meno confusione tra diagnostica moderna e vecchi
  detector/line detection legacy.

