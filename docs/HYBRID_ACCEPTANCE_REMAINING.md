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
| Settings export, Notifications CSV and Excel, Tasks CSV | Received file with expected content. HTTP 200 and completed click are insufficient. Preserve the existing failed/inconclusive receipt observations. |
| Source media and Output downloads | Original FITS, historical camera-1 mini-video 3 and Highlights delivery remain separate from the successfully received camera-2 panorama video and FITS preview exports. |
| Camera profiles | Native Save & Sync confirmation and result; [capability gating](../testing/evidence/hybrid-profile-sync-capability-20261001.json) is already covered separately. |
| Geometry | Actual clipboard contents after copy remain unverified. Simulator link copying was confirmed by the user on 2 October; this does not certify Geometry. |
| Generated-media pages | Exact footer links and per-row downloads still require reconciliation with current templates. Old “Open read-only” observations must be mapped to the current controls, not blindly repeated or marked passed from a different Library link. |
| Account | Admin and ordinary-user save/login flows have [isolated native evidence](../testing/evidence/hybrid-account-native-20260914.json). This does not imply a production password change was performed; do not repeat destructive credential changes merely to erase a historical record. |
| Restore | All four reset/flush combinations now pass real HTTP persistence/cleanup on disposable fixtures. Native destructive confirmation and post-key-reset login remain separate; production keys/history were not changed. |
| Generation and playback | Preserve successful live worker/output proofs for their exact camera/family. Camera-1 timelapse 71 now has natural-end playback evidence; mini-video 7 has generation and natural-end proof. Mini-generation recovery and other families must retain their own evidence scopes. |
| Network | Network-changing effects require identified connections and a recovery plan in the agreed physical-access window. Read-only discovery is not evidence for reconnect/disconnect effects. |

## Control matrix reconciliation

Use the [route register](hybrid-acceptance-route-register.json) and its linked
control discovery, retaining role, camera/profile, prerequisites, expected
request/effect and source revision. There are 28 historical blocked/defect
records without a fully passed resolution after the scoped resolutions, including three user-confirmed CSV/Excel and simulator results on 2 October and the combined Users Copy/CSV/Excel record. That number is not
28 current product defects: some combine scopes, refer to older controls, or
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
