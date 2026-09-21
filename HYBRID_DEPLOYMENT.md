# Hybrid: deployment and rollback

## Installed version

Production runs `7ddd7378d73353d8a58082c42f2d848dc3319375` (21 September 2026).
Classic frontend is removed; Hybrid is the only UI. The media identifier fix rejects
values outside the database integer range. All 165 Python entrypoints passed:
164 in the full run and the remaining test after checking the added validation
separately while retaining the original FITS class fingerprint. Implementation
hashes stayed unchanged during that test-only correction. Prior 34 JavaScript
passes remain applicable; the 822-file manifest matches the installed snapshot.

Backup integrity passed in 53.73 seconds. Configuration 117 and Flask settings
were preserved. Only web restarted (PID 952707); capture was not interrupted.
Native checks returned controlled errors for oversized IDs on all three corrected
handlers. Both Now images decoded at 22:56:47 and 22:56:58.
See [release evidence](testing/evidence/hybrid-media-id-boundary-20260921.json).
The retained backend moon bitmap remains in `indi_allsky/overlay/assets/`.

Both camera/profile round trips through the Settings index and Exposure/Gain
passed in the native production browser. See [Settings navigation evidence](testing/evidence/hybrid-settings-navigation-context-20260921.json).

The latest static cleanup also passed native VirtualSky rendering on both cameras,
fullscreen and preview reset: [cleanup evidence](testing/evidence/hybrid-static-cleanup-20260921.json).

Evidence: [Classic removal acceptance](testing/evidence/hybrid-retirement-final-native-20260921.json).

The camera-detection fix passed native discovery against real devices: the telescope
is no longer selectable as a camera, while IMX708 and ASI678MC remain available.
Both Now images decoded after deployment; configuration117 is unchanged.
Evidence: [detection deployment](testing/evidence/hybrid-camera-detection-release-20260921.json).

## Roll back the installed media identifier release

Use an authenticated SSH terminal on the Raspberry as `eric`, during a maintenance
window. Check the installed revision and preserve any tracked edits first:

```sh
git -C /home/eric/indi-allsky status --short
git -C /home/eric/indi-allsky rev-parse HEAD
```

The protected helper requires exactly the installed revision above and refuses
to discard tracked edits. Its backup is:
`/home/eric/hybrid-backups/hybrid-media-id-boundary-20260921-225523`.
Run on the Raspberry:

```sh
release_backup=/home/eric/hybrid-backups/hybrid-media-id-boundary-20260921-225523
maintenance_deadline="$(date --date='+15 minutes' --iso-8601=seconds)"
python3 "$release_backup/deploy.py" --rollback "$release_backup" \
  --maintenance-until "$maintenance_deadline"
```

This code-only rollback returns to `cfe2c40d` and restarts only web,
including its previous socket activation state. It restores neither the database
nor configuration and does not stop capture. Classic remains removed and the
retained backend moon bitmap remains available.
The helper is prepared; this live release has not been deliberately reverted.
Read the backup's `deployment.json`, confirm the revision and services, then
verify HTTPS Now and new nonempty files from both cameras. Process readiness
alone does not prove browser or capture acceptance.

A database restore is **not** part of this rollback. It would discard records
acquired after the snapshot and requires a separately diagnosed need, stopped
writers and a fresh copy of current data. Database metadata backups cannot
restore deleted image/video files.

## Automatic startup

Capture uses the enabled `indi-allsky.timer`, and Gunicorn uses its enabled
socket. The service units themselves may therefore report `disabled`; do not
add duplicate startup paths. User lingering permits startup without SSH login.
A warm reboot was verified on 14 September; a cold power-cut test remains open.
Evidence: [reboot and autostart](testing/evidence/hybrid-reboot-autostart-20260914.json).

Read-only checks as the deployment user:

```sh
loginctl show-user "$USER" -p Linger
systemctl --user is-enabled indi-allsky.timer indiserver.timer indiserver-asi678mc.service gunicorn-indi-allsky.socket
systemctl --user is-active indi-allsky.service indiserver-asi678mc.service gunicorn-indi-allsky.socket
systemctl is-enabled apache2
```

After any restart, verify actual fresh frames from both cameras. Enabled units
alone do not prove successful acquisition or recovery after a process failure.
Storage Protection settings control the installed automatic cleanup policy;
one-off authorized test-media cleanup does not change that saved policy.

## Historical backup storage

Some older snapshots are archived as `indi-allsky.sqlite.gz` to recover space.
Their `compressed-storage.json` records the original byte length and SHA-256;
complete decompression is verified before removing the uncompressed copy.
The current detection and recent static cleanup/Settings/Classic backups remain
uncompressed, with configuration and code archives preserved.

Before using an archived database snapshot, ensure space for `original_bytes`,
run `gzip -dk indi-allsky.sqlite.gz` in its backup directory, then compare
`sha256sum indi-allsky.sqlite` with `original_sha256` in the marker file.
This reconstructs a backup file; it does not restore the live database.
The same instructions are retained privately on the Raspberry in
`/home/eric/hybrid-backups/COMPRESSED_BACKUPS.md`.

## Before the next deployment

Pin the tested commit and exact changed-file list. Check space, active tasks,
services, configuration revision and tracked/untracked files. Preserve user
files; do not use `git clean`. The checkout database copy is not the runtime
database at `/var/lib/indi-allsky/indi-allsky.sqlite`.

Prepare an integrity-checked backup and a rollback for that exact release.
The current helper uses a bounded WAL read snapshot: writers can continue, but
the read transaction delays checkpoint completion until copying ends. Monitor
space and release the transaction immediately after the copy. Keep backups
private; run code checkout/merge/reset with child umask 022 so Apache can read
public assets. Restart only services affected by the change, then verify
installed hashes, real UI controls, effects and camera recovery.

## Remaining acceptance and history

- Complete the page/control matrix, roles, camera/profile isolation and mobile checks.
- Verify remaining effects and integrations using dedicated test data/destinations.
- Complete the remaining post-removal control and effect checks.
- Run the separate 24-hour observation only when the user starts that activity.

See [acceptance status](HYBRID_ACCEPTANCE_STATUS.md) and the
[route evidence register](docs/hybrid-acceptance-route-register.md). Historical
release descriptions and rollback chains are preserved in Git at `503833b1`:
`git show 503833b1:HYBRID_DEPLOYMENT.md`. Their commands target older releases
and must not be used as the rollback for the current production revision.
