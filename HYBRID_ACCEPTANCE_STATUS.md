# Hybrid acceptance status

Updated 21 September 2026. **Classic removal is deployed; whole-product acceptance remains open.**
The separate 24-hour day/night observation is deferred by the user. Detector and AI implementation are outside this release.

## Installed product

The Raspberry runs `f6975d5f5501b00aa3407dd5da7442b73f793952`.
Classic frontend classes, templates and exclusive assets are physically removed.
Hybrid is the only UI and requires login. Shared workers, drivers, public media/API handlers and navigation redirects remain supported components.
Later main commits document acceptance; they do not change the installed runtime.

The 780-file installed source manifest matches the tested snapshot:
`5a7a89f36f27062b391f17e4fd59cbe491b5d0e38c2f0992f407c8604d08e851`.
All 162 Python entrypoints and 34 JavaScript tests passed, including startup and flows without Classic, Full Config parity, Settings, Safe Actions and Product Spine.
This automated result does not certify every native control or hardware effect.

The deployment preserved configuration revision 117, Flask configuration,
user files and capture PID 1566. Only the web service restarted (PID 740426).
The database backup passed integrity checking in 36.51 seconds.
Use [current deployment and rollback instructions](HYBRID_DEPLOYMENT.md), not commands from historical mission reports.

## Post-removal evidence

| Scope | Verified result | Evidence |
| --- | --- | --- |
| Settings, isolated browser | Login, both camera previews, edit/save, value after reload, snapshot restore and original value recovered | [Release acceptance](testing/evidence/hybrid-retirement-final-native-20260921.json) |
| Production UI and capture | Both Now images decoded; Full Settings search works; source manifest matches; configuration and capture process preserved | [Release acceptance](testing/evidence/hybrid-retirement-final-native-20260921.json) |
| Real mini timelapses | Tasks 12718/12719 succeeded for cameras 1/2. Each output has 9 frames at 2 fps, verified with ffprobe and complete browser playback | [Live generation](testing/evidence/hybrid-mini-generation-post-classic-20260921.json) |
| Loop | Both cameras, individual filters, history, speed selection, native forward/reverse playback and return to forward playback | [Loop acceptance](testing/evidence/hybrid-loop-post-classic-20260921.json) |
| RAW Loop with absent data | Correct empty state on both cameras and navigation back to processed Loop; the live RAW table is empty | [Loop acceptance](testing/evidence/hybrid-loop-post-classic-20260921.json) |
| Satellite provider | Real requests validated 156 visual, 10,695 Starlink and 20 station entries; production catalog unchanged; real task outcomes visible in Hybrid. Historical 403 not reproduced | [Provider recheck](testing/evidence/hybrid-satellite-recheck-20260921.json) |
| Browser downloads | Video and empty CSV clicks returned, but no matching file was found in Mac Downloads; delivery remains unverified | [Open download checks](testing/evidence/hybrid-download-delivery-post-classic-20260921.json) |

Earlier evidence remains useful for its stated revision, role, camera and environment.
It is not automatically recertified against the current release.
The [route evidence register](docs/hybrid-acceptance-route-register.md) links each recorded control to its source.

## Inventory and coverage limits

The current isolated discovery covers all 99 registered Hybrid GET entries in
505 role/camera/detail contexts: 376 rendered and 129 blocked or redirected,
with no rendering defects and no matches for the selected placeholder phrases.
It records 43,978 control occurrences, including repetition across roles,
cameras, aliases and shared navigation. This is not a count of unique features.

The full report is `/home/eric/hybrid-post-classic-controls-20260921.json`, SHA-256
`58ad27d871ee1a648bcef25d3d7b518b4aa8a5ac795849486bd92ddf56670ee4`.
Its source manifest and limitations are recorded in `current_control_discovery`
in the [JSON register](docs/hybrid-acceptance-route-register.json).

Discovery does not mark clicks passed. JavaScript-generated controls, keyboard/mobile behavior,
mutating requests and observable effects require their own evidence.
The full control/effect matrix is not yet certified; blocked cases are not passes.
Absence of selected placeholder phrases is not proof that every function is implemented.

## Remaining acceptance gates

- Finish the control/effect matrix, including uncovered role, camera/profile, mobile, empty/stale-data and failure cases. Reuse applicable evidence and preserve its scope.
- Resolve native download delivery: establish whether the browser has a pending Save dialog or another destination, then verify the received file against its source. Do not substitute a successful HTTP request for native delivery.
- Complete live effects beyond the two short mini timelapses, including dedicated-data cleanup/deletion and test-destination uploads. Previous automatic and isolated tests remain separately labeled.
- Identify devices and arrange recovery/physical presence before interrupting networking, disks or GPIO. Current user clarification is pending. Do not claim unavailable hardware as tested.
- Complete the required repository/dependency review and operational cleanup. Retain useful shared backend, public contracts, user data, migrations and supported functions.
- Cold power-loss recovery has not been directly tested. The earlier warm reboot/startup evidence is in [reboot acceptance](testing/evidence/hybrid-reboot-autostart-20260914.json).

The 24-hour observation is explicitly excluded from this run and is not passed.
No new detector/AI algorithms or simulated classifications belong to these closure tasks.

## Reproducing checks and reading history

Use [the regression instructions](testing/HYBRID_REGRESSION.md) and
[the acceptance workflow](docs/HYBRID_ACCEPTANCE_WORKFLOW.md).
Run discovery and integration tests in the isolated runtime, never against production data.
[Capture cadence documentation](HYBRID_CAPTURE_CADENCE.md) describes shared intervals and independent exposure/gain behavior.

The former 4,412-line chronological status log is preserved in Git at `ad41d847`:
`git show ad41d847:HYBRID_ACCEPTANCE_STATUS.md`.
All individual evidence JSON files remain in `testing/evidence/`.
Those historical entries include superseded candidates, counts, deadlines and rollback targets;
they must not be read as the current installation state.
