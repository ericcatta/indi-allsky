# Combined Hybrid product release

Candidate staged and verified on 14 September 2026; **not installed**. This
supersedes the earlier `8a15ae1e` and `fc926129` bundles and older standalone candidates.
Their artifacts and valid backups remain preserved. The previous acceptance
window ended at 20:00; installation needs a new user-agreed window with an end
time. No 24-hour observation is included.

## Exact candidate and staging

- Installed baseline: `3590a3ee4621e01b23043ac415de499d79f7c9e3`.
- Tested candidate: `eb023b1c21a32c0371c829062d5ae3d53fbe2643`.
- Verified release delta: 98 paths, 30 application paths, including Mask Base,
  Settings, Observatory, System/media contexts, storage policy/forecast, upload
  publication locking, account identity, storage summaries/daily exports,
  independent Astropanel, Action API credential validation and Sync temporary
  upload cleanup. No schema,
  installer or dependency-file changes.
- Regression: 157 Python results including compilation, 34 JavaScript tests;
  all passed with the 830-file source manifest unchanged.

The Raspberry has `~/hybrid-product-eb023b1c-release.bundle`,
`~/hybrid-product-eb023b1c-paths.json` and
`~/hybrid-product-eb023b1c-deploy.py`. Checksums match the local artifacts;
bundle prerequisites, candidate ref and complete path list were verified.
The helper preserves the previous deployment logic with a new pinned revision
and versioned filenames. It has not been executed for this candidate.

This is artifact staging, not a completed pre-deploy backup. The earlier
`fc926129` preparation produced a valid protected backup, retained with its own
helper and state. The new helper must acquire a fresh consistent SQLite/code/
configuration backup before stopping services; its state will be recorded in
`~/hybrid-product-eb023b1c-release-state.json`. Never substitute the old state
for the new candidate. Backup directories are private, and database,
configuration and state must not be published.

Staging preserved production HEAD, tracked work, untracked files, configuration
bytes and service identities/states. Evidence and checksums:
`testing/evidence/hybrid-product-eb023b1c-staging.json`. Historical backup
evidence remains in `testing/evidence/hybrid-product-release-preparation.json`.

## Installation and bounded acceptance

1. Confirm the maintenance window and recovery access. Recheck the installed
   revision, tracked work, disk headroom, camera freshness and task backlog.
2. Execute `~/hybrid-product-eb023b1c-deploy.py` with `--maintenance-until` set to the agreed
   ISO timestamp including timezone. It creates a fresh consistent backup before
   stopping capture/web and their activating timer/socket. It refuses a stale
   baseline, unexpected release paths or an expired/insufficient window.
3. Verify the exact candidate is loaded, capture/web and previously active
   activators are running, Flask bytes and user files are preserved, and Classic
   remains disabled. A process readiness check is not functional acceptance.
4. Observe new nonempty files from both cameras with correct camera/profile
   associations and continued acquisition. Check new worker errors and backlog.
   Perform the scoped mask publication/download checks in
   `HYBRID_MASK_RELEASE_RUNBOOK.md`; do not manufacture a pass with seeded masks.
5. Verify Storage Settings load/save/validation and policy readback. Defaults are
   enabled, 5 GiB trigger, 8 GiB recovery target, minimum image age 3 days.
   Forecasts require sufficient current measured data; an unavailable estimate
   is not a numeric forecast pass. Use dedicated test data for destructive
   acceptance; do not fill the production disk or delete unapproved data.
6. Verify the new account identity display, both-camera Storage inventories,
   daily table categories and actual CSV/Excel downloads. Exercise Astropanel
   refresh and camera selection; malformed camera requests should report JSON
   400, absent cameras 404 and database failures 503. Do not inject a database
   outage in production to manufacture an error test.
7. Record each missing live check explicitly and finish at the agreed deadline.
   Production browser acceptance remains open while its security review is
   unresolved; do not bypass the certificate restriction.

## Recovery

The helper attempts code-only recovery if installation fails. For an explicit
rollback, run the backup's `deploy.py` with `--rollback` pointing to that exact
backup and `--maintenance-until` within an agreed recovery window. It requires
the exact installed candidate and a clean tracked checkout, restores `3590a3ee`,
and restarts capture/web with their previously active activators. Verify fresh
frames from both cameras and web recovery, then record the result.

Do not restore the database or configuration for a code-only rollback. Never use
`git clean`. Preserve new images, configuration revisions, task records and
calibrations. A database backup cannot restore media deleted by retention.
Earlier rollback steps from `3590a3ee` remain in `HYBRID_DEPLOYMENT.md`.

This release does not remove Classic physically or complete the product-wide
control matrix. Cold-boot acceptance also remains open, despite verified boot
activation configuration.
