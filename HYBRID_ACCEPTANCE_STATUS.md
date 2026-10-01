# Hybrid acceptance status

Updated 1 October 2026. **Classic frontend removal is deployed. Whole-product acceptance is not complete.**
The user deferred the separate 24-hour day/night test and detector/AI implementation.
Those activities are outside this acceptance run, not passed tests.

## Current installation and regression

The latest application change is `117d22fb`: panorama previews retain atomic
replacement without redundant file synchronization. Archives still synchronize.
A three-minute live trace changed from 18 preview fsync calls (4.408 seconds of
wait) to zero, retaining 12 archive calls. Both cameras resumed after controlled
capture restart (PID 771992), and their panorama previews decode and match their
archives exactly. All 181 Python/compile and 35 JavaScript checks passed.
[Measurement, deployment and limits](testing/evidence/hybrid-panorama-preview-sync-20261001.json).

The preceding application change is `365f77e5`.
VirtualSky now keeps export disabled while a frame refresh is pending, including
when preview controls, resize or reset redraw the map. The timing defect was
reproduced before correction. Native verification confirms the disabled state,
recovery and a received PNG after completion; the browser loads virtualsky-003.
All seven numeric preview controls have bounded native geometry/render evidence,
including latitude validation, empty-input rejection and reset.
The regression passed **181 Python/compile and 35 JavaScript checks**.
Web-only reload preserved capture PID 537392; both new frames decoded at
18:28:19 / 18:28:26. Configuration remains 118.
[VirtualSky alignment, correction and limits](testing/evidence/hybrid-virtualsky-alignment-20261001.json).

The preceding `04388e02` change protects overlapping HTTP Settings writes, including
Full Config and upload restore. It does not protect sequential submissions of old
forms without a revision token or certify non-HTTP writers.
[Config writer evidence](testing/evidence/hybrid-config-writers-concurrency-20261001.json).
AWB sync native confirmation-dialog acceptance remains open.
[AWB sync evidence](testing/evidence/hybrid-profile-sync-capability-20261001.json).

The preceding worker recovery change is `ffb4335c`.
Video/upload failure logging now uses the already captured task ID before rollback,
so an expired ORM object cannot turn a recoverable commit failure into a second
exception. Both failures were reproduced with real isolated database constraints.
All 178 Python/compile and 35 JavaScript checks passed with unchanged test sources.
After controlled capture restart at 16:17:27, both new frames decoded at
16:17:54 / 16:17:50; capture PID 537392 is active with zero automatic restarts.
[Recovery evidence and limits](testing/evidence/hybrid-worker-rollback-20261001.json).

The preceding application change `f21f87d5` corrected Observatory disk usage.
Observatory now reports the same disk-use percentage as Storage, excluding system-reserved
blocks from usable capacity. Its twenty page-specific links were exercised in the
native browser, including camera-scoped media and completed asynchronous tool loads.
The latest full regression passed 178 Python/compile and 35 JavaScript checks;
web-only reload preserved capture PID 472545. [Evidence and scope](testing/evidence/hybrid-observatory-controls-20261001.json).

History controls now reject malformed inputs; aggregate Loop queries enforce per-camera delivery policies and the existing result ceiling. [History validation](testing/evidence/hybrid-history-query-20261001.json).

Geometry now rejects invalid azimuth before copy/review; the updated asset version is verified in production. 175 Python checks and 35 JavaScript tests passed. [Validation and deployment](testing/evidence/hybrid-geometry-validation-20261001.json).

The geometry-to-Keogram link now preserves camera/profile. Its 175 Python and 34 JavaScript checks passed; native source-to-Settings navigation now passes for both cameras/profiles after network recovery. Both recent frames decoded on 1 October at 13:05:00 / 13:05:07. [Latest change](testing/evidence/hybrid-geometry-scope-20261001.json).

Hybrid is the only UI and requires login. Useful shared backend, drivers, workers,
public media URLs and integration APIs remain. Configuration revision is 118.

Camera Info now handles missing sensor/lens metadata without crashing or inventing zero measurements. Partial known values remain visible. The current application passed **181 Python/compile entrypoints and 35 JavaScript tests**.
Video task preparation now shares the effect failure boundary: malformed tasks and
route setup errors terminate as FAILED, with rollback, while the next valid job can run.
Upload preparation/execution now also terminates failed tasks without abandoning
subsequent work. Remote S3 deletion completes without attempting local cleanup;
unexpected connection failures close the adapter. Real external effects remain
unverified because integrations are disabled.
The full regression passed again (178 Python/compile and 35 JavaScript).
At that upload release, capture PID 472545 was active with zero automatic
restarts; both cameras' new frames decoded at 15:27:37 / 15:27:32 on 1 October.
These are bounded observations, not continuous monitoring.
[Upload regression and deployment](testing/evidence/hybrid-upload-failure-20261001.json).
The cleanup extension is included in this regression. All 719 Full Config fields are interpreted in Hybrid (202 through domain parsers and 517 in its orchestrator); frozen legacy fingerprints remain unchanged.

## Verified outcomes and their limits

| Domain | Proven result | Evidence |
| --- | --- | --- |
| Classic retirement | Frontend classes, templates and exclusive assets removed; isolated and deployed Hybrid acceptance; useful backend retained | [Retirement](testing/evidence/hybrid-retirement-final-native-20260921.json) |
| Authentication | Anonymous Hybrid entries require login; public media/API contracts retain their own policies | [Production boundary](testing/evidence/hybrid-live-auth-boundary-20260921.json) |
| Settings | Native isolated save/reload/history/restore; restored value verified. Concurrent snapshot restore admits one commit and rejects the stale competitor | [Native flow](testing/evidence/hybrid-retirement-final-native-20260921.json), [snapshot concurrency](testing/evidence/hybrid-snapshot-acceptance-20260930.json) |
| Settings context | Camera/profile preserved through Settings, history, snapshot detail and return; malformed uploaded restore files rejected without new revision | [Navigation](testing/evidence/hybrid-settings-chain-20260929.json), [invalid files](testing/evidence/hybrid-restore-invalid-files-native-20260930.json) |
| Media navigation | Image/timelapse list, detail and return retain camera/profile; wrong-camera references rejected | [Navigation](testing/evidence/hybrid-media-detail-context-20260930.json) |
| Generation | Both cameras' day output tasks succeeded; camera-2 generated videos fully decoded and played to natural end in browser | [Generation](testing/evidence/hybrid-generation-followup-20260930.json) |
| Download delivery | User-received panorama video exactly matches the Raspberry file hash. Both camera mask downloads match the server files by SHA-256. Both cameras' JPEG/PNG FITS previews were received and fully decoded; source hashes remained unchanged. These prove individual downloads, not all export families | [Received panorama](testing/evidence/hybrid-generation-followup-20260930.json), [received masks](testing/evidence/hybrid-mask-download-native-20261001.json), [FITS previews](testing/evidence/hybrid-fits-preview-receipt-20261001.json) |
| Cleanup | All four native buttons deleted exactly the expected synthetic files/rows; other camera preserved; archive reflects deletion | [Native effects](testing/evidence/hybrid-cleanup-native-effects-20260930.json) |
| Links after cleanup | 240 download responses and 48 Image/FITS detail responses: removed entries return 404, retained downloads preserve exact bytes | [Regression](testing/evidence/hybrid-cleanup-stale-links-20260930.json) |
| Full Config admission | Malformed/non-object JSON rejected before WTForms; no config revision, content change or queued task; valid parser semantics preserved | [Full Config](testing/evidence/hybrid-full-config-input-20260930.json) |
| Shared AJAX admission | 13 handlers reject malformed/non-object JSON; role/CSRF, anonymous notification behavior and unchanged state verified | [Admission](testing/evidence/hybrid-ajax-json-admission-20260930.json) |
| Action validation | Malformed JSON rejected before discovery, INDI startup or abort planning; role/CSRF checks and valid camera-specific abort enqueue retained | [Validation](testing/evidence/hybrid-action-input-20260930.json) |
| Cold autostart | After orderly shutdown and physical power reconnection, web/INDI/capture start without SSH; both new images decode | [Cold start](testing/evidence/hybrid-cold-start-20260930.json) |
| Storage settings | Capacity estimate restored; same-value native save preserved the 5 GiB / 8 GiB / 3-day policy and other configuration | [Storage](testing/evidence/hybrid-storage-estimate-fix-20260929.json) |
| Hardware availability | Native GPIO and focuser controls correctly disabled with a reason when no driver is configured; no physical effects claimed | [Prerequisites](testing/evidence/hybrid-hardware-prerequisites-20260930.json) |
| Runtime cleanup | Unreachable dashboard template/helpers and unused action catalog removed; active services and regression retained | [Entry/template](testing/evidence/hybrid-entry-retirement-20260930.json), [helpers](testing/evidence/hybrid-dashboard-helper-retirement-20260930.json), [catalog](testing/evidence/hybrid-action-catalog-retirement-20260930.json) |

Both VirtualSky overlay export buttons now have native receipt evidence: the two
896×504 PNG previews were received on the Mac, fully decoded and visually checked
for camera frame plus sky overlay. This does not close configuration/CSV/Excel
receipts or certify every overlay control. [VirtualSky exports](testing/evidence/hybrid-virtualsky-export-native-20261001.json).

VirtualSky also rejects zero diameter with a disabled export and recovers after
Reset preview on camera 2. CSV/Excel native clicks still return HTTP 200 without
a verified received file; PNG success does not close that separate transport
check. [Validation and export limits](testing/evidence/hybrid-export-validation-native-20261001.json).

All six VirtualSky object switches were individually exercised on camera 2 and
verified in received PNGs, followed by a verified default reset. This establishes
the named display effects, not pointing accuracy or every option combination.
[Object switches](testing/evidence/hybrid-virtualsky-flags-native-20261001.json).

Other bounded checks—including Loop, users, notifications, observatory tools,
mobile layouts, provider failures and operations—remain linked in the
[route evidence register](docs/hybrid-acceptance-route-register.md).
Each original record states its role, revision, environment and limitations.
A historical check is not automatically a current full-domain certification.

Storage cleanup now has additional isolated evidence for tasks published after
candidate selection (generation, image upload and thumbnail upload) and an
outside-root thumbnail symlink. Every case preserves the protected files and
parent database row. The full regression passed again: 181 Python/compile and
35 JavaScript checks, with unchanged source hashes. This is test coverage only;
production policy and application code are unchanged. It does not close the
historical I/O latency gate. [Storage review](testing/evidence/hybrid-storage-review-20261001.json).

A bounded automatic night transition check observed five consecutive 45-second
intervals for each camera with independent exposure/gain. Task 14212 completed
the day keogram; its native output link opened camera-1 record 71 and the fully
decoded file matches saved dimensions/size. The remaining day-end tasks were
still running/queued and are not certified by this check.
[Night transition and keogram](testing/evidence/hybrid-night-transition-keogram-20261001.json).

## Remaining acceptance gates

1. **Complete the control/effect matrix.** The latest static inventory is from
   `51a248ee`: 99 GET entries, 500 executed contexts, 376 rendered and 124 blocked;
   [Reconciliation](testing/evidence/hybrid-discovery-reconciliation-20261001.json)
   identifies 89 direct login redirects, 11 anonymous Settings aliases, eight
   expected navigation redirects and 16 fixture-blocked process/DBus contexts;
   these are not 124 demonstrated product defects. Original control statuses are
   unchanged. All seven non-template entries have dedicated contract tests
   passing in the latest regression; native receipts and hardware effects remain
   separate. The discovery includes
   43,978 occurrences grouped into 7,369 exact page/control identities. These are
   discovery counts, not successful clicks. The route register links evidence but
   does not yet certify every identity, dynamic control, role, camera/profile,
   narrow-screen variant and error path. Unobserved cases remain open.
2. **Confirm native export receipt.** Configuration 118 and current CSV/Excel
   exports have no verified received file. Native clicks produced no newly observed
   matching file in Mac Downloads. Manual user verification is requested; do not
   share configuration contents. [Latest attempts](testing/evidence/hybrid-export-receipt-20260930.json).
3. **Resolve remaining storage/publication stalls.** Existing logs from 18:00–19:00
   on 1 October show median 15-second cadence in both cameras, but publication
   delays up to 44/38 seconds and one 35-second processing interval. Live syscall
   tracing subsequently measured actual write/sync waits. `117d22fb` removes the
   redundant panorama-preview synchronization; its bounded post-deploy trace
   retains archive sync and shows no call above 0.5 seconds. Other stalls are not
   proven resolved and the original long interval is not attributed exclusively
   to preview synchronization. [Measurements and limits](testing/evidence/hybrid-panorama-preview-sync-20261001.json).
4. **Record unavailable physical/integration effects as untested.** No GPIO,
   focuser, fan, heater or external sensor driver is assigned in configuration 118.
   The user reports no external disks/storage or upload integrations in use.
   S3/MQTT/Sync/YouTube are disabled; physical connections and external test
   destinations are unavailable/unidentified. Mocked adapter tests and disabled UI
   states do not establish physical effects. Preserve these supported functions.
5. **Finish the remaining repository/backend review.** The existing
   [dependency review](docs/HYBRID_DEPENDENCIES.md), installer checks and specific
   retirements above establish their scopes, not an exhaustive absence of dead
   code, concurrency defects or resource leaks. Clean builds on every supported
   platform have not been performed and must not be implied.

Abrupt power-loss durability is untested. The successful cold start followed an
orderly shutdown; do not conflate the two. No abrupt-power-cut experiment or
24-hour observation is required by the current agreed run.

## Reproduction and history

Use [regression instructions](testing/HYBRID_REGRESSION.md), the
[acceptance workflow](docs/HYBRID_ACCEPTANCE_WORKFLOW.md), and
[deployment/rollback instructions](HYBRID_DEPLOYMENT.md).
Keep synthetic databases separate from production and scope destructive checks
to dedicated disposable data. See [capture policy](HYBRID_CAPTURE_CADENCE.md)
for shared intervals and independent exposure/gain behavior.

All individual evidence files remain in `testing/evidence/`. The preceding
chronological status document is preserved at `a2d53040`:
`git show a2d53040:HYBRID_ACCEPTANCE_STATUS.md`.
Its historical process IDs, counts and intermediate open/closed states must not
be read as the current installation status.
