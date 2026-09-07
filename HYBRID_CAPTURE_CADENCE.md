# Shared capture cadence and independent exposure control

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
