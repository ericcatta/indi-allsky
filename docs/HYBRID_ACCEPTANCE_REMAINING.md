# Remaining Hybrid acceptance work

Updated 24 October 2026. Classic frontend removal is deployed; whole-product
acceptance remains open for runtime verification. Storage contention corrections
are deployed at `58dca579`; the timeout watchdog and capture policy are unchanged.
No further 24-hour observation is authorized by the latest instruction.

## Storage contention follow-up — 24 October

The diagnostics now contain 17 timeout snapshots from 22–24 October: 14 show
at least one rpicam thread in disk sleep (mostly `folio_wait_bit_common`). These
establish I/O/page waits for those attempts, not CPU starvation or a camera
exposure setting fault. Other sampled states remain inconclusive. SQLite BUSY
also recurred during a 500-file storage-pressure cleanup, exhausting three
20-second waits for one FITS registration.

Two targeted corrections are verified in an isolated Raspberry candidate:
- SQLite cleanup yields 10 ms after each completed delete, outside the transaction
  and media lock, allowing competing capture writers to acquire the writer slot.
  Retention, retry limits and upload/generation protections remain unchanged.
- Disposable preview cache publication no longer forces `fsync` per derivative.
  Flush/close, atomic replacement and checksum regeneration remain; science FITS
  and archival assets retain their durability operations.

Thirteen targeted tests pass, including real SQLite contention, protected cleanup,
cache corruption/concurrency, source integrity and full/mini generation. A bounded
16 × 1 MiB SD benchmark measured 13.026 s with the former barriers (one publication
12.052 s), versus 0.033 s without; bytes match. This measures publication latency,
not completion of background disk writes or proof that all timeouts are cured.
No new 24-hour observation is started. Evidence:
`testing/evidence/hybrid-storage-contention-20261024.json`.

Release `58dca579` is active: capture restarted at 10:51:18 CEST and web at
10:51:09. The deployed application files match the tested candidate byte-for-byte.
Four post-restart JPEGs across both cameras exist, match database sizes and fully
decode; the task queue is empty and the 349 log lines through 10:51:58 contain
no error/traceback/retry. Login returns HTTP 200. This is bounded recovery evidence,
not sustained absence of intermittent timeouts. Rollback: restore `preview_cache.py`
and `storage_pressure_runtime.py` from
`/home/eric/hybrid-backups/storage-contention-20261024` into `indi_allsky/`, then
restart capture/web; no configuration or database restore is required.

## Final bounded verification — 21 October, 18:13 CEST

All three outstanding ordinary-user archive controls are user-confirmed in the
native disposable fixture; the scoped control reconciliation is complete.
No new 24-hour observation is authorized or scheduled by this work.

A real fork test reproduced inherited SQLite pool reuse on the old application
and passes with `59b50b8a`. The guard opens child-owned connections before checkpoint
configuration. Five targeted real-SQLite/Flask tests pass, including WAL snapshot
recovery, image/panorama inserts and FITS registration. Bounded retry diagnostics
now record error codes and elapsed time without query data; retry limits are unchanged.
The change is deployed with rollback, config119 unchanged, web HTTP200 and valid
new images from both cameras. This proves the fork defect fixed, not a causal
explanation of every historical `database is locked` incident.

The IMX708 residual is **not resolved**: today's existing logs contain seven lost
exposures during startup; all seven subprocesses were reaped and the five subsequent
recovery images decode and match database sizes. A 35-second read-only sample without
generation load shows three normal short processes; it cannot reproduce or explain
the earlier loaded stalls. No speculative watchdog increase or hardware change was
made. Full runtime acceptance remains open on these intermittent frame losses;
functional migration and frontend removal are not reopened.

Evidence: `testing/evidence/hybrid-sqlite-fork-20261021.json` and
`testing/evidence/hybrid-timeout-final-20261021.json`. No user handoff is outstanding.

## Timeout diagnostic follow-up — 21 October

A bounded 40-second reconstruction of 16 existing night FITS at worker priority
completed without errors while both cameras captured. Two IMX708 processes exited
successfully in 1.94/1.98 seconds. This did not reproduce the morning startup stalls.
Release `5ab0b6c4` adds a bounded live `/proc` snapshot immediately before timeout
termination (8 threads, 16 KiB input, 12 KiB log); it never reads command arguments,
environment or memory contents. Five Linux tests pass, including real-process
sampling, missing files, FIFO/bounds, abort resilience and unchanged timeout/recovery
policy. This is instrumentation, not a claimed cure. No further 24-hour run or
recurring observation was started. The next real startup stall must supply the
missing scheduling/I/O evidence before a causal repair can be selected safely.

Deployed at 18:21:26 CEST with rollback in
`/home/eric/hybrid-backups/timeout-diagnostics-20261021`. Both services are active;
new images 346004 (camera 1) and 346003 (camera 2) match database sizes and fully
decode. The 1,176 log lines through 18:24:53 contain no ERROR/CRITICAL/Traceback.
This brief check does not close the intermittent defect. Evidence:
`testing/evidence/hybrid-timeout-diagnostics-20261021.json`.

## Latest acceptance decision — 21 October

The user explicitly excludes any further 24-hour observation on this version.
It is not a pending user action and historical failed observations are not relabelled
as passes. Ordinary-user native archive filters, detail/back navigation and original
FITS receipt are now user-confirmed and published in `b148a628`; no repeat handoff is
needed. Classic frontend removal is deployed. This final three-control
reconciliation identifies no remaining supported-control gap in that scoped set.
Whole-product acceptance cannot yet be asserted because a 21 October bounded scan
found seven new IMX708 startup timeouts from 08:04 through 08:46, including three
consecutive failed attempts before recovery. Five resumed images were checked
against their database rows and decoded completely. The same scan found one FITS
registration failure from SQLite contention at 01:35. These are current runtime
defects pending correction and verification, rather than missing functional-control
coverage. Unavailable integrations/devices remain untested, not passed.

[Timeout and recovery evidence](../testing/evidence/hybrid-timeout-final-20261021.json).

## Current functional gates — 20 October, after shared-cadence release

This checkpoint supersedes older pending/deployment descriptions below; historical results remain retained.

- Shared normal-multicamera cadence is deployed at `df58afaa`; three paired rounds and six valid FITS passed bounded verification.
- Overwrite preservation is functionally verified using the real worker, SQLite and files, including render/commit failure, collision, recovery and transfer protection, in the passed 216-check regression. “Sustained natural overwrite” is an observational limitation, not an extra acceptance condition introduced after the user declined another 24-hour run.
- Retention boundary checks now pass on Raspberry in isolated fixtures: exactly 24h/5d remain protected, one microsecond older becomes eligible, day precedes night, and MANUAL/QUEUED/RUNNING uploads prevent deletion. This proves the tested policy and effects, not the eligibility of every historical production deletion.
- A demonstrated clock-jump watchdog defect is corrected and deployed at `8305d574`
  (20:59:13 CEST), but it does not resolve the acquisition-startup defect. Seven
  later immediate-mode attempts reached their monotonic deadlines without an image;
  all child processes were reaped and capture recovered automatically. Their cause
  remains unproven, so extending the watchdog or changing capture algorithms is not
  justified by the available evidence.
- The latest production-admin FITS download attempt timed out, but the same current
  admin source-download contract already has a received, hash-matched FITS receipt
  from 18 October. Ordinary-user archive filtering, detail/back navigation and a
  received FITS download now pass in the disposable native localhost fixture;
  this closes those three control scopes without claiming a production-user run.
- No new 24-hour run is required or authorized for this version. Whole-plan
  acceptance remains open for the unresolved intermittent timeout investigation;
  unavailable external devices/integrations stay separately classified.

[Targeted evidence](../testing/evidence/hybrid-final-boundary-checks-20261020.json).

## Historical bounded closure checkpoint — 20 October evening

Native reset/flush restore and relogin are complete. Mobile previews are user-confirmed; upload integrations are not used. The route register now links later scoped proofs instead of treating historic blocked records as current defects.

A read-only scan checked 4,800 daytime JPEGs and 128 nighttime FITS since 08:57:00: every expected file existed and matched its recorded size. Capture/web are active. Available logs (183,719 lines through 19:47:25) show no SQLite error but **one new IMX708 timeout at 19:39:19**, followed by recovery. Its cause is not yet established; concurrent FFmpeg is context, not proof of causality. Whole-plan acceptance therefore remains open.

A separate confirmed priority bug is fixed in `2e2880cf`: only Video/Storage child processes lower their priority, leaving the supervisor and later capture workers unchanged. The real fork test passes on Raspberry. Activated at 19:56:44 CEST after both generation tasks completed. Supervisor/capture/image now have NI0 and Video/Storage NI19; new FITS from both cameras exist and match recorded sizes. No new 24-hour observation was started. [Evidence](../testing/evidence/hybrid-final-bounded-checks-20261020.json).

## Mobile previews and stale backlog delay — 20 October release

`6d93270a` adds the missing device-width viewport and shows complete Now camera
images at intrinsic aspect ratio, with contain sizing and wrapping labels. Native
production checks at 320, 390, 430 and 1280px showed both images fully decoded,
correct proportions and no horizontal page overflow. Source images are unchanged.

`e2195ff9` releases an obsolete multicamera backlog delay when the camera is ready
and its queue is already below the existing minimum. It never starts before the
baseline interval, never catches up in a burst, and preserves active backpressure,
focus, SQM and explicit clock-reset schedules. The earlier backpressure diagnosis
still applies while processing is genuinely overloaded: this does not guarantee
45-second cadence at every load.

Regression: 210/214 initially passed; three failures came from macOS archive
sidecars in the isolated checkout, and one from the intentional CSS cache-version
change. Sidecars removed; viewport/cache assertions updated while retaining shell
fingerprints. All four reruns passed, application sources unchanged. Production
matches the final source manifest. Capture restarted at 08:56:31 CEST; three
camera-1 and two camera-2 daytime files passed existence/size checks at 15/14-second
intervals. Queue empty, no ERROR/CRITICAL/Traceback/timeout through 08:57:33.
No new 24-hour period or artificial production backlog was started.
[Release evidence](../testing/evidence/hybrid-mobile-cadence-release-20261020.json).

## Latest bounded verification — 20 October

No new 24-hour window was started. Existing regression remains 213 Python/compile
passes; these read-only checks require no application change or repeated suite.
The production lightbox now has native admin proof for both camera previews,
Next/ArrowLeft/Escape and a received, valid processed JPEG. Four historical route
records now link their exact later resolutions, preserving earlier outcomes.

Automatic recovery after the user-confirmed power-off passed: boot 23:21:33,
capture active 23:24:19 through the enabled two-minute timer, web through its enabled
socket, linger enabled, both cameras writing again. The observed long offline gap
was intentional. Both latest daytime JPEGs exist and match database sizes.
Keogram 137 remains byte-identical after the observed cleanup work: a protected
night-output sample passes, without claiming exhaustive five-day retention.
Task rows correlated with existing sample timelines support production cleanup
concurrent with generation; per-minute second-task identity was not recorded.

The remaining cadence issue is now diagnosed: queue depths 3/4/5 deliberately add
22.5/30/37.5 seconds to the configured 45-second interval. Production logs match
this formula and show delay removal when the queue drains. This protects processing
from overload; **constant equal 45-second cadence under load is not certified**.
No acquisition/scheduling change was made. Current available logs from 00:18:51
through 07:43:10 contain no ERROR/CRITICAL/Traceback; rotation limits this claim.
The earlier Starlink HTTP 403 remains an external-provider failure with cached
catalog retained.

What remains, without starting another 24-hour run:
- Correct and verify the recurring IMX708 startup loss demonstrated by seven new
  timeouts on 21 October. Recovery works, but repeated lost attempts remain a defect.
- Verify the pending global SQLite fork/pool guard and retry diagnostics against a
  real forked Flask engine, checkpoint checkout behavior, real BUSY/BUSY_SNAPSHOT,
  image/panorama inserts and FITS registration. The 01:35 FITS lock remains open
  until that candidate passes and is deployed with bounded recovery evidence.
  The focused regression is `hybrid_sqlite_fork_pool_test.py`,
  `hybrid_sqlite_checkpoint_flow_test.py`, `hybrid_sqlite_retry_diagnostics_test.py`,
  `hybrid_image_insert_contention_test.py` and `hybrid_fits_registration_test.py`;
  a full-suite repeat is reserved for a broader diff, a focused failure or the
  release policy before deployment.
- Hardware/network-changing effects and external integrations require the actual
  device/provider and recovery arrangements if they become applicable. They are
  absent or unused on this installation and are not marked passed.

The three previously unmatched ordinary-user archive controls are closed by the
[native localhost handoff](../testing/evidence/hybrid-ordinary-user-handoff-20261020.json):
filters, detail/back navigation and original FITS receipt. The fixture is disposable
SQLite/files on the Raspberry and is not described as a production account check.
The historical Output 3 and Tasks 12729 identities do not create new work because
later evidence exercises the same current download contracts.

[Bounded evidence](../testing/evidence/hybrid-remaining-verification-20261020.json).

The following list preserves the previous checkpoint; this section supersedes
its already-resolved scope descriptions.

Current remaining work:
- Observe the corrected generation overwrite lifecycle in sustained operation.
  Previously the Keogram/Startrail worker deleted old outputs before rendering
  with `TIMELAPSE_OVERWRITE=True`. The correction preserves them until publish,
  passes isolated failure, rollback, recovery and transfer tests, and is deployed
  in `cffd7002` (runtime fix `4b694b3e`).
  The 211-case regression had 210 passes and one test-default-path failure; that
  entrypoint passes after correcting its default, with application sources unchanged.
  [Evidence](../testing/evidence/hybrid-overwrite-safety-20261018.json). Production
  regeneration of preserved products is not used as an acceptance shortcut.
- Verify sustained production generation/cleanup concurrency. The dedicated cleanup
  worker and scoped generation protection are deployed in `884f2337` after
  209 Python/compile and 35 JavaScript checks passed. Both cameras resumed
  daytime JPEG capture around 15-second intervals; files match database sizes.
  Config 119 is unchanged; the short post-restart log has no errors.
  [Release evidence](../testing/evidence/hybrid-cleanup-concurrency-20261018.json).
- The timeout traces exposed an omitted five-second rpicam preview phase in the
  watchdog budget. `8af78847` includes that phase without changing autofocus,
  camera arguments or cadence. This explains a demonstrated premature timeout;
  it does not establish that all nine historical stalls had the same cause.
- Complete the scoped functional/control-matrix items below, distinguishing unavailable
  hardware and native handoffs from demonstrated product defects.
- Verify corrected runtime under night/load conditions. The 9–10 October 24-hour
  window closed without acceptance. On 18 October the user authorized a fresh
  24-hour period once corrections are verified and deployed, with lightweight
  collection and notifications only for problems or completion. That new period
  started at **18 October 17:12:10 CEST**, ending **19 October 17:12:10 CEST**,
  on `cffd7002`, configuration 119. Collector PID 488769 has ended; its persistent
  samples remain on the Pi. [Observation](../testing/evidence/hybrid-24h-observation-20261018.json).
  It ended at19October17:12:14CEST with1383samples and is **not passed**.
  Nine IMX708 timeouts, irregular night intervals and SQLite INSERT failures
  (panorama and image-worker exception) occurred in that historical window. Three service-query timeouts,
  one copytruncate gap and incomplete retention eligibility evidence are recorded
  separately. Capture/web remain active; no new period was started.

The sections below preserve earlier release evidence and their original scopes.

The three worker repairs are installed at `db5fc9c0`, followed by daytime-first
pressure cleanup in `677afbab`. Both cameras resumed
night FITS capture; new files match their camera/exposure records. Mini timelapses
9 and 10 generated from FITS, passed complete decoding and native browser playback,
and left original hashes unchanged. The short live check found no regular-log
errors. Pressure recovery reached 8 GiB after a controlled capture stop, preserving
24-hour images and generated outputs. [Release evidence](../testing/evidence/hybrid-worker-release-20261005.json).

The required 24-hour observation completed at 15:34 CEST on 5 October and stopped.
It found defects and evidence gaps, so it is **not an acceptance pass**, nor proof
of 24 hours on the corrected runtime. No new 24-hour period was started in the
reopened maintenance window. [Closure](../testing/evidence/hybrid-observation-closure-20261005.json).

Native Hybrid Controller Save & Sync now passes on two disposable profiles,
including the destination page and single-revision persistence. Other sync sections
and restore/key-reset flows retain their separate scopes.
[Evidence](../testing/evidence/hybrid-native-sync-20261005.json).
Detector/AI remain excluded. Sections below retain historical checkpoints and
scoped gaps; the current update above supersedes their activation/window status.

## Storage cleanup contention repair

Release `91139ece` now retries a contended SQLite deletion at most three times,
rolling back and rechecking pending transfers and generation before each attempt.
A real competing-writer test reproduces the thumbnail failure and verifies recovery;
persistent contention and unrelated errors still fail visibly. All 202 Python/compile
and 35 JavaScript checks pass with unchanged source hashes. Deployed at 22:57 CEST;
both cameras resumed with nonempty, exposure-matched FITS, services active and no
regular-log errors in the short post-restart check. This is not a new 24-hour period.
Before deployment, task 14958 exposed another failure: writing FAILED can itself
collide with SQLite and strand RUNNING work after worker exit. Its orphan row was
reconciled during maintenance. Follow-up release `1c607d16` writes FAILED using a
fresh conditional update, retries only SQLite contention, and never replays the
original effect. The real competing-writer/next-task test and all 202 Python/compile
checks pass; frontend sources are unchanged from the 35-check JavaScript pass.
It was deployed at 23:18 CEST with configuration 119 unchanged. Both cameras
resumed with matching nonempty FITS; services are active and the short log check
contains no errors. Persistent database outage remains outside bounded retry
recovery. A new 24-hour observation awaits the user’s decision after the previous
19:15 cutoff; none has been started. [Task-state evidence](../testing/evidence/hybrid-task-failure-20261005.json). [Evidence](../testing/evidence/hybrid-storage-contention-20261005.json).

## Archive download distinction

Library and Media Archive now distinguish processed image downloads from exact-exposure
FITS/RAW originals. Source matching is batched per page and requires the same camera
and timestamp; missing or ambiguous originals are explicitly unavailable. The change
preserves download authorization and stable archive pagination. Targeted real Flask
checks pass for both roles and both archive entrypoints. All 202 Python/compile checks and 35 JavaScript checks pass. Deployed as `7f93668b` with a web-only reload at 23:48 CEST; capture was not restarted.
Native camera-1 Library labels are verified, but the download receipt remains open
after the browser tool timed out. Both services were active at 08:35 CEST on 6 October.
[Evidence](../testing/evidence/hybrid-archive-downloads-20261005.json). Image-detail wording, exact FITS/RAW links and the recent-image lightbox
are corrected in `67b2db08`; native detail labels pass while browser download receipt and native lightbox remain open; this does not close whole-product acceptance.

## Latest release completed

The scientific archive implementation is deployed, with **198 Python/compile and
35 JavaScript checks** and an exact installed-source match. Both cameras resumed;
real FITS rendering matches saved JPEG pixels. That release initially used configuration 118; configuration 119 now activates
every-frame night FITS. Its sustained acquisition, generation and cleanup gates
remain open. [Release evidence](../testing/evidence/hybrid-scientific-archive-release-20261003.json).

Production Process FITS previews and received downloads now pass for administrator
on both cameras. Four generated-media Open clicks also pass for camera 2.
The filtered Tasks CSV now has a browser download-event receipt (4 October,
filter task 14738, one row); downloaded-file byte integrity was not inspected.
The previous isolated Save & Sync timeout is resolved for Hybrid Controller by the 5 October native/persistence check.
[Follow-up](../testing/evidence/hybrid-acceptance-followup-20261003.json).

The earlier day-end timeout's cause remains unproven; a successful short encode
is not sustained worst-case-load certification. Avoid same-SD online full database
backups: a prior attempt overlapped filesystem stalls. Use the documented rollback
and preserve the existing database.

On 2 October the user confirmed mini-video 7 downloads and opens, both Users CSV/Excel
files save and are readable, and the simulator copies an URL. [Confirmation and
limits](../testing/evidence/hybrid-user-confirmed-delivery-20261002.json).

## Native archive acceptance — 18 October

Production admin now has actual browser receipts for camera-1 daytime JPEG and
same-exposure nighttime FITS/processed JPEG. The received FITS hash matches the
Pi original; both JPEGs decode at 4608 × 2592. The nighttime permanent JPEG is
absent, so that export exercises source-only archive rendering.
The camera-2 Keograms archive also has a production admin browser receipt: from
Keograms, filtering ASI678MC and opening Browse complete archive with Night selected
returned five nighttime rows for camera 2/profile `asi678mc`. Download original on
Keogram 137 delivered `allsky-keogram_ccd2_20261017_night_1792300480.jpg`; its local
SHA-256 matches the Pi at `848a0347a67df8849e932fc2f718a5772741c5b9cc5c121c68e4798a0094725c`
and it decodes at 944 × 700. This certifies the archive's per-row download only;
the summary page exposes Open read-only rather than a separate download control.
Mini task 17177 was submitted from the native form, completed successfully and
produced seven frames at 2 FPS plus a thumbnail. Native playback reached its
natural 3.5-second end without errors; all five FITS inputs retained their hashes.
At the bounded 16:42:27 CEST production query after the 16:03:56 restart, camera 1
had 153 frames from 16:04:22 through 16:42:27 and camera 2 had 153 frames from
16:04:18 through 16:42:23. Both had a maximum 16-second gap and no gap over 20
seconds. The post-restart log had no capture errors; its sole ERROR was the already
recorded Starlink HTTP 403 at 16:09:14. This is a short runtime check, not a 24-hour
or sustained-night pass.
These close the corresponding camera-1 admin receipt/native-submit scopes, not
all roles, families or runtime acceptance. [Evidence](../testing/evidence/hybrid-native-archive-mini-20261018.json).

The historical generation record marked “Worker execution: blocked” predates the
real isolated Keogram/Startrail/FFmpeg flow. Its exact request-to-effect scope has
now been linked to the newer proof and the passing 18 October regression in the
route register; it does not require repeating a destructive production generation.
Native browser submission and scientific/live acceptance remain distinct scopes.

## Named interaction gaps

These are known gaps in addition to the complete matrix reconciliation. Closing
this table alone does not certify all discovered controls.

| Page or flow | Missing proof or remaining scope |
| --- | --- |
| Settings export | User now confirms snapshot download after receiving its location. Notifications CSV/Excel and Tasks CSV are also user-confirmed; these do not establish byte integrity for every export variant. |
| Source media and Output downloads | User confirms FITS, IMX708 mini-video and Highlights receipt. Exact historical mini-video 3 identity remains unspecified. Highlights now has separate processed/FITS/RAW choices, deployed and tested; source files are offered only for the same recorded exposure. |
| Camera profiles | Hybrid Controller native Save & Sync and persistence passed on 5 October; other section variants remain distinct. [capability gating](../testing/evidence/hybrid-profile-sync-capability-20261001.json) is already covered separately. |
| Geometry | User now explicitly confirms Geometry Copy values after receiving its location. This is user-reported completion, not an automated clipboard comparison; simulator copying has separate confirmation. |
| Generated-media pages | Keograms camera-2 footer navigation now passes for Generate media, Realtime and Long Term, including preserved profile and decoded realtime pixels ([evidence](../testing/evidence/hybrid-keogram-footer-20261005.json)). Keogram 137 now has a matching production admin per-row original-download receipt from the filtered camera-2 nighttime archive ([evidence](../testing/evidence/hybrid-native-archive-mini-20261018.json)). Other families still require reconciliation with current templates; the Keograms summary page offers Open read-only, so this receipt does not certify a direct summary-page download. |
| Account | Admin and ordinary-user save/login flows have [isolated native evidence](../testing/evidence/hybrid-account-native-20260914.json). This does not imply a production password change was performed; do not repeat destructive credential changes merely to erase a historical record. |
| Restore | All four reset/flush combinations pass real HTTP persistence/cleanup on disposable fixtures. Native file upload and restore with both flags off also passed on 5 October. A fresh-process HTTP check also proves rejection of the old session and successful new login after key activation. On 20 October the user completed native flush/key-reset and subsequent login: both keys changed, only revision 2 remained, zero tasks; logs show the old session redirected to login and successful new login ([evidence](../testing/evidence/hybrid-native-restore-final-20261020.json)). Activation used an isolated in-process key reload; fresh-process coverage is separate. Production keys/history were not changed. |
| Generation and playback | Preserve successful live worker/output proofs for their exact camera/family. Camera-1 timelapse 71 now has natural-end playback evidence; mini-video 7 has generation and natural-end proof. Mini-generation recovery and other families must retain their own evidence scopes. |
| Network | Network-changing effects require identified connections and a recovery plan in the agreed physical-access window. Read-only discovery is not evidence for reconnect/disconnect effects. |

## Control matrix reconciliation

The 5 October discovery now records 99 GET entries, 500 contexts and 7,377 static
identities. No render defects or searched placeholder phrases were found. The
10 added identities and one reused button identity are linked to explicit scoped
automated/native evidence in the [control delta](../testing/evidence/hybrid-control-delta-20261005.json).
Two old link identities are retired. This updates discovery and the changed-control
proof mapping; it does not certify all existing or JavaScript-generated controls.


Use the [route register](hybrid-acceptance-route-register.json) and its linked
control discovery, retaining role, camera/profile, prerequisites, expected
request/effect and source revision. Historical blocked/defect records retain their original outcomes and now include full or partial later resolutions and current applicability. They are not a count of current product defects: some combine scopes, refer to older controls, or
already have narrower later evidence. The 7,369 static identities likewise are
not 7,369 independently failed functions.

For each historical record, retain the original outcome and attach a scoped
resolution only when the later evidence matches. Examples of prohibited joins:

- production admin FITS preview receipt does not certify ordinary-user delivery;
- panorama-video receipt does not certify original FITS or mini-video receipt;
- keyboard Home navigation does not by itself prove the earlier pointer click;
- isolated account mutation does not imply a production account was modified;
- an absent device does not make its supported implementation obsolete.

The collector now resolves field labels correctly while preserving identities;
this is discovery quality, not functional acceptance. JavaScript-created controls,
modals, keyboard and narrow-screen variants remain part of the matrix. A case is
`superato`, `difetto`, `bloccato`, or `non applicabile` with a specific reason;
blocked cases are never counted as passed.

## Limits already disclosed

Unavailable GPIO/focuser/fan/heater/sensors and disabled external integrations
remain untested live and supported. No new peripheral or cloud account is required
merely to remove that disclosure. Clean builds on every OS/architecture and a
mathematical absence-of-bugs proof were not requested acceptance gates. Preserve
necessary migrations, shared drivers/workers, APIs and dependencies rather than
removing them to make the project look smaller.

The user revoked the 20:00 deadline on 1 October and authorized continuing to
completion. Deploy and bounded live checks can resume. This historical exclusion of the 24-hour
observation was superseded on 4 October; use the completed-but-not-passed
observation and current maintenance scope at the top of this document.

## Accepted archive change — 2 October (implemented candidate; not deployed)

The user selected configurable day/night storage, defaulting to JPEG-only by day
and FITS-only for every retained exposure at night, with optional external storage.
FITS samples must remain untouched by preview/export stretch and overlays. The
rendered result must preserve the current appearance, not the existing simplified
FITS preview. This selects the archive formats. Capacity and minimum retention still need a separate decision before production activation.

Completion requires one shared capture/replay rendering path with recorded
processing settings and acquisition/overlay context; bounded derivative caching;
source-aware Library, Loop, downloads and all generated-media readers; configurable
local/external roots with missing-mount handling; retention/forecast accounting for
sources and cache; and tests for byte-preserved FITS, matching rendered output,
per-camera isolation, day/night transitions, cache eviction/regeneration and output
generation after cached previews are removed. Existing media remain readable.
Do not activate source-only capture while any supported consumer still requires a
permanent JPEG, or count the preview timestamp fix as completing this change.

The first implementation step extracts capture's tone, geometry/color and
presentation stages into `indi_allsky/image_rendering.py`. Their original worker
positions are protected by a whole-method AST fingerprint, plus call/error parity
and real 8/16-bit day/night pixel comparisons including an alpha overlay. This
separates rendering from capture effects but does not yet provide archived-context
replay: calibration/stack/AWB context, label inputs, reusable source access, caching
and consumers still need completion before source-only storage is activated.

FITS serialization now attaches a versioned `HYBRID_CTX` extension containing
camera/profile, exposure timestamp and offset, gain/binning, night/moon mode,
calibration phase and an explicit whitelist of rendering settings. The primary
pixels and other FITS extensions are preserved. Plain/gzip round trips and writer
integration are covered. Unknown credentials/configuration sections are excluded;
metadata serialization failure preserves the exposure without context and logs the
failure. `complete_render_recipe` is explicitly false: this source-save snapshot
must not be mistaken for the later stack/AWB/detection/label replay context. This
change remains in the isolated candidate until the archive release is ready.

Formatted label replay is implemented in the candidate. Capture records the text
actually painted and an immutable style snapshot in image metadata; replay uses
those values rather than reevaluating live templates/sensors/hooks. Empty, disabled
and focus modes remain distinct. Pillow/OpenCV pixel parity is tested against the
frozen previous rendering methods; OpenCV focus coordinates are corrected. This label component alone does not enable FITS-only archival.

Presentation replay is implemented in the isolated candidate. Capture records the
actual logo, moon, lightgraph, downloaded overlay pixels, font assets and orb draw
operations for saved FITS exposures. Replay uses immutable, deduplicated assets
and recorded clocks, without fetching current overlays or recalculating positions.
No URL credentials or precise GPS coordinates are added to presentation metadata.
Real-pixel comparisons cover changed/deleted original resources and all orb modes;
missing assets fail explicitly. The source file itself remains untouched.

This stage starts from an already prepared display image. Full source replay still
needs earlier calibration/stack/AWB/detection state, the final portable recipe,
source-aware consumers, bounded cache and asset retention, storage policy UI and
external-volume handling. Production remains on the existing saving policy until
those requirements are complete; this candidate must not be deployed alone.

The source-rendering candidate now connects the shared stages into a complete
FITS-to-display renderer and the authenticated FITS preview route. It records
actual AWB gains, CCM, effective bit depth, denoise time gate, cached LUTs, masks,
detection drawings, presentation and formatted labels. The final display digest
and source-file digest guard against mismatched or non-identical reconstruction.
FITS primary pixels remain byte-preserved; no live calibration/provider lookup is
performed on read. The final recipe currently persists with the matching image
record, not yet as a complete portable FITS extension.

For ordinary post-calibration single exposures no extra full-frame basis is saved.
Pre-calibration FITS and multi-frame stacks retain their prepared linear array as a
lossless asset, preserving their actual calibration/registration result without
recomputing it against today's dark files or stacking history. This increases
storage for these optional modes and must be counted by forecasting/retention;
those assets cannot be treated as evictable JPEG cache. Shared resources/LUTs are
deduplicated. Lifecycle and the remaining consumers/settings remain required.

The full replay test exposed denoise luminance compensation exceeding the physical
12-bit range (4096+), causing the stretch LUT to fail. Display denoise now clamps
integer output to effective camera bit depth; in-range values retain the previous
result. This is an intentional correction, distinct from capture/replay parity.

The candidate now has a bounded disposable JPEG cache for authenticated FITS
previews (512 MiB and 1024 entries by default in the cache service). It keys the
entire recipe and source file identity, validates cached bytes, serializes identical
reconstructions across processes, and evicts by last access. Responses own their
bytes, so eviction does not invalidate an in-flight HTTP response. Failed cache
writes do not prevent serving a successfully reconstructed image. Source files and
lossless rendering assets live outside this eviction scope.

HTTP tests cover a cache hit without calling the renderer, eviction followed by
identical reconstruction without a permanent JPEG, and explicit recipe/asset
errors on reconstruction. Cache capacity controls still need the storage Settings
UI. Streaming/task consumers, scientific asset retention and format-policy
activation remain separate unfinished work; cache support does not enable nightly
FITS-only capture by itself.

Real-resolution measurements showed that cache misses are memory-intensive. Cold
reconstruction is therefore serialized across processes sharing the cache, even
when persistence is disabled; existing cache hits do not wait for the reconstruction
slot. A failed reconstruction lock produces an explicit error rather than bypassing
the memory bound. Tests exercise distinct simultaneous keys and an immediate warm
read sharing a lock stripe with a blocked cold request. Cache byte-write failure
still permits delivery once rendering has completed successfully.

Generator integration must not pass ordinary evictable cache paths to FFmpeg's
long-lived symlink sequence: eviction could invalidate a running job. Use an
explicit frame reader/stream (or a bounded lease), preserving exposure timestamps
from the database rather than cache access times. `getFilesystemPath()` must remain
free of rendering effects because delete/validation paths also call it. Test video
and keogram/startrail generation after eviction, plus missing-source failures,
before enabling source-only capture.


Keogram and startrail generation now read a missing display frame through its
saved FITS recipe. The reader validates camera, source ID and exposure date and
returns owned pixels, never a cache filename. Both consumers receive the exposure
time from the database for reconstructed frames; the startrail sequence stamps
its generated frames with that same time. Historical JPEG/PNG/other display files
retain their decoder and timestamp behavior. Missing legacy files remain skipped;
a missing or invalid scientific source with a saved recipe fails the task through
the existing worker failure boundary.

The source replay integration test compares actual keogram pixels, startrail
pixels and generated startrail sequence bytes/timestamps against the equivalent
JPEG input after clearing the cache between frames. The historical scientific
worker fingerprint is retained by normalizing only the reviewed frame-reader loop
against its pre-extraction fixture. Panorama source generation remains unfinished;
this does not activate FITS-only
capture or change installed production services.


Ordinary and mini timelapse tasks now select the source-aware generator in the
working candidate. Existing display-only archives retain the prior file-sequence
path. If a selected display frame is absent but has a saved source recipe, the
mixed sequence is ordered by database exposure date and streamed as lossless PNG
frames to FFmpeg. No reconstructed sequence is retained on disk. Deflicker, scaling,
codec options, initial skip and wrap-keogram processing remain available. The wrap
implementation is compared against its frozen previous implementation, and the
source path avoids an additional lossy intermediate compression.

Targeted tests encode and decode real videos for source-only, mixed and ordinary
archives, compare standard/wrap and deflicker modes, and exercise actual FITS replay
with an evicted cache. Failure tests verify child termination, partial-output
removal and draining of stderr larger than the pipe buffer. The full 192
Python/compile checks and 35 JavaScript checks pass with unchanged source hashes.
[Evidence](../testing/evidence/hybrid-timelapse-stream-20261003.json). No deployment
or storage-policy activation has occurred.


The working candidate now finalizes the rendering recipe inside `HYBRID_CTX`
after labeling and before queueing FITS uploads. Publication writes a sibling
file, verifies all scientific HDUs, syncs it and atomically replaces the source;
permissions and timestamps are preserved. The source table receives the final
size and recipe before upload metadata is constructed. A failed publication keeps
the scientific source and the existing processed-JPEG capture path.

The new basis version hashes scientific HDUs independently of the context, avoiding
a self-referential file hash; old basis versions retain their original whole-file
integrity check. Authenticated preview and generation readers can use the embedded
recipe without the Image JSON recipe copy. Shared lossless assets stay under
`.render-assets` on the archive volume and must accompany that volume; publication
does not make each FITS a self-contained bundle of duplicate fonts/masks/arrays.
Typed/gzip, failure, upload-order and actual replay tests pass. The full 193
Python/compile checks and 35 JavaScript checks pass with unchanged source hashes.
[Evidence](../testing/evidence/hybrid-source-publication-20261003.json). Deployment
and format-policy activation remain pending.


Source-only image records now use the existing public media endpoint for rendered
JPEG delivery, preserving optional media-login and camera-local access policy.
Library, detail and Loop keep their existing model URL contract. Processed-image
downloads return JPEG bytes with an explicit overlay label in the public viewer;
the scientific FITS download remains separate and authenticated. Validation checks
the associated FITS without creating a display file or adding rendering effects to
`getFilesystemPath()`. Conditional and range requests work for generated bytes.

Actual Flask route tests pass for admin/ordinary users, Library/detail/Loop links,
inline/attachment delivery, optional anonymous media, cross-camera rejection and
nonlocal policy. These are isolated test-client proofs, not production browser
acceptance. All 193 Python/compile and 35 JavaScript checks pass with unchanged source hashes
([evidence](../testing/evidence/hybrid-source-display-20261003.json)). No capture defaults are activated;
source-aware upload effects, asset lifecycle, storage policy and external-volume
safety remain unfinished.


The next working candidate supplies a short-lived rendered file to image upload
adapters when an Image record explicitly uses FITS storage. FTP, S3, Sync and MQTT
retain their existing destination and task-completion paths. The filename suffix
selects real JPEG, PNG, WebP or TIFF encoding; PNG/TIFF preserve rendered pixels.
Temporary files are removed after success or failure, and remote metadata omits
local source IDs and rendering assets. S3 keys remain based on the logical archive
path. Tests exercise actual FITS reconstruction and upload worker methods with
isolated non-network adapters. All 193 Python/compile and 35 JavaScript checks pass with unchanged source hashes
([evidence](../testing/evidence/hybrid-source-upload-20261003.json)). No production
policy is enabled by this work. Reconstructed display files do not yet recreate the
legacy JPEG/WebP EXIF block; acquisition metadata remains in the original FITS.


The retention candidate protects a FITS file while a source-only Image record
references it. Ordinary FITS deletion refuses before removing its thumbnail.
Pressure cleanup recognizes missing display files backed by FITS, protects the
image during transfers of either representation and checks again after candidate
selection. It removes an eligible expired Image record first; the unreferenced
FITS can then be reclaimed under the existing source-retention policy, potentially
on the next bounded pass. Historical JPEG-plus-FITS acquisitions retain independent
retention. All 194 Python/compile and 35 JavaScript checks pass with unchanged
source hashes ([evidence](../testing/evidence/hybrid-source-retention-20261003.json)).
Rendering asset garbage collection and external-volume checks remain open.


The rendering-asset lifecycle candidate leases the asset store during image
processing and source reconstruction. Under storage pressure, a nonblocking
exclusive collector scans Image/FITS references completely before removing any
managed files. Imported FITS without a database recipe are inspected for embedded
context; an unreadable source aborts collection. Referenced files, young files
(24-hour grace), symlinks and unrelated files are preserved. Old managed crash
partials are collectible. Scientific asset publication syncs both the file and
directory; disposable font derivatives remain reconstructible from their NPZ.
The storage forecast adds actual rendering-asset bytes and newly created assets
in its observation window. All 195 Python/compile and 35 JavaScript checks pass
with unchanged source hashes ([evidence](../testing/evidence/hybrid-render-asset-lifecycle-20261003.json)). The
collector's cost on a large source-only archive needs measurement before final
production acceptance. Capture format policy remains inactive.


The archive-format candidate adds day/night choices to Storage Protection:
FITS only, processed image only, both, or existing detailed output settings
(including RAW). The recommended form defaults are night FITS/day processed image
and compressed FITS. Existing configurations without IMAGE_ARCHIVE remain on
their previous output settings until an explicit save and capture restart.
Processed format follows IMAGE_FILE_TYPE (JPEG on the current installation).
Both cameras can now save FITS at every exposure even when the secondary profile
uses images-only routing. Extra upload gates still apply. Temporary FITS files are
closed/removed on failures and publication precedes the database record.

A source-only transition commits its valid FITS reference before unlinking the
redundant processed image, after thumbnails and post-hooks. Missing/incomplete
source context or unlink failure retains the processed image. Latest images and
small thumbnails remain. MQTT uses the image record rather than a removed local
filename, preserving the existing flat MQTT payload. Archive choices are validated
on settings save and config restore. Five targeted integration/parity suites pass;
the initial 196-check Python/compile regression and 35 JavaScript checks pass.
The final 196-check Python/compile regression and 35 JavaScript checks also pass
with unchanged source hashes ([evidence](../testing/evidence/hybrid-archive-policy-20261003.json)).
This includes frozen capture EXIF in FITS context and its replay into JPEG/WebP,
with scientific pixels and decoded JPEG pixels unchanged. External-volume checks and actual capacity/retention
preflight are still required before production activation.


The volume-protection candidate now pins the configured archive directory to its
block-filesystem UUID. Capture waits for a missing disk; media access and cleanup
reject the wrong or absent filesystem. The installer checks the pinned disk before
rewriting archive paths. Tests cover absence, wrong-device and read-only cases,
reconnection, supervisor shutdown, and administrator recovery through Settings
while the disk is offline. These are automated simulations, not a physical USB
removal test. The final 198-check Python/compile regression and all 35 JavaScript checks passed
with matching source hashes ([evidence](../testing/evidence/hybrid-archive-volume-20261003.json)).
Native Settings saves and the no-UUID error were verified on an isolated database.
No production storage policy or archive format has changed. External setup and recovery instructions are
in HYBRID_DEPLOYMENT.md.


Every-frame FITS and complete context publication now use lossless gzip level 1.
On temporary copies of actual Raspberry FITS, publication fell from 9.18 to 1.87
seconds for camera 1 and 1.83 to 1.43 seconds for camera 2. Scientific digests were
unchanged. Camera 1's compressed file grew from 12.44 to 14.47 MB; camera 2's
became slightly smaller. These are daytime samples, not proof of night capacity or
full capture cadence. All 198 Python/compile and 35 JavaScript checks passed with
matching source hashes ([evidence](../testing/evidence/hybrid-fast-fits-20261003.json)).
Legacy scheduled compression remains unchanged. Deployment and live acceptance
are still required before closing the archive change.


On 3 October the archive candidate was deployed as `3d87c9aa` with unchanged
configuration 118. Both cameras resumed and both first new FITS replayed to pixels
identical to their saved JPEGs. Native Now, Settings and the FITS detail/preview
link were checked. [Deployment and exact limits](../testing/evidence/hybrid-scientific-archive-release-20261003.json).
The every-frame night policy remains inactive until storage capacity/retention is
resolved. Source-only live acquisition, generation and retention acceptance remain
open; deployment alone does not close those gates.


Four historical Open read-only gaps are resolved by native production clicks on
3 October for administrator, camera 2 / asi678mc: Keograms, Startrails, Startrail
Videos and Panorama. Original image decoding and natural video completion were
observed. Mini-timelapse opening also passed. Download receipt and other roles or
cameras remain separate scopes. [Evidence](../testing/evidence/hybrid-generated-open-links-20261003.json).


Process FITS verified in production on 3 October: administrator generated and
downloaded camera 1 PNG (4608×2592) and camera 2 JPEG (3840×2160). Both files
were received on the Mac; original FITS hashes and configuration 118 are unchanged.
This resolves the historical production preview and download-receipt gaps for
this exact scope, not every role or parameter combination.
[Evidence](../testing/evidence/hybrid-process-fits-production-20261003.json).

## 9 October deployment

Deployed `67b2db08` (image detail/originals and lightbox links) and `13c46cd7`
(FITS registration retry). All 203 Python/compile and 35 JavaScript checks pass.
Installed application hashes match the regression. Capture restarted at 15:11 CEST
with config 119 unchanged. At 15:31 both services were active and both cameras had
new nonempty daytime JPEGs, with about 6.6 GiB available. Three orphan FITS sources
were recovered on 6 October without changing source bytes or deleting JPEGs.
The native detail page presents separate processed/FITS downloads; the browser
download tool timed out again, so receipt remains unverified. No new 24-hour
observation has been started. Night operation on this release and the other
acceptance matrix gaps remain open.
[Registration/recovery evidence](../testing/evidence/hybrid-fits-registration-defect-20261006.json).
[Detail evidence](../testing/evidence/hybrid-image-download-details-20261009.json).


### 9 October scoped native follow-up

Production administrator checks passed for image lightboxes on both cameras:
processed pixels decoded, Next/Right updated the exact image-detail target,
Escape closed the preview and restored focus, and AJAX camera switching preserved
camera/profile scope. Selecting and deselecting toggled Download selected correctly;
no receipt is claimed. At 390×844, the ZWO lightbox and detail navigation worked
without horizontal overflow. Existing morning FITS 9974 and 9976 decoded at full
camera dimensions; the FITS lightbox exposed its original download and cleared the
inapplicable image-detail link. This closes only these scoped native controls.
[Native evidence](../testing/evidence/hybrid-image-download-details-20261009.json).

Read-only postdeploy capture evidence covers 15:12–15:51 CEST: 156/157 daytime
frames, median interval 15 seconds and maximum 16 seconds for both cameras,
no interval above 30 seconds, no pending queued/running/manual tasks, and both
latest JPEG files present with matching byte counts. Available storage was
6,962,888,704 bytes. The earlier Starlink catalogue HTTP 403 remains a provider
limitation; this is not an error-free or 24-hour acceptance claim.
[Cadence evidence](../testing/evidence/hybrid-postdeploy-cadence-20261009.json).

Actual browser download receipt for the new detail flow, credential-reset native
handoff, unavailable external hardware/integrations, and the wider matrix remain
separate open scopes. A new 24-hour period has been requested after the expired
user deadline; it has not been started or backdated. No code changed during these
checks, so the passing 203 Python/compile and 35 JavaScript regression was not repeated.


### Authorized corrected-runtime window

The user now authorizes evaluating 9 October 2026 15:11:14 CEST through
10 October 15:11:14 CEST, starting from the recorded FITS-registration deployment.
This supersedes the expired cutoff and the pending authorization above. Existing
evidence will be evaluated retrospectively; no collector start is backdated.
SSH access timed out on the evening check, so live collection is unconfirmed.
The hourly heartbeat is active to recover access and evaluate the window; gaps
remain open and no automatic extension is authorized.
[Window record](../testing/evidence/hybrid-24h-observation-20261009.json).

At 22:16 CEST SSH recovered. Observer 2357391 now collects until the original
10 October 15:11:14 CEST endpoint. Its real start is 20:16:14 UTC, not the
retrospective window start. Both cameras are saving FITS and services are active.
Retrospective records show one IMX708 timeout with a 93-second frame gap and a
failed long-term keogram sample under SQLite contention; these remain defects,
not a passing 24-hour result. Frame/task records and selected error logs are
preserved under /home/eric/hybrid-observation-20261009.


## 10 October: authorized observation closed, acceptance not passed

The observer ended at 13:11:14.502 UTC (15:11 CEST) and its process is absent.
Capture and web remain active; no acquisition or scheduling changes were made.
978 samples cover the actual collection from 9 October 20:16 UTC, while preserved
retrospective frame records extend coverage back to the authorized deployment.
Merged evidence contains 3,832 frames per camera across day and night. The sampled
5,225 frames had no missing files at observation time. Final queue was drained and
7,489,327,104 bytes were free; minimum sampled free space was 3,648,069,632 bytes.

Acceptance is **not passed**: IMX708 exposure timeouts, SQLite keogram/FITS metadata
failures and image-worker recovery, irregular night intervals (maximum 96/90 s),
and generation delaying queued cleanup remain real defects. Automatic queue and
space recovery was observed but does not erase those defects. The first 7h05m lack
continuous service/space samples, and one log rotation gap remains a coverage limit.
The wider functional matrix and five-day retention validation are not closed by
this run. No automatic extension is authorized. The hourly automation is paused
at closure; future correction and verification must not be reported as covered
by this historical runtime window.

[Final evidence](../testing/evidence/hybrid-24h-observation-20261009.json).


## 18 October: SQLite persistence correction validated

FITS metadata finalization and long-term keogram insertion now retry only SQLite
BUSY/LOCKED failures in bounded fresh transactions. FITS publication and uploads
are not replayed; concurrent metadata is reloaded after rollback. Persistent
failures remain visible. Real SQLite conflict tests reproduce the old failures
and pass after the change. All 205 Python/compile checks and 35 JavaScript checks
passed, including one installer rerun after restoring an omitted test archive file.
Source hashes match. Deployed as a40ec0e0 on 18 October at 15:29:15 CEST,
with config 119 unchanged and rollback files under
`/home/eric/hybrid-backups/sqlite-finalization-20261018/`. Capture and web are active.
Seven postrestart JPEG frames per camera were checked: all files exist with
matching database byte counts; intervals were 15 seconds for camera 1 and
13–16 seconds for camera 2. HTTPS Now redirects anonymous requests to login.
No ERROR/CRITICAL/Traceback lines appeared through 15:31:24. This brief daytime
check does not validate nighttime FITS or eliminate intermittent failures. Timeout,
cleanup scheduling and remaining functional acceptance are separate open items.
[Evidence](../testing/evidence/hybrid-fits-metadata-retry-20261012.json).


## 19 October: timeout budget and image INSERT corrections deployed

Camera commit `8af78847` preserves the rpicam command and autofocus while including
the implicit five-second preview in the watchdog budget. A hardware A/B rejected
a faster preview shortcut because autofocus had not finished. SQLite commit
`0284f14a` retries image and panorama INSERTs only for BUSY/LOCKED, with rollback,
fresh ORM rows and a three-attempt limit; filesystem and upload effects are not
replayed. Real competing-writer tests verify recovery, bounded failure and metadata
preservation. All 213 Python/compile checks passed with unchanged source hashes;
35 prior JavaScript checks remain applicable because JavaScript is unchanged.

Production matches the tested manifest. Capture and web restarted by 21:15:51 CEST
with config 119 unchanged. The brief check ended at 21:20:48: five IMX708 and six
ZWO nighttime FITS files exist and match database sizes; three per camera also
decoded and passed FITS verification. Intervals were 45–46 and 43–45 seconds.
No new ERROR/CRITICAL/Traceback or libcamera timeout was found; queue empty,
services active without automatic restarts, 7,264,223,232 bytes free.

This closes the targeted correction and brief verification, not sustained runtime
acceptance or the remaining functional matrix. The prior 24-hour result stays
not passed. The user explicitly requested no new 24-hour period; automation stays
paused. Rollback source files and previous revision are retained in
`/home/eric/hybrid-backups/timeout-sqlite-20261019/`. To roll back these code-only
changes, restore the two files from `previous-code.tar.gz` in the production root
and restart capture/web; no database or configuration restore is required.
[Release evidence](../testing/evidence/hybrid-timeout-sqlite-release-20261019.json).

### User confirmations — 20 October 2026

The user confirms whole mobile previews and no upload integrations in use. Live upload checks are not applicable to the current installation, not marked passed. The isolated native restore handoff is complete; its server and tunnel were stopped. No new 24-hour observation was started. Other acceptance limits remain unchanged.

## 20 October: shared cadence candidate verified

Hybrid now owns normal multicamera start rounds, common queue-pressure decisions, readiness/pre-hook coordination and bounded participant recovery in `SharedCaptureCadence`. Exposure/gain settings remain independent. Single-camera, focus and scientific SQM schedules are preserved. This candidate is not yet deployed.

The isolated Raspberry regression passed all 216 Python/compile entrypoints with unchanged frozen sources. A subsequent two-file compatibility correction preserves existing equal/reversed queue thresholds; six affected entrypoints passed after the exact delta was verified. JavaScript was unchanged and not rerun. See [candidate evidence](../testing/evidence/hybrid-shared-cadence-candidate-20261020.json).

Production deployment and bounded two-camera confirmation remain pending. The earlier IMX708 timeout remains unexplained; this coordinator is not claimed as its fix. No new 24-hour observation is authorized or started.

### Shared cadence deployed and bounded verification

`df58afaa` activated on Raspberry at 20:24:40 CEST, configuration 119 unchanged; MainPID 120191, no restart loop. Three shared rounds gave both profiles the same epoch, 45.048 and 45.027 seconds apart, with no pressure delay or state repairs. All six resulting FITS exist, match database sizes, have FITS SIMPLE headers and pass complete gzip decompression/CRC. The bounded log scan reported no ERROR/CRITICAL/Traceback/SQLite-lock message. Backup: `/home/eric/hybrid-backups/shared-cadence-20261020`. This closes the bounded shared-cadence deployment check, not the earlier unexplained timeout or whole-product acceptance. No new 24-hour observation.

### 24 October: balanced midtones on both cameras

Deployed `dda37307`, configuration 120 (previous 119): adaptive MTF v2, target 0.30, daytime enabled and resolved true for both profiles. Corrected median normalization/MAD and deterministic degenerate handling; legacy recipes retain v1 arithmetic and new recipes freeze their algorithm version. Gamma lookup invalidation now follows live gamma changes while preserving frozen archived lookups. Exposure/gain/cadence settings were unchanged.

Six targeted entrypoints passed on the Raspberry, including actual archived-source replay, publication and media/generation flows. Both live images decode and show Stretch On. Visual inspection of frames 364912/364913 confirms brighter midtones; subsequent frames resumed the 15-second shared daytime cadence. Six measured stretches took 0.0903–0.1166 seconds. The bounded post-restart scan contained 432 log lines and no ERROR/CRITICAL/Traceback. This is a daytime smoke check, not long-term stability or a new night observation.

Backup of prior code/config: `/home/eric/hybrid-backups/midtone-stretch-20261024` (private on Pi). For rollback, restore the three backed-up Python files to their respective paths and save the backed-up config through the config API as a new revision, then restart capture/web. Scientific source files and historical recipes remain unchanged. No new 24-hour period; previous runtime acceptance limits remain open. [Evidence](../testing/evidence/hybrid-midtone-stretch-20261024.json).
