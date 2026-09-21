# Hybrid: deployment and rollback

## Installed version

Production runs `6a3dfc8f6e541ae75ad14b507f5e85d6c8587ec2` (21 September
2026). Classic frontend files are physically removed; Hybrid is the only UI.
All 780 installed source hashes match the validated snapshot: 161 Python tests
passed in the full run, the updated inheritance guard passed its targeted retest,
and 34 JavaScript tests passed. Runtime source was unchanged between those runs. Native isolated Settings save/restore recovered the original
value; production Now decoded current images from both cameras and Full Settings
search returned the expected field. These are bounded acceptance checks.

The database backup passed integrity validation in 57.73 seconds. Configuration
117, Flask configuration, capture PID 1566 and untracked files were preserved.
The web service restarted as PID 802610. A complete control/effect matrix and
unavailable hardware checks remain open; the 24-hour observation is deferred.

Both camera/profile round trips through the Settings index and Exposure/Gain
passed in the native production browser. See [Settings navigation evidence](testing/evidence/hybrid-settings-navigation-context-20260921.json).

Evidence: [Classic removal acceptance](testing/evidence/hybrid-retirement-final-native-20260921.json).

## Roll back the installed web release

Use an authenticated SSH terminal on the Raspberry as `eric`, during a maintenance
window. Check the installed revision and preserve any tracked edits first:

```sh
git -C /home/eric/indi-allsky status --short
git -C /home/eric/indi-allsky rev-parse HEAD
```

The protected helper requires exactly the installed revision above and refuses
to discard tracked edits. Its backup is:
`/home/eric/hybrid-backups/hybrid-settings-navigation-20260921-201054`.
Run on the Raspberry:

```sh
release_backup=/home/eric/hybrid-backups/hybrid-settings-navigation-20260921-201054
maintenance_deadline="$(date --date='+15 minutes' --iso-8601=seconds)"
python3 "$release_backup/deploy.py" --rollback "$release_backup" \
  --maintenance-until "$maintenance_deadline"
```

This code-only rollback returns to `fe2640c8`, restarts the web service and its
previously active socket, and retains capture, database and current configuration.
Classic remains removed after this rollback; it reverts the Settings index context correction while retaining device-identity matching.
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
The current Settings navigation, Settings scope, Classic retirement and preceding Settings polish backups remain
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
