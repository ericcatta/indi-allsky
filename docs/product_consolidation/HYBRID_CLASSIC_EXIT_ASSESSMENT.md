# Hybrid Classic Exit Assessment

This assessment estimates what still prevents complete Classic removal.

It is not a generic audit. It measures the current state of the major product
domains and lists only real blockers observed in the repository today.

## Executive Summary

Classic is no longer the owner of the Product spine. It is still the owner or
compatibility provider for several operational, media, settings, system, and
external API behaviors.

The shortest path to making Classic removable is not to delete Classic pages
first. The shortest path is:

1. complete Hybrid-owned read services for remaining low-risk operational
   domains;
2. define a canonical action contract for mutative operations;
3. replace settings/config ownership behind a Basic / Advanced / Developer
   model;
4. isolate media browsing, preview, download, and public/latest compatibility;
5. keep Classic as fallback until each domain has a native Hybrid owner and
   regression tests.

Current estimate: Classic is removable only after **three blocker classes** are
addressed:

- settings/config mutation and restore;
- media/public/latest/file behavior;
- operational/system/hardware actions.

## Domain Ownership Estimate

| Domain | Hybrid ownership | Remaining Classic dependencies | Blockers | Difficulty | Next milestone |
| --- | ---: | --- | --- | --- | --- |
| Product UI | 95% | Product pages still coexist with Classic/public routes and some Product data uses existing DB models. | No blocker for Product spine; blocker is surrounding compatibility shell. | Low | Keep Product spine protected; do not merge it with operational pages. |
| Notifications | 90% | Legacy `/ajax/notification` and Classic notification pages still exist as compatibility surfaces. | External/Classic callers still use old endpoint semantics. | Low-medium | Decide whether legacy acknowledge endpoint remains compatibility-only or is wrapped by the Hybrid action model. |
| Task Status | 85% | Worker/task execution and mutation remain outside read-only Task Status ownership. | Queue mutation, retry, purge, execution, and worker behavior are not Hybrid-owned. | Medium | Keep read-only Task Status owned; design task action contract separately. |
| Media Metadata | 55% | Gallery, timelapse, loop, FITS, preview, download, URL helpers, public/latest routes, and filesystem/media helpers. | Media behavior mixes metadata, previews, downloads, public URLs, lightbox/client behavior, and file helpers. | High | Finish metadata-only slices only where trivial; then do a dedicated Media Contract replacement plan. |
| Camera Diagnostics | 65% | ADU History, Dark Library, Mask, calibration URLs/filesystem, camera controls, detect/start INDI. | Dark/calibration and mask touch filesystem/media; camera detection/service actions are operational. | Medium-high | Extract one more pure read-only summary only if obvious; otherwise move to Camera Operations action design. |
| Observatory | 60% | Charts, Sensor Panel, Realtime Keogram, AstroPanel live JS/AJAX, Long-term Keogram file/cache, VirtualSky live image loop. | Environmental/live data, JS polling, media URL normalization, and generated keogram file state. | Medium-high | Stop tiny extraction when only live/media behavior remains; define Observatory data/service contracts. |
| System Tools | 60% | Support script execution, log download/export, system time/timezone, network/drive/GPIO wrappers, file-space usage. | Developer actions and sensitive reads are not Hybrid-owned; support info runs external script. | High | Separate read-only diagnostics from Developer actions; design System Action contract before mutations. |
| Settings | 25% | Classic full config, config history/restore, `ConfigView`, raw settings keys, many preview pages inherited from Classic config ownership. | Settings keys, defaults, restore semantics, full config compatibility, and migration risk. | Critical | First real Classic-exit blocker: implement Basic / Advanced / Developer settings ownership without renaming keys. |

## Real Classic Removal Blockers

These are the modules or route families that actually block Classic removal
today. This list excludes theoretical references and harmless coexistence.

### 1. Settings And Config Ownership

Real blockers:

- `ConfigView` and Modern settings previews still inherit from Classic-style
  config ownership.
- `/config`, `/ajax/config`, `/config/restore`, `/modern-admin/system/config`,
  `/modern-admin/settings/full`, config history, and config restore remain
  compatibility and mutation surfaces.
- `tools/hybrid_settings_ownership_map.json` marks most groups as high-risk or
  do-not-move-yet.

Why this blocks removal:

Classic owns the complete fallback for editing, restoring, and understanding
raw config. Hybrid has a contract review, but not native settings execution.

Milestone:

- Create Hybrid Settings read/write contract without renaming settings keys.
- Keep Classic as fallback until save/restore/diff/rollback are tested.

### 2. Media/Public/Filesystem Behavior

Real blockers:

- `ModernAdminMediaListView`, gallery/images/timelapses/loop/FITS detail, and
  public/latest routes still rely on existing media URL/file behavior.
- `/images/<path>`, `/latest*`, FITS viewers, video viewers, thumbnail/public
  routes, preview/lightbox/download helpers, and generated media viewers remain
  compatibility-critical.
- Sync API media routes remain external contracts.

Why this blocks removal:

Classic-era media behavior is not just UI. It defines external URLs, media
serving, previews, downloads, and public integrations.

Milestone:

- Define a Hybrid Media Contract that separates metadata, preview, download,
  public/latest, and filesystem helpers.
- Replace metadata first; replace preview/download only with runtime evidence.

### 3. Operational And Developer Actions

Real blockers:

- Safe Action exists, but most real mutations still live in Classic AJAX,
  action APIs, system wrappers, and direct operational routes.
- Capture service, INDI detect/start, network, drives, GPIO, focus, generate,
  config restore, log download, and external Action/Sync APIs remain outside a
  complete Hybrid execution model.

Why this blocks removal:

Classic is still the compatibility owner for many things that affect hardware,
system state, generated media, credentials, or external automation.

Milestone:

- Define canonical Action Contract schema.
- Move actions family-by-family into Hybrid-owned safe actions while preserving
  legacy endpoints as wrappers.

### 4. System/Auth/User/Support Surfaces

Real blockers:

- User/auth Modern pages are sensitive and still not extracted.
- Support info runs a script via JSON endpoint.
- Log download/export is a sensitive read/export action.
- System time/timezone and service controls remain Developer actions.

Why this blocks removal:

These are security-sensitive and cannot be replaced by simple wrapper moves.

Milestone:

- Keep auth/users Classic-owned until a dedicated security review.
- Treat support/log/system actions as Developer domain, not Product UI.

### 5. External Compatibility APIs

Real blockers:

- `/action/*`
- `/sync/v1/*`
- OAuth/YouTube routes
- public/latest media routes

Why this blocks removal:

They may have external consumers not visible through static analysis.

Milestone:

- Freeze external API compatibility separately from Classic UI removal.
- Replace implementation behind stable contracts only after endpoint tests.

## What No Longer Blocks Classic Removal

These areas are not complete applications by themselves, but they no longer
represent the main Classic-exit blocker:

- Product UI spine: owned by Product view models and `ModernAdminProductView`.
- Notifications read + acknowledge: effectively Hybrid-owned.
- Task Status read-only status: effectively Hybrid-owned.
- Several media metadata slices: Hybrid-owned metadata services exist.
- Camera Info and Image Lag: read-only logic moved into diagnostics service.
- SQM, Long-term Keogram age formatting, VirtualSky form defaults: small
  Observatory ownership slices moved into services.
- System Info overview and Log Detail display policy: moved into System Tools.

## Shortest Path To "Classic Becomes Removable"

### Phase 1: Complete Non-Mutating Domain Ownership

Goal: no Product/Advanced read-only page should depend on Classic for simple
query/formatting/display policy.

Recommended next work:

- finish clearly metadata-only media slices if still safe;
- avoid preview/download/URL/file helpers until the Media Contract exists;
- stop extracting tiny slices when only live JS, filesystem, or action behavior
  remains.

Exit criterion:

- read-only Modern wrappers are orchestration shells around Hybrid-owned
  services.

### Phase 2: Settings Contract Implementation

Goal: Hybrid owns settings organization and safe edit flow while preserving
existing keys.

Recommended next work:

- implement Basic / Advanced / Developer settings ownership behind existing
  keys;
- add diff/preview/rollback semantics before any restore or raw config save;
- keep Classic full config as fallback until coverage is strong.

Exit criterion:

- Classic `ConfigView` is no longer required for normal settings work.

### Phase 3: Action Contract Implementation

Goal: Classic no longer owns mutative semantics.

Recommended next work:

- define action schema;
- migrate one action family at a time behind existing endpoints;
- keep external/public routes stable as wrappers.

Exit criterion:

- capture, generation, config, network/drive/GPIO, notification, log download,
  and task mutations have Hybrid-owned action services or explicit external API
  owners.

### Phase 4: Media Contract Implementation

Goal: media browsing and public/latest behavior become Hybrid-owned without
breaking external consumers.

Recommended next work:

- separate metadata from URL generation;
- separate preview from download;
- separate internal file paths from web URLs;
- add endpoint tests for public/latest compatibility.

Exit criterion:

- Classic media viewers/routes are compatibility wrappers, not implementation
  owners.

### Phase 5: Classic UI Retirement

Goal: Classic can be disabled or removed without losing Product, Operations,
Developer, media, settings, or external API behavior.

Exit criterion:

- route inventory classifies all remaining Classic routes as either removed,
  external compatibility, or wrapper-only.
- no primary workflow requires a Classic template.

## Recommended Next Milestone

The highest-value next milestone is **Settings Contract Implementation Plan
for one safe read-only/edit-preview group**, not another generic extraction.

Why:

- Settings is the lowest Hybrid ownership domain and the biggest real blocker.
- It is central to Classic removal.
- It can start without renaming keys or changing defaults.
- A small group can prove the model before touching critical settings.

Recommended first slice:

- read-only/edit-preview ownership for a low-risk settings group, preserving
  keys and current fallback.

Stop conditions:

- any settings key rename;
- config default changes;
- restore/save behavior changes without rollback;
- Classic fallback removal.
