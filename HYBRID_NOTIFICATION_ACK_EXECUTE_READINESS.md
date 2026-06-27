# HYBRID NOTIFICATION ACK EXECUTE READINESS

## 1. Purpose

This document reviews whether `notification.acknowledge` is ready for the first
real Modern Safe Action execute endpoint.

This is a readiness review only. It does not add a Flask endpoint, UI button,
POST execute path, Classic UI change, or application behavior change.

## 2. Current State

Implemented foundations:

- `ModernAdminSafeAction`
- `ModernAdminSafeActionResult`
- `ModernAdminSafeActionRegistry`
- `ModernAdminSafeActionRunner`
- `ModernAdminSafeActionAuditRecord`
- `ModernAdminSafeActionAuditLog`
- dry-run-only endpoint at `/modern-admin/safe-action/dry-run`
- `NotificationAcknowledgeSafeAction`
- `NotificationAcknowledgeService`

`NotificationAcknowledgeService` now has explicit service states:

- `invalid_id`
- `not_found`
- `already_acked`
- `dry_run`
- `acknowledged`
- `repository_error`
- `acknowledge_failed`

It also has `acknowledge_with_audit(...)`, which can generate a structured audit
record and optionally write it to an injected audit log.

No Modern UI button invokes this action. No execute endpoint exists. The
dry-run endpoint does not inject a mutating callback and does not call
`/ajax/notification`.

## 3. Evidence Reviewed

Reviewed implementation and tests:

- `indi_allsky/modern_safe_action.py`
- `testing/modern_safe_action_test.py`
- `HYBRID_SAFE_ACTIONS_POLICY.md`
- `HYBRID_SAFE_ACTIONS_READINESS_REVIEW.md`
- `indi_allsky/flask/views.py`
- `indi_allsky/flask/models.py`

Relevant legacy behavior:

- `AjaxNotificationView.post()` reads `camera_id` and `ack_id` from JSON.
- It queries `IndiAllSkyDbNotificationTable` by ID.
- If found, it calls `notice.setAck()`.
- `IndiAllSkyDbNotificationTable.setAck()` sets `ack = True` and immediately
  calls `db.session.commit()`.
- Missing notification is silently ignored in the legacy endpoint.
- The legacy endpoint then returns the next active notification.

The direct commit inside `setAck()` means the service boundary cannot currently
manage a broader transaction around the acknowledge mutation unless the legacy
model method is changed or wrapped carefully.

## 4. Readiness Questions

| Question | Answer |
| --- | --- |
| Is the service boundary sufficient for execute real? | Sufficient as a domain/service boundary, not sufficient alone for a browser-exposed execute endpoint. |
| Is direct commit inside `setAck()` acceptable? | Acceptable only if the execute endpoint treats `setAck()` as the transaction boundary and records audit/result around it. It is not ideal for broader rollback semantics. |
| Is a DB adapter needed before the endpoint? | Implemented as `NotificationAcknowledgeDbAdapter`; the future endpoint should use it rather than querying directly in the view. |
| Is explicit rollback needed? | Not for this exact idempotent `ack=True` mutation if `setAck()` remains the transaction boundary. But rollback/no-rollback semantics must be documented in the endpoint contract. |
| Is persistent audit mandatory before execute? | Yes. Real execute must write a redacted audit record for success, already-acked no-op, validation failure, lookup failure, permission denial, and acknowledge failure. |
| Are true Flask session/CSRF tests needed before execute? | Yes. Current tests are unit/static/helper level. Browser-exposed mutation needs Flask-level auth, admin, CSRF, JSON, and failure-path coverage. |
| Is confirmation UX needed for acknowledge? | A full destructive confirmation is probably not needed because acknowledge is idempotent and low blast radius. The UI should still clearly indicate that it will mark a notification acknowledged. |
| Is rate limiting needed? | Not a hard blocker for a single acknowledge action, but repeated acknowledge calls should remain bounded by normal auth/CSRF protections and audit logging. |
| Admin-only or authenticated user? | Admin-only is the safer first execute policy. A later policy can decide whether notification acknowledge should be allowed for all authenticated users. |
| Is a disabled-by-default execute endpoint safe? | Safer than a real execute endpoint if it always returns disabled/not enabled and is covered by tests. It may be useful as a route/contract skeleton, but is not required yet. |
| Is a real functioning execute endpoint safe now? | Not yet. DB adapter exists, but Flask integration tests, audit wiring, response mapping, and permission/CSRF policy must be completed first. |
| Safest next micro-step? | Add Flask-level tests or a disabled-by-default execute skeleton with tests. Prefer Flask-level dry-run/auth/CSRF tests first if the test environment supports it. |

## 5. Readiness Matrix

| Requirement | Current state | Risk | Blocker? | Needed before execute endpoint | Needed before UI button |
| --- | --- | --- | --- | --- | --- |
| Safe Action contract | Implemented | Low | No | Already present | Already present |
| Safe Action runner | Implemented | Low | No | Already present | Already present |
| Notification service boundary | Implemented and hardened | Medium | No | Use through DB adapter | Use through execute endpoint only |
| Explicit states | Implemented | Low | No | Keep stable response mapping | Display clear user feedback |
| Idempotent already-acked behavior | Implemented | Low | No | Required and present | Required and present |
| Missing notification handling | Implemented as `not_found` | Low | No | Required and present | Required and present |
| `setAck()` failure handling | Implemented as `acknowledge_failed` | Medium | No | Required and present | Required and present |
| Direct `setAck()` commit | Legacy behavior | Medium-high | Partial | Endpoint must document transaction boundary; DB adapter should isolate it | UI must not imply rollback exists |
| Persistent audit log | Implemented utility | Medium | Partial | Must be wired into execute path and tested | Must be visible/traceable enough for operations |
| Audit on success/failure | Tested at service level | Medium | Partial | Must be endpoint-tested | Required before UI button |
| Permission model | Admin check exists in dry-run endpoint | Medium | Yes | Define execute permission policy, preferably admin-only first | Required |
| CSRF behavior | Existing Flask-WTF pattern, not fully tested for safe-action JSON execute | High | Yes | Flask integration tests required | Required |
| Flask session/auth tests | Missing for safe-action endpoint | High | Yes | Required before real execute | Required before UI button |
| DB adapter | Implemented and unit-tested, not endpoint-wired | Medium | No | Wire through execute endpoint, not directly in view logic | Required |
| Endpoint response mapping | Not implemented for execute | Medium | Yes | Required for invalid, denied, not_found, already_acked, acknowledged, repository_error, acknowledge_failed | Required |
| UI confirmation copy | Not implemented | Low-medium | No for endpoint, yes for UI | Not required for endpoint | Required before button |
| Rate limiting | Not implemented | Low-medium | No | Optional after audit/admin/CSRF | Optional unless abuse observed |
| Classic fallback | Preserved | Low | No | Must remain | Must remain |
| No direct `/ajax/notification` call | Preserved | Low | No | Must remain | Must remain |

## 6. Blockers Before Execute Endpoint

Blockers for a real functioning execute endpoint:

1. No Flask integration tests for safe-action auth/session/CSRF behavior.
2. `NotificationAcknowledgeDbAdapter` exists for lookup bridging, but it is not
   endpoint-wired and has not been exercised through real Flask/DB integration
   tests.
3. Persistent audit log is implemented, but not wired into an execute endpoint.
4. Execute permission policy is not yet written as an endpoint contract.
5. Endpoint response/status mapping for all service states does not exist.
6. `setAck()` commits directly, so the endpoint must document that it cannot
   provide broader rollback semantics without changing legacy model behavior.

These are local blockers, not global architecture blockers.

## 7. Blockers Before UI Button

Additional blockers before any Modern UI button:

1. A real execute endpoint must exist and pass Flask integration tests.
2. UI copy must make the effect clear: "mark notification acknowledged".
3. The button must never call `/ajax/notification`.
4. The button must include CSRF and handle denied, invalid, not found,
   already-acked, acknowledged, repository error, and acknowledge failure states.
5. The Classic fallback must remain until notification parity is accepted.
6. The audit event must be written for every attempted execute outcome.

## 8. Recommendation

Recommendation: **NOT READY, NEEDS FLASK INTEGRATION TESTS**.

The service boundary and DB adapter are now strong enough for a future execute
path, but the project should not expose a real functioning execute endpoint yet.

Current state:

- Ready: Safe Action contract, registry, runner, audit record, persistent audit
  log, dry-run endpoint, `NotificationAcknowledgeSafeAction`,
  `NotificationAcknowledgeService`, and `NotificationAcknowledgeDbAdapter`.
- Blocked: execute endpoint, Modern UI button, and live acknowledge from Modern.
- Blockers: missing real Flask integration tests for auth/session/CSRF, final
  permission policy, HTTP/status mapping, and persistent audit-log wiring in the
  real execute endpoint.
- Minimum unblocker: make Flask available in the test environment, add
  `test_client` coverage for the dry-run endpoint, then add a tested execute
  endpoint that wires the DB adapter and audit log; only after that should a UI
  button be considered.

Additional static/helper-level coverage now exists for the dry-run endpoint:

- route declaration exists;
- route is POST-only;
- route class has `login_required`;
- the main `bp_allsky` blueprint is not CSRF-exempt;
- permission policy is admin-oriented, with `LOGIN_DISABLED` as the test/dev
  escape hatch;
- helper responses cover missing action ID, unknown action, permission denied,
  successful `notification.acknowledge` dry-run, forced dry-run, and redaction;
- source checks confirm the dry-run view does not call `/ajax/notification`,
  `setAck()`, `db.session`, or `commit()`.

This coverage reduces risk, but it is not a substitute for a real Flask
`test_client` test. The current lightweight test environment does not have Flask
installed, so it cannot validate actual session behavior, CSRF rejection,
request routing, or response status codes at runtime.

A disabled-by-default execute skeleton could be safe if it is non-mutating,
admin-protected, CSRF-protected, tested, and always returns disabled. However,
that skeleton does not advance the real mutation as much as Flask integration
tests and audit/permission wiring would.

The preferred next micro-step is:

1. Add Flask-level tests for Safe Action auth/session/CSRF behavior if the test
   environment can support them.
2. Wire the DB adapter only inside a tested execute wrapper; do not let a future
   view query `IndiAllSkyDbNotificationTable` directly.
3. Only after Flask-level tests are available, consider a disabled-by-default
   execute endpoint skeleton.

## 9. Decision

Do not implement a real functioning execute endpoint yet.

Do not add a UI button yet.

Do not call `/ajax/notification`.

Keep the dry-run endpoint and service boundary as the active Modern foundation
until Flask integration tests, DB adapter endpoint wiring, audit wiring, and
endpoint response mapping are in place.
