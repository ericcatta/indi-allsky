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


## Verified mission: complete media archive

Hybrid now exposes a complete archive for all ten media types, linked from the
recent views. Queries apply camera/profile, capture-day range, filename,
day/night and upload filters to the full dataset. Newest/oldest ordering uses
creation timestamp plus ID. Next/previous cursors paginate 48 records at a time;
changing filters restarts navigation. Preview, original downloads, image/FITS/
video detail and image-centred mini generation remain available for old records.
Video detail no longer requires a Classic viewer endpoint. Gallery updates its
archive link after an AJAX camera switch. Database failures have an explicit
error state rather than masquerading as an empty archive.

`hybrid_archive_flow_test.py` verifies both roles/cameras, all ten types and
original downloads, 111 image records across three pages, both ordering
directions, exact forward/backward traversal, inclusive capture-day filters,
literal wildcard searches, invalid/mismatched scope, anonymous access, provider
failure, deleted cursor anchors, newly arriving records and remote camera policy.
All ten isolated Flask suites, Book 2, original route fingerprints, shell and
existing JS controller suites pass. No config, driver, worker or capture change.

Browser evidence: `testing/evidence/hybrid-archive-2026-09-06.json`. The browser
fixture adds two preview frames, so its camera-1 archive has 113 records. It
reached record 100 beyond the old 100-row limit, downloaded it, inspected detail
and selected it for mini generation. All type/camera/filter controls, pagination,
keyboard submission, empty/reset states, desktop/mobile widths and Gallery
scope preservation were exercised. FITS and RAW previews decoded successfully.
A temporarily moved synthetic JPEG produced an explicit preview failure and
404 original download; restoration recovered the preview. A previously cached
image can remain visible after local-file loss, as expected from browser caching.

The earlier "older than 100 rows" access gap is closed through this archive.
Remaining gates include live production workload/performance, complete media
mutation/player coverage, operational tools, integrations/product placeholders,
physical Classic removal and the minimum 24-hour post-deployment acceptance run.
The overall product audit remains open.


## Verified mission: public media compatibility without Classic

Existing latest/view/watch URLs remain registered. Their lookup, file access and
viewer implementations now live behind independent Hybrid handlers in
`public_media.py`. Nine viewers use an independent public Hybrid template rather
than Classic's base/navigation. Public originals support configured media roots,
including RAW export outside the usual image folder, with scoped record lookup,
range responses and controlled file errors. FITS are deliberately not added to
the public-media surface; their authenticated Hybrid access remains unchanged.

Corrected defects include absent records causing 500 responses, invalid parameter
conversions, the incompatible latest-thumbnail method signature, and camera
policy being taken from unrelated session context. Thumbnail lookup verifies the
owning camera; latest video ordering has deterministic creation/ID tie-breaks.
Public latest redirects retain their existing public role. Viewers/originals
respect both existing optional-auth flags and owning-camera local/remote policy.
Remote-only cameras without a remote URL receive 404 rather than a local fallback.
No public URL, scientific file or capture-worker algorithm was removed.

`hybrid_public_media_flow_test.py` passes for 17 latest endpoints, nine viewers,
both cameras, anonymous/ordinary/admin sessions, both optional-auth flags,
original/range responses, separate RAW export, empty selections, invalid inputs
and remote policy. It forbids loading Classic view/template files. Full Book 2,
route fingerprints, shell, all JS controller suites and 11 isolated Flask suites
pass. The registration fingerprint normalizes only explicitly checked template
migrations; original URL/class registrations remain guarded.

Browser evidence: `testing/evidence/hybrid-public-media-2026-09-06.json`. It covers
anonymous image/video viewing, correct redirects/camera captions, thumbnail,
copy/download/fullscreen, explicit missing/invalid states and mobile playback.
A 64px fixture video initially hid native playback controls; the corrected player
measures 358px within a 390px viewport and was played through its full 2-second clip.
Contrast and buttons now match Hybrid. These are fixture-level rendering and
playback measurements, not production performance results.

Classic removal, OAuth/integrations, remaining operational controls/product
placeholders, production deployment and the 24-hour acceptance period are still
open. The old public template files are left for the separate verified cleanup.

## Verified mission: native YouTube authorization

- The YouTube page now provides account connection, explicit refresh and confirmed
  revocation through the existing OAuth URLs. Admin-only POST forms use CSRF;
  old GET bookmarks safely return to the Hybrid page. The callback checks the
  initiating user, state, PKCE verifier and ten-minute lifetime and consumes the
  pending request. Google denial keeps existing credentials.
- Fixed manual refresh: existing credential payloads do not store expiry, so
  testing `credentials.expired` prevented the requested refresh. Explicit refresh
  now uses the refresh token, preserving the worker payload and encrypted store.
- Token exchange/refresh/revoke have bounded transport timeouts. Failed effects
  retain authorization; storage failures roll back and return controlled errors.
  Revocation sends its token in the request body and removes local credentials
  only after Google confirms success. Tokens/secrets are not rendered or logged.
- Optional Google modules are absent in the production Python environment. The
  page explains this and disables OAuth controls with accessible reasons. An
  isolated OAuth venv was created for tests; production dependencies are unchanged.
- Native Full Settings link filters all YouTube fields across their existing
  groups. Fixed the page's mobile overflow (785 px content at 390 px viewport;
  now 390 px), added its visible heading, and verified desktop at 1280 px.

Evidence: `testing/hybrid_youtube_flow_test.py` uses real Flask auth/CSRF,
configuration and encrypted SQLite state with Classic imports forbidden; **Google
responses are mocked**, not live verification. Cases include admin/ordinary/
anonymous sessions, missing modules/files/credentials, malformed and expired
callbacks, duplicate callback, denied access, absent offline grant, refresh,
revoke, transport failures and database rollback. Controller tests cover revoke
cancellation and duplicate submission. Full Book 2, ten browser-controller tests,
eleven existing Flask/startup suites and the new OAuth suite pass.

Actual browser evidence: `testing/evidence/hybrid-youtube-2026-09-06.json`.
Google account consent, live refresh/revoke and uploads remain **blocked pending
an available test integration**; no external account was connected or changed.
Installation/rollback notes: `HYBRID_YOUTUBE_OPERATIONS.md`.

Inventory refresh after this mission: 91 discovered Hybrid template routes,
324 role/camera contexts, 225 successful renders, 99 blocked/redirected contexts,
**zero rendering defects**, 16,178 discovered control instances. These are
rendering/inventory counts, not 16,178 completed interaction tests. Parameterized
routes and real provider/effect prerequisites still need dedicated acceptance;
public viewers have their separate tests and evidence.

## Verified mission: interactive Image Circle Helper

- Replaced the disabled reference wrapper with native Hybrid camera/image
  selection, editable diameter/offsets, line color/width, keogram/azimuth angles,
  fit/reset, clipboard, fullscreen and an explicit route to review Settings.
  Historical images are selectable by ID; unavailable previews have a visible
  reason. Media policy comes from the owning camera through Hybrid media access.
- Geometry drafts populate only three existing lens fields. Opening the draft
  does not save anything. Existing Camera Settings or Full Settings performs the
  reviewed save using existing permissions, CSRF, revision and reload behavior.
  Camera profile routing is checked and the other profile remains unchanged.
- The original helper did not save geometry; its Hybrid replacement now supports
  a review/save path without creating a second configuration writer. Keogram
  angle has a separate link to its existing Full Settings field.
- Fixed the old azimuth update order and unbounded `tan(90°)` line endpoints.
  Circle center, offset signs and line orientation are preserved in 480 math
  cases. The renderer uses screen resolution for crisp overlays on small source
  images; source files and scientific image processing algorithms are untouched.
- Browser testing found Camera Settings save/sync buttons enabled for ordinary
  users despite backend rejection. All eight buttons now reflect the actual
  permission and reference an accessible explanation. Backend permissions remain
  enforced and tested.

Evidence: `testing/hybrid_geometry_flow_test.py` exercises real Flask/database
profile/global saves, unchanged foreign profile and extension keys, no automatic
reload task, CSRF/roles, invalid drafts, missing image and owner-camera policy.
`testing/hybrid_geometry_math_test.js` covers 480 geometric cases. Full Book 2,
ten browser-controller suites, twelve Flask/startup suites plus isolated OAuth
suite pass. No production settings, capture services or acquired media changed.

Actual browser evidence: `testing/evidence/hybrid-geometry-2026-09-06.json`.
The admin saved profile2 geometry 320/-25/35 and the values persisted on a fresh
GET after the browser connection was interrupted; profile1 overrides stayed
empty. The source image fixture remained available after the missing-file test.
Production geometry changes and their capture/reload effects remain outside this
isolated mission and require the planned live acceptance.


## Verified mission: native Process FITS

Hybrid now owns the processing form, parameter interpretation, source validation,
preview response and native controls. The existing image processor remains a
shared backend. The old view wrapper only composes the shared form; Hybrid no
longer inherits it or uses the disabled generic tool template.

Extracted 144 preview input assignments and 46 scientific stage calls with
pre-extraction fingerprints. These are preview parameters, not additional Full
Config migration counts. Default form values and scientific call order remain
unchanged. Output choices now produce genuine JPEG/PNG; previews deep-copy nested
settings and close owned FITS resources even when processing fails. Source reads
follow camera ownership/media policy and confined media/export roots. Ordinary
users cannot select arbitrary server-side text, mask or font files.

Stack selection excludes the current frame explicitly (SQLite's second-only
server timestamps could otherwise compare before their own bound microsecond
representation). Messages report the actual available frame count. Dark/BPM
stacking cannot silently mix light frames. No source files, config revisions or
worker tasks are changed by previews.

Tests: full Book 2, native route/shell checks, original pixel parity for two
cameras and two roles, true binary PNG, dark/BPM, insufficient/available stack,
CSRF, missing/corrupt files, DB failures, owner-camera media policy, configuration
identity/isolation and resource closure. All twelve existing/new Flask domain
suites plus startup checks pass; the FITS controller test covers duplicate
requests, filter/reset, visible validation and session/error recovery.

Browser evidence: `testing/evidence/hybrid-fits-processing-2026-09-06.json`.
Actual previews, both cameras, search/validation/reset, fullscreen/exit, empty
dark state, archive navigation, anonymous redirect and mobile390px checked.
The data-URL download event was not confirmed by the browser tool, so device-side
receipt remains blocked rather than passed. Production FITS UI deployment and
full-resolution live acceptance are still open. The urgent runtime recovery
record is separate: `HYBRID_IMX708_STRETCH_RECOVERY.md`.

## Verified correction: runtime controls on native tool and media pages

The shared Hybrid context now supplies the existing runtime providers and Safe
Action URLs to native media, task, notification, account and tool pages. These
pages previously rendered a missing-context Unknown badge and disabled controls,
although the same controls worked on Product pages. No effect implementation or
permission policy changed. The shell now reflects admin-only recovery permission
with disabled controls and an accessible explanation for ordinary users, and
ignores clicks on disabled/pending controls.

`testing/hybrid_runtime_shell_flow_test.py` passes on the Raspberry with temporary
DB and Classic imports forbidden: eight pages, admin/ordinary users, exactly one
service-status read per page, both camera/profile abort targets, running/unknown
provider states and anonymous redirect. The 17 Book 2/shell entrypoints and the
archive, operations and FITS Flask suites pass. Only the intentionally changed
Hybrid shell DOM fingerprints were updated; Classic and Full Config fingerprints
are unchanged.

Browser acceptance on localhost sandbox 2026-09-06: archive admin shows all six
recovery buttons enabled; ordinary user shows all six disabled with permission
explanation on Now and archive. Start opens its correct confirmation. The browser
interrupted that modal interaction and no submitted effect was verified: this
is not evidence of service start or failed-effect recovery. The sandbox blocks
subprocess effects, so its Unknown status is legitimate. Running status is
covered by the injected-provider Flask test, not a live service observation.
Production deployment and real recovery-effects acceptance remain open.

## Verified correction: Gallery isolation and complete pagination

Gallery, Images and the shared media selector now reject malformed/unknown camera
selections and mismatched camera/profile pairs instead of silently broadening the
query to all cameras. Gallery JSON pagination uses the same selection validation.
Local/remote policy, S3 prefixes and preview lookup use each record's owner camera,
not the camera stored in the user's session. A database query failure produces an
explicit unavailable state rather than a misleading empty archive.

Fixed Gallery's initial lookahead: query 73 records to detect continuation, render
only 72 and preserve the continuation flag. Previously rendering all 73 made the
72-item equality check false and hid Load more prematurely.

`testing/hybrid_gallery_isolation_flow_test.py` passes with Classic forbidden,
both roles, malformed/mismatched/absent selections, initial 72 cards, 111 fixture
records across two pages without overlap, both directions of session/owner policy
mismatch, owner S3 URL and injected database failures. Full 17-entrypoint Book 2
and shell regression passes with all fingerprints unchanged. Archive, FITS/RAW
and runtime shell Flask regressions pass on the Raspberry's isolated checkout.

Browser localhost sandbox, ordinary user, 2026-09-06: initial camera1 page showed
72 cards and Load more. Scrolling toward Load more triggered automatic loading
before the explicit click could resolve; observed 113 unique cards, end-of-archive
visible and Load more hidden. This proves automatic continuation, not a separate
manual-button click. Selecting Test Profile 2 displayed exactly IDs 2, 6, 5 with
camera filter 2. Production deployment and broader Gallery acceptance remain open.

## Verified prerequisite: focuser failure cleanup

The existing authenticated focuser effect now validates the JSON object, direction
and explicit movement angle before constructing a device. Previously arbitrary
directions could reach a driver and missing angles could select a form default.
Every successfully constructed focuser is released in a finally block, including
failed movement. A successful move followed by release failure returns the step
result and explicitly says movement completed; this avoids representing that
case as an unexecuted move. Combined movement/release failures preserve both
errors without exposing driver details in those responses.

`testing/hybrid_focuser_effect_flow_test.py` uses real Flask/CSRF and a mocked
hardware interface with Classic imports forbidden: input rejection, CSRF, network
and role rejection, success, four movement-error classes, release error and
combined failures. The complete 17-entrypoint Book 2/shell regression passes.
No physical focuser was moved. This is a prerequisite correction: native Focus
controls, multicamera preview isolation and real hardware acceptance remain open;
the existing disabled Hybrid movement controls have not been declared complete.

## Verified prerequisite: independent Focus measurement engine

Focus decoding, ROI selection, star counting, JPEG encoding and Laplacian score
now live outside Flask views in `indi_allsky/focus_preview.py`. The compatibility
endpoint delegates to that shared implementation. Valid crops retain the same
formulas, full-frame star detection and JPEG quality. Invalid zoom/offsets return
an explicit error instead of wrapping negative NumPy indices or passing an empty
crop to OpenCV. FITS reads close their HDU list and copy data before returning.

The captured pre-extraction class and its AST fingerprint are stored in
`testing/fixtures/focus_preview_legacy.json`. On the Raspberry,
`hybrid_focus_preview_parity_test.py` executes the captured legacy method and
compares the complete result to the new engine for 22 valid zoom/offset cases:
JPEG bytes, blur score, star count and focus mode all match. Invalid regions and
RGB FITS decoding/resource closure are checked separately.
`hybrid_focus_endpoint_flow_test.py` verifies actual Flask responses for both
roles, malformed inputs, missing files and anonymous redirect with Classic imports
forbidden. The full 17-entrypoint Book 2/shell regression passes unchanged.

The endpoint still uses the legacy latest file selection. Native Focus UI and
camera-specific live preview are explicitly unfinished; this extraction does not
claim those flows or hardware acceptance are complete. Production is unchanged.

## Native Focus page and camera-owned previews

Hybrid Focus no longer inherits FocusView or renders the disabled Safe Controls
wrapper. It provides camera selection, eight zoom choices, pixel offsets, reset,
manual/optional automatic refresh, bounded measurement history including region,
fullscreen controls and the existing configured focuser commands. The latter
remain admin/network gated and disabled when no device is configured; wording
states that the observatory focuser is global, not selected by the preview camera.

New authenticated `/modern-admin/tools/focus/preview` reads the selected camera's
saved frame under its own local-media policy and returns source, timestamp and
age alongside the existing measurement payload. With FOCUS_MODE enabled, the
shared latest file is used only for the known primary camera. Secondary live
focus requests return an explicit unavailable response rather than substituting
another camera. **Publishing a live secondary focus frame remains open**, as does
physical movement/recovery acceptance and production deployment.

Flask test `hybrid_native_focus_flow_test.py`: both roles/cameras, actual decoded
previews, invalid selection/ROI, local-media denial, primary-only live source,
cache prevention and device/network movement gates; Classic imports forbidden.
`hybrid_focus_browser_test.js`: duplicate requests, target camera, decoding,
errors, session expiration, disabled controls, CSRF and movement-completed/release
failure feedback. Existing focuser effect tests and Book 2 regression pass.
Original measurement fingerprints remain unchanged; route guard explicitly
accounts for the native template and new Hybrid endpoint.

Browser localhost sandbox, ordinary user, 2026-09-06: camera2 preview decoded
64x48; Low zoom decoded25x19 and added a history row. Offset9999 displayed an
explicit error and cleared the previous preview. Reset restored offset0/zoom2
and a decoded64px image. Choosing camera1 returned camera1 metadata and decoded
frame. Movement stayed disabled with its real permission explanation. Fullscreen
entry/exit were attempted but fullscreen state was not conclusively observed;
that browser acceptance remains open. No physical device or production setting
was changed. The final DOM wrapper/JSON-error wording edits were covered by
static/controller checks, not a second browser pass.

## Focus live publication for every camera

The worker's Focus branch now publishes the already encoded image atomically to
`focus-camera-<id>.<extension>` for every camera, including a non-primary camera
which does not update global latest. Each file replaces only that camera's prior
focus frame. No archive records or timelapse files are created in Focus mode.
The primary legacy latest behavior and worker return values remain unchanged.
Publication failures are logged, remove staging files and preserve the previous
focus frame without crashing the worker; the API still reports frame age.

Hybrid Focus reads the camera-specific file first. The old primary latest fallback
remains for a worker that has not yet been updated. A secondary with no published
file reports that state instead of showing the primary. This supersedes the
previous implementation limitation; **live production validation remains open**.

`focus_frames_test.py` executes the actual worker write_img method on synthetic
PNG frames for primary/non-primary cameras, verifies pixels and global latest,
replacement failure, cleanup and no crash on publication failure. The extended
native Focus Flask test decodes the secondary live response and verifies its
70x50 dimensions and pixel value120, distinct from the primary48x64 frame.
Both roles, owner-media policy and missing-source behavior remain covered.
Full Book 2/shell/route regression and the real NumPy/OpenCV multicamera processor
and stretch isolation tests pass. No production worker was restarted or deployed;
real 24-hour acceptance must cover the final deployed worker version.

## Native GPIO: observation separated from hardware commands

Hybrid GPIO no longer inherits ManualGpioView. That legacy GET instantiated three
output drivers, calling GPIO.setup even with disabled UI buttons. Hybrid now reads
configured BCM pin functions and output values without setup/output/cleanup.
Selecting BCM numbering changes only process-local numbering. Input/unconfigured
pins remain explicitly unknown; provider errors disable controls with a reason.

The native page offers explicit On/Off commands, confirmation with the physical
BCM number and manual state refresh. The existing POST endpoint remains
admin/CSRF protected and now validates the three allowed slots, configured pin,
supported RPi.GPIO class and boolean/0/1 state before constructing a driver.
Strings such as "false" are rejected rather than interpreted as true. Invalid
configuration and failed effects return useful messages. Successful commands
still leave the output latched: cleanup would reset it and is intentionally not
called. The UI labels the command-reported state separately from read observation.

`hybrid_gpio_flow_test.py` runs real Flask with Classic imports forbidden and a
mocked GPIO module/driver: both roles, GET never constructing drivers or calling
setup/output/cleanup, On/Off/unknown reads, invalid payloads, CSRF, slot-to-pin
mapping, provider failure and failed effects. `hybrid_gpio_browser_test.js` checks
confirmation/cancel, explicit Off, CSRF, duplicate prevention, session/error
feedback and retaining disabled controls. All 18 Book 2/shell/route entrypoints
pass, with existing fingerprints unchanged and native template accounted for.

No physical pins were read or changed by this mission's tests. Native-page browser
acceptance, real configured devices, production deployment and recovery remain
open pending the identified hardware/maintenance window. Classic's old GPIO page
is still present and must be removed with the final frontend removal.

## Native Drives and shared UDisks command ownership

Hybrid Drives no longer inherits DriveManagerView or its disabled wrapper.
`indi_allsky/drive_manager.py` owns discovery, target selection and validation;
Flask retains authentication, CSRF and response handling. The legacy action URL
and payload names remain. Metadata keeps its thirteen-row response contract.
Each service operation reads one UDisks managed-object snapshot instead of
repeating per-device property queries inside view methods.

The native page lists drives/filesystems, shows metadata, mount/unmount and power
off with admin permission, target-specific confirmation and unavailable reasons.
It requires refreshed inventory after mutation/error before another command.
Mount rejects any existing mount, fixing the old >1 check. Unmount checks every
mount point, not just the first, and protects configured image/export paths in
addition to existing system mount points. Power off requires every filesystem on
the drive to be unmounted. Unknown/ambiguous IDs and non-filesystem blocks fail
without executing effects. D-Bus failures produce a sanitized error.

`hybrid_drives_flow_test.py`: real Flask with Classic forbidden and a mutable fake
UDisks graph, inventory/metadata, mount/unmount/poweroff, one-mounted guard, second
protected mount, configured-media protection, missing inputs/IDs, both roles,
CSRF and provider failure. The fake graph records exact effects and updates mount
state. `hybrid_drives_browser_test.js`: controller confirmation/cancel, duplicate
prevention, metadata rendered as text, exact target/CSRF and fresh-inventory gate.
Full Book 2/shell/route regression passes; Full Config fingerprints unchanged.

No real disks were mounted, unmounted or powered off. Native browser acceptance,
physical storage/recovery and production deployment remain open. The necessary
hardware maintenance window has not yet been supplied. Network management remains
a separate unfinished domain; this mission does not claim to complete it.
