# Hybrid acceptance status

## Completion gate

The complete product audit is **open**. Detector/AI are deferred; their absence
must be represented honestly. Classic has not been removed. The shared capture
cadence mission, operational settings, rollback and live evidence locations are
recorded in [HYBRID_CAPTURE_CADENCE.md](HYBRID_CAPTURE_CADENCE.md).
Its protected `deployment.json` records the installed commit and service start;
`config-change.json` records the configuration revisions. A capture-affecting deployment or capture
restart requires a new 24-hour day/night observation, which has not passed.
The earlier `775a19d0` interval starting at 10:09:50 CEST must not be added to a
post-change interval. Historical sections below retain each mission's deployment
status at that time; they are not a statement of the currently installed version.

## Generated-output fixes deployed; live capture verified — 2026-09-08

Production runs `ca604649`: mini timelapse and EndOfNight dispatch, exact local
profile resolution, optional lens EXIF and the Keogram first-column correction
are installed. All 571 runtime files matched the candidate with 96 passing
regression entrypoints and real isolated generation/SFTP acceptance. The coherent
828,977,152-byte SQLite backup passed integrity checking; protected configuration,
manifest and rollback reside in `/home/eric/hybrid-backups/effects-20260908-174316`.
Configuration revision 110 and all pre-existing untracked user files were preserved.

Capture and Gunicorn restarted at 17:47:25 CEST, PIDs 3734524 and 3734527. At
17:50:19, cameras 1/2 had produced 10/11 nonempty files since deployment; latest
JPEGs decoded at 4608x2592 and 3840x2160. Request interval medians were 15.035s
and 15.030s (maxima 15.042s and 15.229s), with no errors or pending tasks in this
sample. Login returned HTTP 200; anonymous Now/Loop returned HTTP 302.
These HTTP checks do not replace authenticated browser acceptance.

Native browser verification is **blocked by the locked Mac**; automatic unlock
failed and the user was asked to unlock it. Production generation through the UI
and the exhaustive product audit remain open. Video/mini/EndOfNight uploads and
S3, Sync API and YouTube were disabled at the postcheck; no integrations were
enabled. Capture observation restarts at 17:47:25. Earlier periods are interrupted,
not cumulative. The updated 15-minute monitor stores evidence under
`/home/eric/hybrid-effects-evidence`; earliest possible 24-hour completion is
2026-09-09 17:47:25 only with complete day/night evidence.

Rollback for this exact release, after checking current state:

```sh
python3 /home/eric/hybrid-backups/effects-20260908-174316/deploy.py --rollback --backup /home/eric/hybrid-backups/effects-20260908-174316
```

The helper requires the expected release and clean tracked files, restores
`4b009133`, restarts capture/web and preserves user files/configuration and new
acquisitions. It does not restore the database over current data. Its saved
version now stops the Gunicorn activation socket too; the executed original is
retained as `deploy-executed.py`. The corrected helper compiled; rollback was
not executed. Any rollback requires a fresh observation window.
Evidence: `testing/evidence/hybrid-effects-deployment-2026-09-08.json`.

## Production preflight and profile identity resolution — 2026-09-08

Preflight confirmed production at `4b009133`, capture PID 3566586 since 12:01:07,
configuration revision 110, no pending tasks and 60 GiB available. EndOfNight
upload is disabled. All 571 runtime files initially matched the tested staging
candidate `4a928942`. Deployment paused before any service/configuration changes
because the real profiles have no explicit DB camera IDs: the earlier dispatch
policy would give their jobs neutral `default` metadata.

The coordinator now reads the local camera identity and passes it to the Hybrid
policy. Explicit ID bindings keep precedence; otherwise only an exact configured
camera name (including nested INDI names or a libcamera interface identity) with
one matching profile is used. No substring, row-order or remote-camera fallback
is allowed. Missing/ambiguous matches remain neutral. The policy has no database
or view dependency, and saved configuration is unchanged.

Read-only evaluation against actual revision 110 resolves camera 1 to
`imx708-wide` and camera 2 to `asi678mc`. The real coordinator test covers named
profiles and excludes remote-camera matching. The full request/worker/SFTP test
also passes without explicit IDs, including success/failure and duplicate tasks
for both cameras. All 96 regression entrypoints passed, including Book 2,
Full Config parity, Settings, Safe Actions and Product Spine/View Models. All
four source hashes match the tested candidate and `git diff --check` passed.
These are isolated effects; **production remains unchanged**.
See `testing/evidence/hybrid-profile-routing-2026-09-08.json`.

## EndOfNight request through actual SFTP delivery — 2026-09-08

The real Hybrid request was accepted but the multicamera coordinator expired it
as unsupported before reaching VideoWorker. Hybrid's camera-scoped policy now
admits `uploadAllskyEndOfNight`, retaining required camera scope and explicit
profile routing. Global actions and destructive-action restrictions are unchanged.

`hybrid_end_of_night_pipeline_loopback.py` reproduces the rejected baseline and
checks the corrected request -> coordinator -> VideoWorker -> upload queue ->
FileUploader -> real SFTP chain. Both cameras deliver byte-identical `data.json`
to separate disposable loopback folders with the installed SSH host key pinned.
Both also exercise a non-writable destination: the upload child is FAILED and
no destination file appears. Parent receipts link to the child and do not claim
confirmed delivery. Both roles can inspect outcomes; terminal duplicate delivery
cannot open a second SFTP connection. Existing `remove_local=True` cleanup
semantics are verified, and an unrelated disposable sentinel remains intact.

This uses an isolated in-memory database with Classic imports blocked and actual
worker methods called synchronously. It does not prove production scheduling or
an external integration. The test prompts privately for a loopback password and
is a separate manual acceptance entrypoint. All 96 regression entrypoints
passed, including Book 2, Full Config parity, Settings, Safe Actions and Product
Spine/View Models. The three source hashes match the tested candidate and
`git diff --check` passed. The policy fix is **not deployed**. Before deployment,
inspect configured destinations: the tested separation uses `{camera_uuid}`;
existing static destination/overwrite semantics have not been changed.
See `testing/evidence/hybrid-end-of-night-pipeline-2026-09-08.json`.

## Keogram and Startrail real effects — 2026-09-08

The real generation test exposed two backend defects. Nullable camera lens
metadata made EXIF serialization fail (Keogram lens name; Startrail name, focal
length or aperture). Unknown tags are now omitted; supplied values retain their
existing representation. Keogram also initialized an extra uninitialized column
before appending actual frames, introducing arbitrary pixels and an extra frame
in its width/count. It now starts with zero columns and appends each actual
sample exactly once. Rotation, trimming, scaling and Startrail combination stay
unchanged; no previously saved images or configuration are rewritten.

`hybrid_keogram_encoding_flow_test.py` checks exact pre-compression samples and
then submits real authenticated Hybrid requests through coordinator and worker,
with Classic imports blocked. Both cameras produce a Keogram, Startrail and
three-frame Startrail MP4. JPEG decoding, EXIF absent/present tags, per-camera
colors, three Keogram columns, FFprobe, complete task receipts, byte-identical
downloads for both roles and wrong-camera 404 responses are asserted. Uploads
are disabled and all media/database fixtures are disposable. Thresholds explicitly
admit the synthetic frames; this is not astronomical accuracy or live capture
acceptance. All 96 Python/compile regression entrypoints passed, including
Book 2, Full Config parity, Settings, Safe Actions and Product Spine/View Models.
The three tested source hashes match the local candidate; `git diff --check`
passed. The backend correction is **not yet deployed**. Evidence:
`testing/evidence/hybrid-keogram-encoding-2026-09-08.json`.

## Real timelapse effects and multicamera dispatch — 2026-09-08

The isolated end-to-end test exposed two coordinator defects: mini timelapses
were rejected in multicamera mode, and camera 2 jobs inherited camera 1's profile.
Hybrid now admits mini generation and resolves route metadata from explicit DB
camera bindings. Missing or ambiguous bindings retain neutral `default` metadata;
global and single-camera dispatch retain their existing behavior.

With Classic imports blocked, actual authenticated Flask requests, coordinator
methods, VideoWorker, FFmpeg and downloads produced four MP4s: normal and mini
timelapses for both cameras. FFprobe and decoded RGB frames verified H.264,
64x48, three frames at 10 FPS and camera-specific content. Administrator and
ordinary-user task views showed success; downloads matched the generated bytes,
and wrong-camera downloads returned 404. An intentional FFmpeg option failure
produced a FAILED task, no successful asset/file and no upload; all four prior
output hashes stayed unchanged.

All 95 regression entrypoints passed, including Book 2, Full Config parity,
Settings, Safe Actions, Product Spine/View Models and the real encoding flow.
The four changed source hashes match the isolated candidate; existing parser
fingerprints were not changed. `git diff --check` passed.

These effects ran on the Raspberry in an isolated SQLite/media fixture with
uploads disabled, not in the production queue. The coordinator fix is **not yet
deployed**. Its controlled deployment must verify capture recovery and start a
new observation window if capture restarts. External uploads, full-resolution
workloads and all remaining acceptance gates remain open. See
`testing/evidence/hybrid-real-encoding-2026-09-08.json`.

## UI corrections deployed and checked on the Raspberry — 2026-09-08

Production now runs `4b009133`: archive detail return context, optional Loop
measurements, responsive header and Loop playback controls are deployed. Before
release, all 571 runtime files matched the isolated candidate that passed 94
Python/compile entrypoints; 22 JavaScript entrypoints also passed locally.
A coherent 828,977,152-byte SQLite backup passed integrity checking. Protected
configuration, manifest, deployment record and rollback helper are stored at
`/home/eric/hybrid-backups/web-ui-20260908-131241`.

Only Gunicorn restarted, at 13:14:45 CEST (PID 3649890). Capture remained PID
3566586, started at 12:01:07 CEST, with zero restarts and revision 110 unchanged.
The postcheck spans the web deployment: 45 files per camera, none missing/empty,
latest JPEGs decoded at 4608x2592 and 3840x2160. Request-interval medians were
15.038s and 15.032s, with no capture errors in the checked window. This confirms
continuity across this web update; it does not complete the day/night acceptance.
The monitor retains the original capture window and records the new web commit.

Native production-browser checks confirm styled recovery controls, both Loop
image elements, filtered Library -> image 13101 -> Back to results with camera,
profile and search preserved, and recent frames for both cameras on Now.
A deployment defect was caught by visual inspection: the backup's restrictive
umask made Git's replacement CSS file unreadable to Apache. Only the published
tracked files were restored to readable 0644 permissions. The saved helper now
uses checkout umask 022 while protecting its private files explicitly; the styled
production page and CSS hash were rechecked. No acquisition data was deleted.
Evidence: `testing/evidence/hybrid-web-deployment-2026-09-08.json`.

Rollback for this exact release, after inspecting current repository state:

```sh
ssh eric@allsky-pi.local
python3 /home/eric/hybrid-backups/web-ui-20260908-131241/deploy.py --rollback --backup /home/eric/hybrid-backups/web-ui-20260908-131241
```

The helper requires the expected release and no tracked edits, restores the
previous code and restarts Gunicorn only. It preserves user files and never
restores the backup database over new acquisitions. A changed release must be
reviewed before using an older rollback helper. The complete audit, remaining
operational/hardware effects, Classic removal and 24-hour observation remain open.
Earlier mission sections below describe their status before this deployment.

## Loop playback controls and empty/error states — 2026-09-08

History changes previously waited for periodic polling; an empty response left
the previous image visible, and independent preload completions could display
frames out of order. History now reloads both selected cameras immediately and
ignores responses/preloads from superseded selections. Playback advances only
after image completion, keeps one timer per camera, and applies speed/bounce
changes immediately. Bounce preserves chronological playback and avoids repeated
endpoints. Empty or failed requests clear the image; failed frames report an error
and continue to the next frame. The existing periodic refresh can recover after
request failures. Labels now say Playback speed and Play back and forth.

The deterministic JavaScript test executes the actual template script with
controlled fetch/image/timer completions. It fails against the prior template and
passes the corrected history, speed, bounce, camera-isolation, stale-response,
empty/error and recovery cases. The reusable native-browser fixture observes
actual DOM image changes and fetch requests; it is for the isolated sandbox only.

Native checks measured simultaneous per-camera history requests at the control
change, 100–104ms frame changes at 10 FPS and 201–203ms at 5 FPS on cached synthetic
JPEGs. Both cameras bounce through their own three frames without duplicate
endpoints. A historical range without data hides both images and explicitly says
No frames in this time range. These are playback measurements, not camera capture
cadence or production throughput claims. Evidence:
`testing/evidence/hybrid-loop-controls-2026-09-08.json`.

All 94 Python/compile entrypoints pass on the final isolated Pi candidate; both
candidate template and JS test hashes match. All 22 deterministic JavaScript
entrypoints pass locally. These VM-based JS checks are separate from the native
browser observations above. `git diff --check` passes.

Production deployment and broader acceptance remain open. Capture, configuration,
media files and image-processing algorithms are unchanged; only the disposable
browser sandbox was restarted to refresh its fixtures.

## Responsive header correction — 2026-09-08

The header grid allowed the primary navigation column to collapse while runtime
controls exceeded their container. At 1280px links overlapped; smaller screens
hid abort/reboot controls behind an unmarked horizontal scroll area. The shell
now wraps navigation/action groups and individual recovery controls. Long profile
labels wrap within available width. All actions and permission gates remain;
CSS cache version is 007. Only the Hybrid shell asset-version fingerprints change;
Classic and Full Config baselines are unchanged. No ownership claim is made for
this layout correction.

The browser fixture measures real rendered header controls at nine widths from
320 to 1920px, in both themes with normal and long profile labels: 36/36 pass.
Visual inspection at 1280 and 390px confirms all controls are visible. Mobile
checks verify the theme toggle, menu opening/initial focus and Escape restoring
focus. The header becomes taller on narrow screens to keep all controls visible.

The 94-entrypoint isolated Pi regression initially passed 92 checks. Two template
scanners encountered AppleDouble metadata added by the macOS tar transfer. After
removing only those identified transfer files, both checks passed without source
changes. Candidate hashes match the tested source. Evidence and exact limits:
`testing/evidence/hybrid-header-layout-2026-09-08.json`. The reusable browser
fixture belongs under `testing/` and must only be served in the isolated sandbox.

This resolves the header layout defect recorded below in the candidate. Production
deployment, complete role/browser coverage and the overall acceptance remain open.
No acquisition service, configuration or data changed.

## Loop optional measurements and media browser checks — 2026-09-08

Synthetic multi-camera browser testing exposed a real API failure: nullable SQM
samples caused `max(jsqm_list)` to raise TypeError, leaving both Loop panels in
an error state. Hybrid now owns the pure measurement-summary calculation in
`loop_statistics.py`; the existing view retains its scoped query and delegates
aggregation. Invalid/non-finite samples are excluded. Valid numeric results,
missing-key fallbacks, panorama fallback and the public empty-summary shape are
preserved. Image algorithms, capture scheduling and saved configuration are unchanged.

All 94 Python/compile entrypoints pass in the isolated Pi environment; SHA256
checks confirm the three candidate source files match the tested files. Coverage
includes both camera/role combinations, mixed optional sensor data and actual
image-list availability. Native browser checks verified JPEG lightbox opening,
Right/Escape navigation and restored focus, selection/reset across cameras, a
saved and decoded JPEG download, both corrected Loop panels and FITS preview.
Evidence: `testing/evidence/hybrid-loop-statistics-2026-09-08.json`.

The header overlaps navigation/runtime controls at 1280x720: this is an open
layout defect. Loop FPS/Rock/history controls, original FITS download, full role/
viewport coverage and production acceptance remain open. These changes are not
yet deployed; capture was not restarted for this mission.

## Archive detail return context — 2026-09-08

A production browser interaction reproduced loss of Library filename filters:
searching a ZWO frame, opening its detail and using Back to Images switched to
the recent-images list. Detail links now carry their originating archive context.
Image, FITS, video and generated-output details offer Back to results when that
context names an allowed local Library/Media archive route. The helper rebuilds
only whitelisted query fields and rejects external paths, unknown parameters,
duplicates, fragments and control characters. Direct detail links retain their
existing fallback navigation. Media permissions and effects are unchanged.

All 93 Python/compile entrypoints pass in a new isolated Pi checkout, including
both archive entrypoints, camera/role combinations, query/cursor round trips and
untrusted return URLs. Native browser checks on synthetic data preserve a search
and the second page through detail/back navigation; Reset retains camera/profile.
Evidence: `testing/evidence/hybrid-archive-return-2026-09-08.json`.
This correction is not yet deployed; production capture remains unchanged.
The temporary sandbox is loopback-only at Pi port 8104/local tunnel 18104;
revalidate its process before future use. These checks are not the complete audit.

## Exposure hold correction deployed — 2026-09-08 12:01 CEST

Production now runs `a886a9d7`, configuration revision 110 unchanged. Capture
restarted at **2026-09-08 12:01:07 CEST**, PID 3566586. The prior observation
period is interrupted and does not count toward acceptance of this correction.
Backup `/home/eric/hybrid-backups/exposure-hold-20260908-115906` contains a
coherent 828,977,152-byte SQLite backup with integrity `ok`, protected Flask
configuration, deployment state and the deploy/rollback helper. Existing
untracked user files on the Pi were preserved. Only `image.py` changed at runtime.

Both cameras produced valid JPEGs after restart. Initial actual request gaps
were 15.034–15.040 seconds for IMX708 and 15.033–15.034 for ZWO, without capture
errors. Direct on-Pi decoding verified 4608×2592 and 3840×2160 output. A ZWO
Hybrid hold at 0.01669774 seconds/gain 0 was followed by matching capture
requests; no legacy exposure writes appeared in the sample. This does not yet
prove above-minimum gain reduction under live changing illumination.

The existing heartbeat now targets this baseline and retains request timestamps
across journal rotation. New evidence is in `/home/eric/hybrid-exposure-hold-evidence`;
local summary: `testing/evidence/hybrid-exposure-hold-deployment-2026-09-08.json`.
The earliest possible 24-hour completion is September 9 at 12:01:07 CEST,
conditional on complete evidence, day/night coverage and no new restart/change.
The complete product/Classic-removal gate remains open.

## Exposure pipeline regression and first resumed browser checks — 2026-09-08

The exact published `0bf4eb96` candidate was checked out in a new isolated Pi
clone. The full 93-entrypoint Python/compile suite passed 92 checks initially;
the legacy auto-gain fixture lacked the new Hybrid-enable predicate. Declaring
Hybrid disabled in that legacy-only fixture preserves all 40 on-grid parity
cases and off-grid checks. That test and both Hybrid controller/pipeline tests
then passed on the Pi. Runtime source was unchanged after the initial suite;
only this test fixture differs from the clean candidate. Evidence and source
hashes: `testing/evidence/hybrid-exposure-runtime-regression-2026-09-08.json`.
This closes the previously environment-blocked runtime regression, not deployment.

Native browser interaction is available again. Five controls were exercised on
production `0104b282`: Now refresh, camera-1 archive entry, image detail, camera
selection using keyboard, and applying the camera-2 filter. Updated timestamps,
matching record metadata and camera-specific results were observed after actions.
Evidence: `testing/evidence/hybrid-browser-media-2026-09-08.json`. These limited
checks do not replace the full inventory, role/mobile matrix, image decoding,
downloads or effect acceptance. No production settings/services/media changed.
The gain-first hold fix still requires backup, deploy and fresh day/night testing.

## User detail compact layout

The redundant three-card user summary is removed; ID, identity, active/staff/admin
flags, login date and configuration count remain in the metadata panel. The
duplicate Users link is removed. Administrators alone see a Password row explaining
that the original password cannot be retrieved: the application stores an Argon2
hash, not recoverable plaintext. No hash is rendered and storage is unchanged.

Isolated Flask checks passed for both viewer roles and both target users: all
metadata retained, the password explanation only for administrators and no stored
hash in HTML. Existing operations, shell and Product View Models checks passed;
diff checks passed. Native browser verification was blocked by the locked Mac.
This template change has not been deployed to production.

## Clean candidate regression — 6ca73bfe

A fresh `git archive` of `6ca73bfe8d2efe9d95314c14c22b26f90867dec6` was
transferred completely and its SHA256 verified before extraction. All 1,140
tracked files and symlink targets match the local manifest in both the local
JavaScript test copy and `/home/eric/hybrid-acceptance-6ca73bfe` on the Pi.
Neither directory contains earlier candidate overlays or extra files before tests.

All 88 Python/compile checks and 24 JavaScript checks pass on these clean copies.
The Python suite includes Flask startup with Classic enabled/disabled, isolated
Hybrid flows with Classic forbidden, Book 2, Full Config parity, Settings contracts,
Safe Actions, Product View Models/Spine and the recent correction tests. It uses
the installed runtime dependencies and the separate OAuth environment for YouTube.
After testing, tracked source still matches exactly; only 258 Python cache files
were added. The full UI inventory remains a separate discovery entrypoint.

These results consolidate previous overlay-based results without substituting for
browser interactions or real hardware/integration effects. Production remains
`775a19d0`: no deploy, service restart or acquisition-data deletion occurred.
Classic removal and the 24-hour day/night gate remain open. Evidence:
`testing/evidence/hybrid-release-6ca73bfe-2026-09-07.json`.

## Browser sandbox refreshed — 2026-09-07 12:05 CEST

Three obsolete browser acceptance processes were identified by their exact
command lines and checkout paths and terminated (3193471, 3207416, 3245270).
The verified `6ca73bfe` source now serves the isolated sandbox at remote loopback
127.0.0.1:8101, PID 3430143, through the local SSH tunnel 127.0.0.1:18102.
It uses only synthetic in-memory database/media and blocks external effects.
The optional upgrade state remains explicitly synthetic.

An HTTP readiness check through the tunnel logged in with the synthetic identity,
loaded Now, Camera Settings, Tasks and My Account, checked the updated processing
wording, and received sandbox HTTP 409 before a system command could execute.
The Python client explicitly allowed secure session cookies over this loopback
HTTP tunnel after the default cookie policy caused login rejection; no production
cookie configuration was weakened. This client check is not native browser or
click acceptance. The Mac remains unavailable until the user's return.

Production capture remained PID 3284487, active, NRestarts=0. No production
service or acquisition data was changed. The sandbox is ephemeral; recheck its
process and tunnel before relying on this address. Readiness details are in
`testing/evidence/hybrid-release-6ca73bfe-2026-09-07.json`.

## Clean candidate UI discovery — 6ca73bfe

The explicit inventory entrypoint was rerun on the clean candidate with synthetic
users/cameras and hardware/process execution blocked. It discovers 90 pages,
490 role/camera/detail contexts and 28,572 static control occurrences. Rendering
passes for 364 contexts; 126 remain blocked by access redirects or unavailable
providers. The detail verifier covers nine parameterized route families. There
are no render defects in this run and no matches for the known placeholder phrase
list. That phrase scan does not prove functionality or absence of all placeholders.

Every discovered control still has blocked interaction status and no click
evidence. JavaScript-generated controls, desktop/mobile layout, keyboard flows,
modals and observable effects require direct browser acceptance. The unchanged
counts versus prior discovery are not new interaction coverage. This refresh
binds the inventory to the verified clean candidate rather than an overlay tree.

Full matrix: `/home/eric/hybrid-release-evidence-6ca73bfe/ui-inventory.json`;
local copy: `/tmp/hybrid-ui-inventory-6ca73bfe.json`. Its hash and compact counts
are recorded in `testing/evidence/hybrid-release-6ca73bfe-2026-09-07.json`.
Generated full reports remain outside the repository; older inventories are unchanged.

## Verified correction: flush failure termination and partial results

The four system flush operations repeatedly fetched the first 500 matching rows.
When deleteAsset raised OSError, the row remained and the loop retried it forever.
An isolated real HTTP request reproduced a second attempt on the same denied file;
the test stopped that retry with a sentinel exception to avoid hanging the worker.

Hybrid now owns the shared batch progress/termination policy. Existing scoped
queries and per-asset filesystem/database effects remain unchanged. If a batch
reports fewer successful deletions than selected entries, cleanup stops before
another batch/category and returns HTTP 400 with form_global, deleted_count,
failed_count (current batch) and camera_id. Already committed deletions are not
rolled back or described as all-or-nothing. A deliberate retry after fixing the
file error can remove the remaining entries; an empty retry retains the existing
zero-deleted success response. Concurrent deletion/DB failures and crash recovery
are not made transactional by this change.

The isolated test exercises flush_images, flush_16min_images, flush_daytime and
flush_timelapses with actual synthetic files and SQLite records. It checks CSRF,
ordinary-user and admin-network rejection, partial progress, no repeated failing
file, preservation of the other camera, explicit retry and empty completion.
Each command uses a fresh process because the fixture forbids repeated Flask
initialization; the first candidate run reached that fixture guard after its
first command and was corrected without changing runtime behavior. Browser and
production failure acceptance remain open; no acquisition data were touched.
All 88 Python/compile checks pass, including Full Config parity and the complete
selected Book 2 regression. Diff checks pass. Evidence:
`testing/evidence/hybrid-cleanup-failure-2026-09-07.json`.

## Verified correction: Camera Settings processing descriptions

Camera Settings still called Hybrid an opt-in placeholder and exposure control a
future module, despite existing AutoExposureController/AutoGainController calls
in ImageWorker. It also described the configured mode as an active pipeline,
without evidence that capture had reloaded it. The page now identifies the
selected mode and explicitly requires save/restart before applying changes.
Exposure/gain point to Acquisition; stretch and color descriptions refer to
existing configured processing rather than suggesting their functionality is absent.
No new scientific controller, calibration algorithm or processing behavior is claimed.

AWB descriptions distinguish Classic behavior, selected capture/postprocess
application, measurement-only disabled application, and an unsupported interface.
Existing backend capabilities, option values, unavailable choices and save/sync
controls remain intact. This is a correction to product information, not a
replacement of any runtime adapter or proof that the configured backend is live.

The isolated Flask test checks administrator and ordinary-user pages for both
profiles across Classic, Hybrid auto, disabled and unsupported capture modes.
It verifies selected form values and unchanged configuration/task state. Browser
and production acceptance remain open; the change is not deployed.
All 87 Python/compile checks pass. The targeted rendered-page test also passes
after the final wording adjustment; diff checks pass. Evidence:
`testing/evidence/hybrid-processing-status-2026-09-07.json`.

## Live preliminary continuity check — 2026-09-07 11:27 CEST

Production remains at `775a19d0`, capture PID 3284487, active since 10:09:50,
with NRestarts=0. Read-only history inspection through 11:27:45 covers all 102
IMX708 and 310 ZWO image records since that start. Every associated file exists
and is nonempty. Maximum consecutive timestamp gaps are 46 seconds (IMX708)
and 16 seconds (ZWO); first frames were at 10:11:05 and 10:10:14 respectively.
This checks recorded cadence and file presence, not decoded image quality.

The 11:27:03 snapshot has no queued/running/manual tasks, ten successful periodic
tasks since deployment, all five aurora components available for both cameras,
and 81,334,702,080 free bytes. Journal error matches remain the six known startup
gain clamps. No services, settings or acquisition files were changed.

All observed images are daytime. This roughly 78-minute preliminary check does
not pass the 24-hour day/night gate, UI acceptance or the final Classic removal
gate. Candidate corrections after `775a19d0` are still not deployed. Evidence:
`testing/evidence/hybrid-capture-continuity-2026-09-07.json`.

## Verified correction: browser-ambiguous login return URLs

The installed URL validator treated embedded ASCII controls as part of a local
path. The real Flask login returned `/\t/external.invalid` unchanged before the
fix, although browser URL parsing removes the tab. Login now rejects ASCII control
characters before the existing destination validation and falls back to Hybrid
Now. Ordinary local paths retain their camera/profile, repeated queries and
fragments unchanged. No destination allowlist or authentication policy is expanded.

`hybrid_login_redirect_test.py` covers external URLs, slash/backslash ambiguity,
unsafe schemes, embedded tab/newline/carriage-return, NUL/DEL and valid scoped
return paths through the actual login endpoint with CSRF in an isolated app with
Classic forbidden. The pre-fix assertion failed on the tab-containing destination.
This is HTTP/JSON acceptance, not a live browser execution test. The change is not
deployed; no real account, capture service or configuration was modified.
All 86 Python/compile checks pass, including Full Config parity and the complete
selected Book 2 regression. Node URL parsing independently confirms the ambiguous
URL interpretation; this does not substitute for browser acceptance. Evidence:
`testing/evidence/hybrid-login-redirect-2026-09-07.json`.

## Verified correction: login/account JSON input contracts

A non-object JSON body reached Flask-WTF's automatic form conversion and raised
TypeError instead of a controlled validation response. Login and account updates
now require an object and text values for the fields their existing forms submit.
Missing fields, nulls, booleans, numbers, arrays and objects receive field-specific
HTTP 400 JSON errors before form/password handling. Malformed JSON and non-JSON
bodies receive a global error. Valid form validation, CSRF, current-password checks,
name/password effects and ignored privilege fields retain their existing behavior.

`hybrid_account_input_test.py` reproduces the original array-body failure and
exercises invalid body/field variants for administrator and ordinary users. Failed
login requests leave login metadata unchanged and cannot open My Account; failed
account requests preserve name, password, role and email. A valid request after
the failures still succeeds. All state is synthetic and Classic imports are
forbidden. No real account, credential, service or configuration is modified;
the correction is not deployed and browser acceptance remains open.
All 85 Python/compile checks pass, including Full Config parity, Settings,
Safe Actions and Product regressions. `git diff --check` passes. Evidence:
`testing/evidence/hybrid-account-input-2026-09-07.json`.

## Verified correction: disabled-account sessions and API authentication

The existing login rejected disabled users, but the session loader returned them
as authenticated. The new test reproduced a disabled administrator retaining
access to My Account before the correction. Shared session loading now rejects
disabled/deleted users and malformed/out-of-range identities. Active users still
load normally, including through signed remember cookies. Disabling an account
is checked on subsequent requests; requests already executing are not revoked.
Reactivation continues to permit authentication; this change does not rotate
passwords, API keys or globally invalidate every previously issued cookie.

Action API and Sync API had the same missing active-account check. Both now reject
disabled users through their existing authentication-failure response, before
queuing capture commands or processing media. Active Action API administrator and
network requirements and active Sync API HMAC behavior remain unchanged.

`hybrid_session_revocation_test.py` uses two synthetic roles, actual login and
remember cookies, account disabling/reactivation, real encrypted API keys and
HMAC signatures. It verifies denied Hybrid GET/POST access, unchanged account data,
no queued commands after disabled API requests, fresh-login rejection, deleted
users and malformed identities. Active API authentication is exercised separately
without hardware effects. The correction is not deployed; no real user, key,
service or camera configuration is modified. All 84 Python/compile checks pass;
the final targeted test also passed after separating cookie-protection scenarios
and explicitly invoking the loader for invalid identities. Evidence:
`testing/evidence/hybrid-session-revocation-2026-09-07.json`. Browser acceptance remains deferred.

## Verified correction: export Unicode validation and table controller contracts

A JSON table containing an isolated Unicode surrogate passed shape validation,
then CSV encoding raised UnicodeEncodeError. XLSX could silently drop the same
invalid character. The parser now rejects invalid UTF-8 input and surrogate cell
values with a controlled validation error. Both authenticated export formats
return HTTP 400 without an attachment for invalid text. Valid accents, Japanese,
emoji and combining characters round-trip through CSV and XLSX unchanged.
Native attachment responses remain in use; browser blob downloads previously
failed direct acceptance and were not reintroduced.

`hybrid_operations_table_browser_test.js` executes the actual controller with a
simulated DataTables adapter: combined case-insensitive search/exact dropdowns,
visible counts, empty results, filter reset, placeholder-row removal and CSV/XLSX
form payloads containing the filtered data and CSRF token. It also retains the
Copy formula-escaping configuration. This validates controller contracts, not
DataTables implementation, actual clipboard/download behavior or browser layout.
The real Flask operations test covers the new 400 responses and still checks
CSRF, attachment content, notification acknowledgment and failed effects.
All 83 Python/compile and 24 JavaScript checks pass. Evidence:
`testing/evidence/hybrid-export-validation-2026-09-07.json`. No production deploy
or capture restart occurs in this mission.

## Verified correction: all persisted task queues and terminal outcomes

The Hybrid list excluded IMAGE and UPLOAD queues and all EXPIRED tasks, hiding
outcomes needed to inspect processing, delivery and rejected/recovered work.
Its read policy now includes all four queue types and six persisted states,
retaining the three-day window, existing client filters, sorting and pagination.
The page explains that expiry has no confirmed completion and points to the
recorded reason. No task is retried, changed or deleted by this correction.

Task age, recent counts and the lookback now use the database clock, matching the
server-assigned createDate time base instead of a camera-local offset. Details
retain camera/profile context and payload redaction for every queue/state.
`hybrid_task_visibility_test.py` exercises 48 recent queue/state/camera combinations,
both authenticated roles, anonymous denial, an old excluded record, unchanged
persistent states, readable results and ±12-hour camera-clock offsets. The domain
policy unit test now asserts the expanded supported queue/state contract.

A read-only Raspberry count found 475 task rows from the last three days: VIDEO
423 EXPIRED, 7 FAILED, 45 SUCCESS. The aggregate query took about 2.6 ms. This is
volume/query evidence, not a measured whole-page speedup or a large-backlog
performance guarantee. No new index or artificial display cap was introduced.
The correction is not deployed and does not restart capture. Browser filter,
clipboard/export and keyboard acceptance remain separate pending checks. All 83
Python/compile checks pass after removing five archive-generated AppleDouble files
from the isolated copy and rerunning shell, Safe Actions and compilation checks.
The task-flow test also passed again with the final template text. Original
failures and successful reruns are recorded in
`testing/evidence/hybrid-task-visibility-2026-09-07.json`.

## Verified correction: public media directory links and camera scope

The rendered directory linked to root-relative `/latest...` strings rather than
registered Flask URLs. Under `/indi-allsky` these omitted the application prefix,
and no camera/profile was attached. The page now uses url_for and the shared
Hybrid media-camera selection validator. Each link names the selected camera,
preserves a valid profile and respects SCRIPT_NAME mounting. Invalid or mismatched
camera/profile input is rejected. Public handler semantics and media algorithms
are unchanged. The page explains bookmarks/embeds, authentication and absent media
without exposing Flask endpoint names as a user-facing column.

The public-media flow test follows all 16 actual rendered links for both roles
and cameras (64 HTTP navigations), checking final viewer content or byte-exact
fixture files. It also checks a reverse-proxy prefix and rejects invalid scopes.
Its optional evidence output records stable control IDs, requests, resolved URLs,
role/profile, response hashes and observed result. These are HTTP destination
passes, not browser click, keyboard or mobile passes. Existing public-media tests
still cover optional authentication, range responses, RAW export roots, remote
policy and missing media. Production is unchanged and direct browser acceptance
is deferred until the user can unlock the Mac this evening. All 82 Python/compile
checks pass; the targeted test was rerun after adding its evidence output.
Evidence: `testing/evidence/hybrid-public-links-2026-09-07.json`.

## Verified mission: detail pages included in acceptance discovery

The schema-3 discovery uses disposable real JPEG/FITS/RAW/video files and
synthetic task/notification records. It resolves image, video, FITS, task,
notification, user and config IDs plus every registered upload-provider and log
variant. Each case records its concrete request path, path parameters, role,
camera and profile. No production files or configuration are used for fixtures.
Unknown parameterized routes remain blocked rather than silently disappearing.

The current registered TemplateView set contains 90 routes and 490 contexts:
364 render successfully, 126 remain blocked (98 anonymous redirects, 12 other
redirects, 12 hardware-bus blocks and 4 external-process blocks). Nine detail-route
families previously omitted for missing URL parameters now contribute 85 contexts
and 4,158 discovered controls. Overall 28,572 control occurrences are enumerated;
**zero are promoted to interaction passes by this discovery**. There are no
render defects in this fixture run. Static HTML discovery still cannot account
for all JavaScript-created DOM or prove effects, keyboard/mobile behavior, or
permission enforcement of mutating requests.

`hybrid_ui_detail_acceptance.py` validates concrete detail URLs, all three roles,
absence of detail render defects and preservation of pending control outcomes.
The compact evidence retains every blocked context and concrete detail variant:
`testing/evidence/hybrid-ui-details-2026-09-07.json`. The full explicitly generated
inventory is at `/home/eric/hybrid-aurora-status-evidence/ui-details-inventory.json`
with its hash in the compact evidence. Historical inventory files are untouched.
All 82 Python/compile regression checks pass, as do the HTML-discovery parser
checks and the detail-evidence validator. This expands test coverage only; no
production deploy or capture restart occurs.

## Verified correction: per-component aurora web status

The shared status formatter ignored AURORA_COMPONENT_STATUS: one successful
feed renewed the global timestamp and could make retained failed readings look
current. Missing numeric readings also appeared as zero, and malformed metadata
could break the page. Hybrid now owns this read-only presentation in
`modern_admin_aurora_status.py`; BaseView delegates to it.

Each required reading contributes to its component status. Failed, missing,
unknown-age and older-than-six-hour data are explicit; partial updates identify
the affected feeds. Kp trend/rating is suppressed when its feed is not current.
Absent readings display an em dash through a string value that accepts the
existing numeric format specifications, keeping saved web templates usable.
Actual zero remains numeric zero. Valid fresh values, rating thresholds and trend
symbols retain their existing semantics. No config keys, defaults, provider
calculations or capture behavior change.

`hybrid_aurora_status_test.py` exercises zero/missing/nonfinite/malformed readings,
stale and future timestamps, partial failure, retained values, unchanged inputs,
numeric template formatting and real `/ajax/status_update` responses for both
roles and cameras with Classic forbidden. All 82 Python/compile checks pass;
a separate comparison against the captured legacy method passes 60 complete,
fresh Kp/coefficient combinations. Evidence:
`testing/evidence/hybrid-aurora-status-2026-09-07.json`. Direct browser acceptance remains
blocked by the locked Mac. This presentation correction is not deployed; the
live capture baseline remains 775a19d0 at 10:09:50 CEST. Full product acceptance
and physical Classic removal remain open.

## Verified mission: release 775a19d0 deployed with provider failure containment

Evidence: `testing/evidence/hybrid-release-775a19d0-2026-09-07.json`.
The clean release reconstruction matched all 1,116 tracked files before tests.
All 81 Python/compile checks and 23 JavaScript entrypoints passed, including
Full Config parity, Book 2, Hybrid Flask flows and provider/worker failure tests.
These checks do not constitute exhaustive browser or hardware acceptance.

A protected online SQLite backup (828,977,152 bytes, integrity ok) and Flask
configuration copy were verified before maintenance. Sudo was authenticated
before any service stop. Timer, capture and Apache were stopped; checkout was
fast-forwarded from b65cd856 to 775a19d0; compilation and Apache configuration
checks passed; services and the timer restarted at 10:09:50 CEST. Capture PID
is 3284487. Existing untracked user files were preserved. Recovery instructions
and backup location are in `HYBRID_DEPLOYMENT.md`.

The 10:11:18 read-only snapshot confirms actual new image files for both cameras:
IMX708 at 10:11:05 (518,414 bytes), ZWO at 10:11:10 (575,799 bytes). No queued or
running tasks appeared in that sample; the periodic provider jobs had not yet
run. The six known startup gain clamps were the only error lines in the sample.
The subsequent 10:16:31 snapshot confirms automatic aurora tasks 10708/10709
SUCCESS and all five component timestamps renewed for both cameras. Persisted
Bt/Bz are 9.42/-6.46, plasma density/speed/temperature 16.34/372.24/140116,
hemispheric powers 41/43. Both cameras continued writing files (8/26 images since
restart). No new error class appeared. This proves the repaired live data flow,
not independent scientific accuracy. Health, smoke and TLE jobs also report
SUCCESS; smoke geographic coverage remains unverified. Task timestamps use UTC,
whereas image/service timestamps here use local CEST; the evidence selects task
IDs after the pre-deploy high-water mark to avoid mixing time bases.
Direct browser verification is blocked by the locked Mac, not recorded as passed.
The heartbeat baseline is updated to this deployment; 24-hour day/night stability,
full UI acceptance, hardware and physical Classic removal remain open.

## Verified mission: current NOAA solar-wind adapter and real-feed acceptance

The previously failing mag/plasma table URLs are replaced with the current
[NOAA RTSW feeds](https://services.swpc.noaa.gov/json/rtsw/). A dedicated adapter
selects records marked active with overall_quality zero, maps proton fields and
UTC timestamps into the existing table contract, sorts/deduplicates timestamps,
and rejects conflicting active samples. Inactive sources, absent/nonfinite
measurements and malformed timestamps are excluded; no fallback chooses an
inactive spacecraft or fabricates values. Existing twenty-minute averaging
methods are unchanged and continue accepting historical table fixtures.

`hybrid_aurora_rtsw_test.py` verifies both schemas, invalid/conflicting input,
duplicate handling and identical calculation results for equivalent old/new
inputs. The 35-entrypoint regression passes. Separately,
`hybrid_aurora_live_acceptance.py` fetched all five public NOAA feeds and updated
only a disposable camera/database at 08:00 UTC on 2026-09-07. All five components
succeeded. Actual calculated Bt/Bz were 10.13/-5.32, plasma density/speed/temperature
14.9/371.37/131977, hemispheric powers 39/41. These are observed test outputs,
not independent scientific validation or current production readings.
Evidence: `testing/evidence/hybrid-aurora-rtsw-2026-09-07.json`.

This restores the external data flow in isolated live-feed testing. Production
still runs b65cd856; this adapter and the preceding failure-containment change
must be deployed and the task/provider results verified there. The existing
24-hour acceptance remains open after the observed worker failures.

## Verified mission: live maintenance results and provider-failure containment

`testing/evidence/hybrid-live-maintenance-2026-09-07.json` verifies the first
post-deploy periodic effects. Backup task 10706 produced an 8,463,874-byte gzip;
its actual contents were restored only into a disposable directory, yielding an
828,977,152-byte SQLite database with integrity ok, two cameras and image metadata
through 09:48:38. The original compressed backup was untouched. TLE groups now
contain 157, 10,715 and 21 records updated at 07:48 UTC. Health and smoke tasks
reported SUCCESS; smoke sensor/provider correctness is not proved by that status.

Aurora tasks 10701/10702 exposed an uncaught failure after NOAA returned HTTP 404:
the magnetic-data processor indexed None, killing the video worker and leaving
tasks RUNNING. They remain failed/unresolved live work, not acceptance passes.
The local correction turns HTTP errors into explicit provider failures, records
per-component availability/last-success, preserves prior readings on component
failure (including partial mutation), and reports partial updates as failed tasks
rather than full success. No astronomical calculations were changed.
The video execution boundary now rolls back pending DB changes on an effect
exception, marks an unfinished task FAILED, and allows the next job to execute;
unknown actions also receive a terminal failure. Existing terminal outcomes are
not overwritten. This does not supply worker crash leases or external exactly-once
effect guarantees.

The 34-entrypoint regression passed; targeted tests execute provider failures and
the actual video processTask method with real isolated database state. NOAA's
[current RTSW directory](https://services.swpc.noaa.gov/json/rtsw/) and live probes
confirm rtsw_mag_1m.json/rtsw_wind_1m.json return 200, with per-record source/active
flags and a different plasma schema. The adapter migration remains open: URLs
were not replaced blindly, and current aurora data is not declared restored.
This containment correction is not yet deployed. The 24-hour acceptance cannot
be declared passed in the presence of these unresolved runtime errors.

## Verified mission: clean release verification and production deployment b65cd856

Evidence: `testing/evidence/hybrid-release-b65cd856-2026-09-07.json`.
A fresh extraction plus the exact commit patch was verified against all 1,107
tracked file contents/symlink types, with no extra files before tests. The full
selected suite passed 78 Python/compile checks, including all Hybrid flow tests,
Book 2, parser fingerprints, Settings, Safe Actions, Product Spine and processing
isolation tests; all 23 JavaScript entrypoints passed. Eight real loopback SFTP
worker-effect cases also passed, covering two cameras, success/permission failure,
source ownership and duplicate deliveries, plus both roles viewing task results.
This is not exhaustive browser/hardware acceptance.

A separate online SQLite backup (828,977,152 bytes, integrity ok) and protected
Flask configuration copy are at `/home/eric/hybrid-backups/release-b65cd856-20260907-093949`.
The first deployment attempt stopped before checkout changes because sudo needed
reauthentication, and restarted capture. After interactive authentication, timer,
capture and Apache were stopped; the checkout advanced from faf53d86 to b65cd856,
compilation and Apache config checks passed, and all services/timer restarted.
Deployment completed at 09:42:33 CEST. Untracked user files were preserved.

Live Now browser acceptance showed Running and new images for both cameras.
The 09:45 snapshot independently confirms new real files: IMX708 09:44:33 and ZWO
09:44:53, active PID 3263670, no pending tasks and 82,699,472,896 free bytes. Only
the six known startup gain clamps were found in that log sample. This is early
post-deploy evidence, not sustained stability or scientific-quality acceptance.
The heartbeat baseline was updated to this commit/start time; earlier continuity
cannot count toward the new 24-hour requirement. Production effects of newly
allowed maintenance tasks, full browser acceptance, hardware and Classic removal
remain open. Rollback instructions are in `HYBRID_DEPLOYMENT.md`.

## Verified mission: database backup failure semantics and round-trip acceptance

Pre-deploy review found that database backup checked total filesystem capacity
instead of free space and ignored gzip's nonzero exit code. The latter could
return a nonexistent `.gz` path and prune previous backups after compression failed.
The backup now checks free bytes on its actual destination filesystem, closes both
SQLite connections on failure, uses owned temporary files, requires successful
compression and a nonempty output, and atomically publishes a uniquely timestamped
filename before retention. Retention is restricted to recognizable backup names
in the backup directory, excluding symlinks and unrelated/nested files. The unused
recursive enumerator is removed. Existing minimum space and retention count remain
1000 MiB and seven; the pre-attempt BACKUP_DB_TS retry policy is unchanged.

`hybrid_database_backup_test.py` creates a real SQLite backup from the isolated
Flask fixture, gzip-decompresses it, checks SQLite integrity and both camera rows,
and verifies restrictive output permissions. It exercises low free space despite
large total capacity, failed/unavailable gzip, success without output, temporary
cleanup, distinct output names and retention without deleting unrelated files.
The 32-entrypoint regression passes. These are actual backup/compression/restore
file effects on disposable data; production backups and upload remain unverified.

The attempted clean-release extraction started before its large archive transfer
completed and failed with an explicit unexpected-EOF error; no tests or deployment
were run from that partial extraction. The full clean-release verification must
be repeated against a complete, hash-verified archive including this backup fix.
The earlier candidate `31aa263b` is not deployment-ready. No production changes
were made. All 23 JavaScript entrypoints passed for that candidate; changes in this
mission are confined to Python backup handling and its tests/documentation.

## Verified mission: multicamera periodic-task dispatch and 09:20 live sample

Production snapshot `hybrid-live-continuity-2026-09-07-0920.json` records unchanged
`faf53d86`, PID 3206060 and 00:32:40 start. At 09:20 CEST both image files exist:
IMX708 09:20:12 (714 images, 459 night/255 day), ZWO 09:20:23 (1114 images,
464 night/650 day). Largest recorded image gaps remain 46/53 seconds. No queued
or running tasks were present and free space was 83,787,968,512 bytes. Journal
errors remain the six startup gain clamps and insufficient ZWO startrail-video
frames. The elapsed interval is about 8h48m, not 24 hours.

Investigation of EXPIRED periodic tasks found an active product defect: the
coordinator's old multicamera images-only whitelist rejects aurora, smoke, TLE
updates and database backups before the worker receives them. Production journal
entries for tasks 10695–10697 explicitly confirm this rejection. An empty queue
therefore does not establish successful maintenance or fresh external metadata.

A Hybrid dispatch policy now distinguishes camera-scoped generation/aurora/smoke
from global TLE/backup/health-check actions. The coordinator allows these known
responsibilities and retains rejection of unsupported actions or missing camera
scope, now persisting the reason. Queue envelopes, primary worker profile metadata,
actual worker methods and single-camera dispatch remain unchanged.
`hybrid_video_dispatch_test.py` executes the actual coordinator method against
real isolated Flask task records and a local queue: thirteen allowed combinations,
six rejected cases with persisted reasons, and single-camera compatibility. The
31-entrypoint Python regression passes. This proves dispatch, not external-provider
success, backup upload, worker recovery or live effect acceptance.

The change is not deployed: production still rejects these maintenance tasks.
Deploy must verify actual backup files/provider updates and restart the capture
observation period because coordinator behavior changes. Dedicated pre-deploy
backups remain separate from the broken automatic-backup flow. No capture restart,
media deletion or production mutation was performed in this mission.

## Verified mission: live recorded-sensor panel without invented zero readings

Hybrid Sensor Panel now refreshes recorded metadata every five seconds, supports
manual refresh and used/all-slot filtering, and shows source-image timestamp/age.
A Hybrid row builder owns labels, slot visibility and missing-value presentation
for all 60 user plus 60 temperature slots. The shared page and JSON handler use
it; the former inline row loops are removed. Zero readings remain zero. Absent
readings are null/Unavailable, including images outside the existing 15-minute
window. Invalid/nonfinite display values are unavailable. Sensor acquisition,
drivers and stored data are unchanged. The existing public sensor arrays retain
their lengths/keys but now return null rather than fabricated zero for absent
values; a `readings` field adds labels and visibility for Hybrid. The retained
Classic JavaScript formatter already supports null values.

`hybrid_sensor_panel_flow_test.py` checks both roles/cameras, real zero versus
missing and null readings, text escaping, 120 slots, all/used configuration,
stale-image exclusion, authentication and retained recovery context with Classic
disabled. The actual JS controller test checks filter effects, refresh/polling,
atomic response validation, stale/error/session messages and cleanup. All 30
Python regression entrypoints pass, as do the sensor controller tests.

The first direct browser check at 09:17 CEST confirmed metadata age and unavailable
readings and exposed an implementation regression: bypassing normal context
composition disabled the recovery toolbar. It was fixed by retaining normal MRO
composition and replacing the shared inline row policy with the Hybrid service;
the Flask test now guards the toolbar context. A final browser check at 09:19 CEST
confirmed working recovery context, all 120 slots when selected, return to the
11 default visible slots, and manual refresh updating the source-image age.
Server logs also confirmed repeated five-second requests. Hardware sensor-read accuracy and
production deployment remain open. Only the disposable test server was restarted.

## Verified mission: real orbital propagation and isolated satellite failures

`hybrid_astropanel_satellite_test.py` seeds an isolated database with twenty
explicitly synthetic ISS-like TLEs, one malformed entry, one out-of-epoch entry
and a different-group entry. A fixed clock and actual PyEphem propagation/pass
calculation verify both roles and two distinct camera locations, all twenty rows,
sorting, pass times/duration, eclipse/elevation fields and group filtering. These
are orbital-code acceptance fixtures, not claims about current real satellites.

The out-of-epoch entry reproduced an uncaught `ValueError` from `sat.compute()`:
one stale TLE previously failed the entire endpoint. That error is now isolated
per satellite. The additive `satellite_errors` response lists unavailable entries
with a reason; Hybrid displays those reasons as plain text while showing the valid
predictions. Parse and next-pass failures are also reported. Existing successful
payload fields, orbital algorithms and singleton-array pass values are preserved.
The controller remains compatible with responses lacking the new optional field.

All 29 Python regression entrypoints and the Astropanel controller test passed.
The regression exercises the stale-entry failure through real Flask and PyEphem,
not a mocked exception. Current orbital-feed freshness, direct observation of
satellite passes and production deployment remain unverified. The test is fully
isolated and makes no changes to live TLE data or acquisition.

## Verified mission: Hybrid polar finder

Astropanel now includes an independent inline SVG polar finder with accessible
hour-angle description, HH:MM:SS angle display and cardinal-position clock times.
The marker uses the established scope orientation (180 minus hour angle degrees);
no Classic image or stylesheet is needed. Missing angle hides the marker. Missing
or invalid transit makes the cardinal clock times unavailable. Existing 18/12/6
hour offsets are retained, now wrapped to a valid 24-hour clock instead of showing
negative hours. This is a presentation correction; ephemeris calculations and
public payloads are unchanged. These are clock times relative to the reported
transit, not newly calculated astronomical event dates.

The Astropanel controller tests now exercise 0/90/180/270/360 degree positions,
angle formatting, midnight wrapping, absent angle and invalid transit. Direct
isolated-browser inspection at 09:06:45 CEST on 2026-09-07 confirmed the accessible
finder and angle 03:36:44 for 54.18423 degrees, transit 05:26:40 and cardinal times
11:26:40, 17:26:40 and 23:26:40. The 28-entrypoint Python regression and controller
tests pass. This closes the previously missing polar-finder presentation; telescope
alignment, mobile visual inspection and satellite-orbit acceptance remain open.
No production restart or deployment was performed.

## Verified mission: Astropanel details and whole-page refresh feedback

The Hybrid page now exposes the existing lunar transit/coordinates/phases, solar
transit/coordinates/twilights/seasons and Polaris next transit. Satellite rows are
no longer arbitrarily limited to twelve, and include duration and elevation. The
controller accepts the existing singleton-array representation of satellite pass
times/duration without changing the public API. All inserted values use text nodes.
Refresh is explicit, duplicate polling is prevented, and failures mark the whole
page unavailable or explicitly stale instead of leaving overview cards loading or
silently preserving old satellite data. Provider calculations are unchanged.

`hybrid_astropanel_flow_test.py` verifies real ephemeris responses, rendered detail
fields, both roles/cameras and no-satellite state with Classic disabled. The actual
controller test covers twenty satellites (including the public array shapes),
literal untrusted names, manual refresh, polling, malformed/failed responses,
expired sessions, unavailable values, retained stale data and teardown. All 28
Python regression entrypoints passed; chart and Astropanel JavaScript tests pass.
Direct isolated browser inspection at 09:02:54 CEST on 2026-09-07 confirmed computed
values and empty satellites. Clicking Refresh at 09:03:05 updated the timestamp,
solar altitude (21.02 to 21.05 degrees) and Polaris hour angle. This is a real API
refresh against disposable camera configuration, not production deployment or
validation of astronomical accuracy. Satellite-orbit fixtures, full mobile and
keyboard acceptance, and the Classic polar-finder visualization/cardinal-position
presentation remain open; this mission does not claim complete Astropanel parity.

## Verified mission: complete chart series and tolerate absent readings

Hybrid Charts now displays all six active standard series, nine configured custom
series, and the latest image RGB/gray histogram. Previously gain, detections,
custom plots and the histogram were absent from this interface. The chart canvas
has a bounded-height container. The controller validates a complete response
before replacing plots, aborts superseded history requests, prevents overlapping
polls, and reports expired sessions and failed requests while retaining prior data.
Empty and null-only series explicitly report no readings.

Direct isolated-browser selection of 24 Hours reproduced a real HTTP 500 from
`int(None)` when no star count was stored. The API now retains missing star and
temperature values as null; absent custom readings likewise use null instead of
an invented zero. Existing numerical readings, rolling-star calculation, detection
semantics, camera filtering and histogram algorithms are unchanged.

`hybrid_charts_flow_test.py` exercises actual Flask queries and JPEG histogram
calculation with Classic disabled, both roles and cameras, all series, absent
history, missing files and nullable readings. `hybrid_charts_browser_test.js`
executes the actual controller for all datasets, empty/null responses, atomic
validation, range changes, out-of-order responses, polling, HTTP/network/session
errors and teardown. All 27 Python regression entrypoints in the current mission
passed, including Book 2, Full Config parity, Settings, Safe Actions, Product View
Models and Product Spine. Existing fingerprints remain unchanged.

At approximately 08:55–08:59 CEST on 2026-09-07, direct browser acceptance in the
isolated application verified the 16 accessible charts, empty 15-minute history,
selection of 24 Hours, visible error before the fix, and automatic recovery to
"Charts updated" after restarting only the disposable test server. Server output
confirms the same camera-2 / 86400-second request now returns 200; absent metrics
remain marked unavailable. This does not establish full visual/mobile/keyboard
acceptance, every legend interaction, or production deployment. Production capture
was not restarted. The overall completion gate remains open.

## Verified mission: clearer Now capture evidence and live continuity sample

Now no longer displays "Preview remains disabled" beside working image previews
or internal repository/filesystem-scan commentary. It labels images as saved
frames, distinguishes current capture mode from the saved image's mode, and shows
an unavailable profile explicitly. The static "Not evaluated" sky badge is
removed from the capture summary. Camera images, timestamps/ages, exposure/gain,
source/output information, errors and navigation remain. View-model contracts,
providers and scientific/runtime decisions are unchanged.

`hybrid_now_page_flow_test.py` verifies both roles, retained image/source/output
links, missing-provider behavior and absence of the contradictory copy. The
existing image load/error controller tests also pass. Direct browser inspection
at approximately 08:42 CEST in the isolated app confirmed both synthetic previews,
current Day versus saved Night labels, profile Unavailable, exposure 0.5s, gain 10
and the retained output/source links. This is presentation acceptance, not new
proof of production capture health.

Separately, `testing/evidence/hybrid-live-continuity-2026-09-07-0839.json` records
a read-only production sample at 08:39 CEST. Commit `faf53d86`, capture PID 3206060
and start time 00:32:40 remain unchanged. IMX708 has 659 image rows since restart
(459 night/200 day), latest existing file 08:38:36; ZWO has 949 (464 night/485 day),
latest existing file 08:39:10. Maximum adjacent image gaps remain 46s/53s. No
pending tasks were observed and free space was 83,929,112,576 bytes. The journal
sample retains the six startup gain clamps and previously recorded insufficient
Startrail-video frames error; this does not resolve that generation acceptance.

The sample covers about eight hours including the night/day transition, not the
required 24 hours. It does not establish the unverified 15-minute monitor cadence,
nor replace resource/hardware/recovery acceptance. No production restart, deploy,
configuration change or media deletion occurred.

All 26 Python regression entrypoints, the Now image-state JavaScript test and
`git diff --check` pass for this mission. The presentation change is not deployed.

## Verified cleanup: obsolete Hybrid compatibility placeholder removed

After the scoped redirect correction, the unused `ModernAdminPlaceholderView`,
24 stale "coming later" descriptions and `modern_admin/placeholder.html` were
removed. The replacement `ModernAdminCompatibilityRedirectView` derives directly
from the shared BaseView, retains login enforcement and does not require a
template constructor. Its 24 destination mappings, registered ingress URL and
public endpoint name remain unchanged. The ownership map no longer declares the
deleted template and the operational next-steps document reflects this cleanup.

The redirect acceptance test now runs every supported alias with Jinja template
loading explicitly forbidden, both roles and preserved camera/profile queries.
It also asserts physical absence of the placeholder and obsolete class/map.
The historical route fingerprint remains unchanged: its guard explicitly verifies
the new no-template registration before normalizing only that internal class/
template change to the original fingerprint representation. Public route behavior
is separately exercised through Flask. Existing dated inventory/audit reports
remain historical evidence; they were not regenerated as a side effect.

This removes an unused Hybrid placeholder, not the remaining Classic frontend.
Mode switching, the complete interaction matrix and final production acceptance
remain open. No production restart or deployment occurs in this cleanup.

All 25 Python regression entrypoints and `git diff --check` pass after physical
template removal. Searches of application code and ownership tooling find no
remaining references to the removed classes/template; test references are guards.

## Verified correction: scoped compatibility navigation

The 24 supported `/modern-admin/classic/<page>` ingress aliases redirected to
Hybrid but discarded their entire query string, losing camera/profile selection
and filters. They now preserve decoded query values and repeated parameters when
building the destination. The endpoint is resolved separately before query
encoding, so `_external`, `_scheme` and similar query names cannot become
`url_for` control arguments or change the origin. Unknown aliases return 404
instead of a successful placeholder page. Registered URLs and known destinations
are unchanged; the historical class/template registration remains for later
cleanup, but this handler never renders that placeholder.

`testing/hybrid_compatibility_redirect_test.py` requests all 24 aliases with and
without camera/profile/filter queries, both authenticated roles, repeated tags,
spaces/plus signs and URL-builder argument names. It verifies destination paths,
absence of external origins and preserved values. It also verifies unknown-alias
404, anonymous login redirection and follows the log alias through its actual
Hybrid target while retaining camera 2/profile 2. This proves navigation routing,
not every destination's hardware effects or browser interactions. No production
deployment or capture restart occurs in this mission.

All 25 Python regression entrypoints and `git diff --check` pass. Full Config
and route fingerprints are unchanged; this correction changes query handling
and the response for unsupported aliases, not the list of supported functions.

## Verified mission: four Hybrid log downloads and detail recovery links

`ModernAdminLogDownloadService` replaces the four duplicated filesystem/gzip
implementations. A shared authenticated handler retains the capture, webapp,
syslog and kernel URLs, attachment names and octet-stream gzip responses.
Downloads retain original binary bytes (including non-UTF-8 data), oldest-first
within the existing byte window; they do not use the preview's redaction or text
normalization. Historical defaults remain 20,000 estimated lines for capture/
syslog/kernel and 5,000 for webapp at 150 bytes per estimated line. Requests are
now bounded at 3 MB; unlike the preview, this parameter still denotes the legacy
estimated byte window, not an exact line count.

Invalid/nonpositive counts return 400, missing files 404, denied access 403 and
other source I/O errors 503. An empty file retains its explicit HTTP 200 text
message. The same open file handle supplies size and bounded data; no unbounded
read or source modification is performed. This intentionally corrects previously
uncaught input/race errors and unbounded user-requested download size.

All four detail pages contained a link to the Classic log viewer. They now link
to the download of their selected source, retaining the Hybrid return link and
source navigation. The card says "Line limit" rather than implying the requested
limit is the number actually displayed. The preview/download distinction is
explained without frontend architecture terminology.

`testing/hybrid_log_download_flow_test.py` exercises all four endpoints with both
authenticated roles in the Classic-disabled app. It decompresses actual returned
gzip data and compares exact source bytes, filenames, content type, byte-window
selection and maximum size. It also checks anonymous redirects, invalid counts,
empty/missing files, source error mapping and all four detail-to-download links.
Read denial is exercised by chmod on each dedicated temporary file, then restoring
its permissions; missing detail pages show Missing. No production logs are changed.
All 24 Python regression entrypoints pass; download clicks through the browser's
save mechanism and live production files remain unverified. The change is not yet
deployed and does not close the complete product acceptance gate.

## Verified correction: bounded Hybrid application-log reader

The actual `JsonLogView` method at `7648f1d7` was executed against disposable
files before replacement. A file containing only `only line\n` produced
`[indi-allsky log empty]`; requesting 25 entries from a 1,000-line file produced
374 entries. It always discarded the first read line and estimated line counts
from bytes. Invalid but syntactically allowed regex strings could also raise.

`ModernAdminLogReader` now owns validation, backward reading, exact recent-line
selection, filtering and source errors. The Flask route remains POST, authenticated,
CSRF-protected, with the same `{"log": ...}` response. Existing valid case-insensitive
regex filtering, 30-character filter input and the 5,000-line maximum remain.
Invalid line counts/requests/expressions produce explicit ERROR text instead of
uncaught exceptions. Filter matches are selected within the requested recent
lines, as the UI now explains. Complete first lines are retained; an unterminated
last line remains separated from its predecessor; CRLF and malformed UTF-8 are
handled without a decoding failure.

Reading uses a single open file handle and backward chunks capped at 750,000
bytes. An oversized line that cannot be read completely reports the read limit
rather than pretending the file is empty. Missing, denied and unreadable sources
have distinct messages. The shared handler contains only the Hybrid delegation;
it no longer performs its own filesystem/filter algorithm.

Evidence: `modern_admin_log_reader_test.py` uses real disposable files and
instrumented byte streams, verifies exact newest-first results, filters, source
errors, a 5 MB file read of only 8,192 bytes for its latest 25 short entries, and
the hard 750,000-byte cap. This is a measured I/O bound, not a claim about Pi CPU
or latency. `hybrid_log_flow_test.py` verifies actual Flask requests, rendered
CSRF and both roles, including the selected line count and rejected inputs.
Scientific processing, capture and production log files are unchanged.

Direct browser acceptance confirms all four fixture lines including the previously
lost header, changing the line selector from 25 to 100 with a successful reload,
and a change from 15s to 5s polling observed in three successful request timestamps.
The four-line fixture does not prove a 100-row browser result size; exact counts
are covered by reader/HTTP tests. Evidence and remaining controls are explicit in
`testing/evidence/hybrid-log-reader-2026-09-07.json`. All 23 Python regression
entrypoints, the log controller test and `git diff --check` pass. This correction
is not yet deployed; remaining log downloads, browser filter typing, keyboard and
narrow-screen checks are not declared passed.

## Verified correction: upgrade recovery log polling and direct browser controls

On 2026-09-07 direct browser acceptance of Updates found that its System logs
recovery link opened a viewer whose POST `/js/log` always failed CSRF validation.
The Hybrid template omitted `X-CSRFToken`. It now sends the rendered token and
handles expired sessions and unsuccessful HTTP responses explicitly, retaining
plain-text log rendering. No authentication or CSRF exemption was introduced.

`hybrid_log_flow_test.py` verifies the actual rendered header and real log reader
against a disposable file, both authenticated roles, missing-token rejection,
filtering, no matching lines, absent source and anonymous page redirect.
`hybrid_log_browser_test.js` executes the actual inline controller for CSRF,
plain text, redirected sessions and failed/malformed responses. The corrected
recovery link was then clicked again in the real browser: the expected synthetic
file contents appeared instead of the earlier HTTP 400 error.

Direct browser checks also cover the two upgrade confirmations, no/one-confirmation
rejection, valid submit, disabled controls and cleared confirmations, refreshed
running state, unavailable provider, failed service command, completed-run restart,
failed-run display, configuration history and both-camera Now recovery links.
Flask logs show two accepted POSTs and the deliberately failed POST; the explicit
synthetic effect ledger records one StartUnit and one RestartUnit. Neither starts
a real service. Full per-control outcomes and remaining checks are recorded in
`testing/evidence/hybrid-updates-browser-2026-09-07.json`.

The browser sandbox now supports an explicit `--upgrade-fixture` JSON file and
redirects application-log reads to a disposable synthetic file. Without the
upgrade option, its existing command block remains in force. Real process and
D-Bus calls remain blocked. Production code/configuration and capture were not
restarted or deployed. Real upgrade/rollback, all browser roles, keyboard/mobile,
and the remaining log controls/downloads are still open.

Validation for this mission: all 22 Python regression entrypoints pass (the
previous 20 plus log and upgrade Flask flows), both log/upgrade JavaScript
controller tests pass, and `git diff --check` passes. Browser polling returned
HTTP 200 repeatedly from 08:10:12 through 08:11:57 CEST after the correction.

## Verified correction: atomic upload task acquisition (2026-09-07 07:58 CEST)

Two upload workers could read the same QUEUED row and both call `setRunning()`:
the read and write were separate, so both could perform the transfer. The new
shared backend helper `indi_allsky/task_claim.py` conditionally updates only an
UPLOAD/QUEUED row and commits ownership before returning it. Zero affected rows
means no effect. Commit errors propagate after rollback; an uncertain commit is
never treated as permission to upload. Terminal or missing duplicate tasks are
now informational log events instead of misleading missing-task errors.

`testing/hybrid_upload_claim_test.py` deterministically reproduces two winners
with the former algorithm. Ten races using independent sessions/connections to
file-backed SQLite then produce exactly one winner with the new implementation,
including preloaded identity-map entries. It also checks all non-queued states,
other queues, missing IDs, preserved camera/profile payload and failure before
commit versus lost acknowledgement after a real commit. The worker delegates
before connecting to a destination. No database migration is required.

The eight real loopback SFTP cases were repeated successfully after this change:
`testing/evidence/hybrid-upload-worker-atomic-2026-09-07.json`. All 20 regression
entrypoints pass (the previous 19 plus the new claim test). This used the isolated
`hybrid-acceptance-fcc8ab81` copy with the changed helper, uploader and tests
overlaid; it is no longer an unmodified archive. Checked source SHA256 values:
- `uploader.py`: `85fc436867ed4413a05227010eb43054584df56a37105be058e8df6ba64d5efd`.
- `task_claim.py`: `0f6e965ef019f9d2ce64c278d7c5e6b16ee71708137aa1cd5340af2b28da6cbb`.

Scope: one acquisition of one QUEUED task ID. This is not deduplication of distinct
tasks, a lease, automatic recovery after worker death or an exactly-once guarantee
across database/remote-storage failures. A lost commit acknowledgement may leave
RUNNING work requiring inspection. Concurrent database claims and sequential
real upload effects were tested separately; full threaded queue scheduling and
non-SQLite databases remain unverified. No production restart/deployment occurred.

## Verified mission: real SFTP through the upload worker (2026-09-07 07:53 CEST)

`testing/hybrid_upload_worker_loopback.py` executes the actual `processUpload`,
`cleanup` and queue-context methods from `uploader.py`, using the Classic-disabled
Flask fixture, real isolated SQLite task/notification records and real Paramiko
SFTP to the Raspberry's loopback SSH service. The installed public host key is
pinned in memory; certificate bypass remains false. Password input is not saved.

Eight cases pass: two synthetic cameras/profiles, successful versus write-denied
destinations, and both values of `remove_local`. Successful destination bytes are
verified before removal. Failed transfers produce FAILED tasks and an upload
notification. Existing semantics are explicit: `remove_local=True` removes the
owned source even after transfer failure; false preserves it. Unrelated sentinel
files remain unchanged. Replaying terminal tasks does not transfer again. Both
administrator and ordinary-user Flask requests display the resulting task states.
All test files are removed with the isolated fixture, without touching acquisition
media, production records, services, configuration or external destinations.

Evidence: `testing/evidence/hybrid-upload-worker-loopback-2026-09-07.json`.
The isolated copy's source hashes match the local candidate:
- `uploader.py`: `d3540bf81fe3b79751341c8d80dfba4dfafae8c40c0642f1cde4fbfea2fed1da`.
- `paramiko_sftp.py`: `4e5d2bee47f395ef532f449a308f02d393b7d4c86336ae7293baac894aeb607c`.

This exercises synchronous worker execution and Flask responses, not browser
clicks, concurrent queue consumers, scheduler recovery, model-backed asset upload
flags, other protocols or an external integration. Those remain separate gates.
The SFTP correction is still a candidate, not a production deployment.

The initial run at 07:46 passed, but its overlaid test directory had AppleDouble
template metadata and an obsolete route-composition test. Final acceptance was
therefore repeated successfully in `/home/eric/hybrid-acceptance-fcc8ab81`, created
from the exact Git archive with only `examples/` and `content/` excluded. The
archive SHA256 is `abbb643ea4a92e7a8d6f4ecb1cb5860421194ea5e2382d963cabd089106a05aa`.
All 19 regression entrypoints pass there: the twelve `modern_admin_*_test.py`,
Safe Actions, Full Config parity, Product View Models, Product Spine, Hybrid
shell, route composition and SFTP adapter. Individual logs are retained in that
directory's `regression-results/`. No fingerprints or application code changed
in this acceptance mission. Local `git diff --check` also passes.

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

## Network command ownership and independent effect adapter

The twelve NetworkManager intents now use `network_commands.py` for required
inputs, explicit argument types and bounds before constructing an effect adapter.
In particular, hotspot NOSECURITY must be a JSON boolean: the string "false" no
longer becomes true and creates an unintended open hotspot. Saved connection,
scan, connect-AP and hotspot capabilities remain; route/permissions/CSRF persist.

`network_manager_effects.py` contains the existing NetworkManager effects without
Flask view inheritance, request access or Flask response construction. Methods
return the same dictionaries/status tuples which Flask serializes at the route
boundary. The captured normalized AST fingerprints in
`testing/fixtures/network_effects_legacy.json` verify every extracted method;
normalization removes jsonify wrappers and changes app.logger to module logger.
Effect logic, polling, settings updates and D-Bus calls are otherwise unchanged.

`network_commands_test.py` checks all intents, hotspot boolean semantics, required
inputs and ranges, plus every effect fingerprint. Real Flask test
`hybrid_network_command_flow_test.py` runs with Classic imports forbidden and
mocked effects: admin dispatch, protected hotspot arguments, rejected malformed
payloads, ordinary user/CSRF rejection and uncaught provider errors. Full Book 2,
shell and route regression passes with original Full Config fingerprints intact.

This is a prerequisite mission. The native Network page remains unfinished.
Activation polling now skips failed D-Bus state reads instead of calling int(None)
after a first failed read. `network_activation_polling_test.py` executes the real
adapter with a fake bus: transient failure followed by success, thirty failed
reads, thirty still-activating reads and immediate success. It checks the bounded
poll count, response contract and exactly one activation request. These tests and
the real Flask network flow pass on the Pi's Python environment with mocked
effects; all nineteen local Book 2/shell/route/network entrypoints pass. Original
effect fingerprints remain unchanged, with only this explicit recovery addition
accounted for by the guard. The correction is not deployed to production. Live network
changes, reconnect/recovery, browser acceptance and production deployment remain
open. No saved connections, Wi-Fi settings or credentials were changed on the Pi.

## Native Hybrid Network controls

Hybrid Network now inherits only the Hybrid context and shared TemplateView,
without NetworkManagerView. The shared form supplies read-only connection/device
choices; failed inventory is shown separately from an empty Wi-Fi device list.
The native template/controller expose all nine saved-connection commands, scan,
join access point and create hotspot. Password inputs are concealed and cleared
after requests. Open hotspot selection sends an explicit JSON boolean.

Commands require administrator permission and target-specific confirmation.
Scanning explicitly warns that it enables the radio. Scan choices belong to the
selected interface and are cleared when it changes. Requests disable controls
while pending; mutations and failures require refreshed inventory before another
command. Reconnect/session feedback does not claim success after a lost response.
SSID descriptions use text-only option construction, never HTML insertion.

`hybrid_network_command_flow_test.py` runs real Flask with Classic imports
forbidden: native page and twelve controls for admin, disabled fieldsets for
ordinary users, anonymous redirect, provider-error rendering, all twelve effect
dispatches, explicit hotspot security, CSRF and failed effects. Inventory and
effects are simulated. `hybrid_network_browser_test.js` executes the controller
with a synthetic DOM: all command payloads, cancel, pending/refresh guards, scan
results and empty state, interface binding, concealed credential clearing,
hotspot boolean, session expiry and provider failure. All nineteen Book 2/shell/
route/network entrypoints and git diff --check pass.

Actual browser rendering/keyboard/mobile acceptance, real scans and connection
changes, reconnect/recovery and production deployment remain open. No live
network settings were changed. These automated results do not complete the
network hardware acceptance or the overall product plan.

### Scan display correctness

The real adapter now decodes SSID bytes as UTF-8 for display, fixing mojibake
such as `Cafè` becoming `CafÃ¨`. Invalid byte sequences use replacement characters;
empty SSIDs remain empty. The D-Bus AP object path, not the display name, remains
the connection target. No connection credentials or NetworkManager settings are
rewritten. Existing signal conversion was checked with actual dbus.Byte values
0, 50 and 100 and was already correct; it is unchanged.

`network_scan_effects_test.py` runs the real scan method with actual D-Bus value
types and a fake bus: UTF-8/invalid/empty names, exact target paths, signal values,
ordering, empty scans, rejected scans and radio enabling only when initially off.
It passes on the Pi Python environment alongside activation and Flask network
tests. The historical fingerprint remains unchanged with only the exact display
decoding replacement accounted for. No live Wi-Fi scan was performed.

### Direct Network browser observations (isolated server, 2026-09-06)

The browser sandbox now provides explicitly synthetic saved connections and a
wireless interface through read-only form providers. Its existing POST allowlist
still rejects network effects; D-Bus and process effects remain blocked. The
server was restarted only on loopback port 8099, leaving production untouched.

| Page/control | Context and expected behavior | Direct result / evidence |
| --- | --- | --- |
| Network / twelve command controls | Administrator, synthetic inventory; expose existing capabilities | Superato for rendering: accessibility tree contains all twelve named command buttons and the synthetic connection/interface choices. This does not prove command execution. |
| `connectap` without a scan result | Refuse connection before a target exists | Superato: click displays “Scan this interface and choose an access point first.” |
| `createhotspot` protected, empty password | Refuse an insufficient password before submission | Superato: click displays “Enter a hotspot password with at least 8 characters.” |
| `activate` confirmation | Show selected target and interruption warning | Superato for dialog content: browser reports confirmation naming “Synthetic Wi-Fi — Active [prio: 0]” and the remote-access warning. |
| `activate` cancel/submit | Dismiss or accept dialog and observe outcome | Bloccato: CUA click was interrupted by the JavaScript confirm, subsequent DOM inspection timed out, and dialog lookup returned no handle. No retry was sent. Server log contains no network POST. Neither cancellation nor command execution is counted as passed. |
| Other command effects, ordinary/anonymous browser sessions, keyboard/mobile | Full direct interaction acceptance | Still open; automated Flask/controller coverage is separate evidence. |

The live sandbox process was verified listening on 127.0.0.1:8099 (PID 3193471)
after the browser interruption. This is a tool observation issue, not evidence of
a crashed server or a successful network change. Drives/GPIO direct browser
acceptance remains open as well.

## Sky Cycle uses persisted per-camera acquisition records

The operational Sky Cycle page no longer renders the prototype timeline, source
confidence, health, moment or output cards. Its view now calls the independent
`sky_cycle_runtime.camera_cycle` query service. Each camera's latest cycle is
selected from image, FITS and RAW acquisition timestamps, then all aggregates
are scoped to that camera and stored acquisition date. This also exposes the
important FITS-without-JPEG case instead of presenting an empty camera.

The page reports recorded day/night image counts and first/last timestamps,
FITS/RAW counts, and total/successful generation records for timelapse, keogram,
star trails, star-trail video, mini timelapse and panorama video. These are DB
records, explicitly not verified files or uninterrupted coverage. No media bytes
are opened, no AI classifications are simulated, and no capture setting changes.
The obsolete runtime prototype builder call and imports were removed from this
view; historical product payload contracts remain covered by their own tests.

`hybrid_sky_cycle_flow_test.py` uses real Flask with Classic imports forbidden,
in-memory SQL records, both roles and anonymous access: camera/date isolation,
day/night aggregation, successful versus failed output records, missing data,
source-only capture and sanitized provider failures. It passes on the Pi runtime.
All nineteen Book 2/shell/route/network regression entrypoints pass; Product Spine
was repeated after the source-only case, and git diff --check passes.

The report intentionally names the latest recorded cycle rather than claiming
current capture health. Twilight computation, event/condition evidence, lineage,
direct browser acceptance and deployment remain open. This replaces a static
surface with actual acquisition evidence, but does not complete the overall
Sky Cycle feature set or the complete product plan.

## Library opens the operational Hybrid archive

The primary Library navigation no longer renders a static product-memory contract
or example observations. It uses the existing Hybrid archive controller and a
shared content template, exposing the ten supported media types, camera/date/name/
day-night/upload filters, sorting, cursor pagination, previews and original
downloads. Pagination and reset links remain on the selected Library/archive
entrypoint. The separate archive URL remains compatible. No duplicate query or
file-access implementation was introduced, and the unused Library prototype
builder import/call was removed from runtime views.

`hybrid_archive_flow_test.py --entrypoint library` and `--entrypoint archive`
exercise both entries against real Flask with Classic forbidden, temporary files
and an in-memory database: all media types, both roles/cameras, 111-image traversal,
forward/backward/oldest order, date/name/upload filters, literal wildcard search,
bad input, profile isolation, cursor-anchor deletion/new arrivals, provider errors,
remote-media policy and actual download response bytes. Both pass. Pagination
retains the entrypoint and selected camera/profile. Product Spine now permits
explicit GET search forms while retaining its mutation bans, inspects the shared
Library content, and asserts the Hybrid archive inheritance/login boundary.
All other Book 2 regression entrypoints pass; the updated boundary and Spine
guards pass after the intentional ownership change. git diff --check passes.

Semantic retrieval, favorites, tags and AI classifications are not represented as
implemented features by this change. Direct browser acceptance of Library and
production deployment remain open. This completes the connection between the
primary Library entry and existing supported media retrieval, not the entire
product migration or final acceptance.

## Output Detail opens saved generated records

The static Output Detail dossier has been replaced by real metadata/preview/
download for seven output kinds: timelapse, mini timelapse, keogram, star trails,
star-trail video, panorama image and panorama video. Library/archive result cards
link to the exact kind/ID/camera/profile. The existing public Product URL remains;
without an ID it offers the corresponding Library collections, preserving scope.
With an ID it validates kind and bounds, enforces camera/profile scope, and uses
the existing per-record archive serializer and independent download handler.

Displayed dimensions, frame count/rate, size, timestamps, upload/generation state
and notes come from the stored record. Missing recipe and lineage are not filled
with simulated values. Preview errors are observable using the shared archive
controller. No generation, upload or deletion is executed by the page.

`hybrid_output_detail_flow_test.py` passes on the Pi runtime with Classic imports
forbidden, temporary decodable outputs and an in-memory DB: all seven types,
both cameras/roles, real Library-to-detail links and downloaded bytes, empty
selection, malformed IDs/kinds/profiles, wrong-camera/not-found results, anonymous
redirect, sanitized provider errors, remote-only media policy and missing original
returning 404. All nineteen Book 2/shell/route/network entrypoints pass with the
updated explicit Hybrid media boundary. git diff --check passes.

Direct browser playback, production deployment, source lineage and processing
recipe reconstruction remain open. The change completes real generated-record
inspection through this Product entry, not the complete product acceptance.

## Highlights and Moment inspect actual images

The operational Highlights page no longer calls the prototype builder, whose
empty-data fallback generated sample meteor/output/clear-window candidates.
It now queries at most eight actual image records in the selected camera/profile
scope, ordered by detections, stars, SQM, timestamp and ID. The page explains this
all-history ordering and prints the saved values without identifying meteors or
claiming AI classifications. Empty selection and provider failure are distinct.
Previews/download URLs reuse the owner-aware archive policy. Excluded records
remain explicitly labelled, preserving the existing ranking's input scope.

Each Inspect image link supplies the actual ID/camera/profile to Moment. That
entry validates the scope and redirects to the implemented image detail; without
an ID it opens the image Library preserving scope. It no longer renders a fake
case dossier. Historical prototype payload functions/templates remain available
for the later cleanup audit, but these two operational views do not invoke them.

`hybrid_highlights_flow_test.py` passes with Classic imports forbidden, real Flask,
temporary images and a database containing more than a page: controlled ranking,
eight-row bound, both cameras/roles, exact Moment-to-image redirects and rendered
details, missing/invalid IDs, mismatched profiles, empty selection, sanitized
provider failure, remote-only preview policy and zero simulated candidates when
all image records are removed. All nineteen Book 2/shell/route/network regression
entrypoints pass, as does git diff --check.

Direct browser preview/interaction, production deployment, persisted event
review/classification and source lineage remain open. Moment currently provides
image inspection, not the completed detector-event workflow; the larger plan
must still account for that distinction.

### Direct image/video detail scope correction

The older native image/video detail URLs previously looked up only the record ID,
ignoring requested camera/profile scope. Both now resolve the shared camera filter
and constrain the record query accordingly: malformed or mismatched scope is 400,
a record outside the selected camera is 404. An unscoped valid ID remains supported.
The template camera ID comes from the actual record, and navigation back to media,
archive or mini-generation preserves the validated profile.

The extended `hybrid_archive_flow_test.py --entrypoint library` verifies both roles
and direct image/video URLs, valid/invalid/mismatched scope, owner camera context
without query parameters and retained profile links, alongside its complete media
navigation/download tests. `hybrid_highlights_flow_test.py` verifies the connected
Moment path remains functional. Both pass, as do all nineteen Book 2/shell/route/
network entrypoints and git diff --check. This correction has not been deployed to
production; direct browser acceptance remains separate.

## Now presents runtime evidence without prototype panels

Now retains the existing frame, current capture, phase, generated-output metadata
and source providers, but no longer renders static briefing answers, example
moments/looks, prototype health or attention panels. It explicitly identifies the
page as a snapshot at load time and offers refresh. Generated results and source
metadata link to the working Library, scoped to the current camera; each real
camera frame links to that camera's saved images. Missing camera metadata does
not create synthetic Camera 1/2 cards. No capture polling/scheduling was changed.

`now-frames.js` exposes an accessible error message and hides a failed preview,
including a failure cached before script initialization. A later load restores
the image and clears the error. This feedback does not treat a displayed saved
frame as evidence of fresh acquisition.

`hybrid_now_page_flow_test.py` passes with real Flask, Classic forbidden, two
synthetic cameras and generated files: both roles, camera/source/output links
rendering the destination, missing provider fallback without fake camera slots,
absence of prototype sections and anonymous redirect. `hybrid_now_frames_test.js`
checks cached failure, load recovery, subsequent error and missing-image cards.
The full nineteen-entry Book 2/shell/route/network regression and diff check pass.
Production deployment, direct browser visual acceptance and sustained capture
health remain open; no fake detector or AI result was introduced.

## Production capture check and off-grid legacy gain correction

At 2026-09-07 00:15 CEST, production still runs commit 9e721647 plus the two
documented IMX708 recovery hotfixes, not the newly completed UI. Service active
since 22:28:24, same main PID 3184687; 85 GiB free. Since that restart the DB had
141 IMX708 and 142 ZWO JPEG records. Subsequent latest files were verified present:
IMX708 00:16:13, 4608x2592, 6,345,398 bytes; ZWO 00:15:56, 3840x2160,
2,144,051 bytes. No media/configuration was deleted or modified.

The initial SYSLOG_IDENTIFIER=python3 filter returned only three entries and was
not sufficient evidence. The authoritative filter on this installation is
`_SYSTEMD_USER_UNIT=indi-allsky.service`. It returned 15,402 entries since restart,
no Traceback/MaskError/CRITICAL markers, but 66 ERROR markers: six initial gain
limit clamps and sixty “Current gain not found” messages between 22:42:26 and
00:09:58. These errors prevent claiming an error-free soak. The snapshot covers
less than two hours, not the required 24-hour day/night acceptance.

Inspection reproduced a defect in legacy exposure recalculation: off-grid gain
fell back to index zero, so a downward gain step could use index -1 and select
the maximum gain. Runtime recalculation now uses the adjacent ordered step in the
requested direction, with endpoint bounds; exact on-grid behavior is unchanged.
The modern AutoGainController, configuration, drivers and scheduling are unchanged.
The log observation alone does not prove that every observed reset triggered the
wrong-direction branch; that branch was reproduced in an isolated behavioral test.

`legacy_auto_gain_steps_test.py` executes the actual recalculation method, compares
40 on-grid cases against the captured pre-change method, reproduces old off-grid
wraparound, and checks increasing/decreasing intermediate gains and extremes.
It passes with all 23 Book 2/shell/route/network/AE/AG entrypoints. The real NumPy/
OpenCV multicamera processor and stretch tests also pass on the isolated Pi copy.
The correction is not deployed to production. The final capture build still needs
deployment/recovery tests and a new uninterrupted 24-hour acceptance period.


## Verified deployment: 2026-09-07

Production is now `faf53d8653b6c62588025e954688c8ee220a6ce8`. Capture was
restarted at 00:32:40 CEST, PID 3206060. Apache configuration passed and both
services started. Classic is still enabled; its removal gate remains open.
No database migration, user configuration change or media deletion occurred.

The exact tracked release archive (SHA256
`78c94c8d8d4ddb778d398586c44d9b4c5e12e68c0b4fb31e489d588ba466747c`)
was extracted into `/home/eric/hybrid-acceptance-faf53d86`. All 59 Python/check
entries passed there, including compileall; all 18 JavaScript test entrypoints
passed locally. Results and the live snapshot are recorded in
`testing/evidence/hybrid-release-2026-09-07.json`. Full Python logs remain in
`/home/eric/hybrid-release-evidence-faf53d86`. These isolated tests do not prove
hardware effects or browser clicks. Discovery inventory is deliberately excluded
from the pass count because it does not verify interactions.

Only the six missing, tested OAuth packages were installed into production:
google-auth 2.57.1, google-auth-oauthlib 1.4.1, requests-oauthlib 2.0.0,
oauthlib 3.2.2, pyasn1 0.6.4 and pyasn1_modules 0.4.2. The YouTube flow test
then passed using production Python, with Google transport mocked. Actual account
consent/upload remains open. `pip check` reports the pre-existing missing
`rpi-gpio` dependency of adafruit-blinka 9.1.0; GPIO hardware support remains
unverified and no unidentified pin was driven.

Direct production browser evidence: Now decoded both camera previews; the IMX708
Library link showed 48 records scoped to camera 1, loaded previews and a next-page
URL preserving `imx708-wide`. Image details opened record 1881 with camera 1,
4608x2592, 40-second exposure and profile-preserving navigation. This is a partial
admin flow, not acceptance of every media control or ordinary/anonymous sessions.

At 00:43:19 CEST both cameras had saved 13 JPEG records since restart. The latest
IMX708 file (00:43:01, 6,115,755 bytes) and ZWO file (00:42:36, 2,016,562 bytes)
were present. Service PID/start time were unchanged, no queued/running/manual
tasks were found, and 89,694,134,272 bytes remained free. The 1,629 journal lines
contained six initial gain clamps, no new gain lookup errors, MaskError or
Traceback. This eleven-minute sample is not a 24-hour result. Use
`journalctl _SYSTEMD_USER_UNIT=indi-allsky.service`: `journalctl --user -u ...`
returned no journal files on this installation and cannot prove absence of errors.

A thread heartbeat runs every 15 minutes to collect subsequent read-only evidence.
The first possible 24-hour boundary is 2026-09-08 00:32:40 CEST, provided capture
remains continuous and both day and night are evidenced. Restarts or capture/
scheduling changes invalidate that starting point. Unavailable observations stay
unverified, and completion of this period does not close the migration plan.

### Deployment backup and rollback

Backup: `/home/eric/hybrid-backups/release-faf53d86-20260907-002621`.
It contains the online SQLite backup (828,977,152 bytes, integrity check `ok`),
Flask configuration, original hotfix files, binary tracked diff, package inventory,
manifest, deployment record and git deploy log. Keep this directory private.
The old tracked hotfixes are also preserved in stash commit
`74e8b489343eb3295298fcd4fb0d03f93dcd79e8`.

For a rollback, first record the current checkout, service/timer states and any
changes made since this release; preserve new work and acquisition data. Stop
both the user capture timer and capture service, then Apache, before changing the
checkout. Restore previous commit `9e721647765f18c053b89e18619fcf26c3fb4014`
and the two backed-up hotfix files (`indi_allsky/image.py` and
`indi_allsky/stretch/mode1_stddev_cutoff.py`), rather than discarding those fixes.
Validate compilation and Apache configuration, then restore Apache and the
recorded capture service/timer states and verify new files for both cameras.
No schema changed in this deployment: do not overwrite the live database with
its backup as a routine code rollback, since this would lose newer records.
The six added OAuth packages may remain; they did not upgrade existing packages.

The deployment stop emitted an active-timer warning. No premature restart was
observed, but future maintenance must explicitly stop and restore that timer.
The rollback path was prepared in the deployment script; a live rollback was not
executed and is not claimed as a passed recovery drill. Production's four
pre-existing untracked entries were preserved; tracked files are clean.


## Acceptance inventory: inherited state and camera/profile coverage

The static HTML collector previously treated controls inside disabled fieldsets as
enabled and omitted Settings disclosure summaries. It also included textarea
values and script/style text as labels/audit text. It now records native disabled
state (including the first-legend exception), inherited ARIA disabled state,
hidden/inert ancestors, collapsed details and description references separately.
Disclosure, ARIA widgets and focusable custom elements enter the inventory.
Textarea values and script/style bodies are excluded, and explicit aria-labels
remain intact. Existing control identity inputs are preserved.

Schema 2 uses explicit camera/profile requests and synthetic multicamera config,
including both cameras for admin and ordinary user, plus anonymous access. The
full discovery ran against the isolated exact faf53d86 release with Classic
imports, subprocesses and DBus prohibited: 91 routes, 81 with five contexts
(405 contexts), 296 successful renderings and 109 blocked/redirected contexts,
zero rendering defects. Ten parameterized detail routes remain blocked pending
dedicated fixture selection. There are 22,800 control occurrences across contexts,
including 3,156 native-disabled controls and 140 disclosure summaries. These are
not unique product controls and none is marked passed by discovery.

Report: `/home/eric/hybrid-release-evidence-faf53d86/ui-discovery-v2-scoped.json`.
SHA256: `3db8857c5c44574ce1f657a198e062ce24fc2e79d6949eb89789b77ee2682183`.
It is intentionally kept outside the repository rather than committing thousands
of duplicated synthetic controls. Observatory still emits “future backend
contract” and Updates “not implemented”; these signals require functional review.
Absence of those phrases elsewhere is not evidence of functional completeness.
Computed CSS, JS-generated controls, external form ownership, browser interactions
and effects remain separate acceptance work; hidden controls stay in the matrix.

`hybrid_ui_inventory_parser_test.py` passes regressions for fieldset/legend scope,
form boundaries, disclosure states, native versus ARIA disabling, hidden/inert
ancestors, secret-value exclusion and stable IDs across value/state changes. All
18 modern_admin/Book 2/Safe Actions/parity/Product/shell/composition entrypoints
pass, along with compilation and diff checks. No runtime code or capture settings
changed; production soak is unaffected by this test-only mission.


## Observatory: operational evidence replaces the static readiness prototype

The Observatory route now invokes `ObservatoryRuntime` rather than the prototype
product builder. It reads the latest image/FITS/RAW records separately for every
registered camera, reuses the Hybrid capture-health timestamp thresholds, shows
associated enabled/disabled profiles, groups retained tasks by queue/state, and
reads capacity of the configured media filesystem. Service state comes from the
existing shell provider. Configuration indicators expose no credentials and do
not claim integration connectivity. No capture action or scientific algorithm
changed. Historical prototype builder tests remain until the final cleanup audit.

Each independent read section reports errors rather than substituting healthy
zero counts. Missing images do not hide existing FITS/RAW sources. Saved-record
freshness, file integrity, source correspondence, worker liveness and write access
are explicitly distinguished. All registered cameras are shown; camera-specific
media links use the record owner's ID. Existing SQM, AstroPanel, VirtualSky and
keogram tools now have operational links from the summary.

`hybrid_observatory_flow_test.py` passes against the isolated Pi copy with Classic
imports forbidden, real Flask/SQLite and temporary files: fresh/stale/missing
image records, source-only acquisition, profile association, task aggregation,
filesystem capacity, both roles, anonymous redirect, every content link rendering,
and sanitized database/filesystem errors. The injected failure tracebacks in the
test log are expected; none are rendered to users. All 18 Book 2/modern_admin/
Safe Actions/parity/Product/shell/composition entrypoints pass, plus compilation
and diff checks. Remote log: `/tmp/hybrid-observatory-flow.log`.

Direct browser acceptance used a separate synthetic server on localhost:18100,
backed by `/home/eric/hybrid-acceptance-observatory`, with subprocess/DBus effects
blocked. Observatory displayed two camera/profile cards, saved timestamps, task
counts and filesystem capacity. Its Browse FITS link for camera 2 opened Library
with type FITS and Test Profile 2 selected, one camera-2 result; FITS details then
showed ID 2, camera 2, source-camera-2.fit, 64x48, 0.5s and gain 20. The fixture's
old timestamps appeared stale and the blocked service adapter appeared Unknown.
This is partial admin browser acceptance, not a hardware or full-control pass.
The new Observatory page is not deployed to production; the existing capture
soak remains on faf53d86 without interruption from this mission.


## Upgrade prerequisite defect and Hybrid command ownership

Review of Updates found an actual supported Classic operation: the System page
starts the installed `upgrade-indi-allsky.service`, which runs
`misc/unattended_upgrade.sh`. This must be migrated, not labelled a future
feature. Its preflight in AjaxSystemInfoView incorrectly used `disk_usage.total`
instead of `free`, so a large full disk passed. Permission errors were skipped,
and `/var` was checked only if reported as a separate partition.

`ModernAdminUpgradeCommandBoundary` now owns command/authorization validation,
free-space checks on both `/` and `/var`, and delegation to the injected effect.
Both paths require at least 1000 MiB free, preserving the intended threshold;
unknown/malformed or unreadable observations block submission. Native route auth,
CSRF, request fields, configured unit and successful `Job submitted` payload
remain. Read/effect failures return sanitized 503 responses; service exceptions
are logged. The service script itself is unchanged. The check is a prerequisite,
not a reservation of space or proof of a successful upgrade.

`upgrade_command_test.py` covers a large nearly full disk, exact threshold,
root/var failures, malformed observations, rejected permissions/commands, and a
single effect. `hybrid_upgrade_flow_test.py` passes on the isolated Pi copy with
Classic forbidden: real admin/ordinary/anonymous requests, CSRF, low free space,
read failure, exact configured service call and failed effect. The service is
mocked; no upgrade, network package operation or capture restart was performed.
All 19 Book 2/modern_admin/Safe Actions/parity/Product/shell/composition/upgrade
entrypoints pass and git diff --check is clean. Remote test log:
`/tmp/hybrid-upgrade-flow.log` (contains the deliberately injected service error).

Updates UI, explicit confirmation, pending/duplicate handling and observable
upgrade-service completion remain open. In particular the installed oneshot unit
uses RemainAfterExit: repeated Start after completion needs deliberate lifecycle
handling before the UI can claim a new upgrade started. The script's capture
stop also needs timer-aware maintenance review. These are not declared passed
by the preflight correction. The fix is committed but not deployed to production.


## Native Updates service lifecycle and command

Updates now displays the installed application's version and the installed
upgrade unit's actual state, start/exit times, result and exit status. It no longer
claims Classic fallback is available or labels the supported upgrade as a future
feature. It offers the existing unattended upgrade operation, which pulls the
configured origin/main and can update dependencies and migrate the database.
No network release-availability check is claimed.

The new authenticated POST `/modern-admin/updates/start` requires administrator
permission, CSRF, strict true backup/maintenance confirmations and the observed
service token. A per-UID, no-follow, owner-checked file lock serializes submissions;
under the lock the service state is reread. Pending jobs and running/unknown units
are rejected, as is a confirmation of an obsolete start/exit/result state. An
idle or failed unit uses StartUnit; a successfully exited oneshot uses RestartUnit
because Start would otherwise do nothing with RemainAfterExit. The existing
Hybrid free-space boundary runs before the effect. Acceptance returns 202 plus
the job path, never a claim that upgrade completed. The legacy public system API
remains available with its previous request shape.

The controller disables submission while pending and after any response, clears
confirmations, distinguishes expired sessions and asks for explicit refresh after
network/non-JSON failures. It never automatically retries an uncertain operation.
The page explains that capture/web access may stop, and links to configuration
history, logs and camera frames. Configuration downloads are not presented as a
complete system/database backup. Service result is not end-to-end camera recovery.

`hybrid_updates_flow_test.py` passes with Classic imports forbidden and real
Flask/SQLite: both roles, anonymous access, CSRF, strict confirmations, actual lock
contention, stale confirmation, queued duplicate, completed oneshot restart,
failed retry, and sanitized unavailable provider. Systemd commands are mocked.
`hybrid_updates_browser_test.js` passes controller checks for confirmation,
permissions, CSRF, pending and completed-request guards, accepted/failed/expired/
lost responses. This is a JS controller test, not direct browser click evidence.
All nineteen Book 2/modern_admin/Safe Actions/parity/Product/shell/composition/
upgrade entrypoints pass. The historic route fingerprint is unchanged; the new
POST route has a dedicated ownership/method/auth guard. Compilation and diff
checks pass. Remote Flask log: `/tmp/hybrid-updates-flow.log`.

A direct read-only call of the real DBus adapter on the Pi returned the installed
`upgrade-indi-allsky.service` as idle, inactive/dead, with no prior start/exit and
can_start=true. No StartUnit/RestartUnit was called on the live service. Direct
browser acceptance, deployment and real unattended-upgrade/recovery acceptance
remain open. Script timer handling and failure recovery remain separate work;
the production capture soak was not intentionally interrupted by this mission.


## Live night/day transition: 2026-09-07 07:09 CEST

Production remains faf53d86 with capture PID 3206060, started 00:32:40 CEST.
At 07:09:19 both latest JPEG files existed, no pending tasks were found, and
84,521,414,656 bytes remained free. The subsequent history query found 524 IMX708
images (459 night, 65 day) and 612 ZWO images (464 night, 148 day) since restart.
The largest adjacent-image gaps were 46 seconds and 53 seconds respectively.
First day records were 06:21:12 and 06:21:55. Thus the stored frames evidence a
night/day transition and ongoing acquisition, not yet 24 hours. Task createDate
uses UTC/default database time while these image timestamps use local capture
time; do not compare their displayed hours as if they shared a time zone.

The 56,994 journal lines contain the six previously documented startup gain
clamps and one insufficient-frame startrail-video error (59 eligible frames),
without new gain-lookup/MaskError/Traceback markers in the snapshot filter.
No claim of an entirely error-free run is made. The current IMX708 daytime
exposure remains 40s at gain 1.13, with recent saved ADU rising 54 to 60;
its exposure duration alone does not establish a stalled acquisition.

Actual generated night files for capture date 2026-09-06 were inspected:
- IMX708 timelapse: H.264, 4608x2592, 620 frames, 24.80s, 16,409,460 bytes.
- ZWO timelapse: H.264, 3840x2160, 789 frames, 31.56s, 21,321,892 bytes.
- Keograms: IMX708 621x843; ZWO 790x700; both JPEG structures verified.
- Startrail images: IMX708 4608x2592; ZWO 3840x2160; both structures verified.
- IMX708 startrail video: H.264, 496 frames, 19.84s, 9,918,747 bytes.
- ZWO startrail video: no record; no file was verified; not passed. The worker's insufficient-frame
  branch omits that output rather than writing a successful empty video.

All seven inspected records have success=true and existing nonempty files.
ffprobe read video stream/container metadata successfully; this does not prove
full decoding or browser playback. Image.verify is structural, not visual or
scientific validation. End-of-night uploads were disabled and recorded failed;
several expired task rows have no result explanation. Upload acceptance and that
observability review remain open. No new media was deleted or generated manually.

Evidence: `testing/evidence/hybrid-live-night-day-2026-09-07.json`. Raw JSON also
remains under `/home/eric/hybrid-release-evidence-faf53d86`. Only two timestamped
snapshot files were actually present (00:43 and 07:09). The configured heartbeat
is not evidence of fifteen-minute execution; the gap is explicitly unverified
for periodic resource/backlog sampling, even though frame history covers capture.
Do not declare the monitor cadence or the full 24-hour requirement passed.


## Generated-output task receipts: partial output is observable

The live ZWO startrail-video omission exposed that the worker always finished
with the generic `Generated keogram and/or star trail`, even when a requested
output was missing. Its finalization now delegates to Hybrid
`finish_keogram_task`: each output records generated/skipped/not_requested/failed,
record ID and camera ID in `task.data.generation_outcome`, preserving existing
request/profile fields. The task result gives a bounded readable summary.

An optional video skipped for insufficient eligible frames reports Partial
generation and the actual/minimum frame counts while preserving successful task
completion. Disabled video and daytime-only exclusions are not failures. Actual
output failures or missing/empty files fail the task; a missing file clears the
associated record's success flag in the same commit. A result never claims file
integrity or successful upload, only nonempty file presence and generation status.
Existing task detail already displays the readable result and redacted payload;
no fake result is backfilled into historical task rows.

`generation_result_test.py` passes complete/partial/disabled/daytime/failure,
missing/empty file, camera/profile preservation and message-length cases. An AST
fingerprint captured from 3b172949 proves the existing generation method preceding
its final task receipt remains unchanged: no image processing, frame selection,
threshold, encoding or upload operation was altered.
`hybrid_generation_result_flow_test.py` passes with Classic imports prohibited,
real temporary SQLite/media and both roles: persisted partial result, visible
59/250 eligible-frame reason, retained profile and committed missing-output
failure. All 19 Book 2/modern_admin/Safe Actions/parity/Product/shell/composition/
receipt entrypoints pass, plus compilation and diff check. The Pi log is
`/tmp/hybrid-generation-result-flow.log`.

This worker change is not deployed. The live acquisition and its existing
observation period were not modified. Direct acceptance of a new worker-produced
receipt remains open until deployment and another controlled generation.


## End-of-night task state and delivery linkage

Two incorrect outcomes were reproduced in the actual worker method: a daytime
request returned after setRunning without a terminal state, and disabled uploads
were marked Failed. They now finish as explicitly skipped requests. A missing
remote folder when upload is enabled remains a failure. No transfer is attempted
for these gates.

Successful preparation previously reported Uploaded immediately after queueing a
separate transfer. It now reports Queued, stores the child upload task ID and
camera in the parent receipt, and persists camera/profile in the child payload.
The Hybrid parent task page links to that child's current state/result; the link
accepts only a positive integer task ID. A successful preparation is not delivery
confirmation. Historical task records are not rewritten, so old misleading
messages remain distinguishable by their generation version/time.

`end_of_night_task_test.py` executes the actual worker method extracted by AST
and verifies terminal daytime/disabled skips and missing-destination failure.
`hybrid_end_of_night_flow_test.py` executes the full method with real ephem,
temporary SQLite and media: writes data.json, checks its existing sunrise/sunset/
streamDaytime contract and remote camera path, queues exactly once through a
mocked queue adapter, persists parent/child scope and opens both Hybrid task pages
for admin and ordinary user with Classic imports forbidden. No network transfer
runs. All 20 Book 2/modern_admin/Safe Actions/parity/Product/shell/composition/
generation-receipt/EndOfNight-gate entrypoints pass; compilation and diff checks
pass. Pi log: `/tmp/hybrid-end-night-flow.log`.

No scheduling, astronomy calculation, upload destination or credential behavior
was changed. The worker/UI correction is not deployed and live upload completion
remains unverified. Follow-up review remains necessary for the existing polar
fallback `timedelta(years=10)` and temporary-file handling on formatting/enqueue
errors; this mission does not claim those branches passed.

## EndOfNight polar fallback no longer raises TypeError

Both missing-solar-event branches used `timedelta(years=10)`, which Python rejects.
They now use `timedelta(days=3650)` as the intended far-future sentinel. The
existing one-day-past sentinels for continuous daylight remain unchanged. These
values represent unavailable events, not a prediction of sunrise/sunset ten years
later. Ordinary ephemeris calculations and JSON keys/formats are unchanged.
Incorrect hemisphere-only comments were replaced with the actual event condition.

`end_of_night_polar_test.py` reproduces the original TypeError and executes the
actual worker method for eight combinations of rising/setting exception and
solar-altitude branch, including a leap-day clock. It verifies valid ISO timestamps,
the retained streamDaytime field and exactly one queued upload request.
The extended `hybrid_end_of_night_flow_test.py` passes with real PyEphem, temporary
SQLite/files and Classic prohibited: North/South Pole at June/December solstices,
both resulting sentinel values, plus the previous ordinary preparation and linked
Hybrid task-page checks. Only delivery enqueue is mocked; no external transfer
or production coordinate/configuration change occurs. All 21 Book 2/modern_admin/
Safe Actions/parity/Product/shell/composition/generation-receipt/EndOfNight
entrypoints pass, along with compilation and diff checks. The real-PyEphem log
is `/tmp/hybrid-end-night-polar-flow.log`.

The fix is not yet deployed. Temporary-file cleanup and failure handling after
preparation remain a separate open review; polar fallback completion does not
claim that these other branches or live upload delivery have been validated.

## EndOfNight temporary payload preparation

Hybrid `prepare_end_of_night_payload` now owns remote-path formatting and the
new temporary JSON artifact. It validates/formats the configured destination
before allocating a file, preserves the timestamp/ts/camera_uuid substitutions,
JSON indentation/Unicode behavior and data.json basename, and removes only its
own incomplete temporary file when writing or closing fails. Interrupted writes
also clean up before propagating interruption. It does not delete acquisition
media or files already handed to an upload task.

Expected preparation errors now fail the parent task with a sanitized message
and retain the exception in logs; no upload record or queue request is created.
The path timestamp is captured immediately before preparation instead of after
the JSON write. Astronomy, fields and upload destination semantics are unchanged.
Database commit and queue-dispatch error recovery after preparation are not
covered by this cleanup and remain explicitly open: ownership may already have
passed to a persisted transfer, so blind deletion there would be unsafe.

`end_of_night_payload_test.py` verifies exact JSON/path, owner-only temporary
permissions, malformed named/positional/bracket formats rejected before file
creation, partial-write/disk-full/serialization/interruption cleanup and preservation
of an unrelated file. The full real SQLite/PyEphem worker test verifies three
malformed configurations produce failed parent tasks, no new upload task and
no additional files; ordinary and all four polar cases still pass. All 22 Book 2/
modern_admin/Safe Actions/parity/Product/shell/composition/generation-receipt/
EndOfNight entrypoints pass, plus compilation and diff checks. Expected injected
formatting exceptions appear in `/tmp/hybrid-end-night-payload-flow.log`.

The worker change is not deployed and no live upload was attempted.

## EndOfNight database-to-queue handoff

Hybrid now commits the child upload record and parent linkage together before
queue dispatch. The prepared receipt makes file ownership and child identity
observable even when later completion cannot be saved. A persistence exception
prevents dispatch, rolls back the session, records uncertainty/candidate ID and
retains the metadata file for recovery. It does not assume that a lost commit
acknowledgement proves no row exists.

A queue exception records dispatch uncertainty and links the child, retaining its
file. Child state is never overwritten, since a consumer may already have received
or completed that request. After successful dispatch, a failed parent-completion
commit is logged and rolled back without redispatch or file deletion; the durable
prepared linkage remains. A repeated worker invocation with an existing receipt
stops before metadata preparation or creation of another upload. This is a
sequential re-entry guard, not a claim of distributed exactly-once delivery.

`hybrid_end_of_night_handoff_test.py` passes with real SQLite: failed pre-commit,
committed-but-unacknowledged insert, a consumer completing before dispatch raises,
successful dispatch seeing the durable parent link, and final parent-commit
failure. Every ambiguous case retains the owned file; no dispatch occurs after
persistence uncertainty and consumed-child success remains intact. The full
worker flow verifies re-entry creates neither another file nor another task,
alongside existing preparation/error/polar/UI cases. All 22 Book 2/modern_admin/
Safe Actions/parity/Product/shell/composition/generation-receipt/EndOfNight
entrypoints pass; related polar/payload checks were repeated after final changes.
Compilation and diff checks pass. Logs: `/tmp/hybrid-end-night-handoff.log` and
`/tmp/hybrid-end-night-handoff-final.log`; injected tracebacks are expected.

Recovery remains deliberate: inspect the linked upload task, logs and retained
file before resubmission. A persistent database outage can prevent recording a
terminal parent state; the prepared receipt and log are retained rather than
inventing a success. Candidate IDs after persistence uncertainty are diagnostic,
not proof of a committed child. No production task, file or service changed; this
worker change and real external delivery still require deployment/acceptance.

## SFTP trust/error handling and real loopback transfer

The shared Paramiko adapter did not load the service user's known_hosts, so a
normal verified connection could not use an already trusted server. It now loads
that trust store, rejects unknown/mismatched keys through the existing certificate
failure contract, and treats malformed/unreadable trust stores as validation
failures. The explicit legacy AutoAdd setting still allows unknown keys when
configured; known-key mismatches remain rejected. No trust store is rewritten.
SSH/subsystem/EOF/network failures map to existing connection/transfer errors,
and a failed SFTP close no longer prevents closing the underlying SSH session.

`sftp_adapter_test.py` executes the real adapter code with controlled transports:
trusted-key loading, unknown/mismatched/malformed keys, authentication and network
errors, failed SFTP subsystem, mkdir/put disconnects, explicit AutoAdd setting,
and idempotent close after a channel error. It passes with all nineteen Book 2/
modern_admin/Safe Actions/parity/Product/shell/composition/SFTP entrypoints and
compilation/diff checks.

`sftp_loopback_acceptance.py` ran on the Raspberry at 07:39 CEST using the candidate
adapter against its actual SSH/SFTP service on 127.0.0.1. The installed public
Ed25519 host key was pinned in the in-memory test client; cert_bypass=false.
The password was entered without echo and was not saved. Only a private disposable
directory, synthetic 84-byte JSON source and nested test destination were used.
Received bytes matched exactly (SHA256
`7d939c2a1e5b1b5976dad7761cc7542cc7d85471a53b05372fe5964fa5014335`).
A directory without write permission rejected transfer through TransferFailure,
left no destination file and preserved the source. Both channels were closed and
the disposable directory was removed; no acquisition files were touched.
Evidence: `testing/evidence/hybrid-sftp-loopback-2026-09-07.json`.

This is a real network/file effect, but loopback only. The upload worker's full
execution and any configured external SFTP destination remain unverified. The
adapter correction is not deployed to production, and no integration settings,
known_hosts, capture process or service configuration were changed.
