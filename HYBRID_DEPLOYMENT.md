# Hybrid: deployment and rollback

## Installed version

Production runs `cb51d7b417ce6b24b4fece6eb042346ea6730b3e` (20 September
2026). All 837 tested source hashes match. Native Full Settings checks confirm
unique IDs, matching counts, empty-search recovery and keyboard clearing.
Both Now images decode. Configuration 117, Flask configuration, capture PID
1566 and untracked files were preserved during the web-only deployment.

The database backup passed integrity validation in 227.58 seconds. An extended
67-second frame interval occurred during maintenance; final samples were
45 seconds on IMX708 and 45–46 seconds on ASI. These are bounded observations,
not a long-duration stability certification.

Evidence: [Settings production acceptance](testing/evidence/hybrid-settings-polish-deployment-20260920.json).
Classic is disabled but physically present in production. The removal candidate
has separate acceptance gates; do not treat its regression results as a deploy.

## Roll back the installed web release

Use an authenticated SSH terminal on the Raspberry as `eric`, during a maintenance
window. Check the installed revision and preserve any tracked edits first:

```sh
git -C /home/eric/indi-allsky status --short
git -C /home/eric/indi-allsky rev-parse HEAD
```

The protected helper requires exactly the installed revision above and refuses
to discard tracked edits. Its backup is:
`/home/eric/hybrid-backups/hybrid-settings-polish-20260920-204903`.
Run on the Raspberry:

```sh
release_backup=/home/eric/hybrid-backups/hybrid-settings-polish-20260920-204903
maintenance_deadline="$(date --date='+15 minutes' --iso-8601=seconds)"
python3 "$release_backup/deploy.py" --rollback "$release_backup" \
  --maintenance-until "$maintenance_deadline"
```

This code-only rollback returns to `68f35d76`, restarts the web service and its
previously active socket, and retains capture, database and current configuration.
It also removes the latest Settings usability and validation-log privacy fixes.
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
- Complete Classic retirement, then repeat essential production checks.
- Run the separate 24-hour observation only when the user starts that activity.

See [acceptance status](HYBRID_ACCEPTANCE_STATUS.md) and the
[route evidence register](docs/hybrid-acceptance-route-register.md). Historical
release descriptions and rollback chains are preserved in Git at `503833b1`:
`git show 503833b1:HYBRID_DEPLOYMENT.md`. Their commands target older releases
and must not be used as the rollback for the current production revision.
