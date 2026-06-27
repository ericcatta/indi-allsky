# HYBRID SAFE ACTIONS POLICY

## 1. Purpose

This document defines the operational policy for porting Classic UI actions into
Modern Admin.

Hybrid AllSky now has broad Modern read-only/status/detail coverage. The next
porting boundary is not visual parity; it is safe action parity. Any action that
changes database state, filesystem state, hardware state, queue state, external
services, authentication state, credentials, or public/media behavior must have a
clear contract before it is exposed in Modern Admin.

This policy does not implement actions. It defines which actions may be ported
later, which are blocked, and what prerequisites are required.

## 2. Current State

Current porting state:

| Metric | Current state |
| --- | --- |
| Total tracked features | 92 |
| Modern read-only/status/metadata coverage | 66 features |
| Classic-only features | 0 |
| Partial Modern / in progress | 34 |
| Project Modern Coverage | approximately 59-61% |
| Classic Removal Readiness | approximately 37-42% |
| Classic removability | 0% |

Classic-only is now effectively zero, but Classic removability remains zero
because most mutation, download, restore, media, hardware, OAuth, and queue
actions do not yet have a Modern-safe backend contract.

Classic UI remains the fallback for these operations until each action has a
wrapper, policy, tests, rollback model, and deprecation path.

## 3. Global Rules

- No Modern action may be exposed without an explicit backend contract.
- Do not call legacy POST endpoints directly from Modern Admin unless wrapped by
  a safe Modern action layer.
- No filesystem action is allowed without a strict allowlist.
- No download is allowed without path validation, MIME validation, size limits,
  and secret/redaction policy where relevant.
- No config restore is allowed without rollback semantics and operator
  confirmation.
- No auth/user mutation is allowed without explicit permission policy and
  self-lockout prevention.
- No queue mutation is allowed without clear state transitions and race handling.
- No OAuth flow is allowed without credential redaction, token handling policy,
  and negative-path tests.
- No hardware action is allowed without admin permission, admin-network policy,
  dry-run/status-first behavior where possible, and operator confirmation.
- Public/latest endpoints, Sync API, Action API, shared AJAX endpoints, and
  bookmark routes are compatibility surfaces, not dead code.
- Classic fallback remains until Modern parity is complete and has had a
  deprecation window.

## 4. Action Risk Matrix

Status values:

- SAFE NOW: may be ported with existing contract and tests.
- SAFE AFTER WRAPPER: backend exists but needs a Modern wrapper before UI use.
- SAFE AFTER POLICY: conceptually reasonable, but policy is required first.
- BLOCKED UNTIL BACKEND CONTRACT: no safe user-facing contract exists yet.
- DO NOT PORT: should remain out of Modern Admin or external/public compatibility.
- KEEP CLASSIC FALLBACK: Classic must remain available while Modern is incomplete.

| Area | Action | Existing route / class | Method | Backend support | Side effect | Sensitive data | Risk | Status | Prerequisites |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Task Queue | retry/cancel/delete/requeue | `/tasks`, `TaskQueueView` | GET page only | No safe user-facing mutation contract found | Would change task lifecycle | Task payloads may contain camera/profile/path/action data | High | BLOCKED UNTIL BACKEND CONTRACT | Define task state machine, allowed transitions, ownership, audit log, race handling, rollback/no-op behavior, tests for queued/running/failed tasks |
| Logs | download logs | `/log/download`, `/log/webapp_download`, `/log/syslog_download`, `/log/kern_download`; `Log*DownloadView` | GET | Exists as direct download | Reads log files, returns gzip | Logs may contain tokens, paths, IPs, errors, config fragments | High | SAFE AFTER POLICY | File allowlist, max lines/size clamp, redaction pipeline, content disposition policy, tests for missing/large/permission-denied files |
| Logs | clear/rotate/truncate | No safe Modern contract found | N/A | Not suitable from current evidence | Would mutate log files/services | Logs may contain sensitive data | Critical | DO NOT PORT | Keep outside Modern until explicit operational maintenance design exists |
| Config Restore | upload/active restore | `/config/restore`, `/ajax/config/restore`; `ConfigRestoreView`, `AjaxConfigRestoreView` | POST | Exists in Classic | Writes active config, may flush config history, may reset secret keys, writes temporary file | Full config, secrets, password keys, flask secrets | Critical | BLOCKED UNTIL BACKEND CONTRACT | Restore preview, diff, redaction, backup snapshot, rollback, confirmation, admin-only, audit log, tests for invalid/large/secret-reset/flush paths |
| Config History | restore/download parity | `/config/list`, `/config/download`, `/config/restore` | GET/POST | Classic supports list/download/restore surfaces | Download exposes config; restore mutates active config | Full config may contain credentials and secrets | Critical | SAFE AFTER POLICY | Redacted preview first, safe export policy, rollback contract, restore wrapper, no raw config display in Modern |
| Notifications | acknowledge | `/ajax/notification`; `AjaxNotificationView.post()` | POST | Exists in shared AJAX | Mutates notification ack state | Notification text may contain paths/errors | Medium | SAFE AFTER WRAPPER | Modern wrapper with CSRF/auth, row-level ID validation, idempotent ack, audit event, tests for expired/missing/already-ack |
| Notifications | delete | No safe direct evidence found | N/A | Not established | Would remove evidence/history | Notification text | Medium | BLOCKED UNTIL BACKEND CONTRACT | Deletion semantics, retention policy, audit log, undo/rollback or soft delete |
| User Management | update own name/password | `/ajax/user`; `AjaxUserInfoView` | POST | Exists for current user | Updates user row and password hash | Passwords, account metadata | Critical | SAFE AFTER POLICY | Auth policy, current-password confirmation, self-lockout prevention, password validation tests, audit log |
| User Management | admin role/active/delete/reset | Classic users page / user model | Mixed/unknown | No safe Modern contract established | Mutates auth and authorization | Password hash, API key, roles, email | Critical | BLOCKED UNTIL BACKEND CONTRACT | Explicit permission model, self-protection, rollback/disable semantics, audit log, tests |
| FITS Viewer | metadata browsing | `/ajax/fitsimageviewer`; `AjaxFitsImageViewerView` | POST | Exists and mostly read-only | DB reads | FITS filenames/metadata | Low | SAFE AFTER WRAPPER | Prefer existing Modern metadata pages; wrap AJAX only if needed |
| FITS Viewer | preview/conversion | `/fits2jpeg`; `Fits2JpegView` | GET | Exists | Reads FITS, opens file, runs processing/conversion | FITS path/content, image data | High | SAFE AFTER POLICY | Path allowlist by DB ID, conversion sandbox, size limits, timeout, no arbitrary path, cache policy, tests |
| FITS Viewer | download | Existing direct policy not verified | GET/unknown | Not safe enough | Reads and returns FITS/source files | Scientific source paths | High | SAFE AFTER POLICY | Download/file policy, source allowlist, MIME, size, auth, no path exposure |
| Image Viewer | exclude/unexclude | `/ajax/exclude`; `AjaxImageExcludeView` | POST | Exists | Mutates image exclude flag | Image IDs/camera IDs | Medium | SAFE AFTER WRAPPER | Modern media action wrapper, admin-only, camera ownership validation, idempotency, audit log, tests |
| Image Viewer | delete/download/share/process | Classic viewer/media actions | Mixed | Existing behavior spread across media endpoints | Deletes assets, serves files, processes images | File paths, media content | High | SAFE AFTER POLICY | Media action policy, file allowlist, confirmation, soft-delete/rollback where possible |
| Video Viewer | upload to YouTube | `/ajax/uploadyoutube`; `AjaxUploadYoutubeView` | POST | Exists | Creates upload task | Video IDs, upload metadata, external provider behavior | High | SAFE AFTER POLICY | Upload/OAuth policy, task duplication checks, credential status checks, audit log |
| Video Viewer | download/share/delete | Classic video viewer/actions | Mixed | Existing behavior not wrapped safely | File serving/deletion/public sharing | File paths/media URLs | High | SAFE AFTER POLICY | Media action policy, public URL policy, confirmation, tests |
| Gallery | browse/filter | `/ajax/gallery`; `AjaxGalleryViewerView` | POST | Exists, read-like | DB/media listing | Media metadata | Low | SAFE AFTER WRAPPER | Existing Modern read-only coverage preferred |
| Gallery | delete/exclude/download/share | Classic/gallery/media actions | Mixed | Existing behavior not safe as direct Modern action | Mutates DB/filesystem or serves files | Paths/media content | High | SAFE AFTER POLICY | Media action policy, allowlist, confirmation, audit log |
| Upload | provider tests / remote operations | File transfer/S3/YouTube upload pipeline | Mixed | Backend exists for runtime uploads | Contacts remote providers, may create tasks | Hosts, usernames, keys, remote URLs | Critical | BLOCKED UNTIL BACKEND CONTRACT | Provider action contract, credential redaction, dry-run semantics, timeout/error model, audit log |
| YouTube / OAuth | authorize/refresh/revoke | `/youtube/authorize`, `/youtube/oauth2refresh`, `/youtube/oauth2revoke`, `/youtube/oauth2callback` | GET | Exists | Changes external authorization and stored credentials | OAuth tokens/credential payloads | Critical | BLOCKED UNTIL BACKEND CONTRACT | OAuth wrapper, CSRF/state validation review, token redaction, audit log, failure tests |
| YouTube / OAuth | status audit | `/modern-admin/youtube`; `ModernAdminYoutubeView` | GET | Exists in Modern | None beyond existence check | Credentials existence only | Low | SAFE NOW | Keep read-only, do not expose paths/tokens/payloads |
| Focus | move/autofocus | `/ajax/focuscontroller`; `AjaxFocusControllerView` | POST | Exists | Moves hardware focuser | Hardware state | Critical | SAFE AFTER POLICY | Hardware action policy, admin-network check, confirmation, rate limits, dry-run/status first, tests/mocks |
| Timelapse | generate/regenerate | `/ajax/generate`; `AjaxTimelapseGeneratorView` | POST | Exists | Creates VIDEO queue tasks | Camera/day/night/task data | High | SAFE AFTER POLICY | Queue/generation policy, duplicate prevention, per-camera isolation, task feedback |
| Timelapse | delete | `/ajax/generate`; `AjaxTimelapseGeneratorView` | POST | Exists | Deletes DB rows and assets | Media files | High | SAFE AFTER POLICY | Media delete policy, confirmation, audit, rollback/soft-delete decision |
| Mini Timelapse | generate | `/ajax/minigenerate`; `AjaxMiniTimelapseGeneratorView` | POST | Exists | Creates VIDEO queue task | Image IDs, camera IDs | High | SAFE AFTER POLICY | Queue/generation policy, duplicate prevention, bounded window validation |
| Keogram / Startrail | generate/download/delete | `/ajax/generate`; `AjaxTimelapseGeneratorView` | POST | Exists for generation/deletion | Creates tasks or deletes assets | Media files/task data | High | SAFE AFTER POLICY | Queue/generation and media action policy |
| Startrail Video | watch/share/download | Public/latest/watch routes and viewer surfaces | GET/mixed | Public endpoints exist | Public media serving/navigation | Public URLs/media | Medium | KEEP CLASSIC FALLBACK | Preserve compatibility, define public media policy before changes |
| Raw Viewer | decode/download/source inspection | Raw image DB/source layer | Unknown/mixed | Metadata exists; decode policy not established | Reads scientific source files | Raw/source paths | High | SAFE AFTER POLICY | Scientific source file policy, path allowlist, no arbitrary decode, size limits |
| Panorama | generation/conversion/download/actions | Panorama media/queue actions | Mixed | Existing runtime outputs and media routes | Processing, queue, file serving/deletion | Media paths/content | High | SAFE AFTER POLICY | Media and generation policy, preserve public endpoint behavior |
| Public/latest endpoints | behavior changes | `/latest*`, `/images/<path:path>`, public media routes | GET | Exists | External compatibility behavior | Public media URLs and paths | Critical | DO NOT PORT | Preserve as compatibility APIs; do not remove or alter during Classic cleanup |

## 5. Safe Wrapper Requirements

Every Modern action wrapper must provide:

- CSRF protection where applicable.
- Existing auth and permission checks.
- Explicit allowlists for actions, IDs, file categories, and state transitions.
- Input validation with clear error responses.
- Camera/profile ownership validation when relevant.
- Idempotent behavior or explicit duplicate prevention.
- Race-condition handling for worker/queue/hardware state.
- Audit logging with actor, target, action, timestamp, outcome, and reason.
- Dry-run/status-first mode when possible.
- Explicit confirmation for destructive, external, hardware, or credential
  actions.
- Bounded timeouts for external or hardware operations.
- No secret leakage in responses, templates, logs, exceptions, or task payload
  previews.
- Rollback or documented no-rollback semantics.
- Tests for success, invalid target, unauthorized user, stale state, repeated
  action, backend failure, and rollback/fallback behavior.

## 6. Download / File Policy

Modern downloads must not be added by linking existing file paths directly.

Required policy for media, logs, config, FITS, raw, and scientific source files:

- Use DB IDs or explicit symbolic names, not arbitrary filesystem paths.
- Resolve paths only through trusted model/helper methods.
- Enforce an allowlist of base directories and file categories.
- Show basename or symbolic identity in UI; avoid absolute path display.
- Reject path traversal, symlinks outside allowed roots, missing files, and
  unexpected file types.
- Enforce size limits and row/line limits.
- Validate MIME/content type and extension.
- Redact logs/config before download when secret-bearing content is possible.
- Never expose password files, OAuth payloads, key files, flask secrets, raw
  config secrets, or private provider credentials.
- Prefer read-only preview/metadata before download.

## 7. Queue / Generation Policy

Queue and generation actions include task queue mutations, timelapse generation,
keogram/startrail generation, mini timelapse generation, panorama generation,
and upload task creation.

Required policy:

- Define allowed task states and transitions.
- Prevent duplicate task creation for the same camera/profile/day/action unless
  explicitly requested.
- Require camera_id/profile_id for multicamera-sensitive tasks.
- Validate day/night/timespec/camera ownership.
- Handle worker races and already-running tasks.
- Provide status-first and dry-run views before task creation.
- Return task IDs and clear user feedback.
- Record actor/action/reason in audit log.
- Define cancel semantics before exposing cancel.
- Do not expose retry/requeue until failure-state replay semantics are defined.

## 8. Auth / User Policy

User and auth actions are security-critical.

Required policy:

- No password, role, active-state, API key, or user deletion mutation without an
  explicit permission model.
- Prevent self-lockout and last-admin removal.
- Require current-password confirmation for self-sensitive changes.
- Require admin confirmation for role/active-state changes.
- Never expose password hashes, API keys, login IPs, sessions, or reset tokens in
  Modern UI unless a dedicated redaction policy exists.
- Audit every auth mutation.
- Test unauthorized, non-admin, self-action, last-admin, invalid password, and
  rollback/failure paths.

## 9. OAuth / Upload Policy

Upload and OAuth actions interact with external providers and credentials.

Required policy:

- Show credential existence only unless a redacted credential metadata schema is
  created.
- Never show tokens, refresh tokens, credential JSON, client secret contents, or
  raw OAuth payloads.
- Avoid showing full local secret-file paths; prefer "configured yes/no".
- Do not call provider APIs from status pages.
- Do not refresh, revoke, authorize, or test upload without a wrapper.
- Include CSRF/state validation review for OAuth flows.
- Include timeout and retry policy for external calls.
- Include audit logging for every provider action.
- Include tests with mocked provider failures and credential-missing paths.

## 10. Recommended Unblock Order

Recommended order is based on risk, value, and smallest safe wrapper:

1. Notification acknowledge wrapper: bounded DB mutation, clear idempotency, low
   blast radius.
2. Image exclude/unexclude wrapper: simple DB flag, camera ownership validation,
   no filesystem mutation.
3. Log download wrapper: existing read path, but only after redaction/size policy.
4. Queue generation dry-run/status contract: no task creation at first.
5. Timelapse/keogram/startrail generation wrapper: only after duplicate
   prevention and per-camera task policy.
6. Config download redacted export: only after config redaction policy.
7. Config restore preview/diff: preview before active restore.
8. Upload/YouTube task wrappers: only after provider/OAuth policy.
9. User management mutations: only after auth policy.
10. Hardware actions such as focus/GPIO: only after hardware action policy and
    operator confirmation.

## 11. Features That Should Stay Read-only For Now

These features should remain read-only/status/detail until their policies exist:

- Config Restore active restore.
- Config History raw download/restore parity.
- FITS preview/download/conversion.
- Raw decode/download/source-file inspection.
- Upload provider tests and remote operations.
- YouTube authorize/refresh/revoke/upload test.
- User role/password/active-state/API-key changes.
- Task Queue retry/cancel/delete/requeue.
- Focus hardware movement and GPIO state changes.
- Timelapse, keogram, startrail, mini timelapse, panorama generation/deletion.
- Public/latest endpoint behavior changes.
- Media delete/share/download actions.

## 12. Next Recommended Work

The next safest work is not to add an action. It is to create the first small
safe wrapper contract and tests for a low-risk action.

Contract foundation:

- `indi_allsky/modern_safe_action.py` defines `ModernAdminSafeAction` with the
  minimum action metadata, permission check, dry-run behavior, validation hook,
  execution hook, structured result, and sanitized audit message.
- The base contract is safe by default: no real action is implemented, and
  execution returns `not_implemented` unless a future subclass explicitly
  overrides it.
- The contract is not wired to UI, routes, buttons, or existing Classic
  endpoints yet.

Safe Action Registry:

- `ModernAdminSafeActionRegistry` is a catalog for future safe action contracts.
- The default registry is not wired to UI, routes, buttons, Classic endpoints,
  database writes, filesystem writes, or remote operations.
- Placeholder actions are denied by default and remain non-operative even if
  permission is later supplied unless a future subclass implements and tests a
  concrete wrapper.
- Registering a placeholder or wrapper is not authorization to expose that
  action in Modern Admin. Each action still needs its own endpoint wrapper,
  integration tests, policy review, and rollback/fallback decision.

First Pilot Safe Action: `notification.acknowledge`:

- `NotificationAcknowledgeSafeAction` is the first wrapper/test-only pilot.
- It validates a positive notification id, can use an injected notification
  lookup function, supports dry-run, and treats an already acknowledged
  notification as an idempotent safe no-op.
- It does not call `/ajax/notification`, does not require Flask request context,
  and does not write the database unless a future endpoint deliberately injects
  a tested acknowledge callback.
- Status: wrapper/test only, not exposed in Modern UI.
- Required before UI exposure: Modern CSRF/auth endpoint wrapper, audit log,
  confirmation UX, integration test, and Classic fallback/rollback decision.

Safe Action Runner:

- `ModernAdminSafeActionRunner` is a small helper layer for tests and future
  Flask wrappers.
- It resolves an action from the registry, rejects missing or unknown action ids,
  passes actor, payload, and dry-run state into the action contract, and always
  returns a structured `ModernAdminSafeActionResult`.
- The runner has no Flask request dependency and does not expose routes,
  buttons, POST handlers, Classic endpoint calls, database writes, filesystem
  writes, or remote operations.
- Status: helper/test layer only, not exposed in Modern UI.
- Required before UI exposure: CSRF/auth Flask wrapper, confirmation UX,
  integration tests, real audit log, and explicit rollback/fallback decision.

Structured Audit Record:

- `ModernAdminSafeActionAuditRecord` provides an in-memory, serializable audit
  record for safe action results.
- It captures action id, feature, actor label, dry-run state, allowed/denied
  state, status, risk level, redacted payload summary, redacted result summary,
  reason, and timestamp.
- It does not write to the database, filesystem, application log, or any remote
  service.
- It redacts secret-bearing payload/result keys before serialization.
- Status: structured contract only; persistent audit storage remains required
  before any execute endpoint.

Dry-Run Endpoint:

- `/modern-admin/safe-action/dry-run` is the first Modern Safe Action endpoint.
- It is authenticated and covered by the normal Flask-WTF CSRF protection for
  the `indi_allsky` blueprint.
- It forces `dry_run=True`, uses the safe action runner, and currently registers
  only the `notification.acknowledge` dry-run action.
- It does not inject an acknowledge callback, does not call `/ajax/notification`,
  does not write the database or filesystem, and is not wired to any UI button.
- Status: endpoint plumbing only; execute remains blocked.

Recommended next micro-step:

1. Add Flask-level tests for the dry-run endpoint, including CSRF/auth behavior.
2. Add persistent audit storage design before any execute endpoint.
3. Do not wire any Modern UI button until endpoint tests and confirmation UX
   exist.
4. Keep Classic fallback unchanged.
5. Do not add delete/download/restore/OAuth/hardware actions until their specific
   policy sections are satisfied.

If action work is still considered too risky, the next safe alternative is
Settings Redesign preparation: document ownership and grouping without changing
runtime configuration behavior.
