# Hybrid Classic Exit Assessment

This assessment estimates what still prevents complete Classic removal after
the latest Product Consolidation work.

It is not a generic audit. It measures the current state of the major product
domains and lists only real blockers observed in the repository today.

## Executive Summary

Classic is no longer the owner of the Product spine, and it is no longer the
only owner of several operational read-only domains. Since the previous
assessment, Hybrid gained:

- domain-owned read services for Notifications and Task Status;
- ownership boundaries for Product, Observatory tools, Camera diagnostics,
  System tools, Task status, Notifications, Media metadata, and Media browse;
- several media metadata services;
- Camera diagnostics, Observatory, and System read-only helper ownership;
- many read-only Settings contracts;
- consolidated Settings contract helpers and guardrail tests;
- a minimal `ModernAdminSafeActionContract` foundation.

The center of gravity has moved. The main problem is no longer "too many
Modern pages inherit Classic wrappers." The main problem is now deeper:
Classic still owns or defines sensitive behavior for configuration writes,
media/file/public URL semantics, mutative operations, external compatibility
APIs, and several hardware/provider-backed operational surfaces.

Current estimate: Classic is removable only after **five blocker classes** are
addressed:

1. settings write/restore/config execution;
2. media/public/latest/filesystem behavior;
3. action execution ownership for mutating operations;
4. external compatibility APIs and public contracts;
5. hardware/provider/system/auth surfaces that need dedicated security or
   runtime reviews.

## Domain Ownership Estimate

| Domain | Hybrid ownership | Remaining Classic ownership | Remaining blockers | Technical risk | Architectural maturity |
| --- | ---: | --- | --- | --- | --- |
| Product UI | 96% | Classic/public compatibility routes coexist around the Product spine; some data still comes from existing DB models. | No Product spine blocker. Remaining risk is compatibility shell and surrounding operational routes. | Low | High. Product view models, Product routes, visual system, and DATA001-DATA006 are stable. |
| Notifications | 95% | Legacy AJAX/Classic notification compatibility endpoints still exist. | Compatibility endpoint semantics and future notification write/action ownership beyond acknowledge. | Low | High. Read, acknowledge, result/audit policy, and settings contract are Hybrid-owned. |
| Task Status | 90% | Worker execution, retry, purge, clear, and queue mutation remain outside read-only Task Status ownership. | Mutating queue/workflow actions require Action Contract ownership. | Medium | High for read-only status; medium for full task domain. |
| Media Metadata | 68% | Gallery, timelapse, loop, FITS, preview/download/lightbox, URL helpers, public/latest routes, and filesystem helpers. | Metadata services exist for several slices, but media product behavior still mixes DB metadata, media serving, previews, downloads, client behavior, and file helpers. | High | Medium. Metadata-only ownership is maturing; media behavior ownership is not. |
| Camera Diagnostics | 74% | ADU History, Dark Library, Mask, calibration/file behavior, camera controls, camera detection/start flows. | Remaining safe read-only slices are limited; camera control/action behavior is separate and risky. | Medium-high | Medium-high for read-only diagnostics; low for camera operations. |
| Observatory Tools | 70% | Charts, Sensor Panel, Realtime Keogram, AstroPanel live behavior, Long-term Keogram file/cache/generation boundaries, sensor/provider data. | Live/provider/environmental behavior and generated/media-backed observatory surfaces need explicit service contracts. | Medium-high | Medium. Several display policies are owned, but live data ownership is still unclear. |
| System Tools | 70% | Support script execution, log download/export, time/timezone, network/drive/GPIO, service controls, users/auth. | Developer/system actions and security-sensitive auth/support behavior remain Classic-owned or compatibility-owned. | High | Medium. Safe read-only summaries are owned; sensitive actions are not. |
| Settings | 48% | Full config edit/save/restore/history, raw config compatibility, many high-risk groups, Classic fallback, config mutation semantics. | Read-only contracts cover many important groups, but no Hybrid write/save/restore contract exists. | Critical | Medium for read-only contract layer; low for write ownership. |
| Safe Actions | 35% | Most live mutative operations still live in Classic AJAX, action APIs, system wrappers, external APIs, and domain-specific handlers. | Action metadata foundation exists, but action registry validation, domain action ownership, compatibility wrappers, and permission/audit semantics are incomplete. | Critical | Early. Useful foundation, not yet an execution ownership model. |

## Updated Top 5 Classic Removal Blockers

### 1. Settings Write / Restore / Config Execution

Current status:

- Many read-only Settings contracts are Hybrid-owned.
- Shared contract helpers and guardrail tests exist.
- Opportunistic contract-only slices have intentionally paused.

Real blockers:

- full config editing and save behavior;
- config history and restore;
- raw config compatibility;
- default/key compatibility;
- rollback/diff semantics;
- remaining provider/hardware-backed groups such as sensors/GPS.

Why this is now blocker #1:

Settings is no longer undocumented, but Classic still owns the dangerous part:
changing configuration. Classic cannot be removed while config write/restore is
the only complete path.

Next milestone:

- Build a Hybrid Settings write contract for one already-owned low-risk group.
- Preserve existing keys/defaults and Classic fallback.
- Add preview/diff/rollback semantics before any real write expansion.

### 2. Media / Public / Latest / Filesystem Contract

Current status:

- Media metadata boundaries and services exist.
- Some multi-camera UX and Loop layout issues were fixed.
- Metadata-only slices are safer than before.

Real blockers:

- preview/lightbox/download behavior;
- public/latest routes;
- media URL generation;
- FITS/raw/source viewer behavior;
- filesystem paths and helper semantics;
- external consumers of media URLs.

Why this is now blocker #2:

Media is not just a page family. It is an external contract and a filesystem
contract. Classic removal requires stable Hybrid ownership of metadata, URL,
preview, download, and public/latest semantics.

Next milestone:

- Define and implement a narrow Hybrid Media Contract starting with URL/preview
  classification, not behavior change.
- Keep filesystem/media helpers unchanged until tests prove compatibility.

### 3. Safe Actions / Mutating Operation Ownership

Current status:

- Safe actions are discovered.
- Notifications acknowledge is domain-owned.
- `ModernAdminSafeActionContract` now gives a minimal metadata foundation.
- `modern_safe_action.py` remains an orchestrator.

Real blockers:

- capture controls;
- task retry/cancel/clear/purge;
- config restore/save;
- log download/export;
- media delete/generation/regeneration/upload;
- network/drive/GPIO/system controls;
- external `/action/*` and `/sync/v1/*` mutations.

Why this is now blocker #3:

Read-only ownership is mostly no longer the hard part. Classic remains
essential because it owns many operations that change system, camera, media, or
config state.

Next milestone:

- Add registry-level guardrails for `ModernAdminSafeActionContract`.
- Then migrate one low-risk existing action family behind a domain-owned action
  service while preserving current endpoint/response behavior.

### 4. External Compatibility APIs

Current status:

- Route roles and safe action discovery identify the danger.
- No full replacement contract exists yet.

Real blockers:

- `/action/*`;
- `/sync/v1/*`;
- public/latest media endpoints;
- OAuth/YouTube integrations;
- legacy AJAX endpoints that external scripts may call.

Why this is now blocker #4:

These APIs may have consumers outside the UI. Static analysis cannot prove they
are unused, so Classic cannot be removed until their compatibility ownership is
explicit.

Next milestone:

- Create endpoint-level compatibility tests for the highest-risk public/action
  routes before changing implementation ownership.

### 5. Hardware / Provider / System / Auth Surfaces

Current status:

- Camera diagnostics, Observatory tools, and System tools have better
  read-only boundaries.
- Sensitive behavior remains intentionally untouched.

Real blockers:

- users/auth;
- support script execution;
- log export/download;
- network/drive/GPIO controls;
- service start/stop/restart;
- sensors/GPS/provider polling;
- camera detect/start/control.

Why this is now blocker #5:

These are not cleanup tasks. They are security/runtime ownership milestones.
Treating them as ordinary wrapper extraction would be unsafe.

Next milestone:

- Separate read-only diagnostics from Developer actions.
- Review one hardware/provider family at a time before implementation.

## Blockers That Disappeared Since The Previous Assessment

These no longer deserve blocker status:

- Product spine ownership: Product routes and payloads are protected by
  `ModernAdminProductView` and regression tests.
- Easy read-only wrapper extraction: completed for the obvious families.
- Notifications read/acknowledge ownership: effectively Hybrid-owned, with
  Classic endpoints remaining as compatibility surfaces.
- Task Status read-only ownership: effectively Hybrid-owned for list/detail
  status.
- "No settings product contract": no longer true. Many read-only contracts
  exist, and helper duplication has been reduced.
- "No action schema at all": no longer true. A minimal safe-action metadata
  contract exists.
- Several small operational display policies: Camera Info, Image Lag, System
  Info, Log Detail, SQM, Long-term Keogram age display, and VirtualSky context
  defaults now have Hybrid-owned service/helper ownership.

## Remaining Blockers That Are Architectural Milestones

These should not be treated as incremental cleanup:

1. Settings write/save/restore ownership.
   This needs contracts, diff/preview, rollback, compatibility, and tests.

2. Media/public/latest/filesystem ownership.
   This needs a media contract that separates metadata, URL generation,
   preview, download, public routes, and filesystem helpers.

3. Action execution ownership.
   This needs action contracts, permissions, audit, dry-run semantics,
   compatibility wrappers, and domain services.

4. External API compatibility.
   This needs endpoint-level compatibility tests before implementation moves.

5. Auth/users/system operations.
   This needs security review, not simple view extraction.

## Future Work That Should Stop Or Pause

Low-value work to stop for now:

- Adding more opportunistic Settings contract-only slices for groups marked
  `do_not_move_yet`.
- Extracting more tiny read-only wrapper classes just to reduce inheritance
  counts.
- Continuing media metadata slice extraction mechanically when the remaining
  value is in preview/URL/filesystem contracts.
- Polishing settings formatter internals beyond meaningful duplication removal.
- Redesigning Product UI or shell. The visual system is frozen except for bugs,
  accessibility, responsive fixes, and consistency.
- Broad documentation audits that restate existing inventories without changing
  ownership or decisions.

Work that may continue only with evidence:

- route ownership-map corrections backed by current route matrix evidence;
- safe-action guardrail tests;
- endpoint compatibility tests;
- one-domain service extraction where behavior and context shape are proven
  unchanged.

## Shortest Realistic Path To "Classic Removable"

### Phase 1: Freeze Compatibility Baselines

Goal: know which behaviors must remain stable before replacing implementations.

Recommended work:

- add Safe Action Contract adoption guardrails;
- add endpoint compatibility tests for public/latest and external action APIs;
- update ownership metadata only where evidence is strong.

Exit criterion:

- every sensitive route family has a stable contract or an explicit
  compatibility owner.

### Phase 2: Settings Write Contract Pilot

Goal: prove Hybrid can own configuration changes without renaming keys or
removing Classic fallback.

Recommended work:

- choose one already-owned, low-risk settings group;
- implement preview/diff semantics first;
- then implement save through existing keys only if rollback/fallback is clear.

Exit criterion:

- one settings group can be read, previewed, changed, and rolled back through a
  Hybrid-owned contract while Classic remains compatible.

### Phase 3: Action Contract Pilot

Goal: move one mutating operation family into a domain-owned Hybrid service.

Recommended work:

- validate all registered safe actions expose `ModernAdminSafeActionContract`;
- preserve registry output shape;
- choose one low-risk existing action family;
- keep legacy route/API as wrapper.

Exit criterion:

- one non-trivial mutation is Hybrid-owned end-to-end with permission, audit,
  dry-run/execute semantics, tests, and unchanged external response shape.

### Phase 4: Media Contract Pilot

Goal: separate media metadata from URL/preview/download/filesystem behavior.

Recommended work:

- classify media endpoints by metadata, preview, download, public/latest, or
  filesystem behavior;
- add compatibility tests;
- replace one tiny URL/preview helper behind an unchanged route only after
  tests exist.

Exit criterion:

- one media product path is Hybrid-owned without changing URLs, previews,
  downloads, cache, or filesystem behavior.

### Phase 5: Developer/System/Auth Separation

Goal: keep Product/Operations independent from Developer/security-sensitive
actions.

Recommended work:

- keep users/auth Classic-owned until security review;
- move only read-only diagnostics with no filesystem mutation or process
  control;
- treat support/log/system controls as Developer actions.

Exit criterion:

- Classic no longer owns normal Product/Operations flows; remaining Classic
  routes are either external compatibility wrappers or deliberately retained
  Developer/security surfaces.

## Updated Recommendation For The Next Project Phase

The next phase should be **Action Contract hardening**, not more Settings
slices and not more visual/Product UI work.

Why:

- Settings contract-only work has reached diminishing returns.
- The largest remaining blockers involve mutation, compatibility, and runtime
  safety.
- `ModernAdminSafeActionContract` is intentionally small and needs adoption
  guardrails before action migration starts.
- A stronger action foundation will also help future Settings write, Task
  mutation, media generation, system controls, and hardware/provider work.

Recommended next mission:

- Add registry-level Safe Action Contract guardrails:
  - every registered safe action exposes contract metadata;
  - required fields are non-empty;
  - risk levels are allowlisted;
  - registry public output remains backward-compatible;
  - no route/API/permission/response behavior changes.

This is the shortest safe step toward Classic removable because it prepares
the mutation model without touching dangerous mutations yet.
