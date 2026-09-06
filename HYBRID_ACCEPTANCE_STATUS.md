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
The first ordinary-user browser attempt hit navigation/focus timeouts after
the SSH tunnel failed. Restarting the isolated server with its own log and
restoring the tunnel resolved it: ordinary-user acknowledgement and persistence
after reload subsequently passed in the browser as well. Production services
were checked and remained active. The new inventory still finds nine
parameter-free pages with Classic URL BuildErrors (media, generation, YouTube).
Parameterized routes and all other control states remain subject to the full
acceptance matrix. Classic removal and live validation remain open.


## Verified mission: interactive camera simulator

The disabled Hybrid simulator has been replaced with its real lens/sensor
selectors, pixel offsets, image-circle canvas and shareable link. It has its
own Hybrid view/template; it no longer inherits the old simulator view or uses
the generic disabled-controls template. All 25 lenses and 60 sensors retain
their original constants. The drawing parity test compares 3,000 lens/sensor/
offset cases against a frozen pre-migration drawing routine. Full Config and
other existing parity fingerprints remain unchanged; the simulator template
registration change is explicitly checked before normalizing the old route hash.

The form rejects invalid lens/sensor query values and non-integer offsets with
400 rather than an unhandled conversion. Browser input errors have visible
feedback. The current link retains camera/profile and simulator parameters;
reloading it recreates the result. Native fields, a real Copy button, an external
text summary and stacked narrow controls replace the disabled wrapper. On
narrow screens metadata labels are shown below the canvas to avoid collisions;
image-circle geometry is unchanged. The simulator writes no settings or tasks.

`hybrid_camera_simulator_flow_test.py` verifies controls, catalog coverage,
both user roles, IMX708/IMX678 and invalid requests in Flask with Classic absent.
`hybrid_camera_simulator_parity_test.js` verifies catalog and drawing parity.
Browser results are in `testing/evidence/hybrid-simulator-2026-09-06.json`.


## Verified mission: FITS/RAW source access and media interactions

Baseline `15ebbbe0`. FITS Inspection, FITS Detail and RAW Source render without
Classic links and provide original downloads through a new Hybrid handler.
Downloads resolve a database record scoped to its camera, enforce that camera's
local/remote storage policy, support the configured separate RAW export folder,
and reject paths/symlinks outside configured media roots. Local responses are
private binary attachments with range support. Remote originals redirect only
to a recorded HTTP(S) location; no server-side remote fetch is introduced.

FITS preview keeps the existing ImageProcessor algorithm. Missing/invalid IDs,
missing files and malformed headers now have explicit 400/404/422 responses;
local previews obey storage policy. The metadata reader closes its FITS handle
even when a header conversion fails. Its valid output/defaults are unchanged.

Actual clicks found and corrected a shared media defect: the Gallery script
intercepted camera links on FITS/Image viewer pages even when no Gallery grid
existed. Only AJAX Gallery now intercepts its ordinary clicks; other pages and
modified clicks retain native navigation. Lightbox keyboard focus, return focus,
missing-preview feedback, filename caption and narrow-screen controls are fixed.
The caption now sits below the image, preserving visibility of small originals.
Source download actions appear near the table ID with a continuous hit area.

`hybrid_source_media_flow_test.py` uses two real synthetic FITS and 16-bit PNG
exports: both roles/cameras, exact download bytes, unchanged FITS after JPEG
conversion, 64x48 JPEG dimensions, byte ranges, anonymous redirects, camera-ID
mismatch, missing original, invalid header, configured external export folder,
outside path/symlink rejection, permission failure and remote policy. No task
or config revision is created. `hybrid_media_browser_test.js` guards the camera
link interception and prevents trying to display FITS originals as images.

Browser evidence: `testing/evidence/hybrid-source-media-2026-09-06.json`.
The first RAW semantic clicks were inconclusive; after inspecting the wrapped
link and making its hit area continuous, semantic download events passed for
both cameras, including 390x844. Native mobile filtering, FITS preview, lightbox
navigation and scope-preserving links were observed directly. Browser admin
coverage and production storage remain open; Flask role coverage is not
substituted for browser coverage. Full Book 2, existing JS regressions and all
six isolated Flask startup/account/Settings/operations/simulator/media suites
pass. No throughput or memory optimization is claimed from these small fixtures.

The source lists still have their existing recent-item limits; complete archive
traversal and the remaining media actions are not declared finished. Classic,
production deployment and the 24-hour day/night validation remain open.

Post-mission discovery still contains 89 template routes and 316 parameter-free
role/camera contexts: 198 successful renders, 21 defective renders across seven
page families, and 97 redirects/blocked contexts. The 14,378 discovered control
occurrences are not click passes. Remaining render failures are generated media
(keograms, mini timelapses, panoramas, startrail images/videos), generation and
YouTube; parameterized routes need their separate fixtures and evidence.


## Verified mission: native Hybrid generation workflow

Baseline `dbd5893f`. Generate no longer inherits the old page class or renders
the generic disabled-controls wrapper. It has a native Hybrid form and reads
real available dates and recent camera-scoped tasks. All ten existing action
choices are retained, including individual/combined generation, individual/
combined output deletion, source-image deletion and end-of-night upload.
Existing action names, valid payloads, queue policy and FISH2PANO gate are kept.
Task links expose the actual queued record; the page does not claim an encoded
file merely because a task was submitted. Its 12-hour read window uses UTC
consistent with task timestamps.

The controller requires an explicit action and confirmation, invalidates the
confirmation on scope changes, prevents concurrent submits, explains destructive
and upload semantics, and retains uncertain/failed outcomes for inspection.
Non-admin forms are disabled with a reason; the existing server role and admin-
network restrictions remain enforced. Invalid JSON/camera requests return
controlled 400/404 responses. Database/filesystem failures roll back pending DB
state and report a potentially partial operation without leaking backend details.
The route's legacy valid action behavior is not rewritten.

`hybrid_generation_flow_test.py` passes in Flask without Classic: both roles/
cameras, missing CSRF, invalid payload/camera/date/action, anonymous access,
network gate, exact generation task payloads/order/priority/state, panorama gate,
end-of-night queue intent, failed commit rollback, and every individual/combined
deletion using only dedicated fixture markers and synthetic JPEG sources.
Camera-1 records/files survive camera-2 deletions. These deletion tests are real
filesystem/DB effects in a temporary directory; they are not browser or live
production-media deletion tests. Encoding and actual remote upload remain open.

Browser evidence is in `testing/evidence/hybrid-generation-2026-09-06.json`.
It records ordinary-user restrictions, admin submissions, confirmation reset,
actual task IDs/payloads, camera filtering and Generate All on a 390x844 viewport.
The mobile form initially overflowed to 424px; bounded native select widths and
a responsive grid reduced document width to the 390px viewport. Task tables
reuse the already-tested operations controller for sorting, paging and exports.
All Book 2/JS regressions and seven isolated Flask suites pass. No execution-
throughput improvement is claimed. A stale login-required flash seen after
sign-in remains an identified shared-auth UI defect for the subsequent pass.


## Verified correction: stale login-required message

The browser generation test exposed a login-required flash that survived the
login form and appeared later on an authenticated task detail. The native login
template now displays/consumes pending flash messages, with normal template
escaping. The authenticated flow test confirms the notice appears before login
and is absent after successful authentication. A browser logout/login/task-detail
sequence reproduced and verified the correction. This changes no credentials,
permissions, sessions or redirects. The full Book 2/shell/route regression passes.


## Verified mission: generated media and native mini timelapses

Five generated-media pages now render with Classic disabled: keograms,
startrails, startrail videos, mini timelapses and panorama images. Their original
files are downloadable by database record and camera, including records outside
the 12 preview cards. The Hybrid download handler also supports ordinary images,
full timelapses and panorama videos. Existing root confinement, remote-URL
validation, authentication, range responses and private caching apply to every
kind. Generated previews now use the owning camera's access policy and S3 prefix,
fixing cross-camera policy selection in an all-camera listing. Image detail now
links to its original and to a native mini generator centred on that image.

The mini generator owns source selection, full-interval preview, validation and
queue submission through `mini_generation.py`; the compatibility POST delegates
to it. Existing worker payload keys, priority and queue/state are unchanged.
Invalid or missing image/camera data return controlled errors; failed commits
roll back. The supported interval is 0–12 hours on either side; frame rate is
validated against the existing UI's 0.25–25 FPS range, and notes are bounded by
the database's 255-character capacity. The old default-image ID zero bug and
four-hour preview truncation are corrected. Preview uses the worker's inclusive
bounds and excluded-record rule, reports the full count and an explicit 1,000-
record preview cap. Missing files can still reduce the encoded output, which is
stated next to the estimate. No acquisition or scientific algorithm changed.

Browser evidence in `testing/evidence/hybrid-generated-media-2026-09-06.json`
covers both camera selections, exact task payloads, optional description,
confirmation, ordinary-user restrictions, preview playback/fullscreen, mobile
width, all five pages' filters, and original downloads. Synthetic MP4 files are
real decodable clips; they do not establish live capture-worker correctness.
Individual footer/Open clicks not exercised are explicitly marked blocked.

Nine real Flask suites pass with isolated data, including new generated-media
and mini-generation coverage. Full Book 2, existing route fingerprints and all
JavaScript controller suites pass. Discovery now covers 90 template routes and
320 parameter-free role/camera contexts: 219 render successfully, 3 fail (the
YouTube page still references Classic config), and 98 are blocked. It enumerates
15,758 control occurrences; rendering alone does not pass these interactions.
Dynamic detail routes still require their dedicated fixtures.

Still open: browsing older records beyond the existing 100-row limits, complete
player/context controls across every media type, YouTube/integrations, remaining
operational tools, product placeholders, physical Classic removal, production
deploy/rollback verification, and the minimum 24-hour day/night acceptance run.
No performance improvement or complete product acceptance is claimed.
