# Hybrid: deployment and rollback

## Installed release, 10 September 2026

The Raspberry runs `ba6cbd3b42d54eeb46f93a1aa2a704815ae534b0`, upgraded from
`aa0afeff43de388bb2c393518a545ff4482435a9`. This release adds direct internal
snapshot restore and SQLite serialization of simultaneous restores. Capture,
scheduling, schema and saved configuration were not changed by deployment.

Only the user web service and its activating socket were restarted. Capture
remained unchanged; both cameras produced fresh nonempty files after deployment.
`HYBRID_ENABLE_CLASSIC_UI=false` is preserved byte-for-byte in Flask configuration.
Classic files remain present; physical removal is still open.

Release evidence: `testing/evidence/hybrid-snapshot-restore-deployment.json`.
All 137 Python entrypoints passed before deployment. The unchanged JavaScript
has 34 passing entrypoints from the preceding candidate. Native sandbox checks
verified direct restore, history and sequential duplicate rejection; the two-process
SQLite test reproduced two successes before the fix and one success/one rejection
after it. Production browser acceptance is **blocked** by automatic browser
security review of the HTTPS origin. No bypass was attempted, and no production
configuration restore was submitted. Service readiness and new capture files do
not establish acceptance of the deployed restore form.

These are bounded acceptance checks, not completion of the whole migration.
The 24-hour day/night observation is a separate future activity, after migration
and Classic removal, as requested. It is not a gate for this migration and must
not be restarted automatically.

## Recovery assets

On the Raspberry, `~/hybrid-snapshot-restore-release-state.json` records the exact
previous/candidate revisions and protected backup directory. That directory
contains an online SQLite backup with successful integrity check, the previous
code archive, Flask configuration, deployment script and deployment record.
Keep backup permissions restricted; do not publish their contents or private logs.

Preserve untracked user files in the checkout. Never use `git clean` for
deployment. The checkout database copy is not the runtime database. This release
preserved the untracked files and verified a clean tracked checkout.

## Restore the previous frontend mode

The latest protected `~/hybrid-backups/classic-mode-*` directory contains the
original Flask configuration, `mode.json` and `mode.py`. Only the Classic flag
changed. Restoring it restarts only the web service/socket and preserves capture.
The helper refuses to overwrite configuration modified since the mode change.
The mode helper is pinned to release `0291efd4`. From the current release, first
roll back this snapshot release to `aa0afeff`, preserving the disabled mode.
If mode rollback is also needed, then use the previous image-preview release's
protected script, located by `~/hybrid-image-preview-release-state.json`, to return
to `0291efd4`. Only then run the mode helper below. Do not bypass revision guards.
An even older code rollback must follow its own recorded recovery instructions.

```sh
mode_backup="$(python3 -c 'from pathlib import Path; print(max((Path.home()/"hybrid-backups").glob("classic-mode-*"), key=lambda p: p.stat().st_mtime))')"
python3 "$mode_backup/mode.py" --rollback "$mode_backup"
```

Check the protected `mode.json` result and verify HTTPS Now and both cameras.
Do not copy the entire old configuration over subsequent user changes. This
fallback is prepared; it has not been drilled by reverting the current mode.

## Roll back this web release

Use an authenticated SSH terminal on the Raspberry under the deployment user.
Inspect the current Git revision and tracked changes before proceeding. Save any
new work first. The protected script requires the exact installed candidate and
a clean tracked checkout; it refuses to discard tracked edits or roll back an
unrelated release.

```sh
release_backup="$(python3 -c 'import json; from pathlib import Path; print(json.loads((Path.home()/"hybrid-snapshot-restore-release-state.json").read_text())["backup"])')"
python3 "$release_backup/deploy.py" --rollback "$release_backup"
```

The script stops the web socket and service, restores the previous code, starts
the web service and previously active socket, and checks process readiness. It
does not stop capture or restore the database. Then verify HTTPS Now, fresh files
for both cameras, service state and the Git revision. Read the protected backup's
`deployment.json` for the rollback result; do not infer success from a checkout
command alone. The rollback path is prepared but has not been exercised by
reverting this live release.

A database restore would discard records acquired after the backup. Perform one
only for a diagnosed need, with all writers stopped and a fresh copy of current
data saved first. No database restore is part of this web rollback.

## Remaining acceptance

- Complete the page/control matrix, roles, camera/profile isolation and mobile checks.
- Verify remaining effects and integrations using dedicated test data/destinations.
- Treat image jSQM as an uncalibrated index; dedicated magnitude measurements are separate.
- Demonstrate functional parity, remove Classic, and repeat essential checks.
- Schedule the separate 24-hour observation only when the user starts that activity.
