# HYBRID SETTINGS REDESIGN READINESS

## 1. Current State

Hybrid AllSky has reached a useful checkpoint:

- Classic-only feature coverage is effectively zero, but Classic removal is not
  possible yet.
- Modern Admin already includes settings inventory, full settings, capture
  settings, camera/profile settings, config history, and config restore
  inspection.
- Safe Actions now has contract, registry, runner, audit records, persistent
  JSONL audit log, dry-run endpoint, and service-ready foundations for:
  - `notification.acknowledge`
  - `image.exclude`
  - `image.unexclude`
  - `log.download`
- Mutative Modern actions remain blocked until true Flask integration tests can
  verify auth/session/CSRF behavior.

The next useful work is not another UI action. The project needs a settings
ownership redesign that can proceed without exposing new runtime mutations.

## 2. Why Settings Redesign Is Useful Now

Safe Actions progress is now gated by Flask-level test availability. Continuing
to add service-only action families is still possible, but it risks turning into
over-engineering if no endpoint/UI can be safely exposed yet.

Settings Redesign preparation can advance safely because it can be:

- documentation-first;
- read-only;
- profile-first;
- multicamera-first;
- independent from execute endpoints;
- independent from Classic removal;
- useful for future Basic / Advanced / Developer pages.

The current settings surface is broad and duplicated:

- Classic `/config` and `/ajax/config` still expose the large
  `IndiAllskyConfigForm`.
- Modern `/modern-admin/settings/full` is safer and searchable, but still close
  to the raw config model.
- Modern `/modern-admin/settings/cameras` is already profile-first and should
  remain canonical for camera/profile fields.
- Modern `/modern-admin/settings/capture` handles global capture fallback
  defaults.
- Config history and restore are read-only in Modern, while raw restore/download
  remain blocked.

## 3. What Not To Do Yet

Do not implement Settings UI changes yet.

Do not:

- remove Classic `/config`;
- remove `/ajax/config`;
- change config save behavior;
- change profile resolver behavior;
- move profile-owned fields back to global config;
- expose config restore/download;
- expose raw secret-bearing config payloads;
- redesign the database schema;
- add frontend-heavy dashboards;
- make runtime behavior depend on a new grouping model.

This phase should define ownership and grouping only.

## 4. Proposed Settings Architecture

### Basic

Daily operational controls that normal users need often.

Candidate groups:

- Camera/profile selection and camera status.
- Acquisition basics:
  - exposure;
  - gain;
  - target ADU;
  - auto exposure;
  - auto gain.
- Hybrid AWB status and simple mode.
- Scientific source persistence summary:
  - Never;
  - Periodic;
  - Every frame;
  - Event-window buffered.
- Storage status and retention summary.
- Display/rendering summary:
  - display image;
  - overlay;
  - stretch;
  - scientific source separation.

### Advanced

Operational controls that matter, but not every day.

Candidate groups:

- Timelapse / mini timelapse.
- Keogram / realtime keogram / longterm keogram.
- Startrail / startrail video.
- Panorama.
- Upload destinations and reporting status.
- Public/latest behavior.
- Sensor/environment settings.
- Lens/image circle/mask settings.
- Darks, bad pixel maps, defect maps.

### Developer

Dangerous, legacy, diagnostic, compatibility, or experimental settings.

Candidate groups:

- Raw full config editor.
- Legacy global fallbacks for profile-operated settings.
- Config restore/download/import.
- Hooks and external scripts.
- Legacy `DETECT_METEORS` / line detection settings.
- Event Foundation experimental toggles.
- Detector/RMS/AI placeholders.
- Network/GPIO/hardware actions until safe policies exist.
- Debug logging and diagnostics.

## 5. Current Modern/Profile Coverage

Already strong or protected:

- Multi-camera.
- Camera Profiles.
- Profile-first configuration.
- Camera Settings.
- Auto Exposure.
- Auto Gain.
- Hybrid AWB.
- Metadata.
- Analytics.
- Quality.
- Environmental Awareness.
- Event Foundation.
- Scientific Source Layer.

Already present but still too raw or incomplete:

- Modern Full Settings.
- Modern Capture Settings.
- Settings Inventory.
- Config History.
- Config Restore inspection.
- Upload status/config placeholders.
- Media/source settings scattered across Full Settings and media pages.

Still duplicated or confusing:

- global `CCD_CONFIG` / `CCD_EXPOSURE` / gain / ADU fallbacks vs profile values;
- FITS/RAW/source persistence settings vs display/rendering settings;
- upload provider settings spread across file transfer, S3, Sync API, YouTube;
- media-product settings for timelapse, keogram, startrail, panorama;
- Classic config restore/download vs Modern metadata-only inspection.

## 6. Relationship With Safe Actions

Settings Redesign should not bypass Safe Actions.

Rules:

- Config restore remains blocked until restore preview, rollback, audit, and
  Flask integration tests exist.
- Config download remains blocked until redaction and file/download policy exist.
- Settings save actions must stay within existing tested save paths until a
  dedicated Safe Action contract is designed.
- Profile-owned settings must remain under profile-aware Modern pages.
- Dangerous operations belong in Developer, even if they remain Classic-backed
  temporarily.

Safe Actions answered the question "how do we mutate safely?" Settings Redesign
should answer "where should each user-facing concept live?"

## 7. Raspberry Pi 5 Risks

Settings Redesign must remain Raspberry Pi 5-first:

- no large live dashboard polling;
- no full-table unpaginated config/history scans;
- no filesystem scans for settings discovery;
- no FITS/video conversion in settings pages;
- no heavyweight frontend bundle requirement;
- no client-side rendering of huge raw config payloads;
- no automatic background validation that competes with capture/processing.

The safe direction is static metadata, cached summaries, and explicit user
actions.

## 8. Profile / Multicamera Risks

The biggest design risk is accidentally flattening profile-first behavior into
global config again.

Guardrails:

- every setting must declare ownership:
  - global;
  - camera profile;
  - camera hardware;
  - display/rendering;
  - scientific source;
  - media product;
  - external integration;
  - developer/legacy fallback.
- profile-owned settings must show profile identity.
- sync/copy between profiles must remain explicit.
- global fallback fields must be labelled as fallback, not canonical.
- Modern Camera Settings remains canonical for profile-operated acquisition and
  camera-specific fields.

## 9. First Safe Micro-Step

Create a read-only settings ownership matrix generated from the existing
evidence, without changing UI or runtime behavior.

Suggested next artifact:

`HYBRID_SETTINGS_OWNERSHIP_MATRIX.md`

Scope:

- list major config keys/groups;
- map each to Basic / Advanced / Developer;
- map each to owner:
  - global;
  - profile;
  - camera;
  - media;
  - source/scientific;
  - external integration;
  - developer/legacy;
- note current UI exposure:
  - Classic `/config`;
  - Modern Full Settings;
  - Modern Capture Settings;
  - Modern Camera Settings;
  - Modern status/read-only pages;
- mark migration risk;
- mark "do not move yet" fields.

This micro-step is small, reversible, and verifiable. It does not require Flask
runtime tests, new UI, endpoint changes, config refactors, or Classic removal.

## 10. Checkpoint Answers

1. We are blocked on mutative Safe Actions because true Flask integration tests
   for auth/session/CSRF are not available in the current lightweight
   environment.
2. Continuing service-only Safe Actions is useful for a few low-risk families,
   but doing many more without endpoint testability risks over-engineering.
3. Settings Redesign preparation can advance now because it can be read-only and
   ownership-focused.
4. Modern/profile/multicamera already cover camera profiles, camera settings,
   auto exposure, auto gain, Hybrid AWB, metadata, analytics, quality,
   scientific sources, and much of capture/profile operation.
5. The largest Classic/duplicated areas are monolithic `/config`,
   `/ajax/config`, raw full settings, config restore/download, upload/provider
   groups, media product settings, display/rendering/source settings, and
   legacy detector/hook/developer settings.
6. The first safe micro-step is a settings ownership matrix, not a UI change.
