# HYBRID ARCHITECTURE V2

## 1. Executive Summary

Hybrid AllSky started this chapter as a Classic UI to Modern UI migration. The
current repository shows that the project has moved beyond a page-by-page UI
port.

The architecture is now moving from:

```text
Classic UI -> Modern UI
```

to:

```text
Core -> Modern UI -> Safe Actions -> Audit -> future UI/API independence
```

Classic-only feature coverage is effectively zero, and many operational areas
now have Modern read-only, status, metadata, usability, or detail surfaces.
However, Classic removability is still zero because important mutations,
downloads, restores, media generation, OAuth, hardware, queue, and user/admin
actions do not yet have safe Modern contracts.

The important architectural shift is that Modern Admin is no longer just a new
Jinja surface. It is becoming the visible client of a safer operational model:
read-only observability first, explicit Safe Action contracts before mutation,
structured audit records, and preserved Classic fallback until parity is proven.

## 2. Current Architecture

### Core/runtime

The core runtime remains responsible for acquisition, processing, capture
control, media generation, uploads, metadata production, scientific source
persistence, event foundations, detector result foundations, and meteor
intelligence foundations. This layer is not owned by the UI migration and must
remain acquisition-first, profile-first, multicamera-first, and scientific-first.

### Database models

Database models remain shared infrastructure for Classic views, Modern views,
AJAX endpoints, and runtime workers. Modern read-only pages increasingly query
these models directly through Flask views. Mutation semantics are still often
embedded in legacy views or AJAX handlers rather than extracted into stable
service contracts.

### Config

Configuration is currently split between legacy/global config surfaces and newer
profile-first/multicamera-aware concepts. Camera Profiles, profile-first
configuration, Auto Exposure, Auto Gain, Hybrid AWB, metadata, analytics,
quality, environmental awareness, Event Foundation, and the Scientific Source
Layer are protected Modern/shared work and must not be flattened back into
single-camera or global-only behavior.

### Flask views

`indi_allsky/flask/views.py` is still the central route registration point. It
contains Classic routes, Modern Admin routes, shared AJAX endpoints, public
media routes, OAuth routes, system actions, and the first Modern Safe Action
dry-run endpoint:

```text
POST /modern-admin/safe-action/dry-run
```

This is functional but still tightly coupled. V2 architecture should gradually
move behavior out of view classes and into service/API/action boundaries.

### Classic UI

Classic UI remains an active fallback and compatibility surface. It is no longer
the only place for operational visibility, but it still owns or exposes many
actions such as config restore, log downloads, media mutations, queue/generation
operations, user/auth mutations, OAuth flows, and legacy AJAX behavior.

Classic must not be removed merely because Modern pages exist. Removal requires
parity, deprecation, compatibility handling, and rollback.

### Modern UI

Modern Admin is now the operational center. It includes broad read-only/status
coverage across task queue, users, notifications, config history/restore
inspection, FITS metadata, logs, media metadata/detail pages, uploads, YouTube
status audit, observatory pages, storage pages, settings pages, and safe-control
wrappers.

Modern UI is not yet a full action parity layer. Its strongest maturity today is
read-only observability, metadata/status inspection, and protected Hybrid
concepts.

### Shared AJAX/API

Shared AJAX endpoints, Sync API, Action API, public/latest endpoints, bookmark
routes, and public media routes are compatibility surfaces. They must not be
treated as dead Classic code just because a static inventory cannot find a
Modern consumer.

### Safe Actions layer

The Safe Actions layer now exists as a real technical foundation:

- `ModernAdminSafeAction`
- `ModernAdminSafeActionResult`
- `ModernAdminSafeActionRegistry`
- `ModernAdminSafeActionRunner`
- `ModernAdminSafeActionAuditRecord`
- `NotificationAcknowledgeSafeAction`
- placeholder registry entries for future actions
- dry-run-only Modern endpoint at `/modern-admin/safe-action/dry-run`

This layer is deliberately conservative. It does not make actions safe by
itself; it defines the shape that future safe actions must follow.

### Audit layer

The audit layer currently exists as structured, in-memory audit records. It can
redact payload and result summaries and can represent actor, action, status,
risk, allow/deny state, dry-run state, and reason.

There is no persistent audit log yet. Persistent audit storage remains a
required boundary before real execute endpoints are exposed.

## 3. Architecture Before vs After

### Before

The old shape was mostly:

```text
Flask view -> DB/query -> Jinja template
```

For many operations, especially Classic AJAX actions, the shape was:

```text
Browser action -> Flask/AJAX endpoint -> DB/filesystem/hardware/external side effect
```

This made UI migration risky because visual parity could accidentally become
mutation parity without a clear permission, validation, audit, or rollback
contract.

### Now

The emerging V2 shape is:

```text
Core / DB / runtime services
  -> Modern read-only views
  -> Safe Action contract
  -> Registry
  -> Runner
  -> Audit record
  -> future endpoint/UI
```

Read-only Modern pages are allowed to progress quickly. Mutating Modern actions
must pass through explicit safe-action boundaries before being exposed.

## 4. What Is Already Decoupled

The following areas are already relatively decoupled from Classic UI semantics:

- Protected Modern work:
  - Multi-camera
  - Camera Profiles
  - Profile-first configuration
  - Auto Exposure
  - Auto Gain
  - Hybrid AWB
  - Metadata
  - Analytics
  - Quality
  - Environmental Awareness
  - Event Foundation
  - Scientific Source Layer
  - Detector / Meteor foundations
  - Modern Admin shell
  - Modern safe controls
- Read-only Modern surfaces for many operational features.
- Metadata/status/detail pages that do not mutate DB, filesystem, hardware, or
  external services.
- The Safe Action contract, result, registry, runner, and audit record.
- The `notification.acknowledge` wrapper as a pilot contract, not a UI action.
- The dry-run-only Safe Action endpoint, which validates plumbing without
  executing a real mutation.

This decoupling is partial. It improves future flexibility, but it is not a
complete service extraction.

## 5. What Is Still Coupled

The following areas remain coupled to Flask, Jinja, Classic behavior, or legacy
AJAX:

- Legacy AJAX mutation endpoints.
- Config restore, config download, and raw config handling.
- Log downloads and log file exposure.
- FITS preview/conversion/download paths.
- Image/gallery/video delete, exclude, share, download, upload, and processing
  actions.
- Timelapse, mini timelapse, keogram, startrail, panorama, and video generation
  actions.
- Task queue retry/cancel/requeue/delete semantics.
- User management mutations, password changes, roles, active state, API keys,
  and auth state.
- YouTube/OAuth authorize, callback, refresh, revoke, upload test, and upload
  task creation flows.
- Hardware actions such as focus movement and GPIO control.
- Config forms and settings layout, which still need a Basic / Advanced /
  Developer redesign.
- The monolithic `indi_allsky/flask/views.py` route/view layer.
- Template coupling between route registration and Jinja pages.
- Public/latest/media routes that are compatibility APIs and cannot be treated
  as removable Classic surfaces.

## 6. Safe Actions Layer

### Implemented foundation

`ModernAdminSafeAction` defines the base contract for future Modern actions. By
default it does not execute meaningful work. Permission checks are injected, and
the default execution path returns `not_implemented`.

`ModernAdminSafeActionResult` returns structured action status, message,
feature, risk level, dry-run state, allow/deny state, audit message, details,
and timestamp.

`ModernAdminSafeActionRegistry` catalogs actions by `action_id`, rejects
duplicate IDs, supports lookup, lists actions, and filters by feature or risk.

`ModernAdminSafeActionRunner` resolves an action from a registry, enforces
missing/unknown action handling, invokes permission and validation through the
action contract, supports dry-run, and can return an audit record with the
result.

`ModernAdminSafeActionAuditRecord` captures a structured, redacted audit event
for a result. It is serializable and independent of Flask request context.

`NotificationAcknowledgeSafeAction` is the first pilot wrapper. It validates a
notification ID, supports injected lookup and execute callbacks, handles
already-acknowledged notifications idempotently, and remains non-mutating unless
a future caller injects a real callback.

The dry-run endpoint at `/modern-admin/safe-action/dry-run` exists to validate
the web plumbing. It forces `dry_run=True`, does not inject a mutating callback,
and is not called by any Modern UI button.

### Still forbidden

The following remain forbidden until specific prerequisites are met:

- real execute endpoint;
- UI button or AJAX call that mutates state;
- direct calls to legacy POST endpoints from Modern UI;
- `notification.setAck()` from the dry-run endpoint;
- config restore execution;
- delete/download/upload/processing actions;
- filesystem writes;
- hardware movement;
- OAuth refresh/revoke/authorize/upload-test actions;
- queue retry/cancel/requeue/delete.

### Missing before real execute

Real execute endpoints require:

- canonical Modern permission policy;
- Flask-level auth and CSRF tests;
- persistent audit log backed by structured audit records;
- DB-backed lookup and execution callbacks;
- integration tests for success, failure, unauthorized, missing target, stale
  target, repeated action, and backend failure;
- confirmation UX for destructive, external, credential, hardware, and
  filesystem actions;
- rollback or explicitly documented no-rollback semantics.

## 7. Why This Matters For Future UI Redesign

If Hybrid AllSky eventually gets a completely redesigned UI, V2 architecture
makes some things easier and exposes what remains hard.

### Relatively easy

- Redesign the Modern Jinja shell.
- Reorganize read-only dashboard layouts.
- Build alternative metadata/status pages.
- Improve Modern Admin navigation.
- Create new read-only reports from existing domain/status data.
- Build UI around already-safe status and metadata endpoints.

### Medium difficulty

- Build a separate frontend that consumes read-only APIs.
- Add a UI for Safe Action dry-run results.
- Create richer media viewer components without mutating or processing files.
- Reorganize settings into Basic / Advanced / Developer.
- Split some shared AJAX reads into explicit read-only API contracts.

### Hard / requires service extraction

- Build a full React, Vue, Svelte, or other standalone app with complete parity.
- Provide a complete REST API for all operational workflows.
- Safely expose media downloads, FITS conversion, raw/source file inspection, and
  log downloads.
- Execute config restore, queue generation, media processing, and upload actions.
- Replace user/auth management flows.
- Replace OAuth/upload flows.
- Remove Classic fallback.

The main lesson is that a future frontend rewrite is a client problem only after
the service/action/API boundaries exist. Without those boundaries, a rewrite
would mostly duplicate the current coupling in a different frontend.

## 8. Target Architecture

The target architecture should be:

```text
Core Services
  -> Service/API Layer
  -> Safe Actions
  -> Audit
  -> UI Clients
```

Possible UI clients:

- Flask Modern UI;
- future React/Vue/Svelte UI;
- CLI;
- local/mobile dashboard;
- external API clients.

In this target architecture, UI clients do not call legacy mutation endpoints
directly. They call explicit read-only APIs or Safe Action endpoints. Safe
Actions validate permissions, inputs, state, risk, dry-run behavior, audit, and
rollback/no-rollback semantics before any real mutation is allowed.

## 9. Raspberry Pi 5 First Constraint

Raspberry Pi 5 remains the primary target hardware for Hybrid AllSky. The V2
architecture must not drift into a heavyweight enterprise platform that competes
with capture, acquisition, or processing.

Every new layer must be:

- lazy;
- optional where possible;
- testable without a full runtime stack;
- disableable when practical;
- light in RAM and CPU;
- free of aggressive polling;
- free of heavy processing inside UI request paths.

The UI must not compete with capture or processing. Modern Admin pages should
prefer bounded metadata/status reads, pagination, cached summaries, and explicit
operator-triggered actions.

Raspberry Pi 5-first rules:

- No live dashboard polling without rate limits.
- No unpaginated queries over large tables.
- No frequent filesystem scans.
- No FITS, raw, video, or panorama conversion on demand without queueing,
  limits, and timeouts.
- No heavy media preview generation inside normal page rendering.
- Safe Actions must stay lightweight and run only on explicit request.
- Persistent audit storage must include retention, pruning, or bounded storage
  behavior.
- Background processing must remain subordinate to acquisition-first operation.

A future React, Vue, Svelte, or other separate frontend is optional, not a
destination by default. If considered, it must be evaluated for:

- build size;
- browser and server RAM;
- CPU use on Raspberry Pi 5;
- static asset size;
- caching behavior;
- startup cost;
- whether a large bundle is actually justified.

The target design may support external clients, but the Pi should not become a
heavy general-purpose application server. UI independence can mean a cleaner
Flask Modern UI, lightweight read-only APIs, optional external clients, or a
minimal local dashboard. It does not mean a heavyweight frontend is mandatory.

## 10. Migration Roadmap From Here

### Phase 1 - Modern read-only surfaces

Mostly broad coverage exists. Continue filling small gaps and improving
metadata/status/detail pages, but avoid mistaking read-only coverage for full
parity.

### Phase 2 - Safe Actions Infrastructure

In progress. Contract, registry, runner, pilot wrapper, dry-run endpoint, tests,
and structured audit records exist. Persistent audit and full Flask integration
tests remain important next steps.

### Phase 3 - Service extraction / API contracts

Define service boundaries for read-only data and for one low-risk action at a
time. Start with notification acknowledge or another bounded action only after
permission, audit, and tests are ready.

### Phase 4 - Safe UI actions

Expose UI controls only after the action has a backend contract, dry-run path,
permission policy, audit persistence, confirmation behavior where needed, and
integration tests.

### Phase 5 - Settings redesign

Reorganize configuration around Basic / Advanced / Developer concepts while
preserving profile-first and multicamera ownership.

### Phase 6 - Classic deprecation

Add user-facing deprecation paths only after Modern parity exists for the target
feature and compatibility surfaces have been audited.

### Phase 7 - Classic removal

Remove Classic only by micro-step after Phase F/G criteria are met, fallbacks are
known, public/external routes are excluded, and rollback is possible.

### Phase 8 - Optional UI rewrite

Consider a separate frontend only after enough read-only APIs, service
boundaries, Safe Actions, and audit semantics exist to prevent duplicating the
current Flask/Jinja coupling. UI independence does not require a heavyweight
frontend; a cleaner Flask Modern UI, lightweight API contracts, optional external
clients, or a minimal local dashboard may be the better Raspberry Pi 5-first
outcome.

## 11. Design Principles

- Profile-first.
- Multicamera-first.
- Modern-first.
- Scientific-first.
- Explainability-first.
- Safe-actions-first.
- No mutation without contract.
- No UI action without audit.
- No Classic removal without parity.
- No frontend rewrite until service boundaries exist.
- No heavyweight frontend or polling loop that competes with Raspberry Pi 5
  acquisition and processing.
- Preserve public/latest, Sync API, Action API, shared AJAX, and bookmarked
  routes as compatibility surfaces.
- Keep Classic fallback until the feature has proven Modern parity and a
  deprecation path.

## 12. Current Maturity Estimate

These are qualitative estimates, not precision metrics.

| Area | Maturity | Notes |
| --- | --- | --- |
| Governance | High | Protocol, guardrails, backlog, ownership map, inventory, Safe Actions policy, and readiness review exist. |
| Read-only Modern migration | Medium-high | Classic-only coverage is effectively zero, and many pages have Modern status/metadata/detail surfaces. Parity is still incomplete. |
| Safe Actions infrastructure | Medium | Contract, registry, runner, dry-run endpoint, pilot wrapper, tests, and in-memory audit record exist. Execute is still blocked. |
| Service separation | Low-medium | Some domain modules exist, but many workflows remain in Flask views, legacy AJAX, and model/view coupling. |
| API readiness | Low-medium | Public/shared endpoints exist, but a clean service/API layer for Modern or external clients is not complete. |
| UI independence | Low-medium | Modern UI is broad, but independence should remain Raspberry Pi 5-first. It may mean cleaner Flask Modern pages, lightweight APIs, optional clients, or a minimal dashboard rather than a large frontend. |
| Classic removal readiness | Low | Classic removability remains effectively 0% because mutations, downloads, restore, media generation, OAuth, auth, and hardware actions are not safely ported. |
| Raspberry Pi 5 fit | Medium | The current approach is mostly lightweight/read-only, but future APIs, dashboards, audit persistence, and UI rewrites must be explicitly bounded. |

## 13. Recommended Next Steps

Recommended next work should stay small and contract-driven:

1. Consolidate Safe Action dry-run endpoint testing when a real Flask test
   client environment is available.
2. Design persistent audit log storage for Modern Safe Actions.
3. Define the service boundary for `notification.acknowledge`, including
   DB-backed lookup, DB-backed execute callback, permission policy, and
   integration tests.
4. Define read-only API contracts for Modern metadata/status pages before
   considering a separate frontend.
5. Continue unblocking safe actions one action family at a time, starting with
   the lowest-risk wrappers from `HYBRID_SAFE_ACTIONS_POLICY.md`.
6. Prepare settings redesign only after a dedicated review of profile-first,
   camera-profile-first, global, and developer-only ownership.
7. Keep Classic fallback and compatibility routes unchanged until parity and
   deprecation criteria are met.
8. Review future dashboard/API/frontend ideas against the Raspberry Pi 5-first
   constraint before implementation.

## 14. Risks

- Over-engineering before the next safe action proves the pattern end to end.
- Treating Classic-only count of zero as Classic removal readiness.
- Duplicating UI/API surfaces instead of extracting service boundaries.
- Exposing Safe Actions too early, before persistent audit and integration tests.
- Losing Classic fallback while mutations still depend on legacy behavior.
- Regressing Multi-camera, Camera Profiles, profile-first config, metadata,
  quality, Event Foundation, or Scientific Source behavior during UI work.
- Leaking tokens, secrets, credential payloads, password hashes, API keys, or
  absolute sensitive paths through status pages, audit records, logs, or JSON
  responses.
- Keeping too much behavior in `indi_allsky/flask/views.py` and making future UI
  independence harder.
- Assuming static inventory proves external compatibility safety. Public,
  bookmarked, Sync, Action, shared AJAX, and latest/media endpoints may have
  external consumers.
- Designing a future dashboard, API layer, audit log, or frontend that is too
  heavy for Raspberry Pi 5 and competes with acquisition, capture, or processing.
