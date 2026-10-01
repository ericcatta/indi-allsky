# Hybrid acceptance status

Updated 1 October 2026. **Classic frontend removal is deployed. Whole-product acceptance is not complete.**
The user deferred the separate 24-hour day/night test and detector/AI implementation.
Those activities are outside this acceptance run, not passed tests.

## Current installation and regression

The latest application change is `04388e02`; subsequent commits add evidence.
All HTTP callers of the Settings save/full-save/upload-restore services now pass
the request's base revision into transactional persistence. Six real concurrent
Flask cases cover Timelapse, storage protection, camera mode, camera selection,
Full Config and upload restore: the first profile edit is retained and the stale
competitor rejected. Rejected requests do not enqueue reload or flush history.
The regression passed **181 Python/compile and 35 JavaScript checks**.
Web-only reload preserved capture PID 537392; both new frames decoded at
17:51:14 / 17:51:11. Configuration remains 118.
[Config writer evidence and limits](testing/evidence/hybrid-config-writers-concurrency-20261001.json).
This protects overlapping requests, not sequential submissions of old forms
without a form revision token. Non-HTTP writers are outside this guardrail.
The preceding profile protection is `0afac099`; the AWB sync capability fix is
`db205760`, whose native confirmation-dialog acceptance remains open.
[Profile evidence](testing/evidence/hybrid-profile-concurrency-20261001.json),
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

Other bounded checks—including Loop, users, notifications, observatory tools,
mobile layouts, provider failures and operations—remain linked in the
[route evidence register](docs/hybrid-acceptance-route-register.md).
Each original record states its role, revision, environment and limitations.
A historical check is not automatically a current full-domain certification.

## Remaining acceptance gates

1. **Complete the control/effect matrix.** The latest static inventory is from
   `51a248ee`: 99 GET entries, 500 executed contexts, 376 rendered and 124 blocked;
   seven non-template entries require dedicated tests. The discovery includes
   43,978 occurrences grouped into 7,369 exact page/control identities. These are
   discovery counts, not successful clicks. The route register links evidence but
   does not yet certify every identity, dynamic control, role, camera/profile,
   narrow-screen variant and error path. Unobserved cases remain open.
2. **Confirm native export receipt.** Configuration 118 and current CSV/Excel
   exports have no verified received file. Native clicks produced no newly observed
   matching file in Mac Downloads. Manual user verification is requested; do not
   share configuration contents. [Latest attempts](testing/evidence/hybrid-export-receipt-20260930.json).
3. **Resolve the historical storage/publication uncertainty.** A bounded encoding
   load on 30 September showed 45–46-second capture intervals and 3.31–5.35-second
   capture-to-observed latency, with no read errors. Earlier multi-tens-of-seconds
   I/O stalls were not reproduced, but are not proven resolved. No additional
   performance change was justified by that sample. [Measurement](testing/evidence/hybrid-storage-load-20260930.json).
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
