# Hybrid: deployment and rollback

## Installed version

Production runs `07b2098dd24e1992b0f4f418d066a4672ec6f594` (29 September 2026).
Classic frontend is removed; Hybrid is the only UI. The latest release protects
capture previews and archives from partial copy failures. The 824-file tested
manifest matches production. Validation covers 166 Python entrypoints (full run
plus the corrected focus harness rerun) and 34 JavaScript entrypoints.

Capture was restarted between 12:17:01 and 12:17:13; capture PID is 1447332,
web PID 1415309 was preserved, and configuration revision 118 is unchanged.
Three newly saved images per camera decoded from disk and both Now previews decoded
in the native browser. This bounded check does not certify steady cadence or
power-loss durability. [Release evidence](testing/evidence/hybrid-image-publication-20260929.json).

The mobile management-grid correction remains installed: Uploads, YouTube and
Sensor Panel fit 320px. [Layout evidence](testing/evidence/hybrid-upload-management-layout-20260929.json).
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

## Roll back the installed image publication release

From an authenticated Raspberry SSH terminal as `eric`, the protected helper
requires exactly `07b2098dd24e1992b0f4f418d066a4672ec6f594` and a clean tracked
checkout. It restores code to 52eb6b23 with a controlled capture restart, preserving
the running web service, database, configuration and media. It has not been
exercised in production.

```sh
python3 /home/eric/hybrid-image-publication-deploy.py --rollback /home/eric/hybrid-backups/hybrid-image-publication-20260929-121700
```

This release backed up code and Flask configuration. It did not migrate or copy
the database; the coherent snapshot at
`/home/eric/hybrid-backups/hybrid-image-encoder-20260929-113656/indi-allsky.sqlite`
remains available. Code rollback does not restore that older database.

## Historical mobile layout rollback

Use this only after rolling the current image publication release back to 52eb6b23.

Use an authenticated SSH terminal on the Raspberry as `eric`, during a maintenance
window. Check the installed revision and preserve any tracked edits first:

```sh
git -C /home/eric/indi-allsky status --short
git -C /home/eric/indi-allsky rev-parse HEAD
```

The protected helper requires exactly revision 52eb6b23607fff2cd961b0f8890b8311d8a391d1 and refuses
to discard tracked edits. Its backup is:
`/home/eric/hybrid-backups/hybrid-management-grid-20260929-115230`.
Run on the Raspberry:

```sh
release_backup=/home/eric/hybrid-backups/hybrid-management-grid-20260929-115230
python3 "$release_backup/deploy.py" --rollback "$release_backup"
```

This code-only rollback returns to `2142968d` and reloads web. Capture keeps
running. It restores neither database nor configuration. Classic remains removed,
and encoder failure protection and the retained backend moon bitmap remain available.
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
The current storage-estimate release backup remains uncompressed, with configuration
and code archives preserved. On 29 September four older database snapshots were
compressed and fully verified, reclaiming 3,219,880,401 bytes; free space was
8.53 GiB afterward. See [archival evidence](testing/evidence/hybrid-backup-archival-20260929.json).

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
The current frontend-only helper backs up code/configuration and reloads web,
preserving capture. Backend or schema changes require a suitable coherent database
backup; earlier online WAL backups coincided with acquisition stalls, while the
encoder release used a controlled pause. Monitor space and actual frame recovery. Keep backups
private; run code checkout/merge/reset with child umask 022 so Apache can read
public assets. Restart only services affected by the change, then verify
installed hashes, real UI controls, effects and camera recovery.

The 29 September backup window coincided with queue growth and one recovered
IMX708 timeout. A running capture service alone does not prove uninterrupted
cadence: inspect frame intervals and queue recovery before accepting maintenance.
The [latency review](testing/evidence/hybrid-capture-queue-review-20260929.json)
also found earlier stalls, so backup causation remains unproven.

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
