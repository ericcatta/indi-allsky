# Remaining Hybrid acceptance work

Checked against deployed source `48c2eddb` and the recorded evidence on 1 October 2026.
This is a work queue, not a coverage percentage or a replacement for the control
matrix. Classic removal is deployed; whole-product acceptance remains open.
The 24-hour observation and detector/AI remain outside the agreed current run.

## Latest release completed

The combined candidate is deployed: 182 Python/compile and 35 JavaScript checks
passed, exact installed source hashes match, both cameras resumed, and all four
Keogram links passed native checks. Task 14234 generated and played a mini-video;
both cameras captured during encoding. See the [release evidence](../testing/evidence/hybrid-combined-release-20261001.json).
The earlier day-end timeout's cause remains unproven; the successful short encode
must not be represented as sustained worst-case-load certification. A same-SD
backup caused overlapping filesystem waits and was interrupted; its incomplete
copy is not a usable backup. Rollback uses retained code files, not the old DB.

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
| Camera profiles | Native Save & Sync confirmation and result; [capability gating](../testing/evidence/hybrid-profile-sync-capability-20261001.json) is already covered separately. |
| Geometry | User now explicitly confirms Geometry Copy values after receiving its location. This is user-reported completion, not an automated clipboard comparison; simulator copying has separate confirmation. |
| Generated-media pages | Exact footer links and per-row downloads still require reconciliation with current templates. Old “Open read-only” observations must be mapped to the current controls, not blindly repeated or marked passed from a different Library link. |
| Account | Admin and ordinary-user save/login flows have [isolated native evidence](../testing/evidence/hybrid-account-native-20260914.json). This does not imply a production password change was performed; do not repeat destructive credential changes merely to erase a historical record. |
| Restore | All four reset/flush combinations now pass real HTTP persistence/cleanup on disposable fixtures. Native destructive confirmation and post-key-reset login remain separate; production keys/history were not changed. |
| Generation and playback | Preserve successful live worker/output proofs for their exact camera/family. Camera-1 timelapse 71 now has natural-end playback evidence; mini-video 7 has generation and natural-end proof. Mini-generation recovery and other families must retain their own evidence scopes. |
| Network | Network-changing effects require identified connections and a recovery plan in the agreed physical-access window. Read-only discovery is not evidence for reconnect/disconnect effects. |

## Control matrix reconciliation

Use the [route register](hybrid-acceptance-route-register.json) and its linked
control discovery, retaining role, camera/profile, prerequisites, expected
request/effect and source revision. There are 23 historical blocked/defect
records without a fully passed resolution after the scoped resolutions, including three user-confirmed CSV/Excel and simulator results on 2 October and the combined Users Copy/CSV/Excel record. That number is not
23 current product defects: some combine scopes, refer to older controls, or
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
completion. Deploy and bounded live checks can resume; the separate 24-hour
observation remains excluded. Do not request the expired window again.

## Accepted archive change — 2 October (not implemented)

The user selected configurable day/night storage, defaulting to JPEG-only by day
and FITS-only for every retained exposure at night, with optional external storage.
FITS samples must remain untouched by preview/export stretch and overlays. The
rendered result must preserve the current appearance, not the existing simplified
FITS preview. This supersedes the pending retention-choice question.

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
