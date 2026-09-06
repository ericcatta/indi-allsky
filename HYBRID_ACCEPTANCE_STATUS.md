# Hybrid acceptance status

## Completion gate

The complete product audit is **open**. Detector/AI are deferred; their absence
must be represented honestly. Classic has not been removed and these changes
have not been deployed to the live Raspberry checkout. A 24-hour product
validation has not started.

## Verified mission: authenticated Hybrid navigation and account

Baseline: `6b80191f`. Real Flask reproduction found `BuildError` on successful
login with Classic disabled: the response required `indi_allsky.index_view`.
Authenticated page context also required the Classic `user_view` endpoint.

Corrections:
- Login and logout land on Hybrid Now.
- My Account has a native Hybrid route/form and uses the existing account-save
  endpoint. Navigation exposes sign-in, account and sign-out appropriately.
- Account edits preserve username/email/role restrictions; name and password
  changes still require the current password. Returned user labels are escaped.
- Login fits narrow screens, prevents duplicate submission, and displays
  unexpected/non-JSON failures safely.

Evidence:
- `testing/hybrid_authenticated_flow_test.py`: real login, authenticated page
  rendering, name persistence, password change and subsequent login, rejected
  incorrect passwords, mismatched passwords, missing CSRF, ordinary-user
  privilege isolation and anonymous access. Synthetic users/configuration,
  two cameras, in-memory database, Classic import prohibited.
- `testing/hybrid_account_browser_test.js`: controller request contract,
  duplicate submission, failed/expired/network responses, clearing passwords
  only after success. This is a controller test, **not a browser click test**.
- Classic shell and existing route fingerprints retained. The Hybrid shell
  baseline is updated for its accessible navigation button and controller; the
  account navigation and additional route are explicitly tested separately.

## Initial runtime discovery: gaps remain

`testing/hybrid_ui_acceptance_test.py` derives template routes from registration
and requests them through real authenticated test sessions. Hardware bus and
external process calls are blocked. It never touches production data.

Initial discovery after the authentication fix:
- 89 template routes; 79 parameter-free routes requested in four contexts
  (admin/camera 1, admin/camera 2, ordinary user/camera 1, anonymous/camera 1).
- 316 contexts: 159 render successfully, 63 fail, 94 are blocked or redirect.
- 11,660 control occurrences discovered across rendered contexts. These are
  **not unique features and not successful interactions**.
- 10 parameterized routes need dedicated detail fixtures.
- 21 pages fail: ten Settings contract pages hit a Jinja dictionary/method
  collision; remaining failures include legacy route links in media, task,
  notification, generation and integration surfaces.

Every discovered control starts `bloccato` until its interaction and effect
are explicitly tested. The JSON contains route, stable control identifier,
role, camera, form method/action, link, disabled state and evidence slots.
Input values are excluded. Dynamic browser-created controls and all detail
states must supplement this discovery before a coverage claim is possible.

Run explicitly, outside the production checkout:

```
python testing/hybrid_ui_acceptance_test.py --output /tmp/hybrid-controls.json
python testing/hybrid_authenticated_flow_test.py
node testing/hybrid_account_browser_test.js
```

## Verified mission: Settings rendering and persistence

- Fixed ten contract pages: Jinja's `section.keys` resolved the dictionary method
  instead of the `keys` collection. Explicit dictionary indexing preserves the
  contract shape and displayed content.
- `/modern-admin/system/config` now redirects to the working Full Settings
  editor, retaining camera/profile query values. The contradictory disabled
  editor has been removed; the entry URL remains supported.
- Full Settings controller is separate from the template; duplicate submission
  and expired/unreadable responses are covered. Non-admin users receive a
  disabled form and a clear explanation; server permissions remain enforced.
- Removed redundant native-validation diagnostics from the controller. Form
  submission already used `novalidate`; server-side validation remains authoritative.

Evidence: `testing/hybrid_settings_flow_test.py` uses actual rendered form
values and Flask HTTP requests to save, download and restore with Classic
absent. It verifies new revision persistence, unchanged older revisions,
unchanged two-camera profile dictionaries (including extension keys), no reload
task when disabled, and rejection of invalid values, empty/oversize/malformed
restore files, missing CSRF and ordinary-user writes. No operational config,
security keys, live database or capture service are modified by this test.

`testing/hybrid_full_settings_browser_test.js` covers the controller's payload,
checkbox values, filtering, duplicate submit, permissions, field errors,
network failures, session expiry and invalid responses. Browser save and restore now also pass against the isolated app (see below).
Live save/restore and the complete camera-profile editor matrix remain open.

## Remaining gates

Complete Settings, media, operational tools and all supported effects; replace
static product panels with real data or explicit capability states; execute
actual browser paths and hardware/integration checks. Test destructive actions
only on dedicated new fixtures. Arrange physical presence for connectivity
and device interruption tests. Keep migration and physical Classic removal in
separate commits, then repeat essential tests and the required day/night soak.


## Verified mission: browser navigation, mobile login and restore

Actual in-app browser tests on 2026-09-06 used `hybrid_browser_sandbox.py`
on the Raspberry's installed Python environment, forwarded over SSH to
localhost. This is a separate worktree with Classic disabled, synthetic users,
two synthetic camera profiles and an in-memory database. External processes,
DBus, security-key resets and history purge are blocked. These results do not
claim validation of production effects or real camera acquisition.

Browser defects corrected:
- Navigation was a label without native keyboard-button behavior and persisted
  open across page changes. It now uses a button, Escape/return focus, explicit
  expanded state and an inert closed drawer; navigation closes after selection.
- Mobile login had low-contrast labels and misaligned Bootstrap columns. A
  dedicated Hybrid card fits the inspected 390 × 844 viewport, with visible
  focus and appropriately sized fields and submit button.
- Full Settings now links directly to history and restore. History revision IDs
  open snapshot details; stale claims that restore requires Classic are removed.

Observed browser outcomes are recorded in
`testing/evidence/hybrid-browser-2026-09-06.json`. They include invalid-login
feedback and successful retry, sign-out, account-name persistence after reload,
Settings filtering and saved-value persistence, ordinary-user read-only state,
menu keyboard behavior, history filtering/details, download event, file chooser
upload, successful restore, a new history revision and the restored OWNER value
in Full Settings. No password was changed through the browser.

The download event proves browser initiation; the complete downloaded payload
is verified by the separate Flask persistence test. The browser restore file
was generated independently from the synthetic fixture, not taken from live
configuration. Full Config parity fingerprints remain unchanged. No performance
improvement is claimed from these usability changes.


## Verified mission: task and notification workflows

Baseline `20731758`. Task/notification list and detail templates contained
Classic links that raised BuildError when Classic was disabled. These links
are replaced with working Hybrid navigation. Notification detail now permits
acknowledgement through a Hybrid command handler and the existing domain
service. Every authenticated user retains the old modal's permission; notices
are explicitly system-wide. Missing IDs, CSRF failures, duplicate requests and
failed effects are tested; failures roll back the session and expose sanitized
messages. The notification record remains present.

Task and notification tables retain sorting, pagination, Copy, CSV and Excel
capabilities using the bundled DataTables library. Task rows beyond the former
200-row display cut are accessible; the existing three-day queue policy is
unchanged. Both lists share a small controller. No query speedup is claimed.

Browser blob exports produced no observable download in the in-app browser.
CSV and XLSX now use a bounded Hybrid attachment response instead, preserving
the currently filtered/sorted columns and rows. Both browser download events
then passed. The exporter uses in-memory CSV/ZIP/XML, no optional package or
temporary filesystem, escapes CSV formulas and writes Excel cells as strings.
Content, malformed input, size bounds, CSRF and authenticated access are tested.

`hybrid_operations_flow_test.py` covers both roles/cameras, 205 task records,
detail redaction, missing records, acknowledgement persistence/idempotency,
effect failure and CSV/XLSX payloads against actual Flask with Classic absent.
`hybrid_notification_ack_browser_test.js` tests pending/error/session-expiry
controller behavior. `hybrid_table_export_test.py` checks actual CSV and workbook
contents. The full Book 2 regression, shell/route checks and existing runtime
login/Settings/startup tests pass after the changes.

Actual browser results are in `testing/evidence/hybrid-operations-2026-09-06.json`.
A later attempt to repeat acknowledgement as the ordinary user hit CDP navigation
and focus-command timeouts; that browser-only case remains blocked, although
the real Flask ordinary-user case passes. The new inventory still finds nine
parameter-free pages with Classic URL BuildErrors (media, generation, YouTube).
Parameterized routes and all other control states remain subject to the full
acceptance matrix. Classic removal and live validation remain open.
