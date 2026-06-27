# HYBRID SETTINGS OWNERSHIP MATRIX

## 1. Purpose

This document is a read-only ownership matrix for the future Hybrid AllSky
Settings Redesign.

It does not change UI, runtime configuration, config save behavior, Classic UI,
database schema, or resolver logic. Its job is to make each major settings area
explicit before any Basic / Advanced / Developer redesign work begins.

Primary evidence:

- Classic `/config`, `/ajax/config`, `/config/list`, `/config/download`,
  `/config/restore`, `/ajax/config/restore`.
- Modern `/modern-admin/settings`, `/modern-admin/settings/full`,
  `/modern-admin/settings/capture`, `/modern-admin/settings/cameras`,
  `/modern-admin/config-history`, `/modern-admin/config-restore`.
- `ModernAdminSettingsInventoryView`, `ModernAdminFullSettingsView`,
  `ModernAdminCaptureSettingsView`, `ModernAdminCameraSettingsView`.
- `IndiAllskyConfigForm`.
- `HYBRID_SETTINGS_REDESIGN_READINESS.md`, `HYBRID_FEATURE_MAP.md`,
  `HYBRID_PORTING_BACKLOG.md`, `HYBRID_ARCHITECTURE_V2.md`, and
  `HYBRID_PORTING_GUARDRAILS.md`.

## 2. Principles

- Profile-first: profile-owned camera/acquisition values stay in camera profile
  settings.
- Multicamera-first: every camera/profile setting must preserve camera identity.
- Modern-first: Modern Admin is the operational center, but Classic remains
  fallback until parity and deprecation are complete.
- Scientific-first: display JPEGs, overlays and stretch must not be treated as
  scientific source data.
- Raspberry Pi 5-first: no heavy polling, filesystem scans, large client
  bundles, full-table scans, or conversion work in settings pages.
- Safe-actions-first: restore, download, upload, hardware, queue and auth
  mutations require Safe Action contracts before UI exposure.
- No config removal yet.
- No runtime behavior change.

## 3. Ownership Levels

| Owner | Meaning |
| --- | --- |
| Global | Applies to the whole instance or remains a legacy/global fallback. |
| Camera | Tied to a DB camera row or physical camera identity. |
| Camera Profile | Stored or resolved through `MULTI_CAMERA.profiles[n]` or profile-aware fallback. |
| Media Product | Controls generated outputs such as timelapse, keogram, startrail or panorama. |
| Scientific Source | Controls FITS/RAW/source metadata and detector-grade persistence. |
| External Integration | Upload, OAuth, Sync API, remote destinations and provider credentials. |
| Developer / Legacy | Debug, compatibility, hooks, legacy detector, raw config, experimental toggles. |
| Runtime / System | Operating-system, service, storage, network, logs, queue and hardware state. |

## 4. UI Levels

| Level | Meaning |
| --- | --- |
| Basic | Daily-use concepts normal operators need to keep the system working. |
| Advanced | Useful operational settings that should not be changed every day. |
| Developer | Dangerous, legacy, diagnostic, compatibility or experimental settings. |

## 5. Matrix

| Setting group | Example keys / forms / area | Current UI | Proposed owner | Proposed level | Modern status | Migration risk | Do not move yet? | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Camera connection | `camera_interface`, INDI server/port/name, libcamera camera id/options, camera DB rows | Modern Camera Settings; Classic config fallback | Camera Profile / Camera | Basic for select identity, Advanced for driver details | Strong Modern/profile coverage | Critical | No, but preserve exactly | Do not flatten per-camera driver fields into global config. |
| Camera profile identity | `MULTI_CAMERA.profiles[n].profile_id`, label, enabled, primary, camera id | Modern Cameras; Modern Camera Settings; Settings Inventory | Camera Profile | Basic | Protected Modern work | Critical | No | Profile identity must remain visible during saves/syncs. |
| Exposure | `CCD_EXPOSURE_*`, `exposure_default`, profile overrides | Modern Camera Settings; Capture Settings fallback; Classic `/config` | Camera Profile with Global fallback | Basic | Protected/profile-first | Critical | No | Profile values are canonical; global fields are fallback. |
| Gain | `CCD_CONFIG.*.GAIN`, `gain_night`, `gain_day`, profile overrides | Modern Camera Settings; Capture Settings fallback; Classic `/config` | Camera Profile with Global fallback | Basic | Protected/profile-first | Critical | No | Keep runtime Auto Gain gates intact. |
| Auto Exposure | `AUTO_EXPOSURE_*`, target ADU fields, metering mode | Modern Camera Settings; Full Settings; Classic `/config` | Camera Profile with Global fallback | Basic / Advanced | Protected/profile-first | Critical | No | Explain exposure-first behavior and target ADU ownership. |
| Auto Gain | `AUTO_GAIN_*`, `CCD_CONFIG.AUTO_GAIN_*`, profile gain limits | Modern Camera Settings; Full Settings; Classic `/config` | Camera Profile with Global fallback | Basic / Advanced | Protected/profile-first | Critical | No | Apply gate and runtime state must not become implicit. |
| Hybrid AWB | `HYBRID.AWB.*`, profile `awb`, libcamera AWB gains, RGB factors | Modern Camera Settings | Camera Profile | Basic for status/mode, Advanced for tuning | Protected Modern work | Critical | No | Hardware-specific; do not sync CFA/debayer/AWB blindly. |
| Image acquisition | exposure period, day/night capture, binning, cooling, pause, camera temp | Capture Settings; Camera Settings; Full Settings; Classic `/config` | Camera Profile / Global fallback | Basic / Advanced | Partial Modern | High | No | Split daily acquisition from legacy fallback values. |
| Image save formats | image file type, thumbnails, image save flags, day save flags | Full Settings; Capture Settings partial; Classic `/config` | Global / Camera Profile | Advanced | Partial Modern | Medium | Yes | Needs display vs source terminology first. |
| FITS/source files | `IMAGE_SAVE_FITS*`, `IMAGE_SAVE_FITS_PERIOD`, `IMAGE_EXPORT_RAW`, raw/source metadata | Full Settings; FITS metadata pages; Classic FITS viewer | Scientific Source | Basic summary, Advanced policy | Protected source layer / partial UI | Critical | Yes | Redesign as Never / Periodic / Every frame / Event-window buffered. |
| Metadata | frame metadata paths, frame metadata JSONL, metadata reports | Modern analytics/status; Full Settings | Scientific Source / Global | Advanced | Protected Modern work | High | Yes | Keep malformed-row tolerance and JSONL compatibility. |
| Analytics | 24h/nightly analytics, charts, ADU/SQM summaries | Modern dashboard/analytics; Charts; Classic charts | Global / Runtime | Basic summary, Advanced charts | Protected/partial Modern | Medium | No | Settings should link concepts, not duplicate chart logic. |
| Quality | quality scoring, stable frame flags, weather/visibility context | Modern quality/environment pages | Runtime / Scientific Source | Basic summary, Advanced diagnostics | Protected Modern work | Critical | Yes | Do not weaken explainability or schema. |
| Environmental Awareness | smoke, aurora, weather, cloud/environment context | Modern environment/observatory pages; Full Settings partial | Runtime / External Integration | Advanced | Protected Modern work | Medium | Yes | Depends on sensors/providers and external data. |
| Scientific Source Layer | `ScientificFrame`, source paths, detector paths, FITS/RAW policy | Modern FITS/source reports; Full Settings partial | Scientific Source | Basic summary, Advanced policy, Developer diagnostics | Protected Modern work | Critical | Yes | Never promote display JPEG to scientific source. |
| Timelapse | `TIMELAPSE_*`, daytime timelapse, video generation settings | Modern media status; Full Settings; Classic generation/actions | Media Product | Advanced | Partial Modern | High | Yes | Generation actions remain blocked by Safe Actions policy. |
| Keogram | realtime/longterm keogram settings | Modern media status; Full Settings; Classic tools | Media Product | Advanced | Partial Modern | High | Yes | Generation/download/conversion blocked. |
| Startrail | `STARTRAILS_*` | Modern media status; Full Settings; Classic tools | Media Product | Advanced | Partial Modern | High | Yes | Generation/download/conversion blocked. |
| Startrail video | startrail video settings, public watch routes | Modern metadata/status; public endpoints | Media Product / Public | Advanced | Partial Modern / preserve public | High | Yes | Public behavior is compatibility surface. |
| Mini timelapse | mini timelapse settings/generation | Modern metadata/status; Classic mini generate | Media Product | Advanced | Partial Modern | Medium | Yes | Generation/download blocked. |
| Upload providers | `FILETRANSFER`, `S3UPLOAD`, `SYNCAPI`, upload flags per media type | Modern uploads status/detail; Full Settings; Classic config | External Integration | Advanced | Partial Modern | Critical | Yes | Provider actions and remote operations remain blocked. |
| YouTube/OAuth | YouTube OAuth credentials/status/upload flags | Modern sanitized status; Classic OAuth routes; Full Settings | External Integration | Advanced / Developer for credentials | Partial Modern | Critical | Yes | Never expose tokens, refresh tokens, client secret or raw payload. |
| Notifications | notification settings, delivery/status, acknowledge/delete | Modern list/detail; Classic/shared AJAX | Runtime / External Integration | Basic for status, Advanced for delivery | Partial Modern | High | Yes | Acknowledge service-ready; execute/UI blocked pending Flask tests. |
| Users/auth | users, passwords, roles, API key metadata | Modern read-only users; Classic user/admin forms | Runtime / System | Developer | Partial Modern | Critical | Yes | Mutations need explicit auth policy and self-lockout prevention. |
| Logs | `/log`, `/js/log`, log download routes | Modern log/detail; Classic downloads | Runtime / System | Developer | Partial Modern | High | Yes | `log.download` policy exists; real download remains blocked. |
| Task Queue | queue/action/status/payload | Modern list/detail; Classic task queue | Runtime / System | Advanced / Developer | Partial Modern | High | Yes | Retry/cancel/requeue/delete blocked. |
| Focus | focuser status/movement/autofocus | Modern safe controls/read-only; Classic focus controller | Runtime / System / Camera | Advanced | Wrapper only | Critical | Yes | Hardware movement requires hardware action policy. |
| GPIO | GPIO manual controls/settings | Modern wrapper; Classic/system tools; Full Settings | Runtime / System | Developer | Wrapper only | Critical | Yes | Hardware action risk; keep wrapper. |
| Network | NetworkManager settings/actions | Modern wrapper/status; system tools | Runtime / System | Developer | Wrapper only | Critical | Yes | OS-level mutation; keep outside Basic. |
| Drives/storage | storage paths, drive status, retention, space | Modern storage pages; Full Settings | Runtime / System / Global | Basic summary, Advanced policy | Partial Modern | High | Yes | Avoid scans and unbounded queries on RPi5. |
| GPS | GPS enable/source/status | Full Settings; sensors/status unclear | Runtime / System | Advanced | Needs verification | Medium | Yes | Verify hardware/provider ownership first. |
| Sensors | environment sensors, SQM, ADU, weather providers | Modern observatory/ADU/SQM; Full Settings | Runtime / System / External Integration | Advanced | Partial Modern | Medium | Yes | Sensor ownership is still mixed. |
| Mask/lens/image circle | lens data, image circle, mask, crop, rotate, flip, optics | Modern Camera Settings; Full Settings; Classic tools | Camera Profile / Camera | Advanced | Partial Modern | High | Yes | Hardware/image-geometry settings are camera-specific. |
| Public/latest endpoints | `/latest*`, public image/raw/video routes, web display settings | Public routes; Classic config; Modern summaries | Public / Global | Advanced | Preserve | Critical | Yes | Do not treat as Classic-removal target. |
| Legacy detector/meteor | `DETECT_METEORS`, `DETECT_*`, legacy line detection | Full Settings / Classic config | Developer / Legacy | Developer | Needs verification | Critical | Yes | Do not present as real meteor detector. |
| Developer/debug options | hooks, external scripts, debug flags, raw JSON, experimental toggles | Full Settings; Classic config | Developer / Legacy | Developer | Partial Modern | High | Yes | External scripts may depend on them. |
| Config history/restore | config list/history, restore metadata, active restore | Modern read-only history/restore; Classic restore/download | Developer / Runtime | Developer | Partial Modern | Critical | Yes | Restore/download blocked by Safe Actions and redaction policy. |
| Config import/export/download | config download, raw payload, import/restore files | Classic config/download/restore | Developer / Legacy | Developer | Classic fallback | Critical | Yes | No raw config exposure until redaction/diff/rollback policy exists. |

## 6. Basic Proposal

Basic should show only concepts that normal operators need to keep the system
healthy:

- active camera/profile identity;
- camera enabled/primary status;
- exposure/gain/target ADU summary;
- Auto Exposure / Auto Gain status;
- Hybrid AWB status and simple mode;
- source persistence summary: Never / Periodic / Every frame / Event-window
  buffered;
- storage free-space and retention summary;
- latest capture/source/metadata health;
- notifications/log warnings summary;
- safe links to Advanced or Developer when more detail is required.

Basic should avoid raw config key names unless they clarify profile ownership.

## 7. Advanced Proposal

Advanced should contain operational settings that matter but are not daily:

- media products: timelapse, mini timelapse, keogram, startrail, startrail
  video, panorama;
- upload provider status and non-secret configuration summaries;
- public/latest behavior summaries;
- lens, mask, image circle and geometry;
- sensor/environment/GPS/SQM/ADU settings;
- storage/retention policies;
- scientific source persistence policy details;
- display/rendering controls that do not alter source data.

Advanced may link to blocked Safe Action readiness states, but should not expose
mutations without contracts and tests.

## 8. Developer Proposal

Developer should contain dangerous, compatibility and diagnostic surfaces:

- raw Full Settings editor;
- Classic fallback global fields;
- config history, restore, import/export/download;
- hooks and external scripts;
- legacy detector/meteor/line-detection toggles;
- Event Foundation experimental toggles;
- detector/RMS/AI placeholders;
- network/GPIO/hardware operations;
- auth/user mutation surfaces;
- log downloads and support bundle-like actions;
- raw JSON/config inspection with redaction warnings.

Developer is not a trash bin. It is the explicit place for high-risk settings
that must remain possible but should not clutter normal operation.

## 9. Do Not Move Yet

Do not move or redesign these into active new UI yet:

- Config restore, import, export and raw download.
- User/auth mutations.
- Queue retry/cancel/requeue/delete.
- Focus/GPIO/hardware movement.
- Network connection mutations.
- Upload/OAuth actions.
- FITS/raw/source download or conversion.
- Log download runtime endpoints.
- Media generation/delete/share/download actions.
- Legacy detector/meteor settings.
- Scientific Source Layer runtime behavior.
- Event Foundation runtime behavior.

These areas need Safe Action contracts, Flask integration tests, redaction,
rollback/no-rollback semantics, or domain validation first.

## 10. First Safe Micro-step

Create a machine-readable settings group map, for example:

`tools/hybrid_settings_ownership_map.json`

The map should be read-only metadata only:

- group id;
- display label;
- proposed owner;
- proposed level;
- example config keys/prefixes;
- current UI surfaces;
- risk;
- do-not-move flag;
- notes.

Do not wire it to UI yet. Use it first to generate or validate a Markdown report
so the grouping can be reviewed before any runtime setting moves.

## 11. Risks

- Breaking profile/multicamera behavior by moving profile fields into global
  config.
- Hiding legacy fallback settings that the runtime still reads.
- Duplicating Classic config instead of simplifying concepts.
- Hiding advanced options that existing installations depend on.
- Creating a heavy settings dashboard that competes with capture/processing on
  Raspberry Pi 5.
- Treating source/display/rendering settings as the same concept.
- Exposing config restore/download before redaction and rollback policy exist.
- Making Safe Actions look complete just because a service-only contract exists.
