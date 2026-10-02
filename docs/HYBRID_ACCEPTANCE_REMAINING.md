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
request/effect and source revision. There are 25 historical blocked/defect
records without a fully passed resolution after the scoped resolutions, including three user-confirmed CSV/Excel and simulator results on 2 October and the combined Users Copy/CSV/Excel record. That number is not
25 current product defects: some combine scopes, refer to older controls, or
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
