# Hybrid Safe Action Registry Discovery

## Executive Summary

Hybrid has a strong read-only Product spine, but its mutative operations still
come from several historical layers:

- Classic AJAX endpoints;
- external Action and Sync APIs;
- Modern safe-control wrappers;
- service/system helper routes;
- service-only Safe Action pilots.

This document is a discovery registry, not an implementation plan. It does not
change endpoints, permissions, UI, runtime behavior, Classic, settings keys, or
API contracts.

The main finding is that Hybrid does not yet have a single product-level action
model. It has a good Safe Action foundation, but most real mutations still live
outside that model. Future work should introduce a canonical action contract
before exposing any new Product or Operations mutation.

## Existing Safe Action Foundation

The existing Safe Action policy and readiness documents remain authoritative for
the current framework details:

- `HYBRID_SAFE_ACTIONS_POLICY.md`
- `HYBRID_SAFE_ACTIONS_READINESS_REVIEW.md`
- `HYBRID_NOTIFICATION_ACK_EXECUTE_READINESS.md`

Current foundation:

- `ModernAdminSafeAction`
- `ModernAdminSafeActionResult`
- `ModernAdminSafeActionRegistry`
- `ModernAdminSafeActionRunner`
- dry-run endpoint: `/modern-admin/safe-action/dry-run`
- service-only pilots:
  - `notification.acknowledge`
  - `image.exclude`
  - `image.unexclude`
  - `log.download`

Current boundary:

- dry-run is available;
- execute remains blocked;
- no Product UI button executes a Safe Action;
- Classic remains fallback for real mutative workflows.

## Proposed Action Taxonomy

| Category | Meaning | Product stance |
| --- | --- | --- |
| Safe User Actions | Low-risk, explainable, audited, bounded operations a normal user may eventually trigger. | Must use Safe Action contract before UI exposure. |
| Operational Actions | Camera, capture, output, upload, media, or observatory operations used by operators. | Operations/Advanced, not Product-first unless rewritten as safe actions. |
| Maintenance Actions | Restore, export, download, cleanup, storage, logs, and retention operations. | Developer/Operations; require confirmation, audit, rollback or redaction policy. |
| Developer Actions | Hardware, network, system, raw config, credentials, debug tools. | Developer-only or Classic fallback. |
| Dangerous Actions | Destructive, hardware/OS-level, filesystem/media deletion, credential reset, service control. | Never Basic; never Product UI without explicit contract and tests. |
| External API Actions | `/action/*` and `/sync/v1/*` contracts used by automation or remote systems. | Preserve compatibility; do not fold into Product UI casually. |
| Query-style POST | POST endpoints that fetch/list data rather than mutate. | Not actions, but semantically confusing and worth future audit. |
| Legacy Actions | Existing Classic/shared mutations still required as fallback. | Keep until a native Safe Action replacement exists. |

## Future Action Contract Fields

Every future action should have an explicit registry entry with:

- action id;
- human label;
- current endpoint;
- caller;
- target subsystem;
- owner;
- Product / Operations / Developer / Classic role;
- destructive flag;
- reversible flag;
- confirmation requirement;
- authentication and authorization requirement;
- CSRF requirement;
- runtime risk;
- expected frequency;
- dry-run behavior;
- audit behavior;
- rollback/fallback behavior;
- future owner;
- stop conditions.

## Current Action Inventory

### Product Candidate Safe Actions

| Action | Current endpoint / code | Caller | Target | Role | Destructive | Reversible | Confirmation | Auth | Risk | Frequency | Future owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Notification acknowledge | Service-only `notification.acknowledge`; legacy `/ajax/notification` | Classic notifications today; no Product execute path | Notification DB state | Candidate Product / Operations | No | Mostly no; idempotent | No in legacy; yes for Product execute policy | login/admin policy still needs final endpoint tests | Medium | Medium | Safe Action service |
| Image exclude | Service-only `image.exclude`; legacy `/ajax/exclude` | Gallery/Image viewer | Image metadata flag | Candidate Operations | No data deletion, but hides image from outputs/review | Yes via unexclude | Should be explicit | Admin | Medium | Low-medium | Safe Action service / Media Operations |
| Image unexclude | Service-only `image.unexclude`; legacy `/ajax/exclude` | Gallery/Image viewer | Image metadata flag | Candidate Operations | No | Yes | Should be explicit | Admin | Medium | Low-medium | Safe Action service / Media Operations |
| Log download | Service-only `log.download`; legacy log download routes | Logs pages | Log file download | Candidate Developer | No mutation, but sensitive export | No | Yes | Admin | High | Low | Safe Action service / Developer |

### Capture And Camera Operations

| Action | Current endpoint / code | Caller | Target | Role | Destructive | Reversible | Confirmation | Auth | Risk | Frequency | Future owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Pause capture | `/action/pause` | External API clients | Task queue / capture state | External API / Operations | No | Yes via unpause | API has no interactive confirmation | API username/password + admin + admin network | Medium-high | Low-medium | Capture Operations Safe Action |
| Unpause capture | `/action/unpause` | External API clients | Task queue / capture state | External API / Operations | No | Yes via pause | API has no interactive confirmation | API username/password + admin + admin network | Medium-high | Low-medium | Capture Operations Safe Action |
| Start/stop/restart capture service | `/modern-admin/capture/service` | Hybrid shell/operations | `systemctl --user indi-allsky.service` | Developer / Operations | Potentially disruptive | Partially | Required | login/admin | High | Low | Developer Operations |
| Reconfigure INDI server | `/ajax/indiserver` | Classic config/camera workflow | user systemd service file and INDI service | Developer / Classic | Yes, writes service config | Partially via config restore/manual edit | Required | admin | Critical | Rare | Developer / Camera Operations |
| Restart INDI server during reconfigure | `/ajax/indiserver` with restart flag | Classic config/camera workflow | INDI user service | Developer / Classic | Disruptive | Partially | Required | admin | Critical | Rare | Developer / Camera Operations |
| Detect INDI camera/drivers | `/modern-admin/cameras/detect-indi` | Modern camera operations | INDI detection/runtime probe | Developer / Operations | No write expected, but runtime probing | N/A | Optional | login/admin context | High | Rare | Camera Operations |
| Start INDI | `/modern-admin/cameras/start-indi` | Modern camera operations | INDI service/runtime | Developer / Operations | Disruptive | Partially | Required | login/admin context | High | Rare | Camera Operations |
| Select active camera | `/ajax/select_camera` | UI camera selector | Flask session camera id | Operations | No system mutation | Yes by selecting another camera | No | session/login context | Low | Medium | Product shell / Operations |

### Configuration And Settings Operations

| Action | Current endpoint / code | Caller | Target | Role | Destructive | Reversible | Confirmation | Auth | Risk | Frequency | Future owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Save full configuration | `/ajax/config` | Classic full config | Config DB row | Developer / Classic | Potentially | Partially via config history | Required | admin | Critical | Medium | Settings Safe Action / Classic fallback |
| Queue config reload | `/ajax/config` when reload requested | Classic full config | Task queue / runtime reload | Developer / Classic | Disruptive | Partially | Required | admin | High | Medium | Settings Safe Action |
| Restore config upload | `/ajax/config/restore` | Classic config restore | Config DB row | Developer / Classic | Yes | Partially if previous config retained | Required | admin | Critical | Rare | Restore Safe Action |
| Flush old config records | `/ajax/config/restore` with flush flag | Classic config restore | Config history DB rows | Developer / Classic | Yes | No | Required | admin | Critical | Rare | Restore Safe Action |
| Reset Flask security keys | `/ajax/config/restore` with reset flag | Classic config restore | `/etc/indi-allsky/flask.json` secrets | Developer / Classic | Yes | No unless backed up | Required | admin | Critical | Rare | Restore Safe Action |
| Download config | Classic config download route | Classic config history | Config export | Developer / Classic | No mutation, sensitive export | N/A | Yes | admin | High | Rare | Download/redaction policy |
| Raw config inspection | Classic config history/raw surfaces | Classic developer pages | Config contents | Developer / Classic | No mutation, sensitive read | N/A | Yes | admin | High | Rare | Developer Config |

### Media, Output, And File-Oriented Operations

| Action | Current endpoint / code | Caller | Target | Role | Destructive | Reversible | Confirmation | Auth | Risk | Frequency | Future owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Generate timelapse/keogram/startrail outputs | `/ajax/generate` | Classic Generate | Task queue / generated media | Operations / Classic | No direct deletion unless selected action deletes first | Partially | Required | admin + admin network | High | Medium | Output Operations Safe Action |
| Delete generated media for selected day | `/ajax/generate` action `delete_video_k_st_p` | Classic Generate | Generated media DB rows and assets | Operations / Classic | Yes | No | Required | admin + admin network | Critical | Low | Output Maintenance Safe Action |
| Generate mini timelapse | `/ajax/minigenerate` | Classic Mini Generate | Task queue / generated media | Operations / Classic | No direct deletion expected | Partially | Required | admin | High | Low-medium | Output Operations Safe Action |
| Generate long-term keogram | JSON long-term keogram endpoint | Long Term Keogram page | Long-term keogram file/cache | Operations / Classic | Writes cache image | Regenerable, but overwrites cache | Required | login | High on RPi5 | Low | Output Operations |
| Upload video to YouTube | `/ajax/uploadyoutube` | Video/Mini/Startrail/Panorama pages | Upload task queue / external provider | Operations / Integration | No local deletion, external publish | Partially via provider | Required | login/admin expectation | High | Low | Integration Safe Action |
| FITS to JPEG conversion/download | FITS conversion route | FITS viewer / processing | Derived preview/download | Advanced / Developer | No mutation expected | N/A | Optional | media/auth policy | Medium-high | Low | Source/Download policy |
| Image processing preview | Image processing endpoint/page | Process FITS page | FITS/media processing result | Developer / Classic | Usually no persistent mutation, but heavy media read/process | N/A | Required | login/admin context | High | Low | Source Processing |
| Public/latest downloads | `/latest*`, media routes | Public/external users | Media download/read | Public / External | No mutation | N/A | No/optional media auth | Public/media auth | Medium | High | Public compatibility |

### System, Hardware, Network, And Storage Operations

| Action | Current endpoint / code | Caller | Target | Role | Destructive | Reversible | Confirmation | Auth | Risk | Frequency | Future owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Set system time | `/ajax/settime` | Classic/Developer system page | System clock, NTP disabled | Developer | Yes | Manual only | Required | admin | Critical | Rare | Developer System Safe Action |
| Set timezone | `/ajax/settimezone` | Classic/Developer system page | System timezone | Developer | Yes | Manual only | Required | admin | Critical | Rare | Developer System Safe Action |
| Network activate/deactivate/delete/autostart/priority/powersave | `/ajax/network` | Network page / Modern wrapper | NetworkManager DBus | Developer / Classic | Some commands destructive/disruptive | Partially | Required | admin | Critical | Rare | Developer Network |
| Wi-Fi scan/connect/hotspot create | `/ajax/network` | Network page / Modern wrapper | NetworkManager DBus | Developer / Classic | Disruptive, credential handling | Partially | Required | admin | Critical | Rare | Developer Network |
| Drive mount/unmount/poweroff | `/ajax/drives` | Drives page / Modern wrapper | UDisks2 DBus | Developer / Classic | Potentially disruptive/data-loss | Partially | Required | admin | Critical | Rare | Developer Storage |
| Manual GPIO set state | `/ajax/manual_gpio` | Manual GPIO page / Modern wrapper | GPIO device pins | Developer / Classic | Hardware effect | Partially/manual | Required | admin | Critical | Rare | Developer Hardware |
| Focus movement | `/ajax/focuscontroller` | Focus page / Modern wrapper | Focuser hardware | Operations / Developer | Hardware movement | Partially/manual | Required | admin + admin network | High | Low | Camera Hardware Safe Action |

### External Sync API Actions

| Action family | Current endpoint | Caller | Target | Role | Destructive | Reversible | Confirmation | Auth | Risk | Frequency | Future owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Sync camera metadata | `/sync/v1/camera` GET/POST/PUT/DELETE | External sync clients | Camera DB records | External API | Yes for DELETE/PUT | Partially | API-level only | Sync API auth | Critical | Deployment-dependent | External API contract |
| Sync image/video/generated media metadata | `/sync/v1/image`, `/video`, `/minivideo`, `/keogram`, `/startrail`, `/startrailvideo`, `/panoramaimage`, `/panoramavideo` | External sync clients | Media DB records and possibly assets | External API | Yes for DELETE/PUT | Partially | API-level only | Sync API auth | Critical | Deployment-dependent | External API contract |
| Sync RAW/FITS/thumbnail metadata/assets | `/sync/v1/rawimage`, `/fitsimage`, `/thumbnail` | External sync clients | Source/media DB records and possibly assets | External API | Yes for DELETE/PUT | Partially | API-level only | Sync API auth | Critical | Deployment-dependent | External API contract |

External Sync API routes are not Product UI safe actions. They are versioned
external contracts and should remain separate from Product/Operations action
design.

### Query-Style POST Endpoints That Are Not Actions

These routes use POST but primarily list, filter, inspect, or retrieve data.
They should not be treated as mutative actions, but their semantics are a future
cleanup concern:

- `/ajax/imageviewer`
- `/ajax/fitsimageviewer`
- `/ajax/gallery`
- `/ajax/videoviewer`
- `/ajax/minivideoviewer`
- `/ajax/systeminfo`
- `/ajax/userinfo`
- support/status JSON helpers

Recommendation: do not change these before Alpha. Later, document them as
read-query POST compatibility endpoints or migrate behind explicit read APIs
only after consumer evidence exists.

## Main Architectural Findings

### 1. There Is No Unified Action Registry Yet

Safe Action classes exist, but the real mutative surface is still spread across
Classic AJAX routes, external APIs, DBus/system helpers, media generation
queues, and Modern wrappers.

Benefit of fixing later: Product and Operations actions become discoverable,
auditable, and testable.

Risk of fixing too early: breaking Classic/external workflows.

Priority: P0 for contract design, P1/P2 for implementation by action family.

### 2. Modern Product UI Correctly Avoids Mutation

The Product spine does not expose real mutative actions. This is consistent with
the Product Domain Contract and DATA001-DATA006 safety pattern.

Future rule: Product UI may show action availability as metadata, but execution
needs a Safe Action contract, confirmation, audit, and fallback.

### 3. HTTP Semantics Are Mixed

Some GET routes trigger processing/download-like behavior. Some POST routes are
read/list endpoints. This is not immediately unsafe if compatibility is
preserved, but it makes ownership harder to reason about.

Do not normalize route methods before Alpha.

### 4. Several "Read" Actions Are Sensitive

Config download, log download, raw config inspection, FITS conversion, and media
downloads may not mutate state, but they can expose sensitive data or perform
heavy work.

Future model should classify these as sensitive read/download actions, not as
ordinary page views.

### 5. Hardware And OS Actions Must Stay Developer-Only

Network, drives, GPIO, focus movement, service control, time, timezone, and INDI
service rewriting are not Product actions. They are Developer/Operations actions
with high or critical runtime risk.

### 6. Queue-Based Work Needs Request/Execution Separation

Media generation, upload, config reload, and capture pause/unpause often create
task queue entries. The future action model should distinguish:

- the user/request action;
- the queued execution record;
- the worker-side execution result.

### 7. Classic Fallback Is Still Required

Many high-risk workflows have Modern read-only wrappers, but the live mutation
still belongs to Classic/shared endpoints. That is acceptable before Alpha and
should remain explicit.

## Biggest Inconsistencies

1. Safe Action policy exists, but most live actions bypass it.
2. Product surfaces are read-only, while adjacent Operational pages still expose
   Classic-style mutations.
3. POST is used both for mutation and for read/list AJAX.
4. Some dangerous actions are grouped visually near normal operational pages.
5. Download/export actions are not consistently modeled as sensitive actions.
6. Queue-creating actions lack a unified product-level request schema.
7. External API actions share concepts with Product actions but should not share
   the same ownership model.
8. Confirmation semantics differ by page and action family.
9. Rollback/reversibility is rarely explicit.
10. Future ownership is known conceptually but not encoded in a registry.

## Recommendations

### P0: Define A Safe Action Contract Schema

- Motivation: this registry identifies actions, but there is no canonical
  contract schema for future action metadata.
- Benefits: every future mutation can be reviewed consistently before code.
- Risks: low if documentation-only.
- Impact: high.
- Dependencies: this registry, Safe Action policy, Route Role Matrix, Settings
  Contract Review.
- Verification: every candidate action can be expressed with the schema fields.

### P0: Keep Product Spine Read-Only Until Action Contracts Exist

- Motivation: Product UI quality depends on trust and low runtime risk.
- Benefits: prevents accidental admin-panel regression.
- Risks: product remains less interactive in Alpha.
- Impact: high safety.
- Dependencies: Product view model tests and template review.
- Verification: Product routes expose no POST/fetch/AJAX mutation.

### P1: Add Action Ownership Metadata To Governance

- Motivation: ownership maps currently classify pages/features, not actions.
- Benefits: future inventory can detect unsafe exposure.
- Risks: medium if guessed.
- Impact: medium-high.
- Dependencies: action contract schema.
- Verification: action entries have endpoint, owner, risk, and fallback fields.

### P1: Audit Query-Style POST Endpoints Separately

- Motivation: read/list POST endpoints are not actions but create confusion.
- Benefits: avoids mixing compatibility reads with dangerous mutations.
- Risks: low if audit-only.
- Impact: medium.
- Dependencies: browser/network evidence for consumers.
- Verification: each POST endpoint classified as query, mutation, or mixed.

### P1: External API Action Compatibility Review

- Motivation: `/action/*` and `/sync/v1/*` are critical external contracts.
- Benefits: prevents Product consolidation from breaking remote automation.
- Risks: low if review-only.
- Impact: high safety.
- Dependencies: current API consumers if known.
- Verification: external API routes stay unchanged and documented.

### P2: Download/Export Sensitivity Policy

- Motivation: downloads are not mutations but can leak secrets or heavy media.
- Benefits: clearer handling for logs, config, FITS, source, and media.
- Risks: medium if endpoint behavior changes; keep policy-only first.
- Impact: medium.
- Dependencies: log download policy, config restore/download review, media route
  audit.
- Verification: symbolic allowlists and redaction requirements are defined.

## Stop Conditions

Do not implement or expose a new action if any of these are unclear:

- authentication and authorization level;
- CSRF behavior;
- confirmation UX;
- audit destination and retention;
- rollback/fallback path;
- whether the action touches filesystem, hardware, service state, credentials,
  or external providers;
- whether Classic remains the fallback;
- how the action behaves on Raspberry Pi 5 under failure.

## Recommended Next Mission

Recommended next mission: **Safe Action Contract Schema**.

This should be documentation-only and should define the canonical metadata model
for future actions. It should not add execute endpoints, UI buttons, route
changes, or runtime behavior.

Reason: the action inventory is now known enough to avoid guessing, but still
too risky to implement. A small schema step will let future work convert one
action family at a time without repeating policy debates.
