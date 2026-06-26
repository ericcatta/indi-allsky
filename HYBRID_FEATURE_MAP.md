# HYBRID FEATURE MAP

Audit date: 2026-06-26

Scope: semantic feature ownership map for future Classic UI to Modern UI
consolidation. This document does not implement, remove, refactor, rename, or
change runtime behavior.

Related documents:

- `HYBRID_UI_SIMPLIFICATION_PLAN.md`
- `HYBRID_UI_EVIDENCE_MATRIX.md`
- `HYBRID_UI_INVENTORY_REPORT.md`
- `tools/hybrid_ui_inventory.py`

## 1. Purpose

This document describes Hybrid AllSky by user-facing and architectural
features, not by files. It exists to guide future Classic to Modern UI porting
without breaking the modern Hybrid work already added to this fork.

The guiding rule is simple: Classic UI cleanup must never flatten, remove, or
regress profile-first, multi-camera, scientific-first, explainability-first
behavior. A feature may be wrapped by a legacy class today, but its future owner
must be chosen by semantics, not by historical file location.

## 2. Protected Modern Work

All entries in this section are `PROTECTED MODERN WORK`. Future porting may
improve their UX, but must preserve their behavior, data contracts, logs,
profile/camera semantics, and explainability.

| Feature | Files/routes/API/config involved | Why protected | Risk if touched | Porting rule |
| --- | --- | --- | --- | --- |
| Multi-camera | `MULTI_CAMERA`, `MULTI_CAMERA_CAPTURE_ENABLE`, `indi_allsky/capture_profiles.py`, `indi_allsky/capture.py`, `indi_allsky/allsky.py`, `/modern-admin/cameras`, `/modern-admin/settings/cameras` | Core Hybrid operating model. | Reverting to single-camera assumptions breaks capture, profiles, timelapse, metadata, and analytics. | Preserve camera isolation and camera_id/profile_id on every migrated surface. |
| Camera Profiles | `MULTI_CAMERA.profiles`, `capture_profiles.py`, `modern_admin/settings_cameras.html`, `ModernAdminCameraSettingsView` | Defines profile-first camera behavior. | Global settings may override active profile values or save to wrong profile. | Modern Camera Settings remains canonical for profile-owned fields. |
| Profile-first configuration | `capture_profiles.py`, `ModernAdminCameraSettingsView`, `ModernAdminFullSettingsView`, `settings_capture.html`, `settings_full.html` | Prevents global fallback bugs and supports per-camera behavior. | Flattening config breaks ASI/IMX divergence and runtime resolver correctness. | Any migrated setting must declare global, profile, or camera-profile ownership. |
| Auto Exposure | `indi_allsky/auto_exposure_controller.py`, `indi_allsky/image.py`, `capture_profiles.py`, `AUTO_EXPOSURE_*`, `TARGET_ADU_*`, `/modern-admin/settings/cameras` | Exposure-first control is central to image stability. | Incorrect UI/config migration can change exposure behavior or hide blockers. | Preserve exposure-first semantics, profile target ADU, logs, blockers, and convergence diagnostics. |
| Auto Gain | `indi_allsky/auto_gain_controller.py`, `indi_allsky/image.py`, runtime gain state, `AUTO_GAIN_*`, `/modern-admin/settings/cameras` | Gated, profile-specific, explainable gain control. | Real gain could be applied unexpectedly or reset across restarts. | Keep `apply_enabled` default false unless explicitly configured; write only intended runtime targets. |
| Hybrid AWB | AWB config/resolver paths, camera profile lens/processing settings, `/modern-admin/settings/cameras` | Camera/profile-specific color behavior. | CFA/debayer or AWB sync can corrupt different sensors. | Keep hardware-specific fields per-camera and non-syncable unless explicitly safe. |
| Metadata | `indi_allsky/frame_metadata.py`, `indi_allsky/frame_metadata_analytics.py`, `/var/lib/indi-allsky/frame_metadata/YYYY-MM-DD.jsonl`, Modern dashboard | Foundation for analytics, quality, environment, events, and scientific source linking. | Dashboard and offline tools lose evidence trail. | Never remove metadata fields without backward-compatible migration. |
| Analytics | `frame_metadata_analytics.py`, `/modern-admin`, `modern_admin/index.html` | Read-only observability layer for both cameras. | Modern dashboard can crash or lose operational insight. | Preserve malformed-row tolerance and single-camera fallback. |
| Quality | `indi_allsky/frame_quality.py`, metadata `quality_score`, `quality_flags`, dashboard/nightly summary | Provides first non-AI frame quality evidence. | Event and environment layers lose filtering context. | Keep quality metadata optional/backward compatible for old JSONL rows. |
| Environmental Awareness | `sky_condition.py`, `cloud_detection.py`, `sky_trend.py`, `condensation_detection.py`, `frame_metadata_analytics.py`, dashboard Sky Awareness | Diagnostic-only sky interpretation before event/AI work. | Environmental signals could influence runtime or become overconfident. | Keep read-only/diagnostic unless a future roadmap explicitly promotes behavior. |
| Event Foundation | `event_candidate.py`, `detector_result.py`, EventCandidate/EventTimeline/EventClassification JSONL, dashboard Event Foundation | Detector-agnostic, shadow-first evidence pipeline. | Event candidates could be misrepresented as real detections. | Keep candidate/timeline/classification shadow-only until validation gates are met. |
| Scientific Source Layer | `frame_metadata.py`, `scientific_frame.py`, `scientific_frame_provider.py`, `scientific_frame_sequence.py`, `timeline_frame_set.py`, FITS/RAW config | Raw-first scientific input contract for future detectors. | JPEG/overlay images could be treated as scientific sources. | Do not promote display images to detector/scientific source. |
| Detector API foundation | `detector_result.py`, detector runner contract, offline reports/bridges | Generic detector output path before real detectors. | Future RMS/OpenCV/AI adapters may diverge or become meteor-specific. | Keep detector result generic, shadow-first, and detector-agnostic. |
| Meteor Intelligence foundation | `meteor_observation.py`, MeteorReview, MeteorValidation, offline report/summary | Domain contract separate from detection. | Meteor counts could be produced without validation trust state. | Keep observation, review, and validation distinct. |
| Modern Admin shell | `/modern-admin`, `modern_admin/index.html`, `_shell_header.html`, `modern-admin.css` | Main Hybrid operational UI. | Navigation/service controls and dashboard context may break. | Modern shell is future canonical admin surface. |
| Modern safe controls | `ModernAdminSafeControlsMixin`, `modern_admin/safe_controls.html` | Transitional compatibility layer. | Removing wrappers before parity can strand operational tools. | Treat wrappers as active dependencies until native Modern pages exist. |

## 3. Feature Ownership Matrix

| Feature | Classic support | Modern support | Profile-first | Multicamera-first | Scientific/explainability aware | Future owner | State | Porting priority | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Camera Profiles | no true equivalent | yes | yes | yes | yes | Modern | PROTECTED MODERN WORK | preserve | Canonical Hybrid concept. |
| Multi-camera | limited/legacy DB views | yes | yes | yes | yes | Modern | PROTECTED MODERN WORK | preserve | Do not regress to single-camera UI. |
| Auto Exposure | global legacy config | yes | yes | yes | yes | Modern | PROTECTED MODERN WORK | preserve | Exposure-first remains binding. |
| Auto Gain | global legacy config | yes | yes | yes | yes | Modern | PROTECTED MODERN WORK | preserve | Gated apply and runtime state must remain intact. |
| Hybrid AWB | partial/global | yes | yes | yes | partial | Modern | PROTECTED MODERN WORK | preserve | CFA/debayer per-camera is hardware-specific. |
| Metadata | no | yes | yes | yes | yes | Modern/Shared | PROTECTED MODERN WORK | preserve | JSONL schema must remain backward compatible. |
| Analytics | charts legacy | yes | yes | yes | yes | Modern | PROTECTED MODERN WORK | preserve | Dashboard is Modern canonical. |
| Quality | no | yes | yes | yes | yes | Modern/Shared | PROTECTED MODERN WORK | preserve | Used by environment/events. |
| Environmental Awareness | no | yes | yes | yes | yes | Modern/Shared | PROTECTED MODERN WORK | preserve | Diagnostic-only. |
| Event Foundation | no | yes | yes | yes | yes | Modern/Shared | PROTECTED MODERN WORK | preserve | Shadow-only evidence pipeline. |
| Scientific Source Layer | no | partial/config/report | yes | yes | yes | Shared/Modern | PROTECTED MODERN WORK | preserve | Needs UX clarity, not detector work. |
| Image Capture | service/runtime | service controls | yes | yes | logs | Shared | MODERN CANONICAL | high | Runtime remains shared; Modern owns admin controls. |
| Image Viewer | yes | media list partial | partial | partial | partial | Modern | PARTIAL MODERN | medium | Advanced exclude/FITS actions still Classic. |
| Gallery | yes | yes | partial | yes | no | Modern | MODERN CANONICAL | medium | Verify PhotoSwipe parity before Classic removal. |
| FITS / Source Files | yes viewer | media FITS list/source contracts | yes | yes | yes | Modern/Shared | PARTIAL MODERN | high | FITS viewer parity remains important. |
| Timelapse | yes | media list/safe generate | partial | partial | no | Modern | WRAPPER ONLY | high | Generation UI still safe-control/legacy. |
| Keogram | yes | observatory/media partial | partial | partial | no | Modern | PARTIAL MODERN | medium | Realtime/long-term use wrappers/data sources. |
| Startrail | yes | media/public partial | partial | partial | no | Modern | PARTIAL MODERN | medium | Startrail generation parity unclear. |
| Startrail Video | yes/public redirects | media/public partial | partial | partial | no | Modern | PARTIAL MODERN | medium | Preserve public latest endpoints. |
| Task Queue | yes | no clear page | no | no | no | Modern | CLASSIC ONLY | high | Operationally important before Classic removal. |
| User Management | yes | missing | no | no | no | Modern | CLASSIC ONLY | high | Auth/user admin parity needed. |
| Notifications | yes | missing | no | no | no | Modern | CLASSIC ONLY | high | Notification admin parity needed. |
| Upload | yes | partial uploads page | no | partial | no | Modern | PARTIAL MODERN | medium | YouTube/OAuth is still Classic-heavy. |
| YouTube / OAuth | yes | missing | no | no | no | External/Modern | CLASSIC ONLY | medium | External auth flow must be preserved. |
| Network | yes | safe control | no | no | no | Modern | WRAPPER ONLY | medium | Hardware/system risk. |
| Storage | yes | yes/safe drives | no | partial | no | Modern | PARTIAL MODERN | medium | File space native; drives wrapper. |
| GPIO | yes | safe control | no | no | no | Modern | WRAPPER ONLY | medium | Hardware action risk. |
| Focus | yes | safe control | no | camera-related | no | Modern | WRAPPER ONLY | medium | Needs native page or keep wrapper. |
| Mask | yes | Modern camera wrapper/page | partial | yes | partial | Modern | PARTIAL MODERN | medium | Mask affects processing; protect multicamera shape-awareness. |
| SQM | yes | Modern observatory wrapper | no | partial | no | Modern | PARTIAL MODERN | low | Recent SQM mask fixes are runtime-protected. |
| ADU | yes | Modern ADU history | yes | yes | yes | Modern | PARTIAL MODERN | medium | ADU ties to Auto Exposure/Gain. |
| Config Editor | yes | Modern full/settings/camera | partial | partial | partial | Modern | PARTIAL MODERN | high | Needs Basic/Advanced/Developer redesign. |
| System Info | yes | yes | no | no | no | Modern | MODERN CANONICAL | medium | Support/log wrappers remain. |
| Logs | yes | yes | no | no | explainability support | Modern/Shared | PARTIAL MODERN | medium | Shared `/js/log`. |
| Charts | yes | yes/dashboard | partial | partial | yes | Modern | PARTIAL MODERN | medium | Shared `/js/charts`. |
| Public latest endpoints | yes | no admin replacement | no | partial | no | Shared/Public | SHARED LEGACY | preserve | Do not remove as UI cleanup. |
| Sync API | yes external | n/a | no | yes | no | External | EXTERNAL API | preserve | Not Classic UI. |
| Action API | yes external | n/a | no | no | no | External | EXTERNAL API | preserve | Not Classic UI. |
| Admin / Safe Controls | n/a | yes | mixed | mixed | no | Modern | WRAPPER ONLY | high | Transitional, not final parity. |

## 4. Feature Detail Sections

### Camera Profiles

Current State: Modern-only core concept exposed through
`/modern-admin/cameras` and `/modern-admin/settings/cameras`.

Evidence: `ModernAdminCamerasView`, `ModernAdminCameraSettingsView`,
`modern_admin/cameras.html`, `modern_admin/settings_cameras.html`,
`MULTI_CAMERA.profiles`, `capture_profiles.py`.

Modern Gap: UX still needs clearer ownership labels and source persistence
settings.

Protected Work: Yes, `PROTECTED MODERN WORK`.

Porting Rule: Never move profile-owned fields back to global-only config.

Removal Risk: High if Classic config editor remains able to obscure profile
ownership.

Recommended Action: Make profile ownership visible in future settings UX.

### Multi-camera

Current State: Modern UI and resolver are multicamera-first; Classic is mostly
single-camera-era UI plus DB utility pages.

Evidence: `/modern-admin/cameras`, `/modern-admin/settings/cameras`,
`MULTI_CAMERA_CAPTURE_ENABLE`, `allsky.py`, `capture.py`, `capture_profiles.py`.

Modern Gap: Some legacy tools wrapped in Modern may still assume one active
camera.

Protected Work: Yes, `PROTECTED MODERN WORK`.

Porting Rule: Every migrated page must display or preserve camera_id/profile_id.

Removal Risk: Critical if shared APIs are removed because static consumers are
not obvious.

Recommended Action: Add route/feature ownership metadata before any removal.

### Auto Exposure

Current State: Runtime controller is modernized and profile-first; UI exposure
configuration is primarily Modern Camera Settings.

Evidence: `auto_exposure_controller.py`, `image.py`, `capture_profiles.py`,
`TARGET_ADU_*`, `/modern-admin/settings/cameras`.

Modern Gap: Full explanatory UI for convergence/blocker diagnostics is not yet
complete.

Protected Work: Yes, `PROTECTED MODERN WORK`.

Porting Rule: Preserve Exposure-first behavior and target ADU profile resolver.

Removal Risk: High if global `CCD_EXPOSURE_*` fields are treated as canonical.

Recommended Action: Document exposure field ownership in the next UX/settings
map.

### Auto Gain

Current State: Gated profile-first Auto Gain exists with runtime state,
convergence, apply gating, and diagnostics.

Evidence: `auto_gain_controller.py`, `image.py`, runtime state paths,
`AUTO_GAIN_*`, `GAIN_MAX_*`, `/modern-admin/settings/cameras`.

Modern Gap: UI clarity around apply enablement and runtime restore can improve.

Protected Work: Yes, `PROTECTED MODERN WORK`.

Porting Rule: Default apply remains disabled unless explicitly configured; keep
mode/profile gates.

Removal Risk: Critical if a UI migration writes camera gain directly or loses
runtime state behavior.

Recommended Action: Keep Auto Gain entirely Modern/profile-owned.

### Hybrid AWB

Current State: Hybrid AWB and CFA/debayer concerns are camera/profile-specific.

Evidence: Camera Settings Lens/Optics sections, CFA/debayer non-sync rule,
profile config.

Modern Gap: More help text is needed to explain hardware-specific fields.

Protected Work: Yes, `PROTECTED MODERN WORK`.

Porting Rule: Do not sync hardware-specific color/debayer fields across cameras.

Removal Risk: Medium; bad migration can corrupt different sensor rendering.

Recommended Action: Keep AWB/CFA in Camera Settings and mark hardware-specific.

### Metadata

Current State: Daily JSONL frame metadata is the foundation of analytics,
quality, environment, events, and scientific source linkage.

Evidence: `frame_metadata.py`, `frame_metadata_analytics.py`,
`frame_metadata/YYYY-MM-DD.jsonl`, Modern dashboard.

Modern Gap: UI can expose source readiness and health more clearly.

Protected Work: Yes, `PROTECTED MODERN WORK`.

Porting Rule: Preserve backward compatibility with legacy rows.

Removal Risk: Critical; dashboard and offline reports depend on it.

Recommended Action: Treat metadata as Shared infrastructure, not UI code.

### Analytics

Current State: Modern dashboard has 24h analytics, nightly summary, health,
quality, event diagnostics, and environmental indicators.

Evidence: `/modern-admin`, `modern_admin/index.html`,
`frame_metadata_analytics.py`.

Modern Gap: Some classic charts have separate legacy JSON surfaces.

Protected Work: Yes, `PROTECTED MODERN WORK`.

Porting Rule: Do not remove shared `/js/charts` until all chart consumers are
mapped.

Removal Risk: Medium.

Recommended Action: Keep Modern dashboard canonical; keep shared APIs until
replaced.

### Quality

Current State: Quality score and flags are persisted and shown in Modern
dashboard/nightly summary.

Evidence: `frame_quality.py`, `quality_score`, `quality_flags`,
`frame_metadata_analytics.py`, Modern dashboard.

Modern Gap: User-facing explanation of flags can improve.

Protected Work: Yes, `PROTECTED MODERN WORK`.

Porting Rule: Never make quality dependent on UI rendering or overlays.

Removal Risk: High for event/environment pipeline.

Recommended Action: Preserve as metadata infrastructure.

### Environmental Awareness

Current State: Metadata-only diagnostic classifiers are integrated in analytics
and read-only Modern UI.

Evidence: `sky_condition.py`, `cloud_detection.py`, `sky_trend.py`,
`condensation_detection.py`, `frame_metadata_analytics.py`, dashboard.

Modern Gap: Needs Raspberry threshold tuning and UX explanations.

Protected Work: Yes, `PROTECTED MODERN WORK`.

Porting Rule: Keep diagnostic/read-only until explicitly promoted.

Removal Risk: High for future event/AI correctness.

Recommended Action: Preserve and expose only as read-only status.

### Event Foundation

Current State: EventCandidate, EventTimeline, EventClassification,
DetectorResult, offline reports/bridges, and dashboard diagnostics exist in
shadow-only form.

Evidence: `event_candidate.py`, `detector_result.py`,
`event_candidates/YYYY-MM-DD.jsonl`, `event_timelines/YYYY-MM-DD.jsonl`,
`event_classifications`, Modern dashboard Event Foundation section.

Modern Gap: No review UI, no real detector, no classification promotion.

Protected Work: Yes, `PROTECTED MODERN WORK`.

Porting Rule: Do not turn shadow candidates into claims or notifications.

Removal Risk: Critical for future Event Intelligence.

Recommended Action: Keep event surfaces read-only while detector validation is
blocked.

### Scientific Source Layer

Current State: FrameMetadata carries raw-first fields; ScientificFrame,
ScientificFrameProvider, ScientificFrameSequence, TimelineFrameSet and source
reports exist.

Evidence: `scientific_frame.py`, `scientific_frame_provider.py`,
`scientific_frame_sequence.py`, `timeline_frame_set.py`, `frame_metadata.py`,
FITS/RAW config keys.

Modern Gap: Source persistence modes are not yet clear in UI.

Protected Work: Yes, `PROTECTED MODERN WORK`.

Porting Rule: Display images are not detector/scientific sources.

Removal Risk: Critical for future meteor/RMS work.

Recommended Action: Add UX/storage policy map before detector implementation.

### Image Capture

Current State: Runtime remains shared backend; Modern has service actions and
dashboard status.

Evidence: `capture.py`, `image.py`, `/modern-admin/capture/service`,
`_shell_header.html`.

Modern Gap: Capture settings are split between Full, Capture and Camera pages.

Protected Work: Touches protected multicamera/profile logic.

Porting Rule: UI changes must not alter capture timing, camera drivers, or
profile resolver behavior.

Removal Risk: High.

Recommended Action: Keep runtime shared; consolidate configuration semantics.

### Image Viewer

Current State: Classic image viewer remains richer for per-image actions;
Modern media list covers browsing.

Evidence: `/imageviewer`, `/ajax/imageviewer`, `imageviewer.html`,
`/modern-admin/media/images`, `modern_admin/media_list.html`.

Modern Gap: Exclude/actions/detail parity unclear.

Protected Work: May touch metadata/source paths.

Porting Rule: Preserve media IDs and camera/profile filters.

Removal Risk: Medium.

Recommended Action: Compare Classic image actions before porting.

### Gallery

Current State: Classic gallery uses PhotoSwipe; Modern media gallery exists.

Evidence: `/gallery`, `/ajax/gallery`, `gallery.html`,
`/modern-admin/media/gallery`, `modern_admin/media_list.html`.

Modern Gap: PhotoSwipe-style review parity and advanced actions need checking.

Protected Work: Low direct risk, but media filters must stay multicamera-aware.

Porting Rule: Do not remove PhotoSwipe vendor assets until Classic gallery is
fully retired.

Removal Risk: Medium.

Recommended Action: Runtime compare Modern gallery vs Classic gallery.

### FITS / Source Files

Current State: Classic FITS viewer exists; Modern has FITS media list and
scientific source contracts.

Evidence: `/fitsimageviewer`, `/ajax/fitsimageviewer`, `/fits2jpeg`,
`fitsimageviewer.html`, `/modern-admin/media/fits`, `frame_metadata.py`.

Modern Gap: No full native FITS inspection/review equivalent confirmed.

Protected Work: Yes, touches Scientific Source Layer.

Porting Rule: Do not equate rendered JPEG with source FITS/RAW.

Removal Risk: High.

Recommended Action: Keep Classic FITS viewer until source review UX exists.

### Timelapse

Current State: Classic generator and viewers exist; Modern has media list and a
safe-control generator wrapper.

Evidence: `/generate`, `/ajax/generate`, `generate.html`,
`/modern-admin/tools/generate`, `/modern-admin/media/timelapses`.

Modern Gap: Native profile/camera-aware generation controls unclear.

Protected Work: Touches recent multicamera timelapse repairs.

Porting Rule: Every generated product must remain camera-scoped.

Removal Risk: High.

Recommended Action: Port generator semantics only after Raspberry validation.

### Keogram

Current State: Classic and Modern observatory/media pages coexist.

Evidence: `/realtime_keogram`, `/longtermkeogram`, `/js/longtermkeogram`,
`/modern-admin/observatory/realtime-keogram`,
`/modern-admin/observatory/long-term-keogram`.

Modern Gap: Native parity and generation controls need validation.

Protected Work: Medium; generated products are multicamera-sensitive.

Porting Rule: Preserve per-camera product separation.

Removal Risk: Medium.

Recommended Action: Map keogram route/API consumers before removal.

### Startrail

Current State: Public latest redirects and media views exist; Modern media
coverage is partial.

Evidence: `/lateststartrail`, `/lateststartrailview`, `/view_startrail`,
`/modern-admin/media/*`.

Modern Gap: Native generation/status parity unclear.

Protected Work: Medium; generated product pipeline recently changed.

Porting Rule: Keep camera_id/profile_id in tasks and media queries.

Removal Risk: Medium.

Recommended Action: Validate startrail output and UI parity separately.

### Startrail Video

Current State: Public redirects/watch routes exist; Modern media list may expose
generated media.

Evidence: `/lateststartrailvideo`, `/lateststartrailvideowatch`, `watch_video.html`.

Modern Gap: Native watch/share parity unclear.

Protected Work: Low direct risk, but public links may be external.

Porting Rule: Preserve public redirects even if admin UI changes.

Removal Risk: High for external users/bookmarks.

Recommended Action: Treat as Shared/Public until access logs prove otherwise.

### Task Queue

Current State: Classic hidden/admin page exists; no clear Modern native page.

Evidence: `/tasks`, `taskqueue.html`, DataTables assets.

Modern Gap: Missing.

Protected Work: Indirectly touches timelapse/event/background diagnostics.

Porting Rule: Do not remove before Modern task diagnostics exist.

Removal Risk: High operational risk.

Recommended Action: Port read-only task queue to Modern early.

### User Management

Current State: Classic user pages exist; Modern parity not confirmed.

Evidence: `/user`, `/ajax/user`, `/users`, `user.html`, `users.html`.

Modern Gap: Missing current-user and admin user management.

Protected Work: None direct, but auth is critical.

Porting Rule: Do not touch `/login` or `/logout` during UI cleanup.

Removal Risk: High.

Recommended Action: Design Modern user/admin parity before removal.

### Notifications

Current State: Classic notifications page/API exists.

Evidence: `/notifications`, `/ajax/notification`, `notifications.html`.

Modern Gap: Missing.

Protected Work: Future event/meteor notification work must not reuse legacy
assumptions blindly.

Porting Rule: Keep notification config separate from Event Foundation until
explicitly designed.

Removal Risk: Medium.

Recommended Action: Inventory notification backends before Modern port.

### Upload

Current State: Classic upload surfaces and Modern uploads page coexist.

Evidence: `/modern-admin/uploads`, `/ajax/uploadyoutube`, upload config groups,
video viewer upload actions.

Modern Gap: Full upload/provider parity unclear.

Protected Work: External APIs and user credentials are high-risk.

Porting Rule: Do not remove upload/OAuth routes because they lack static
consumers.

Removal Risk: High.

Recommended Action: Build upload provider inventory.

### YouTube / OAuth

Current State: Classic routes handle OAuth and upload interactions.

Evidence: `/youtube/authorize`, `/youtube/oauth2callback`,
`/youtube/revoke`, `/ajax/uploadyoutube`, `videoviewer.html`.

Modern Gap: Missing native OAuth workflow.

Protected Work: External integration, not a Modern core feature yet.

Porting Rule: Preserve credentials and callback routes until replaced.

Removal Risk: High.

Recommended Action: Treat as External/Classic until Modern upload design.

### Network

Current State: Classic network manager is wrapped by Modern safe controls.

Evidence: `/network`, `/ajax/network`, `network.html`,
`/modern-admin/system/network`, `ModernAdminNetworkView`.

Modern Gap: Native Modern page missing.

Protected Work: System operations can affect Raspberry reachability.

Porting Rule: Preserve safe controls until a native page is tested on Raspberry.

Removal Risk: High.

Recommended Action: Keep wrapper; add ownership metadata.

### Storage

Current State: Modern storage exists; drive manager remains safe-control wrapped.

Evidence: `/filespaceusage`, `/drives`, `/ajax/drives`,
`/modern-admin/storage`, `/modern-admin/storage/file-space-usage`,
`/modern-admin/storage/drives`.

Modern Gap: Native drive operations still missing.

Protected Work: Scientific source retention depends on storage clarity.

Porting Rule: Do not hide storage impact of FITS/RAW source persistence.

Removal Risk: Medium.

Recommended Action: Prioritize storage UX after task queue.

### GPIO

Current State: Classic manual GPIO is wrapped by Modern safe controls.

Evidence: `/manual_gpio`, `/ajax/manual_gpio`,
`/modern-admin/system/gpio-control`.

Modern Gap: Native Modern page missing.

Protected Work: Hardware control risk.

Porting Rule: Keep explicit confirmation/safety behavior.

Removal Risk: High.

Recommended Action: Leave wrapper until native hardware-control audit.

### Focus

Current State: Classic focus page/API is wrapped by Modern safe controls.

Evidence: `/focus`, `/js/focus`, `/ajax/focuscontroller`,
`/modern-admin/tools/focus`, `safe_controls.html`.

Modern Gap: Native Modern focus tool missing.

Protected Work: Camera/profile context matters.

Porting Rule: Future focus UI must respect selected camera/profile.

Removal Risk: Medium.

Recommended Action: Port after camera/profile ownership map is complete.

### Mask

Current State: Classic and Modern camera mask pages coexist.

Evidence: `/mask`, `mask.html`, `/modern-admin/cameras/mask-base`,
`ModernAdminMaskView`.

Modern Gap: Native multicamera mask editing details need verification.

Protected Work: Recent shape-aware mask fixes in processing/SQM/stars.

Porting Rule: Masks must be camera/shape-aware.

Removal Risk: High if global masks are assumed.

Recommended Action: Treat mask as protected processing-related UI.

### SQM

Current State: Classic SQM view and Modern observatory SQM wrapper exist.

Evidence: `/sqm`, `sqm.html`, `/modern-admin/observatory/sqm`,
`ModernAdminSqmView`.

Modern Gap: Native profile/camera context may be limited.

Protected Work: Recent SQM non-fatal mask handling.

Porting Rule: SQM failures must not crash ImageWorker.

Removal Risk: Medium.

Recommended Action: Keep wrapper while validating multicamera SQM.

### ADU

Current State: Classic ADU history and Modern camera ADU history exist.

Evidence: `/adu`, `adu.html`, `/modern-admin/cameras/adu-history`,
`TARGET_ADU_*`.

Modern Gap: Need clearer link to Auto Exposure/Gain target settings.

Protected Work: Yes, target ADU persistence/resolver fixes.

Porting Rule: Do not break profile target ADU pipeline.

Removal Risk: High.

Recommended Action: Keep ADU in Camera/Analytics context.

### Config Editor

Current State: Classic config and Modern Full/Inventory/Capture/Camera Settings
coexist.

Evidence: `/config`, `/ajax/config`, `config.html`,
`/modern-admin/settings/full`, `/modern-admin/settings/capture`,
`/modern-admin/settings/cameras`.

Modern Gap: Basic/Advanced/Developer redesign not implemented.

Protected Work: All profile-first config depends on save path correctness.

Porting Rule: Do not make legacy global fields canonical over profile fields.

Removal Risk: Critical.

Recommended Action: Next UX work should classify settings ownership.

### System Info

Current State: Classic and Modern system info pages exist.

Evidence: `/system`, `/ajax/system`, `/modern-admin/system`,
`/modern-admin/system/info`.

Modern Gap: Some actions are still Classic AJAX-backed.

Protected Work: Operational controls.

Porting Rule: Do not remove system actions until Modern replacements are tested.

Removal Risk: Medium.

Recommended Action: Keep Modern system pages canonical, wrappers active.

### Logs

Current State: Classic log and Modern log share JSON source.

Evidence: `/log`, `/js/log`, `/modern-admin/system/log`,
`modern_admin/log.html`.

Modern Gap: Download parity and filtering need verification.

Protected Work: Explainability and debugging depend on logs.

Porting Rule: Preserve log download routes until replacements exist.

Removal Risk: Medium.

Recommended Action: Keep shared API.

### Charts

Current State: Classic charts and Modern observatory charts share `/js/charts`;
dashboard also has metadata analytics.

Evidence: `/charts`, `/js/charts`, `chart.html`,
`/modern-admin/observatory/charts`, dashboard.

Modern Gap: Legacy chart options may not be fully ported.

Protected Work: Analytics/explainability.

Porting Rule: Do not remove `/js/charts` until Modern chart parity is proven.

Removal Risk: Medium.

Recommended Action: Split future analytics API only after parity.

### Public latest endpoints

Current State: Public redirects and latest media routes remain active.

Evidence: `/latestimage`, `/latesttimelapse`, `/lateststartrail*`,
`/latestraw*`, `/latestpanorama*`, `/images/<path:path>`.

Modern Gap: Modern Admin is not a replacement for public URLs.

Protected Work: External links/bookmarks.

Porting Rule: Public routes are Shared/Public, not Classic-only.

Removal Risk: High.

Recommended Action: Preserve until an explicit public URL compatibility policy
exists.

### Sync API

Current State: External sync API routes exist outside UI cleanup.

Evidence: `/sync/v1/*`, `syncapi_views.py`.

Modern Gap: None required for UI porting.

Protected Work: External integration.

Porting Rule: Do not classify as Classic UI.

Removal Risk: Critical.

Recommended Action: Leave untouched.

### Action API

Current State: External action API routes exist for pause/unpause.

Evidence: `/action/pause`, `/action/unpause`, `actionapi_views.py`.

Modern Gap: Modern service action exists separately but is not a replacement.

Protected Work: External automation.

Porting Rule: Do not remove as UI cleanup.

Removal Risk: High.

Recommended Action: Leave untouched.

### Admin / Safe Controls

Current State: Modern safe-control wrappers expose legacy tools inside Modern
shell.

Evidence: `ModernAdminSafeControlsMixin`, `modern_admin/safe_controls.html`,
`/modern-admin/tools/*`, `/modern-admin/system/network`,
`/modern-admin/storage/drives`.

Modern Gap: Native pages missing for several tools.

Protected Work: Transitional safety for operations.

Porting Rule: Wrapper means partial parity, not removal readiness.

Removal Risk: High if removed too early.

Recommended Action: Replace wrappers one at a time with native pages.

## 5. Modern Canonical Features

- Camera Profiles
- Multi-camera management
- Modern dashboard and analytics
- Camera Settings for acquisition/profile fields
- Auto Exposure profile controls
- Auto Gain profile controls
- Hybrid AWB/profile color controls
- Metadata Health
- Quality Score and Nightly Summary
- Environmental Awareness read-only diagnostics
- Event Foundation read-only diagnostics
- Scientific Source Layer contracts and reports
- Modern media list for routine browsing
- Modern Admin shell/navigation

## 6. Classic-Only Features

- Task Queue page
- Current user page
- Users administration
- Notifications administration
- YouTube/OAuth workflow
- Mini timelapse generation
- Some advanced image/FITS viewer actions
- Config history/restore parity
- Some public/latest route behaviors that are not admin UI replacements

## 7. Wrapper Features

- Timelapse generator: `/modern-admin/tools/generate`
- Focus: `/modern-admin/tools/focus`
- FITS/image processing: `/modern-admin/tools/process-fits`
- Camera simulator: `/modern-admin/tools/camera-simulator`
- Image circle helper: `/modern-admin/tools/image-circle-helper`
- Network: `/modern-admin/system/network`
- GPIO: `/modern-admin/system/gpio-control`
- Drives: `/modern-admin/storage/drives`
- Config safe control: `/modern-admin/system/config`
- Several observatory/camera pages using `ModernAdminContextMixin`

## 8. Shared / External Features

These must not be treated as pure Classic UI:

- Public latest endpoints: `/latest*`, `/images/<path:path>`
- Sync API: `/sync/v1/*`
- Action API: `/action/*`
- Shared AJAX/JSON: `/ajax/config`, `/js/charts`, `/js/log`,
  `/js/focus`, `/ajax/generate`, `/ajax/network`, `/ajax/drives`,
  `/ajax/manual_gpio`
- Authentication: `/login`, `/logout`
- Media object routes: `/view_*`, `/watch_*`
- YouTube/OAuth callback routes

## 9. Porting Order Recommendation

1. Preserve and label protected Modern work before touching Classic surfaces.
2. Add machine-readable feature/route ownership metadata.
3. Port Task Queue read-only diagnostics to Modern.
4. Port User Management and Notifications to Modern.
5. Port Config history/restore and settings ownership explanations.
6. Port Timelapse/Keogram/Startrail generation controls natively.
7. Port FITS/source review actions without weakening raw-first rules.
8. Port Network/Drives/GPIO/Focus from safe controls to native pages.
9. Validate public/latest and external API compatibility.
10. Only then begin Classic deprecation and removal by feature group.

## 10. Do-Not-Break Rules

- Do not remove profile-first configuration.
- Do not flatten multicamera logic into single-camera assumptions.
- Do not replace Modern endpoints or profile-aware pages with legacy global
  behavior.
- Do not remove metadata, quality, event, detector-result, meteor-intelligence,
  or scientific-source layers during UI cleanup.
- Do not reduce explainability, blocker logging, diagnostics, or shadow-only
  evidence trails.
- Do not eliminate fallbacks while Classic remains active.
- Do not remove public routes or external APIs only because no static consumer
  is found.
- Do not remove vendor assets without runtime verification and package policy.
- Do not promote display/JPEG/overlay images to scientific detector inputs.
- Do not make EventCandidate, DetectorResult, or MeteorObservation imply
  validation or ground truth.
- Do not sync hardware-specific camera fields across profiles unless explicitly
  safe.
- Do not remove safe controls until native Modern parity exists.

## 11. Next Safe Micro-Step

Create a small, non-invasive ownership map used by
`tools/hybrid_ui_inventory.py`, for example:

`HYBRID_UI_OWNERSHIP_MAP.md` or `tools/hybrid_ui_ownership_map.json`

The map should list known route/template/API ownership categories:

- protected_modern
- modern_canonical
- wrapper_only
- classic_only
- shared_api
- external_api
- public_compat
- unknown

The script can then report differences between inferred ownership and declared
ownership without changing runtime behavior. This gives future porting work a
repeatable safety net before any Classic removal.
