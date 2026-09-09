> Current production baseline (2026-09-09): cd45148f, capture start 12:12:35 CEST,
> PID 188464. Earlier observation periods are interrupted and cannot be added.
> Earliest possible 24-hour completion: 2026-09-10 12:12:35 CEST. See
> testing/evidence/hybrid-maintenance-deployment-2026-09-09.json.

# Shared capture cadence and independent exposure control

Current observation baseline: production release `498ba959`, capture PID 4112458,
started **2026-09-08 23:21:17 Europe/Zurich**. The earlier 21:15:41 window ended
at the controlled release restart. Configuration revision 110 and cadence
settings are unchanged. Initial post-release images pass; 24-hour day/night
acceptance is still open, earliest September 9 at 23:21:17. See
`testing/evidence/hybrid-release-deployment-2026-09-08.json` and the latest
production-release section of `HYBRID_ACCEPTANCE_STATUS.md` for backup/rollback.

With `MULTI_CAMERA_CAPTURE_ENABLE`, `EXPOSURE_PERIOD_DAY` and
`EXPOSURE_PERIOD` are the shared day and night start-to-start intervals.
Camera Settings → Acquisition exposes them as **Shared interval Day/Night**.
Saving either profile changes the interval for all cameras; exposure, gain and
other acquisition parameters still belong to the selected profile. Save & Sync
continues to copy its explicitly selected per-camera acquisition fields.
Restart capture after saving to apply the new configuration.

Existing per-profile `exposure.period` / `period_day` keys are retained for
compatibility but do not override the shared interval in multicamera mode.
Single-camera cadence behavior is unchanged.

Each camera's effective exposure ceiling is the lowest of its configured
maximum, its hardware maximum, and the common interval minus six seconds.
The allowance comes from measured IMX708/rpicam overhead of approximately
5.4 seconds beyond the requested exposure. With a 40-second configured maximum,
15/45-second intervals yield 9/39-second exposure ceilings. A camera with a
lower independent maximum keeps that lower ceiling.

Invalid nonfinite intervals and intervals incompatible with configured minimum
exposures are rejected before a configuration revision is persisted, including
Full Config and restore. Camera-specific hardware limits are also checked at
capture time. `[CAPTURE_CADENCE]` records the effective ceiling;
`[CAPTURE_CADENCE_LATE]` reports starts more than one second beyond the target.
Hardware stalls, queue pressure and explicit focus/SQM measurements can still
interrupt normal cadence; this is not a hard real-time guarantee. Focus and
scientific SQM exposures retain their explicit settings.

With automatic exposure/gain enabled:

- For a dark image, increase exposure up to the effective ceiling, then gain.
- For a bright image, decrease gain to its configured/hardware minimum, then
  decrease exposure. This includes normal, aggressive and confirmed small-error
  corrections; small corrections retain their trend confirmation and deadband.
- Disabled automatic gain remains manual. A target already reached holds both
  values. No brightness or detector results are fabricated.

The observed ZWO minimum is 0; the IMX708 driver minimum is 1.13. The deployment
configuration uses these minima independently. IMX708 gain can rise to 16;
ZWO retains maxima 200 day and 300 night/moonmode. The covered IMX708 can remain
underexposed even at its limits; that is distinct from missing captures.

## Verification and rollback

All 92 source-bound Python/compile checks pass; results are recorded in
`testing/evidence/hybrid-capture-cadence-2026-09-07.json`. The regression includes
Book 2, all Full Config fingerprints,
Settings contracts, Safe Actions, Product View Models/Spine and new tests for
all correction bands, both gain minima, driver exposure caps, day/night budgets,
Settings save from either profile, unchanged opposite profile, roles and CSRF.
Native browser clicks remain unverified while the Mac is locked. Daytime live
samples do not constitute a night test or the required 24-hour observation.

Pre-change production: `775a19d0`, config revision 109. The coherent SQLite
backup passed integrity checking and is protected at:
`/home/eric/hybrid-backups/capture-cadence-20260907-134506`.
The deployment records its exact candidate, previous revision, new revision,
service start and outcome in that directory's `deployment.json` and
`config-change.json`. Automated results and subsequent live samples are kept in
`/home/eric/hybrid-cadence-evidence`.

The deployment helper stops capture and Apache, checks source hashes against the
passed test manifest, saves a new configuration revision through the existing
persistence service and restarts services. A deployment failure restores the
previous configuration revision and code; it does not restore the full database
over new media records. Copies of the deployment/config helpers are retained in
the protected backup directory for rollback. No acquisition files are deleted.
Every capture restart or scheduling change starts a new 24-hour observation;
this mission does not complete the broader Classic-removal acceptance gate.

## Live timing follow-up

The first live deployment at 14:02:12 CEST saved revision 110 and produced
15-second steady-state intervals for both cameras. IMX708 actual driver requests
held exposure at 9 seconds while gain rose from 1.13 to 1.30, 1.49 and beyond.
All observed output files were present and nonempty, with no capture errors.

The first ZWO interval was 11 seconds: the scheduler reused a timestamp taken
before preparation/reconfiguration work. The follow-up changes the interval and
exposure-timeout origin to a fresh clock reading after that work, retaining the
full interval following preparation delays. A simulated four-second delay
regression checks that a 15-second interval does not become 11 seconds.

The follow-up backup and authoritative deployment/service-start record are in
`/home/eric/hybrid-backups/cadence-clock-20260907-140555`; it preserves revision
110 unchanged. This deployment restarts capture only. Its automatic test report
and live samples are in `/home/eric/hybrid-cadence-clock-evidence`.
The required 24-hour observation starts again at the follow-up restart.

All 92 Python/compile checks also pass on the timing follow-up (source hashes
verified); see `testing/evidence/hybrid-capture-cadence-clock-2026-09-07.json`.
The longer pre-follow-up sample contained 29 IMX708 and 30 ZWO frames, both
with median interval 15 seconds and all files nonempty. A separate satellite
TLE download returned HTTP 403; that integration remains an open verification
item and is not counted as a successful provider check.

## Hybrid hold isolation follow-up (2026-09-08)

The legacy ADU calculation could still queue an exposure reduction before
Hybrid applied its decision. A Hybrid `hold` then returned without overwriting
that legacy command, bypassing gain-first reduction. The legacy recalculation
now retains ADU target/stability bookkeeping but stops before planning changes
when Hybrid automatic exposure is enabled. Disabled Hybrid control retains
the legacy behavior. Capture cadence and saved configuration are unchanged.

`hybrid_exposure_pipeline_test.py` exercises the actual worker calculation and
apply methods with disagreeing legacy/Hybrid measurements, gain minima 0 and
1.13, hold, gain reduction, exposure reduction and disabled Hybrid control.
The local regression passed 25 entrypoints; 54 integration entrypoints remain
blocked by unavailable runtime Flask configuration or OpenCV. These are not
counted as passes. Controller and cadence tests also pass. See
`testing/evidence/hybrid-exposure-pipeline-2026-09-08.json`.

This follow-up is not deployed: SSH authentication/session establishment failed
(connection reset). Production acquisition has not been restarted. Before
deployment, complete the runtime regression, acquire a current rollback backup,
and verify both cameras. Deployment requires a new 24-hour observation window.

## Deployment of hold isolation (2026-09-08)

The follow-up above is now deployed as `a886a9d7`, after runtime regression and
a coherent backup in `/home/eric/hybrid-backups/exposure-hold-20260908-115906`.
Revision 110 is unchanged; capture restarted at 12:01:07 CEST, PID 3566586.
Both cameras produced decoded JPEGs with approximately 15.03-second request
intervals. The ZWO hold was observed in subsequent real requests; live gain
reduction above minimum and the new 24-hour day/night gate remain open.
See `testing/evidence/hybrid-exposure-hold-deployment-2026-09-08.json`.

Rollback uses the recorded previous commit `0104b282` and unchanged revision 110.
Stop capture/timer, verify tracked files are clean, return tracked code to that
commit, then restart capture and restore the timer's recorded state. Preserve
untracked user files and current media records; do not restore the whole database
over acquisitions made since the backup. A rollback also resets the observation
period. The protected `deploy.py` records the automatic failure rollback procedure.

## Web-only update during observation — 2026-09-08

The UI release `4b009133` restarted only Gunicorn at 13:14:45 CEST. Capture remained
PID 3566586, start 12:01:07, zero restarts, revision 110. Its code and scheduling
were unchanged. File and request evidence across the deploy is recorded in
`testing/evidence/hybrid-web-deployment-2026-09-08.json`; median request intervals
remain about 15.03s for each camera. The capture observation window therefore
continues; 24 hours including night have not yet been verified. Web backup and
rollback are separate at `/home/eric/hybrid-backups/web-ui-20260908-131241`.

## Effects release observation reset (2026-09-08)

Release `ca604649` required a controlled capture restart at **17:47:25 CEST**,
PID 3734524, revision 110 unchanged. The 12:01:07 window is interrupted and
cannot count toward the new 24 hours. First postcheck: 10/11 files, both latest
JPEGs decoded; request medians 15.035s/15.030s and no errors in the sample.
New evidence: `/home/eric/hybrid-effects-evidence`, scripts
`/tmp/hybrid-effects-live.py` and `/tmp/hybrid-effects-starts.py`. The monitor was
updated. Earliest possible completion is September 9 at 17:47:25, conditional
on complete day/night evidence. Live gain-first decrease, browser checks (Mac
locked), remaining effects and post-Classic-removal acceptance remain open.
See `testing/evidence/hybrid-effects-deployment-2026-09-08.json` and the rollback
instructions in `HYBRID_ACCEPTANCE_STATUS.md`.

## Live gain-first reduction sample (2026-09-08, 18:56 CEST)

The read-only check at 18:56:32 found the same capture PID 3734524 and start
17:47:25, with zero restarts. Both cameras had 275 saved frames after the
release, 15-second median file timestamps and no missing/empty files. There
were no pending tasks or errors in the journal returned by this check.

The IMX708 saved-frame sequence contains 59 decreases in gain, all with
unchanged exposure. The final three are 5.51 → 5.30 → 5.10 → 4.91 while
exposure remains 9 seconds. This directly supports gain-first reduction above
the minimum. It does not yet verify the later transition at gain 1.13 or a
complete night/day cycle. ZWO's latest frame has gain 0 and exposure 0.236054s;
this snapshot alone does not prove its entire adjustment sequence.

The raw evidence is `/home/eric/hybrid-effects-evidence/live-20260908-185632.json`;
the `live_observation` in `testing/evidence/hybrid-users-table-2026-09-08.json`
contains the summary and transition examples. This check did not deploy the
users-table candidate or modify services/configuration. The 24-hour gate,
browser acceptance and post-Classic-removal tests remain open.

## Production observation restarted — 2026-09-08 21:15 CEST

The completed panorama/Keogram/camera-management batch is installed as `80896495`.
Capture PID 3977508 and web PID 3977512 started at 21:15:41 CEST; configuration
revision 110 remains unchanged. Both cameras produced decoded frames at a
45-second median night interval in the first postcheck. This short sample does
not prove 24-hour stability. The monitor now uses `/home/eric/hybrid-batch-evidence`
and `/tmp/hybrid-batch-live.py` plus `/tmp/hybrid-batch-starts.py`.
The previous 17:47:25 window is closed and cannot be added to this one.
Backup/rollback and precise live evidence are recorded in
[the deployment report](testing/evidence/hybrid-batch-deployment-2026-09-08.json)
and [acceptance status](HYBRID_ACCEPTANCE_STATUS.md).
