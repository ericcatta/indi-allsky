# Remaining Hybrid acceptance work

Checked against source `584f066f` and the recorded evidence on 1 October 2026.
This is a work queue, not a coverage percentage or a replacement for the control
matrix. Classic removal is deployed; whole-product acceptance remains open.
The 24-hour observation and detector/AI remain outside the agreed current run.

## Candidate and release

| Work | Existing evidence | Required closure |
| --- | --- | --- |
| IMX708 missed exposure under video encoding | [Observed timeout](../testing/evidence/hybrid-night-load-20261001.json): one 90-second interval and recovery. [Output correction](../testing/evidence/hybrid-libcamera-output-fix-20261001.json): separate pipe deadlock reproduced and fixed in source. | Full combined regression, controlled deployment and bounded acquisition under encoder load. Do not equate the reproduced pipe mechanism with a proven cause of the observed timeout. |
| Keogram tool navigation | [Before/after isolated test](../testing/evidence/hybrid-keogram-links-20261001.json): both links preserve camera/profile and load the expected destination camera. | Combined regression and native clicks after deployment, both cameras. |
| Combined candidate regression | The rpicam suite completed 182 cases, with one syslog timing failure that passed unchanged on targeted recheck; subsequent collector and Keogram changes have targeted checks. | Run the exact combined source once before release. Preserve failures and source hashes; do not call the earlier report a clean combined pass. |
| Final delivery | Local/main are synchronized; production intentionally has not received the pending application changes after the live-test cutoff. | Agreed maintenance window, source/version/backup checks, deployment, affected real effects and fresh frames, final diff, operational instructions and synchronized release. |

## Named interaction gaps

These are known gaps in addition to the complete matrix reconciliation. Closing
this table alone does not certify all discovered controls.

| Page or flow | Missing proof or remaining scope |
| --- | --- |
| Settings export, Users/Notifications CSV and Excel, Tasks CSV | Received file with expected content. HTTP 200 and completed click are insufficient. Preserve the existing failed/inconclusive receipt observations. |
| Source media and Output downloads | Original FITS, the previously checked mini-timelapse output and Highlights delivery remain separate from the successfully received camera-2 panorama video and FITS preview exports. |
| Camera profiles | Native Save & Sync confirmation and result; [capability gating](../testing/evidence/hybrid-profile-sync-capability-20261001.json) is already covered separately. |
| Camera Simulator and Geometry | Actual clipboard contents after copy. A success message alone did not establish delivery. Preserve the successful geometry scope correction and numeric-validation evidence. |
| Generated-media pages | Exact footer links and per-row downloads still require reconciliation with current templates. Old “Open read-only” observations must be mapped to the current controls, not blindly repeated or marked passed from a different Library link. |
| Account | Admin and ordinary-user save/login flows have [isolated native evidence](../testing/evidence/hybrid-account-native-20260914.json). This does not imply a production password change was performed; do not repeat destructive credential changes merely to erase a historical record. |
| Restore | Confirm the precise remaining reset/flush variants against isolated tests and native evidence; keep destructive variants on disposable configuration fixtures. |
| Generation and playback | Preserve successful live worker/output proofs for their exact camera/family. Camera-1 timelapse 71 opened successfully but natural-end playback was not recorded. Mini-generation recovery and other families must retain their own evidence scopes. |
| Network | Network-changing effects require identified connections and a recovery plan in the agreed physical-access window. Read-only discovery is not evidence for reconnect/disconnect effects. |

## Control matrix reconciliation

Use the [route register](hybrid-acceptance-route-register.json) and its linked
control discovery, retaining role, camera/profile, prerequisites, expected
request/effect and source revision. There are 38 historical blocked/defect
records without a fully passed resolution as of this review. That number is not
38 current product defects: some combine scopes, refer to older controls, or
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

No live test or deployment is authorized beyond the expired 20:00 window until
the user supplies a new window. A new window has been requested; no answer is
assumed from elapsed time. No 24-hour test should be started as part of it.
