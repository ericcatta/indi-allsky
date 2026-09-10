# Hybrid: deployment and rollback

## Installed release, 10 September 2026

The Raspberry runs `0291efd493a12a7b4eae204f33f4e193d12b7d90`, upgraded from
`0733234875d6d12e6e07a1fa0db5de7943df3ecb`. This release updates the web interface,
observatory/diagnostic reads, camera navigation and VirtualSky. It does not change
capture workers, scheduling, database schema or saved configuration.

Only the user web service and its activating socket were stopped and started.
The capture process remained unchanged. Classic is still enabled and present.

Release evidence: `testing/evidence/hybrid-observatory-ui-deployment.json`.
The 136 Python and 33 JavaScript entrypoints passed before deployment. Direct
HTTPS browser checks covered Now, both camera images, SQM camera navigation,
VirtualSky on both cameras and its fullscreen round-trip. Newly saved image
records had corresponding nonempty files for both cameras.

These are bounded acceptance checks, not completion of the whole migration.
The 24-hour day/night observation is a separate future activity, after migration
and Classic removal, as requested. It is not a gate for this migration and must
not be restarted automatically.

## Recovery assets

On the Raspberry, `~/hybrid-observatory-ui-release-state.json` records the exact
previous/candidate revisions and protected backup directory. That directory
contains an online SQLite backup with successful integrity check, the previous
code archive, Flask configuration, deployment script and deployment record.
Keep backup permissions restricted; do not publish their contents or private logs.

Preserve untracked user files in the checkout. Never use `git clean` for
deployment. The checkout database copy is not the runtime database. This release
preserved the untracked files and verified a clean tracked checkout.

## Roll back this web release

Use an authenticated SSH terminal on the Raspberry under the deployment user.
Inspect the current Git revision and tracked changes before proceeding. Save any
new work first. The protected script requires the exact installed candidate and
a clean tracked checkout; it refuses to discard tracked edits or roll back an
unrelated release.

```sh
release_backup="$(python3 -c 'import json; from pathlib import Path; print(json.loads((Path.home()/"hybrid-observatory-ui-release-state.json").read_text())["backup"])')"
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
- Review anomalous stored SQM values separately from UI data/selection correctness.
- Demonstrate functional parity, remove Classic, and repeat essential checks.
- Schedule the separate 24-hour observation only when the user starts that activity.
