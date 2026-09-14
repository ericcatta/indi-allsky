# Hybrid: deployment and rollback

## Operations Copy installed, 14 September 2026

Production is `b34b97d556c587f016bbf03e06e6a306d0155b66`. Web-only deployment
preserved capture PID 1566, configuration revision 117 and Flask configuration
bytes. The online SQLite backup passed integrity checks. All 831 tested source
hashes match production. Native Copy exported only task 11772 and confirmed
“Copied 1 record.” Evidence: `testing/evidence/hybrid-copy-fix-deployment.json`.

Code rollback uses `~/hybrid-copy-fix-deploy.py --rollback` with the exact
`backup` path in `~/hybrid-copy-fix-release-state.json` and a fresh timezone-aware
`--maintenance-until` deadline. It restores `0e6f445c` and restarts only the web
service/socket; database, configuration and capture are retained. The corrected
helper is also saved as `deploy.py` inside that backup.

Keep backup files private, but run git checkout/merge/reset with child umask 022
so Apache can read public assets. The original private umask produced a 403 for
the new JS; its mode is repaired to 0644 and the helper now separates the two.
Verify actual asset loading and controls after deployment, not only HTTP pages.
Classic remains disabled and present; final retirement is not certified.

## Previous FITS writer correction, 14 September 2026

That deployment installed `0e6f445ca0312acb14100cf36ddc992d8635df47`. The existing video
queue completed before the guarded capture/web restart. A fresh online SQLite
backup passed integrity checks; configuration revision 117, Flask configuration
bytes and untracked files were preserved. All 831 tested source hashes match
production. Full regression: 158 Python and 34 JavaScript checks passed.

New FITS 516 (IMX708) and 517 (ASI) have matching database/header dimensions of
4608x2592 and 3840x2160. The source viewer shows the new IMX708 capture correctly.
Both mini videos from tasks 11744/11753 completed, passed ffprobe and played to
the end in the native browser after deployment. Evidence and bounded limits:
`testing/evidence/hybrid-fits-dimensions-deployment.json` and
`testing/evidence/hybrid-mini-generation-live-20260914.json`.

That release’s rollback uses `~/hybrid-fits-dimensions-deploy.py --rollback` with
the exact backup in `~/hybrid-fits-dimensions-release-state.json` and a fresh
technical `--maintenance-until` deadline. It restores `29c75ffb` and restarts
capture/web; it does not restore the database or undo the corrected historical
FITS metadata. This historical helper is not the rollback command for the current Copy release.
Classic remains disabled but present; complete acceptance/removal remain open.

## Previous Astropanel deployment, 14 September 2026

At this earlier step, production ran `29c75ffb016a6d9841ed00b274993ebab1c5bc63`, fast-forwarded
from `eb023b1c`. Fresh online SQLite backup integrity and private permissions
passed. Only the web service/socket restarted; capture PID/state/restart count,
Flask configuration and user files were preserved. Both cameras produced fresh
nonempty files after this web-only deployment.

Both new camera/profile links were clicked in the production Astropanel; each
loaded ephemerides, seven planet rows and the satellite table. The full isolated
regression passed 157 Python and 34 JavaScript entrypoints on matching sources.
Evidence: `testing/evidence/hybrid-astropanel-camera-deployment.json`.

For rollback, use `~/hybrid-astropanel-camera-deploy.py --rollback` with the exact
backup recorded in `~/hybrid-astropanel-camera-release-state.json`, and a fresh
`--maintenance-until` deadline within the user's authorized maintenance. This
restores code to `eb023b1c` and restarts only web. Earlier release helpers have
different pinned baselines and must not be used for this release. Configuration
and database restoration is not part of this code-only rollback.
Classic remains disabled and physically present; full acceptance remains open.

## Previous installed release, 14 September 2026

At this earlier step, production ran `eb023b1c21a32c0371c829062d5ae3d53fbe2643`, installed from
`3590a3ee` after the user authorized maintenance for as long as necessary.
A fresh online SQLite backup passed integrity checks, with protected code and
Flask configuration copies. The versioned helper supports code-only rollback;
private state is `~/hybrid-product-eb023b1c-release-state.json`.

Capture/web and their timer/socket restarted successfully. Both cameras produced
new nonempty files after restart. A later 12-frame sample for each camera showed
15-second median cadence (IMX708 15–15 seconds, ASI 15–16 seconds).
Flask configuration bytes and untracked files were preserved; tracked checkout
was clean. Classic is disabled but its files remain present.

Native production browsing now works without bypassing a security interstitial.
Now, navigation, Storage inventory and daily table rendered. Storage Protection
save was verified through UI feedback and database readback: only
`STORAGE_PRESSURE` changed, enabled with 5/8 GiB thresholds and three-day retention.
The forecast displayed real consumption-based estimates. CSV download emitted
a browser event; file inspection and clipboard receipt remain unverified.

This is partial live acceptance, not completion of every page/control or Classic
removal. The 24-hour observation remains explicitly deferred. Evidence:
`testing/evidence/hybrid-product-deployment-20260914.json`.

## Installed release, 10 September 2026

The Raspberry runs `3590a3ee4621e01b23043ac415de499d79f7c9e3`, upgraded from
`2b7dea37332879e31530916a4f28707b52c190c5`. Focus preview requests now time out
with retry guidance, release their controls and cancel when leaving the page.
Focus expansion remains usable inside the window when native fullscreen is
unavailable or does not remain active, with explicit exit and keyboard handling.
Capture, scheduling, schema and saved configuration were not changed.

Only the user web service and its activating socket were restarted. Capture
remained unchanged; both cameras produced fresh nonempty files after deployment.
`HYBRID_ENABLE_CLASSIC_UI=false` is preserved byte-for-byte in Flask configuration.
Classic files remain present; physical removal is still open.

Release evidence: `testing/evidence/hybrid-focus-controls-deployment.json`.
All 137 Python entrypoints and 34 JavaScript entrypoints passed before deployment.
Synthetic native browser checks cover both camera previews, timeout and retry,
Reset, preview expansion and explicit exit. Final Tab handling is covered by
controller tests rather than native keyboard input. Production
browser acceptance remains **blocked** by automatic browser security review of
the HTTPS origin. No bypass was attempted. Process readiness and capture files
do not prove native download receipt or full product acceptance.

These are bounded acceptance checks, not completion of the whole migration.
The 24-hour day/night observation is a separate future activity, after migration
and Classic removal, as requested. It is not a gate for this migration and must
not be restarted automatically.

## FITS dimensions repair, 14 September 2026

The twelve existing IMX708 FITS records 492 through 514 (even IDs) had planar
RGB dimensions recorded as 2592x3. Original FITS headers confirm 4608x2592 with
three channels. A coherent SQLite backup with successful integrity check was
created under the private `~/hybrid-backups/fits-dimensions-*` directory before
repair. `metadata-before.json` records the exact old/new dimensions and IDs.
One transaction updated only matching ID/camera/old-dimension rows. Comparing
every column against the backup confirms only width and height changed.
Original media files were not changed; both JPEG preview endpoints decode at
the correct camera dimensions.

This metadata repair preceded the capture writer deployment recorded above.
Do not restore the entire database to undo metadata while capture is active:
that would discard subsequent acquisition records. If an unexpected issue
requires reversing this repair, use its saved per-record dimensions with exact
ID/camera/current-dimension checks in one transaction. No reversal is needed for
an ordinary code rollback. Newly captured FITS 516/517 verify the deployed writer;
the earlier previews alone did not prove that step.

## Automatic startup and storage recovery, 13 September 2026

Read-only production verification, repeated on 14 September, confirms user lingering is enabled, so login
is not required. `indi-allsky.timer` is enabled and starts capture two minutes
after boot; `indiserver.timer` starts the generic server after thirty seconds.
The dedicated ASI driver service is enabled and ordered before capture. Apache
and the Gunicorn socket are enabled. The Gunicorn service is socket-activated.
The capture and web service units being `disabled` is normal in this arrangement:
their enabled timer/socket activates them. Do not enable duplicate immediate
startup paths merely because the service unit itself says disabled.

Verify as the deployment user:

```sh
loginctl show-user "$USER" -p Linger
systemctl --user is-enabled indi-allsky.timer indiserver.timer indiserver-asi678mc.service gunicorn-indi-allsky.socket
systemctl --user is-active indi-allsky.service indiserver-asi678mc.service gunicorn-indi-allsky.socket
systemctl is-enabled apache2
```

A cold boot was not performed in this verification. After an agreed reboot,
verify both cameras publish new nonempty frames and the UI is usable without
logging in over SSH first. Enabled units alone do not prove this full sequence.
Capture, generic INDI and Gunicorn currently have no automatic restart policy;
boot activation is distinct from recovery after a process failure.
Evidence: `testing/evidence/hybrid-boot-startup-20260913.json`.

The user-authorized test-media cleanup removed 68,287 media records within the
initial snapshot and recovered 61.6% free disk space. Capture was stopped and
started with explicit authorization to recover its full private temporary
filesystem; both cameras then produced new files. Settings, accounts,
calibrations and backups were preserved. A consistent database backup preserves
metadata but cannot restore the deleted media themselves. Automatic storage
protection is implemented and tested in candidate `eb023b1c`, but is not an
installed safeguard. Previous valid backups are preserved; the new candidate requires a fresh backup before installation. See
`HYBRID_STORAGE_RELEASE_RUNBOOK.md`.
Evidence: `testing/evidence/hybrid-storage-recovery-20260913.json`.

## Recovery assets

On the Raspberry, `~/hybrid-focus-controls-release-state.json` records the exact
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
The mode helper is pinned to release `0291efd4`. To reach that release, the
prepared code rollbacks must follow this order, using each state's recorded
backup/deploy.py rather than bypassing revision guards:

| Installed candidate | Rollback target | State file under `~/` |
| --- | --- | --- |
| `0e6f445c` | `29c75ffb` | `hybrid-fits-dimensions-release-state.json` |
| `29c75ffb` | `eb023b1c` | `hybrid-astropanel-camera-release-state.json` |
| `eb023b1c` | `3590a3ee` | `hybrid-product-eb023b1c-release-state.json` |
| `3590a3ee` | `2b7dea37` | `hybrid-focus-controls-release-state.json` |
| `2b7dea37` | `f9aeaf88` | `hybrid-history-pages-release-state.json` |
| `f9aeaf88` | `ba6cbd3b` | `hybrid-config-download-release-state.json` |
| `ba6cbd3b` | `aa0afeff` | `hybrid-snapshot-restore-release-state.json` |
| `aa0afeff` | `0291efd4` | `hybrid-image-preview-release-state.json` |

Only then run the mode helper below if restoring Classic is necessary. Every
code rollback preserves the current Flask configuration. An older code rollback
must follow its own recorded recovery instructions.

```sh
mode_backup="$(python3 -c 'from pathlib import Path; print(max((Path.home()/"hybrid-backups").glob("classic-mode-*"), key=lambda p: p.stat().st_mtime))')"
python3 "$mode_backup/mode.py" --rollback "$mode_backup"
```

Check the protected `mode.json` result and verify HTTPS Now and both cameras.
Do not copy the entire old configuration over subsequent user changes. This
fallback is prepared; it has not been drilled by reverting the current mode.

## Roll back this web release

Rolling back this release removes Focus timeout recovery and the usable in-window
preview expansion. Rolling back the earlier permission fix as well restores its
download authorization defect; account for that exposure before further rollback.

Use an authenticated SSH terminal on the Raspberry under the deployment user.
Inspect the current Git revision and tracked changes before proceeding. Save any
new work first. The protected script requires the exact installed candidate and
a clean tracked checkout; it refuses to discard tracked edits or roll back an
unrelated release.

```sh
release_backup="$(python3 -c 'import json; from pathlib import Path; print(json.loads((Path.home()/"hybrid-focus-controls-release-state.json").read_text())["backup"])')"
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

## Prepared next worker release

Mask Base per-camera publication and error recovery are published but not installed.
The exact candidate, worker restart requirements, rollback and bounded acceptance
are in [HYBRID_MASK_RELEASE_RUNBOOK.md](HYBRID_MASK_RELEASE_RUNBOOK.md).
A new live acceptance window is required; the current installed release above
remains unchanged.

## Remaining acceptance

- Complete the page/control matrix, roles, camera/profile isolation and mobile checks.
  The [route evidence register](docs/hybrid-acceptance-route-register.md) links
  explicit historical records without certifying current coverage.
- Verify remaining effects and integrations using dedicated test data/destinations.
- Treat image jSQM as an uncalibrated index; dedicated magnitude measurements are separate.
- Demonstrate functional parity, remove Classic, and repeat essential checks.
- Schedule the separate 24-hour observation only when the user starts that activity.
