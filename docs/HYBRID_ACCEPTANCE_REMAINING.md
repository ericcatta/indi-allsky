# Remaining Hybrid acceptance work

Updated 9 October 2026. Classic frontend removal is deployed; whole-product
acceptance remains open. The user reopened maintenance after the 19:15 cutoff.

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

## Named interaction gaps

These are known gaps in addition to the complete matrix reconciliation. Closing
this table alone does not certify all discovered controls.

| Page or flow | Missing proof or remaining scope |
| --- | --- |
| Settings export | User now confirms snapshot download after receiving its location. Notifications CSV/Excel and Tasks CSV are also user-confirmed; these do not establish byte integrity for every export variant. |
| Source media and Output downloads | User confirms FITS, IMX708 mini-video and Highlights receipt. Exact historical mini-video 3 identity remains unspecified. Highlights now has separate processed/FITS/RAW choices, deployed and tested; source files are offered only for the same recorded exposure. |
| Camera profiles | Hybrid Controller native Save & Sync and persistence passed on 5 October; other section variants remain distinct. [capability gating](../testing/evidence/hybrid-profile-sync-capability-20261001.json) is already covered separately. |
| Geometry | User now explicitly confirms Geometry Copy values after receiving its location. This is user-reported completion, not an automated clipboard comparison; simulator copying has separate confirmation. |
| Generated-media pages | Keograms camera-2 footer navigation now passes for Generate media, Realtime and Long Term, including preserved profile and decoded realtime pixels ([evidence](../testing/evidence/hybrid-keogram-footer-20261005.json)). Other families and per-row downloads still require reconciliation with current templates. Old “Open read-only” observations must be mapped to the current controls, not blindly repeated or marked passed from a different Library link. |
| Account | Admin and ordinary-user save/login flows have [isolated native evidence](../testing/evidence/hybrid-account-native-20260914.json). This does not imply a production password change was performed; do not repeat destructive credential changes merely to erase a historical record. |
| Restore | All four reset/flush combinations pass real HTTP persistence/cleanup on disposable fixtures. Native file upload and restore with both flags off also passed on 5 October. A fresh-process HTTP check also proves rejection of the old session and successful new login after key activation. The native flush/key-reset flow awaits the prepared user handoff; production keys/history were not changed. |
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
request/effect and source revision. There are 17 historical blocked/defect
records without a fully passed resolution after the scoped resolutions through 3 October, including the later Process FITS production preview and download evidence. That number is not
17 current product defects: some combine scopes, refer to older controls, or
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
