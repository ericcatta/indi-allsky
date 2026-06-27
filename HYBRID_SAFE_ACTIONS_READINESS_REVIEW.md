# HYBRID SAFE ACTIONS READINESS REVIEW

## 1. Purpose

This document reviews whether Hybrid AllSky is ready to expose the first Modern
Safe Action endpoint after the contract, registry, runner, and
`notification.acknowledge` wrapper foundations.

This is a readiness review only. It does not add a Flask route, POST endpoint,
UI button, browser-executable action, or Classic UI change.

## 2. Current Safe Action Foundation

Implemented foundation:

- `ModernAdminSafeAction`
- `ModernAdminSafeActionResult`
- `ModernAdminSafeActionRegistry`
- `ModernAdminSafeActionRunner`
- placeholder action catalog
- `NotificationAcknowledgeSafeAction`
- unit tests for permission, validation, dry-run, execution callback,
  idempotent already-acknowledged behavior, missing action ids, unknown action
  ids, structured failures, and audit redaction
- static/helper-level endpoint tests for the dry-run route registration,
  POST-only declaration, no legacy ack path, response shape, permission denied,
  forced dry-run, and redaction
- structured in-memory audit records for result, actor, payload, status, risk,
  allowed/denied state, reason, and redacted result summaries

Current boundary:

- a dry-run-only Modern endpoint exists at `/modern-admin/safe-action/dry-run`
- no Modern UI button exists
- no Modern UI path or button invokes a safe action
- no safe action calls `/ajax/notification`
- no safe action writes the database unless a future endpoint injects a callback
- no full Flask `test_client` safe-action test exists yet in the lightweight
  test runner because Flask is not available there
- static/helper-level tests cover dry-run route declaration, POST-only routing,
  `login_required`, CSRF non-exemption of the main blueprint, admin permission
  policy shape, response shapes, forced dry-run behavior, redaction, and absence
  of `/ajax/notification`, `setAck()`, `db.session`, or `commit()` in the
  dry-run view
- a lightweight append-only JSONL audit log utility exists, but it is not wired
  to execute endpoints, UI, DB sessions, or application logging
- `NotificationAcknowledgeDbAdapter` exists as a lookup-only bridge between
  `IndiAllSkyDbNotificationTable` and `NotificationAcknowledgeService`; it does
  not call `setAck()`
- `NotificationAcknowledgeService` exists as a testable service boundary for
  lookup and explicit acknowledge behavior, including transaction/error/audit
  tests, but no endpoint or UI invokes it for real execution
- legacy `IndiAllSkyDbNotificationTable.setAck()` commits directly, so future
  execute work must explicitly account for that transaction boundary

## 3. Evidence Reviewed

Reviewed files and patterns:

- `indi_allsky/modern_safe_action.py`
- `testing/modern_safe_action_test.py`
- `HYBRID_SAFE_ACTIONS_POLICY.md`
- Flask auth decorators in `indi_allsky/flask/views.py`
- existing JSON response patterns using `jsonify(...)`
- existing `login_required` usage on Modern Admin views
- existing AJAX mutation patterns using `methods = ['POST']`
- legacy notification acknowledge path:
  - `/ajax/notification`
  - `AjaxNotificationView.post()`
  - `IndiAllSkyDbNotificationTable`
  - `IndiAllSkyDbNotificationTable.setAck()`

## 4. Readiness Questions

| Question | Answer |
| --- | --- |
| Is the contract sufficient to expose an action? | Not by itself. It is sufficient as the action-domain contract, but not as a web exposure contract. |
| Is the registry sufficient? | Yes for lookup/catalog behavior; no for HTTP exposure, auth, CSRF, or audit. |
| Is the runner sufficient? | Yes for testable invocation and future Flask wrappers; no for browser exposure by itself. |
| Is CSRF missing? | Yes. No Modern Safe Action endpoint should execute without explicit CSRF/auth handling. |
| Is persistent audit logging missing? | Partially. `ModernAdminSafeActionAuditLog` can persist redacted JSONL records with retention/limits, but no execute endpoint uses it yet. |
| Is a permission model missing? | Partially. The contract supports injected permission checks, but no canonical Modern Safe Action permission policy exists yet. |
| Is confirmation UX missing? | Yes. This is not required for dry-run endpoints, but is required before real mutation UI. |
| Is Flask integration testing missing? | Yes. Unit tests exist; endpoint-level tests do not. |
| Is a dry-run-only endpoint safe? | Conservatively yes, if it is authenticated, CSRF-protected, does not inject execute callbacks, returns only redacted results, and is covered by Flask tests. |
| Is a real execute endpoint for notification acknowledge safe now? | Not yet. The service boundary and DB adapter now have unit coverage, but execute still needs CSRF/auth wrapper, persistent audit wiring, permission policy, Flask integration tests, and confirmation/UX decision. |
| What is the safest next micro-step? | Add a dry-run-only Flask wrapper endpoint for `notification.acknowledge`, behind login/admin policy and CSRF, with tests, but no UI button and no execute callback. |

Current `notification.acknowledge` state after the DB adapter:

- Ready: contract, registry, runner, audit record, persistent audit log, dry-run
  endpoint, service boundary, and DB adapter.
- Blocked: execute endpoint, Modern UI button, and live acknowledge in Modern.
- Minimum unblocker: provide a test environment with Flask available, add real
  `test_client` coverage for dry-run auth/session/CSRF behavior, then add a
  tested execute endpoint that wires the DB adapter, persistent audit log,
  final permission policy, and HTTP/status mapping before any UI button.

## 5. Readiness Matrix

| Requirement | Status | Risk | Needed Before Dry-Run Endpoint | Needed Before Execute Endpoint |
| --- | --- | --- | --- | --- |
| Structured action result | Implemented | Low | Yes, already present | Yes, already present |
| Registry lookup | Implemented | Low | Yes, already present | Yes, already present |
| Runner invocation | Implemented | Low | Yes, already present | Yes, already present |
| Missing/unknown action handling | Implemented | Low | Yes, already present | Yes, already present |
| Payload redaction | Implemented at contract level | Medium | Yes, already present; verify endpoint response does not add raw payload | Yes, plus persistent audit redaction |
| Structured audit record | Implemented in memory only | Medium | Useful for dry-run observability | Required as source for persistent audit |
| Notification id validation | Implemented in wrapper | Low | Yes, already present | Yes, already present |
| Idempotent already-acknowledged handling | Implemented in wrapper | Low | Not required for dry-run, but present | Required and present at wrapper level |
| Permission check hook | Implemented as injection | Medium | Endpoint must inject canonical permission check | Endpoint must inject canonical permission check |
| Flask auth | Existing project pattern via `login_required` | Medium | Required | Required |
| CSRF protection | Existing form ecosystem, not yet applied to safe actions | High | Required | Required |
| JSON response pattern | Existing via `jsonify(...)` | Low | Required | Required |
| Persistent audit log | Utility implemented, not wired to execute | High | Optional for dry-run if response remains non-mutating | Required and must be wired/tested before execute |
| Endpoint integration tests | Static/helper coverage only | High | Full Flask client test still recommended | Required |
| Confirmation UX | Missing | Medium | Not required for dry-run-only endpoint | Required before UI execution |
| DB-backed lookup callback | Service boundary implemented, not endpoint-wired | Medium | Not required for dry-run-only validation if endpoint remains conservative | Required and must be endpoint-tested |
| DB-backed execute callback | Service boundary implemented, not endpoint-wired | High | Must not be injected for dry-run-only endpoint | Required and must be endpoint-tested |
| Browser/UI exposure | Missing by design | Medium | Not needed | Required only after endpoint and UX policy |
| Classic fallback | Preserved | Low | Required | Required |

## 6. Recommendation

Recommendation: **DRY-RUN ENDPOINT CREATED; EXECUTE NOT READY**.

Hybrid AllSky is not ready for a real execute endpoint. The current dry-run
endpoint only runs `dry_run=True`, does not inject a mutating callback, and
returns a redacted `ModernAdminSafeActionResult`.

This dry-run endpoint should be treated as endpoint plumbing validation, not
feature parity and not user-facing action support.

## 7. Not Ready For Execute

`notification.acknowledge` should not be executable from Modern Admin yet.

Missing before real execution:

- canonical Modern Safe Action permission policy
- CSRF-protected endpoint wrapper
- persistent audit event backed by the structured audit record and JSONL audit
  log utility
- Flask integration tests
- DB-backed notification lookup callback wired into the execute endpoint
- DB-backed acknowledge callback wired into the execute endpoint
- tests for missing notification, already acknowledged notification,
  unauthorized user, malformed payload, stale/expired notification, and DB
  failure
- confirmation UX decision
- rollback/fallback decision

## 8. Next Micro-Step

The safest next micro-step is:

1. Add Flask-level tests for the dry-run endpoint authentication, CSRF, missing
   action id, unknown action id, invalid notification id, and dry-run response
   shape once a lightweight Flask test environment is available.
2. Design the execute endpoint wrapper for `notification.acknowledge` around the
   service boundary, but keep it unexposed until permission policy, persistent
   audit wiring, and integration tests are ready.
3. Keep `notification.acknowledge` execute blocked until the execute
   prerequisites are complete.

Do not implement real `ack` execution until the execute prerequisites in this
review are complete.

## 9. Stop Conditions For The Next Step

Stop before implementing an endpoint if any of these are unclear:

- how CSRF should be applied to JSON POST endpoints in this project
- whether the endpoint must be admin-only or login-only
- where persistent audit events should be stored
- how endpoint tests should initialize Flask app context and users
- whether a dry-run endpoint may validate notification existence without a DB
  mutation

## 10. Other Safe Action Families

`image.exclude` / `image.unexclude` are service-ready only. They have a service
boundary, DB adapter, safe action wrappers, audit integration and fake-callback
tests, but no endpoint or UI exposure.

`log.download` now has a policy/service foundation only. It supports symbolic
allowlisted log names, basename/path validation, metadata-only size checks via
an injected provider, redaction helpers and audit records. It does not read log
files, stream files, create download responses, expose an endpoint, or add UI.
Real download remains blocked until runtime path/download policy, Flask
auth/session/CSRF tests, endpoint response mapping, persistent audit wiring,
line/size limits, redaction verification and no-arbitrary-path tests exist.
