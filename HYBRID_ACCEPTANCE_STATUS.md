# Hybrid acceptance status

Updated 30 September 2026. **Classic frontend removal is deployed. Whole-product acceptance is not complete.**
The user deferred the separate 24-hour day/night test and detector/AI implementation.
Those activities are outside this acceptance run, not passed tests.

## Current installation and regression

The latest application change is `4d2e08fa`; subsequent commits add tests and evidence.
Hybrid is the only UI and requires login. Useful shared backend, drivers, workers,
public media URLs and integration APIs remain. Configuration revision is 118.

The unchanged application passed **174 Python/compile entrypoints and 34 JavaScript tests**.
The latest runtime evidence includes the exact report hashes, web-only deployment,
unchanged capture PID 1565, zero automatic restarts, and decoded frames from both
cameras at 23:21:38 / 23:21:24. These are dated observations, not continuous monitoring.
[Latest runtime regression and deployment](testing/evidence/hybrid-full-config-input-20260930.json).
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
| Download delivery | User-received panorama video exactly matches the Raspberry file hash. This proves that individual download, not all export families | [Received panorama](testing/evidence/hybrid-generation-followup-20260930.json) |
| Cleanup | All four native buttons deleted exactly the expected synthetic files/rows; other camera preserved; archive reflects deletion | [Native effects](testing/evidence/hybrid-cleanup-native-effects-20260930.json) |
| Links after cleanup | 240 download responses and 48 Image/FITS detail responses: removed entries return 404, retained downloads preserve exact bytes | [Regression](testing/evidence/hybrid-cleanup-stale-links-20260930.json) |
| Full Config admission | Malformed/non-object JSON rejected before WTForms; no config revision, content change or queued task; valid parser semantics preserved | [Full Config](testing/evidence/hybrid-full-config-input-20260930.json) |
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
   `970d1799`: 99 GET entries, 505 contexts, 376 rendered and 129 blocked/redirected;
   43,978 occurrences grouped into 7,368 exact page/control identities. These are
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
