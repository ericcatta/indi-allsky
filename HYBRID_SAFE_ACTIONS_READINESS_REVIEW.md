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

Current boundary:

- no Modern endpoint exists
- no Modern UI button exists
- no browser path can invoke a safe action
- no safe action calls `/ajax/notification`
- no safe action writes the database unless a future endpoint injects a callback

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
| Is persistent audit logging missing? | Yes. Current audit messages are structured/redacted result fields only. They are not persisted as an audit trail. |
| Is a permission model missing? | Partially. The contract supports injected permission checks, but no canonical Modern Safe Action permission policy exists yet. |
| Is confirmation UX missing? | Yes. This is not required for dry-run endpoints, but is required before real mutation UI. |
| Is Flask integration testing missing? | Yes. Unit tests exist; endpoint-level tests do not. |
| Is a dry-run-only endpoint safe? | Conservatively yes, if it is authenticated, CSRF-protected, does not inject execute callbacks, returns only redacted results, and is covered by Flask tests. |
| Is a real execute endpoint for notification acknowledge safe now? | Not yet. It needs CSRF/auth wrapper, persistent audit, permission policy, integration test, and explicit idempotency behavior with DB-backed lookup/callback. |
| What is the safest next micro-step? | Add a dry-run-only Flask wrapper endpoint for `notification.acknowledge`, behind login/admin policy and CSRF, with tests, but no UI button and no execute callback. |

## 5. Readiness Matrix

| Requirement | Status | Risk | Needed Before Dry-Run Endpoint | Needed Before Execute Endpoint |
| --- | --- | --- | --- | --- |
| Structured action result | Implemented | Low | Yes, already present | Yes, already present |
| Registry lookup | Implemented | Low | Yes, already present | Yes, already present |
| Runner invocation | Implemented | Low | Yes, already present | Yes, already present |
| Missing/unknown action handling | Implemented | Low | Yes, already present | Yes, already present |
| Payload redaction | Implemented at contract level | Medium | Yes, already present; verify endpoint response does not add raw payload | Yes, plus persistent audit redaction |
| Notification id validation | Implemented in wrapper | Low | Yes, already present | Yes, already present |
| Idempotent already-acknowledged handling | Implemented in wrapper | Low | Not required for dry-run, but present | Required and present at wrapper level |
| Permission check hook | Implemented as injection | Medium | Endpoint must inject canonical permission check | Endpoint must inject canonical permission check |
| Flask auth | Existing project pattern via `login_required` | Medium | Required | Required |
| CSRF protection | Existing form ecosystem, not yet applied to safe actions | High | Required | Required |
| JSON response pattern | Existing via `jsonify(...)` | Low | Required | Required |
| Persistent audit log | Missing | High | Optional for dry-run if response remains non-mutating; recommended | Required |
| Endpoint integration tests | Missing | High | Required | Required |
| Confirmation UX | Missing | Medium | Not required for dry-run-only endpoint | Required before UI execution |
| DB-backed lookup callback | Not implemented | Medium | Not required for dry-run-only validation if endpoint remains conservative; recommended for target existence validation | Required |
| DB-backed execute callback | Not implemented | High | Must not be injected for dry-run-only endpoint | Required |
| Browser/UI exposure | Missing by design | Medium | Not needed | Required only after endpoint and UX policy |
| Classic fallback | Preserved | Low | Required | Required |

## 6. Recommendation

Recommendation: **READY FOR DRY-RUN ENDPOINT ONLY**.

Hybrid AllSky is not ready for a real execute endpoint. The current foundation
is strong enough to create a Modern Safe Action endpoint that only runs
`dry_run=True`, never injects a mutating callback, and returns a redacted
`ModernAdminSafeActionResult`.

This dry-run endpoint should be treated as endpoint plumbing validation, not
feature parity and not user-facing action support.

## 7. Not Ready For Execute

`notification.acknowledge` should not be executable from Modern Admin yet.

Missing before real execution:

- canonical Modern Safe Action permission policy
- CSRF-protected endpoint wrapper
- persistent audit event
- Flask integration tests
- DB-backed notification lookup callback
- DB-backed acknowledge callback
- tests for missing notification, already acknowledged notification,
  unauthorized user, malformed payload, stale/expired notification, and DB
  failure
- confirmation UX decision
- rollback/fallback decision

## 8. Next Micro-Step

The safest next micro-step is:

1. Create a dry-run-only Modern Safe Action Flask endpoint for
   `notification.acknowledge`.
2. Require login and the existing/admin permission pattern selected for Modern
   Safe Actions.
3. Require CSRF protection.
4. Do not inject `acknowledge_callback`.
5. Do not expose a UI button.
6. Return only `ModernAdminSafeActionResult.to_dict()`.
7. Add Flask-level tests for authentication, CSRF, missing action id, unknown
   action id, invalid notification id, and dry-run response shape.

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
