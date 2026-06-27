# HYBRID PRODUCT CONSOLIDATION MATRIX

## 1. Purpose

This document reframes Hybrid AllSky work from "port everything from Classic UI
to Modern UI" into **product consolidation**.

Classic UI remains valuable evidence: it shows existing capabilities, edge
cases, historical workflows and compatibility surfaces. It is not the product
definition. The product definition should come from Hybrid AllSky's current
architecture, protected Modern work, operator value, backend contracts, safety
requirements and Raspberry Pi 5 constraints.

The goal is to preserve useful capability while building a cleaner product:

- do not lose useful functions;
- do not redo protected Modern work;
- do not copy bad Classic UX into Modern;
- do not remove anything without evidence;
- build backend/service boundaries that can support a future frontend;
- avoid spending major effort on marginal features before core product surfaces
  are coherent.

## 2. Core Principle

Classic UI is a reference implementation, not the product definition.

No useful capability should be lost.

No feature should be removed until classified and verified.

Existing protected Modern work must not be degraded.

Every Modern screen must be designed as the final product experience, not as a
copy of the Classic screen.

## 3. Classification Labels

| Label | Meaning | Use when | What not to do yet |
| --- | --- | --- | --- |
| KEEP | The capability is part of the product and should remain user-facing. | It has clear operator value and a safe Modern or shared surface. | Do not remove or hide it. |
| REDESIGN | The capability matters, but the current UX or information architecture is wrong. | The feature is useful but Classic-shaped, duplicated, confusing or too raw. | Do not copy Classic one-to-one. |
| DEVELOPER | The capability is useful for experts, diagnostics, compatibility or experiments. | The setting/action is dangerous, low-frequency or technical. | Do not put it in Basic. |
| LEGACY FALLBACK | Keep the old surface until a safe replacement exists. | Existing installs or unsafe actions still depend on Classic/shared behavior. | Do not remove just because Modern has a read-only page. |
| DEPRECATE LATER | The capability may leave the main product after parity and telemetry/evidence. | Modern replacement is mature and external usage risk is understood. | Do not deprecate now. |
| REMOVE CANDIDATE | Likely obsolete, but not yet proven removable. | Evidence suggests no user/product value. | Do not remove without verification and rollback. |
| PROTECTED MODERN WORK | Modern/shared work is already the canonical product direction. | Multi-camera, profiles, analytics, scientific source, event foundations, etc. | Do not rewrite or simplify away its architecture. |
| NEEDS EVIDENCE | Current product value, consumers or ownership are unclear. | Static evidence is incomplete or usage may be external/dynamic. | Do not classify as dead code. |

## 4. Product Areas Matrix

| Product area | Existing Classic surface | Existing Modern surface | User value | Backend importance | Frontend importance | Classification | Why | Risk if lost | Recommended action | Do not remove yet? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Dashboard | Classic latest/public pages, charts | Modern Admin dashboard, analytics/status cards | High | High | High | REDESIGN | Modern should be operational command center, not a Classic landing page. | Operators lose health/status awareness. | Consolidate around actionable status, not legacy page parity. | Yes |
| Settings | `/config`, `/ajax/config`, config history/restore | Modern settings inventory/full/capture/cameras | Critical | Critical | Critical | REDESIGN | High-value but currently raw/duplicated. | Wrong config ownership can break capture/profiles. | Continue Settings Ownership Matrix into machine-readable group map. | Yes |
| Camera Profiles | Classic global config fallback | Modern Camera Settings, Cameras, profile resolver | Critical | Critical | High | PROTECTED MODERN WORK | Canonical product model. | Multicamera/profile regressions. | Preserve and make profile ownership clearer. | Yes |
| Multi-camera | Classic not designed around it | Modern Cameras, profile-aware settings/status | Critical | Critical | High | PROTECTED MODERN WORK | Core Hybrid differentiator. | Wrong camera/profile writes or mixed frames. | Preserve, test and explain. | Yes |
| Capture / camera control | Classic camera/config controls | Modern service/capture controls and profile settings | Critical | Critical | High | KEEP | Operationally essential. | Capture unavailable or wrong camera state. | Keep Modern canonical; leave risky actions guarded. | Yes |
| Auto Exposure | Classic/global config fallback | Modern profile-first controls/status | Critical | Critical | Medium | PROTECTED MODERN WORK | Exposure stability is core runtime behavior. | Poor images, wrong ADU behavior. | Preserve profile-first semantics and explain blockers. | Yes |
| Auto Gain | Classic/global fallback | Modern profile-first controls/status | Critical | Critical | Medium | PROTECTED MODERN WORK | Gated runtime behavior is already optimized. | Unexpected gain changes. | Preserve apply gates and runtime state. | Yes |
| Hybrid AWB | Classic/global color settings | Modern Camera Settings / Hybrid AWB | High | High | Medium | PROTECTED MODERN WORK | Hardware/profile-specific color behavior. | Wrong color pipeline per sensor. | Keep per-camera; improve explanation. | Yes |
| Metadata | None or implicit Classic artifacts | Modern metadata, analytics, JSONL reports | High | Critical | Medium | PROTECTED MODERN WORK | Evidence layer for analytics/events/science. | Loss of explainability and reports. | Preserve schema compatibility. | Yes |
| Analytics | Classic charts | Modern dashboard/analytics/status | High | High | High | PROTECTED MODERN WORK | Modern insight layer. | Operators lose trends and diagnostics. | Keep, consolidate charts later. | Yes |
| Quality | Not productized in Classic | Modern quality/environment evidence | High | High | Medium | PROTECTED MODERN WORK | Input for environment/events. | False confidence in data quality. | Keep explanatory and read-only. | Yes |
| Environmental Awareness | Partial Classic/status | Modern observatory/environment context | Medium | High | Medium | PROTECTED MODERN WORK | Adds situational context. | Operators lose weather/visibility clues. | Keep; tune with field evidence. | Yes |
| Scientific Source Layer | FITS/RAW settings/viewers | Modern raw-first contracts, FITS/source metadata | Critical | Critical | High | PROTECTED MODERN WORK | Future detector-grade foundation. | JPEG/display images treated as science. | Preserve raw-first; design clear source UX. | Yes |
| Event Foundation | None as product UI | Event candidate/timeline/classification foundations | Future high | Critical | Medium | PROTECTED MODERN WORK | Foundation for intelligence, not Classic parity. | Detector/event architecture confusion. | Keep shadow/read-only until validated. | Yes |
| Detector / Meteor foundations | Legacy `DETECT_METEORS` toggles | Domain contracts/offline bridges | Future high | High | Medium | PROTECTED MODERN WORK | Architecture exists but real detector is blocked. | Misleading meteor claims. | Keep blocked pending outdoor FITS validation. | Yes |
| Task Queue | `/tasks` | Modern list/usability/detail | Medium | High | Medium | KEEP | Operators need visibility; mutations unsafe. | Lost operational diagnostics. | Keep read-only; actions need contract. | Yes |
| Notifications | `/notifications`, `/ajax/notification` | Modern list/usability/detail; safe action service-ready | High | Medium | Medium | KEEP | Operational warnings matter. | Missed failures/status. | Keep read-only; acknowledge execute blocked. | Yes |
| User Management | `/user`, `/users`, `/ajax/user` | Modern read-only list/usability/detail | Medium | Critical | Medium | DEVELOPER | Security-critical, low-frequency admin surface. | Security/account lockout. | Keep read-only until auth policy exists. | Yes |
| Config History | `/config/list`, `/config/download` | Modern read-only history/usability | High | High | Medium | KEEP | Important audit trail. | Lost config provenance. | Keep metadata-only; raw download blocked. | Yes |
| Config Restore | `/config/restore`, `/ajax/config/restore` | Modern read-only inspection/detail | High | Critical | Medium | LEGACY FALLBACK | Restore is useful but dangerous. | No recovery path or unsafe restore. | Keep Classic fallback; design preview/diff/rollback later. | Yes |
| FITS Viewer | `/fitsimageviewer`, `/fits2jpeg`, AJAX | Modern FITS metadata/usability/detail | High | High | Medium | REDESIGN | Should be scientific source inspection, not just Classic viewer copy. | Loss of source validation. | Keep metadata-first; conversion/download blocked. | Yes |
| Image Viewer | `/imageviewer`, `/ajax/imageviewer`, exclude | Modern media list/detail; exclude service-ready | High | Medium | High | REDESIGN | Should become media center, not table clone. | Operators lose image review workflow. | Keep read-only; actions need media policy. | Yes |
| Video Viewer | Classic video viewer/upload/share | Modern metadata list/detail | Medium | Medium | Medium | REDESIGN | Media actions are useful but unsafe. | Lost review/playback access. | Keep metadata; define media action policy. | Yes |
| Gallery | Classic gallery/PhotoSwipe | Modern gallery usability | High | Medium | High | REDESIGN | Valuable user-facing media browsing. | Poor review/browsing. | Keep, redesign as coherent media center. | Yes |
| Timelapse | Classic generation/settings/actions | Modern status/usability/wrapper | Medium | High | Medium | REDESIGN | Product output matters; generation unsafe. | Lost nightly products. | Keep status; actions require queue policy. | Yes |
| Keogram | Classic generation/settings | Modern metadata/status | Medium | High | Medium | REDESIGN | Useful sky summary product. | Lost observatory product. | Keep status; generation/download blocked. | Yes |
| Startrail | Classic generation/settings | Modern metadata/status | Medium | High | Medium | REDESIGN | Useful media product. | Lost output product. | Keep status; generation/download blocked. | Yes |
| Mini Timelapse | Classic mini generate | Modern metadata/status | Low-medium | Medium | Low | REDESIGN | Useful but less core. | Minor loss of convenience. | Keep but lower priority. | Yes |
| Panorama | Classic/runtime outputs/public routes | Modern metadata/status | Medium | High | Medium | REDESIGN | Useful where configured; public endpoints matter. | Public/output breakage. | Preserve; redesign later. | Yes |
| Raw Viewer | Classic/public raw routes | Modern raw metadata/status | High | High | Medium | REDESIGN | Scientific/source review matters. | Lost raw/source inspection. | Keep metadata; decode/download blocked. | Yes |
| Upload providers | Classic config/upload pipeline | Modern provider/status/detail | Medium | High | Medium | REDESIGN | Useful but credential/remote risk. | Upload failures hidden. | Keep status; actions blocked. | Yes |
| YouTube/OAuth | Classic OAuth/refresh/revoke/upload | Modern sanitized status audit | Low-medium | High | Low | LEGACY FALLBACK | External credential flow is risky and specialized. | OAuth breakage or token leakage. | Keep Classic fallback; do not copy flow yet. | Yes |
| Logs | Classic logs/downloads | Modern log/detail; download policy foundation | High | Medium | Medium | KEEP | Diagnostics are essential. | Harder troubleshooting. | Keep read-only; download blocked until policy/tests. | Yes |
| Storage/Drives | Classic/system tools | Modern storage/drive status | High | High | Medium | KEEP | RPi storage health is operationally critical. | Disk exhaustion unseen. | Keep RPi5-first, no scans. | Yes |
| Network | Classic/system network tools | Modern wrapper/status | Medium | Critical | Low | DEVELOPER | Useful but OS-level mutation risk. | Remote access loss. | Keep wrapper; no Basic mutation. | Yes |
| GPIO | Classic/manual tools | Modern safe wrapper/status | Low-medium | Critical | Low | DEVELOPER | Hardware state risk. | Hardware regressions. | Keep wrapper until hardware policy. | Yes |
| Focus | Classic focus controller | Modern wrapper/read-only status | Medium | High | Medium | REDESIGN | Important for some setups; movement is risky. | Lost focus control. | Keep read-only; hardware action policy needed. | Yes |
| GPS | Classic/full settings unclear | Needs verification | Low-medium | Medium | Low | NEEDS EVIDENCE | Hardware/provider ownership unclear. | Wrong time/location context. | Audit before productizing. | Yes |
| Sensors | Classic/full settings, observatory | Modern observatory/sensor partial | Medium | Medium | Medium | REDESIGN | Environment data useful but mixed. | Context loss. | Consolidate under observatory/health. | Yes |
| Mask/Lens/Image Circle | Classic tools/config | Modern Camera Settings/wrappers | High | High | Medium | REDESIGN | Camera/profile-specific geometry is important. | Bad crops/masks/calibration. | Keep profile/camera ownership. | Yes |
| Public/latest endpoints | Public Classic-style routes | Public/shared routes, Modern summaries | Critical | Critical | Low | KEEP | Compatibility surface, bookmarks/external clients. | Existing integrations break. | Preserve behavior; do not redesign as admin UI. | Yes |
| Sync API | `/sync/v1/*` | External/shared API | High | Critical | Low | KEEP | External sync contract. | Remote integrations break. | Preserve; version carefully. | Yes |
| Action API | `/action/*` | External/shared API | Medium | Critical | Low | KEEP | External control contract. | Remote automation breakage. | Preserve and audit separately. | Yes |
| Developer/debug options | Classic config, hooks, raw settings | Modern Full Settings/developer docs | Medium for experts | High | Low | DEVELOPER | Compatibility/debug features matter. | Power users lose recovery paths. | Keep in Developer, not Basic. | Yes |
| Legacy detector toggles | Classic/full settings | Full Settings only | Low now | Medium | Low | LEGACY FALLBACK | Existing code exists but not real Hybrid detector. | Misleading detection UX. | Hide as Developer/Legacy until validated. | Yes |
| Classic-only templates/assets | Classic templates/DataTables/PhotoSwipe | Some Modern replacements | Low-to-medium | Low | Low | DEPRECATE LATER | Remove only after parity/runtime usage is verified. | Breaking fallback pages. | Track, do not remove now. | Yes |
| Vendor JS/CSS | DataTables, PhotoSwipe, VirtualSky | Shared/Classic/Modern wrappers | Medium | Low | Medium | NEEDS EVIDENCE | Runtime loading can be dynamic. | Viewer/gallery regressions. | Verify before removal. | Yes |

## 5. Backend Foundation Priorities

Backend work should prioritize reusable product capability over frontend shape:

- Service boundaries for actions and domain concepts.
- Read-only API contracts for metadata/status pages before frontend rewrites.
- Safe Actions only where actions are actually needed.
- Audit records and persistence for every mutating action.
- Ownership metadata for settings, profiles, cameras, media products and
  scientific sources.
- Clear profile/camera separation in every save path.
- No frontend-specific business logic trapped in templates.
- Raspberry Pi 5-first constraints:
  - lazy work;
  - bounded queries;
  - no aggressive polling;
  - no filesystem scans;
  - no conversion work in request/UI paths.

## 6. Frontend Future Priorities

A future frontend should be shaped around product centers, not Classic pages:

- Settings center:
  - Basic / Advanced / Developer;
  - profile ownership;
  - source/display separation.
- Operational dashboard:
  - capture health;
  - camera/profile state;
  - source persistence health;
  - storage warnings.
- Media center:
  - image, video, gallery, FITS, raw, panorama and generated products with
    consistent metadata/action policy.
- Health / maintenance center:
  - logs;
  - storage;
  - network;
  - task queue;
  - notifications.
- Scientific / event center:
  - source readiness;
  - quality;
  - event foundations;
  - future detector outputs.
- Developer center:
  - raw settings;
  - hooks;
  - legacy fallback;
  - diagnostics.

## 7. What Must Not Be Reworked

Do not redo or degrade:

- Multi-camera.
- Camera Profiles.
- Profile-first configuration.
- Auto Exposure / Auto Gain.
- Hybrid AWB.
- Metadata / Analytics / Quality.
- Environmental Awareness.
- Event Foundation.
- Scientific Source Layer.
- Detector / Meteor domain foundations.
- Modern Admin shell.
- Modern safe controls until native parity exists.
- Safe Action infrastructure.
- Existing read-only Modern surfaces unless the redesign has a better product
  reason than Classic parity.

## 8. What Must Not Be Removed Yet

Do not remove:

- Classic fallback for actions.
- Public/latest endpoints.
- Sync API.
- Action API.
- Shared AJAX endpoints.
- Restore/download paths.
- Media generation actions.
- Upload/OAuth routes.
- User/auth Classic mutation surfaces.
- Developer/debug assets.
- Vendor JS/CSS.
- Any feature classified `NEEDS EVIDENCE`.
- Any feature without a rollback plan.

Ugly legacy code is not the same as unused product capability.

## 9. First Product Consolidation Target

Recommended first target: **Settings**.

Why:

- highest user value;
- high impact on simplicity;
- already analyzed in Settings Readiness and Settings Ownership Matrix;
- can advance without Flask execute tests;
- prepares any future frontend;
- strengthens profile/multicamera clarity;
- reduces confusion around scientific source persistence, display rendering and
  legacy global fallbacks.

Settings should not begin with a new UI. It should begin with machine-readable
ownership metadata.

## 10. Next Safe Micro-step

Create:

`tools/hybrid_settings_ownership_map.json`

Scope:

- metadata only;
- no runtime import;
- no UI wiring;
- no config changes;
- no removal;
- no behavior change.

The JSON should encode:

- group id;
- product label;
- classification;
- proposed owner;
- proposed Basic / Advanced / Developer level;
- example config key prefixes;
- current UI surfaces;
- protected/do-not-move flags;
- migration risk;
- notes.

After that, add a small report generator or validation section that compares the
map against known settings groups. Do not make it drive UI until it has been
reviewed.
