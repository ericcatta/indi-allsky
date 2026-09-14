# Combined Hybrid product release

Candidate prepared on 14 September 2026; **not installed**. This supersedes the
13 September worker candidate and the standalone Mask Base candidate. Their
private artifacts and backups remain available for recovery. The previous acceptance window ended at 20:00;
installation needs a new user-agreed window with an end time. No 24-hour
observation is included.

## Exact candidate and preparation

- Installed baseline: `3590a3ee4621e01b23043ac415de499d79f7c9e3`.
- Tested candidate: `fc926129a2a1c79c9f5dcb3fd37e103a6b17c94d`.
- Verified release delta: 84 paths, including Mask Base, Settings, Observatory,
  System/media contexts, storage policy/forecast, upload publication locking,
  account identity, complete storage summaries/daily exports and the independent
  Astropanel endpoint. No schema, installer or dependency-file changes.
- Regression: 153 Python results including compilation, 34 JavaScript tests;
  all passed with the 826-file source manifest unchanged.

The Raspberry has the pinned bundle, path manifest and
`~/hybrid-product-deploy.py`. Its `--prepare-only` execution finished
successfully: online SQLite backup passed integrity checking, previous code and
Flask configuration were preserved in a protected backup directory. The private
`~/hybrid-product-release-state.json` identifies the backup and revisions.
Post-preparation checks confirmed unchanged service identities, installed code
and Flask bytes, a clean tracked checkout and all untracked user files preserved.
Never publish the private state, database or configuration contents. The backup
directory has mode 0700 and its database, configuration and state files 0600.
The helper rejects combining preparation and rollback, and rejects installation
without a user-agreed maintenance deadline. Artifact checksums and preparation
evidence are in `testing/evidence/hybrid-product-release-preparation.json`.

## Installation and bounded acceptance

1. Confirm the maintenance window and recovery access. Recheck the installed
   revision, tracked work, disk headroom, camera freshness and task backlog.
2. Execute the prepared helper with `--maintenance-until` set to the agreed
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
