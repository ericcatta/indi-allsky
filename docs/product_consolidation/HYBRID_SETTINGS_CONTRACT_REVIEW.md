# Hybrid Settings Contract Review

This review defines the intended product contract for Hybrid settings without
renaming, migrating, deleting, moving, or changing any runtime setting.

It uses:

- `tools/hybrid_settings_ownership_map.json`
- `HYBRID_SETTINGS_INVENTORY_REPORT.md`
- `docs/product_consolidation/HYBRID_PRODUCT_CONSOLIDATION_AUDIT.md`
- `docs/product_consolidation/HYBRID_ROUTE_ROLE_MATRIX.md`
- static inspection of current settings routes and ownership metadata

## Executive Summary

Settings are still the highest-risk consolidation area in Hybrid AllSky.

The inventory has 39 settings groups:

- 9 Basic groups
- 19 Advanced groups
- 11 Developer groups
- 33 high-risk groups
- 30 `do_not_move_yet` groups
- 13 final read-only product settings pages

The current settings structure is useful as a read-only ownership map, but it
must not become the main product path. The Product Architecture already says
to stop expanding `/modern-admin/settings/*` as the primary direction. Settings
should support the Product UI; they should not define it.

## Contract Rules

1. Basic summarizes and exposes safe intent, not raw keys.
2. Advanced exposes control, but only where ownership is clear.
3. Developer exposes internals, compatibility, raw config, diagnostics, and
   dangerous controls.
4. Classic remains fallback for full recovery and compatibility.
5. No setting moves until its owner, fallback, user level, and rollback path are
   explicit.
6. Profile-owned camera settings must not be flattened into global settings.
7. Source preservation settings must not be mixed with derived image/output
   settings.
8. Generated media settings are not generation actions.
9. Credential, restore, hardware, network, GPIO, log download, and raw config
   controls are never Basic.
10. Detector/meteor legacy toggles are not the future Hybrid detector product.

## Future Settings Architecture

### Basic

Basic should answer normal-user questions:

- Which camera/profile am I using?
- Is capture configured in a recognizable way?
- Are exposure, gain, and AWB policies understandable?
- Are important notifications available?
- Is storage healthy enough for normal operation?

Basic should not expose raw config names, credentials, paths, restore/download
controls, queue internals, detector toggles, filesystem details, or hardware
mutation controls.

### Advanced

Advanced should expose product-domain control for experienced users:

- profile-aware capture behavior;
- image acquisition/save format policy;
- source/FITS preservation policy;
- analytics and quality policy;
- environmental/sensor provider summaries;
- generated output settings;
- upload provider policy;
- mask/lens/image-circle geometry.

Advanced may be high risk. Advanced does not mean "safe to edit today"; many
groups remain read-only or `do_not_move_yet`.

### Developer

Developer should expose internals and fallback tools:

- raw/full settings;
- config history/restore/import/export;
- users/auth;
- logs and task queue;
- network/GPIO/system-like controls;
- OAuth credential state;
- legacy detector/meteor toggles;
- Classic fallback surfaces.

Developer exists so Advanced and Basic can stay product-readable.

## Settings Group Contract Matrix

Legend:

- Normal exposure: `Yes` means safe to expose conceptually to normal users as
  summarized product language. It does not mean safe to edit today.
- Technical/internal: `Yes` means raw fields should stay out of Basic.
- Duplicate/confusing: `Yes` means current surfaces or concepts overlap enough
  to require careful product language.
- Manual verification: `Yes` means do not migrate or redesign without runtime,
  Raspberry, or owner-specific evidence.

| Group | Product domain | Visibility | Ownership | Runtime risk | Migration risk | Normal exposure | Technical/internal | Duplicate/confusing | Manual verification | Contract decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `camera_connection` | Camera | Basic | Operations | High | High | Yes, as camera identity/connection summary | Yes | Yes | Yes | Keep read-only until camera/profile ownership is proven in UI. |
| `camera_profile_identity` | Camera Profile | Basic | Product / Operations | High | High | Yes | No | Yes | Yes | Protect profile-first ownership; never flatten to global. |
| `exposure` | Capture | Basic | Product / Operations | High | High | Yes, as exposure policy | Yes | Yes | Yes | Product-facing owner is profile, Classic/global remains fallback. |
| `gain` | Capture | Basic | Product / Operations | High | High | Yes, as gain policy | Yes | Yes | Yes | Preserve sensor/profile capability gates. |
| `auto_exposure` | Capture Automation | Basic | Product / Operations | High | High | Yes, as auto-exposure intent | Yes | Yes | Yes | Expose concepts, not raw target/metering internals. |
| `auto_gain` | Capture Automation | Basic | Product / Operations | High | High | Yes, as auto-gain intent | Yes | Yes | Yes | Preserve min/max/apply gates and profile limits. |
| `hybrid_awb` | Image Capture / Color | Basic | Product / Operations | High | High | Yes, as color policy | Yes | Yes | Yes | Camera/profile-aware; not global-only. |
| `image_acquisition` | Capture | Advanced | Operations | High | High | Partial | Yes | Yes | Yes | Split daily operator controls from legacy fallback keys. |
| `image_save_formats` | Derived Image Output | Advanced | Shared | Medium | High | Partial | Yes | Yes | Yes | Do not confuse with FITS/RAW/source preservation. |
| `fits_source_files` | Scientific Source | Advanced | Product / Operations | High | High | Partial, as source preservation policy | Yes | Yes | Yes | Keep source truth backend-owned; no filesystem exposure. |
| `metadata` | Scientific Source | Advanced | Product | High | High | Partial | Yes | Yes | Yes | Keep schema/source linkage tolerant and backend-owned. |
| `analytics` | Analytics | Advanced | Operations | Medium | Medium | Partial | Yes | Yes | Yes | Link to analytics config; do not duplicate chart logic. |
| `quality` | Scientific Quality | Advanced | Product | High | High | Partial | Yes | Yes | Yes | Explainability required; detector readiness remains separate. |
| `environmental_awareness` | Environmental Context | Advanced | Shared / Unknown | Medium | High | Partial | Yes | Yes | Yes | Provider ownership must be verified before redesign. |
| `scientific_source_layer` | Scientific Source | Advanced | Product | High | High | Partial | Yes | Yes | Yes | Preserve raw-first, non-destructive source semantics. |
| `timelapse` | Generated Output | Advanced | Operations | High | High | Partial | Yes | Yes | Yes | Settings only; generation actions need Safe Action policy. |
| `keogram` | Generated Output | Advanced | Operations | High | High | Partial | Yes | Yes | Yes | Keep separate from generation/download actions. |
| `startrail` | Generated Output | Advanced | Operations | High | High | Partial | Yes | Yes | Yes | Queue/media actions remain blocked. |
| `startrail_video` | Generated Output | Advanced | Operations / Shared | High | High | Partial | Yes | Yes | Yes | Preserve public latest/watch compatibility. |
| `mini_timelapse` | Generated Output | Advanced | Operations | Medium | High | Partial | Yes | Yes | Yes | Lower product priority but still explicitly owned. |
| `upload_providers` | Integrations | Advanced | Operations / Shared | High | High | Partial, as status/policy | Yes | Yes | Yes | Credential changes and remote tests are not safe yet. |
| `youtube_oauth` | Integrations / Credentials | Developer / Classic fallback | Developer / Classic | High | High | No | Yes | Yes | Yes | Never expose raw OAuth data outside Developer/fallback. |
| `notifications` | Notifications | Basic | Operations | High | High | Yes, as alert delivery/status | Yes | Yes | Yes | Basic status is OK; acknowledge/delete needs auth/CSRF tests. |
| `users_auth` | Users / Auth | Developer | Developer | High | High | No | Yes | No | Yes | Keep out of Basic/Advanced; self-lockout risk. |
| `logs` | Logs | Developer | Developer | High | High | No | Yes | No | Yes | Visibility is Developer; downloads need redaction/path policy. |
| `task_queue` | Task Queue | Developer | Developer | High | High | No | Yes | No | Yes | Diagnostics only; retry/cancel/delete blocked. |
| `focus` | Hardware / Focus | Advanced / Classic fallback | Classic / Operations | High | High | Partial, status only | Yes | Yes | Yes | Movement/autofocus needs hardware Safe Action policy. |
| `gpio` | Hardware / GPIO | Developer / Classic fallback | Classic / Developer | High | High | No | Yes | No | Yes | Hardware side effects; never Basic. |
| `network` | System / Network | Developer / Classic fallback | Classic / Developer | High | High | No | Yes | No | Yes | Mutations can disconnect device; keep guarded. |
| `storage_drives` | Storage | Basic | Operations | High | High | Yes, as readiness/risk summary | Yes | Yes | Yes | Basic summary is OK; avoid scans and raw paths. |
| `gps` | Location / Time | Advanced | Unknown / Operations | Medium | High | Partial | Yes | Yes | Yes | Needs provider/runtime usage evidence. |
| `sensors` | Environmental Sensors | Advanced | Shared / Unknown | Medium | High | Partial | Yes | Yes | Yes | Ownership split across hardware/providers/runtime. |
| `mask_lens_image_circle` | Camera Geometry | Advanced | Operations | High | High | Partial | Yes | Yes | Yes | Camera/profile-owned geometry; not global-only. |
| `public_latest_endpoints` | Public Compatibility | Advanced | Shared | High | High | Partial | Yes | Yes | Yes | Compatibility contract; do not treat as Classic dead code. |
| `config_history` | Config Audit | Developer | Developer | High | High | No | Yes | Yes | Yes | Metadata may be safe; raw config needs redaction. |
| `config_restore` | Config Restore | Developer / Classic fallback | Classic / Developer | High | High | No | Yes | Yes | Yes | Active restore needs preview/diff/rollback/redaction. |
| `config_import_export` | Config Import/Export | Developer / Classic fallback | Classic / Developer | High | High | No | Yes | Yes | Yes | Raw secrets risk; keep fallback-only. |
| `developer_debug` | Developer Internals | Developer | Developer | High | High | No | Yes | No | Yes | Expert-only compatibility/debug surface. |
| `legacy_detector` | Legacy Detector / Meteor | Developer / Classic fallback | Classic / Developer | High | High | No | Yes | Yes | Yes | Not the future detector product; no Basic exposure. |

## Findings

### Clearly Product UX

These can shape future Basic/Advanced product language, even if some remain
read-only or high risk:

- camera connection;
- camera profile identity;
- exposure/gain/auto-exposure/auto-gain;
- Hybrid AWB;
- source/FITS preservation;
- storage readiness summary;
- notifications summary;
- scientific metadata/source quality summaries.

### Should Stay Hidden From Normal Users

- raw/full settings;
- config import/export/restore;
- users/auth internals;
- logs/download internals;
- task queue internals;
- network/GPIO controls;
- OAuth credentials;
- legacy detector/meteor toggles;
- raw filesystem paths, URLs, tokens, secrets, provider payloads.

### Classic-Only Or Fallback-Only For Now

- `config_restore`;
- `config_import_export`;
- `youtube_oauth`;
- `gpio`;
- `network`;
- `legacy_detector`;
- hardware movement/focus actions;
- generation/delete/download actions for media products.

### Do Not Move Yet

30 groups remain `do_not_move_yet`. The common reasons are:

- filesystem/path/media risk;
- credentials or external provider risk;
- hardware/system mutation risk;
- Classic compatibility;
- unclear provider ownership;
- generated media action coupling;
- profile/camera ownership uncertainty;
- source preservation semantics.

### Duplicated Or Confusing Areas

The most confusing overlaps are:

- `image_save_formats` vs `fits_source_files` vs `scientific_source_layer`;
- generated output settings vs generation actions;
- `notifications` as Basic status vs mutative acknowledge/delete behavior;
- storage readiness vs raw storage paths/drives;
- environmental awareness vs sensors vs GPS;
- legacy detector settings vs future detector product;
- Classic `/config` vs read-only Modern settings surfaces.

## Recommended Contract

### Basic Contract

Basic may expose only summarized, user-oriented settings concepts:

- camera/profile identity;
- capture exposure/gain/AWB policy;
- capture automation intent;
- storage readiness;
- alert delivery/readiness.

Basic must not expose raw keys, restore/import/export, credentials, paths,
hardware controls, queue actions, raw detector toggles, or Classic fallback
internals.

### Advanced Contract

Advanced may expose deeper product-domain controls:

- acquisition cadence and day/night behavior;
- save format policy;
- source preservation;
- scientific metadata and quality;
- environmental/sensor/GPS policy after ownership verification;
- generated output configuration;
- upload provider policy;
- camera geometry.

Advanced settings still need safe-action separation for any mutative or heavy
operation.

### Developer Contract

Developer owns:

- raw/full config compatibility;
- logs/tasks/users/auth;
- network/GPIO/system controls;
- config restore/import/export/download;
- OAuth credentials;
- legacy detector/meteor compatibility;
- debug flags and experimental toggles.

Developer settings can be technical. They should be clearly outside the normal
Product journey.

## Required Guardrails Before Any Settings UI Change

1. Confirm owner and fallback for the group.
2. Confirm whether values are global, camera-scoped, or profile-scoped.
3. Confirm whether the setting can mutate hardware, filesystem, credentials,
   background workers, capture behavior, or generated media.
4. Confirm whether Classic remains the recovery path.
5. Confirm secrets/paths/raw values are redacted or hidden.
6. Confirm Raspberry-safe performance: no unbounded scans, no heavy queries in
   settings request path.
7. Confirm the UI language is product-domain language, not raw config keys.

## Backlog Impact

Completed:

- P0 Settings Contract Review.

Reprioritized:

- Product Spine Regression Checklist remains P0 because future consolidation
  work now has both route and settings contracts to protect against.
- Route Role Matrix follow-up in ownership metadata remains P0/P1 boundary
  work, but it should not over-classify settings or wrapper routes without
  evidence.
- Safe Action Registry Discovery becomes more important after this review,
  because generated media, restore, focus, GPIO, network, config, and
  notification actions are repeatedly blocked by action-policy gaps.

## Verification

This review is documentation-only. No settings keys, config defaults, routes,
templates, UI behavior, Classic behavior, or runtime behavior were changed.
