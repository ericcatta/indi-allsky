# Hybrid: deployment and rollback

## Installed version

Production runs `4ca063a6a8da0ec116c0963a51f83fd594602b53` (29 September 2026).
Classic frontend remains removed. Background SQLite checkpoint maintenance is
active for capture; failed/stale maintenance restores automatic checkpoints.
All capture/web SQLite processes and the dedicated virtualenv CLI load verified
SQLite 3.51.3. The OS library is unchanged.

Historical checkpoint release: its 829-file manifest matched that candidate. Tests cover 166 existing
Python entrypoints plus checkpoint lifecycle, Flask checkout and installer
checks, and 34 JavaScript tests. The original new-test harness failure and its
correction are retained in the evidence. Native Now, Settings/history and
Library checks pass. Both cameras resumed; 29 frames each show 15-second median
and 16-second maximum spacing. This short sample does not close all cadence or
whole-product acceptance gates.
[Release evidence](testing/evidence/hybrid-sqlite-checkpoint-20260929.json).

Capture/web were stopped for a coherent database backup (integrity_check: ok),
then restarted; configuration 118 is unchanged. Maintenance 13:51:57–13:54:13.
Backup: `/home/eric/hybrid-backups/hybrid-checkpoint-20260929-135156`.

The prior atomic image publication correction remains installed.
[Image publication evidence](testing/evidence/hybrid-image-publication-20260929.json).

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

## Current task sorting release rollback

The task age correction passed 171 Python checks and native sorting on all 501
production rows in both directions. Only web workers were reloaded; capture
PID 1739126 remained active with zero automatic restarts. The tested 833-file
manifest is `16d12f76aa538f61abc8eb24235640888043e8501847d06535e012410c938964`.
[Release evidence](testing/evidence/hybrid-task-age-sort-20260929.json).

From exactly `4ca063a6a8da0ec116c0963a51f83fd594602b53`:

```sh
/home/eric/indi-allsky/virtualenv/indi-allsky/bin/python /home/eric/hybrid-task-age-deploy.py --rollback /home/eric/hybrid-backups/hybrid-task-age-20260929-170404
```

This restores `970d1799` and reloads web workers without restarting capture or
restoring the database. The following older rollback then applies.

## Syslog release rollback

The syslog release passed 171 Python/compile entrypoints and 34 JavaScript tests.
Its 833-file manifest includes `allsky.py`; deployment verifies the tested hashes.
Maintenance ran 16:21:42–16:21:57. Capture restarted and web workers reloaded;
configuration 118 is unchanged. Both camera files decode. The 171-case load replay passes, but cadence remains open: frame maxima are
19/25 seconds. System-log isolation is traced and verified; this is not
whole-product acceptance.

For rollback from exactly `970d179941dd3dbfc76da76965cee1d7f40cadb9`:

```sh
/home/eric/indi-allsky/virtualenv/indi-allsky/bin/python /home/eric/hybrid-async-syslog-deploy.py --rollback /home/eric/hybrid-backups/hybrid-async-syslog-20260929-162142
```

This returns to `96c2049d`, restarts capture and reloads web. It preserves the
SQLite bootstrap, database, configurations and media. The older rollback below
applies only after returning to that exact revision.

## Diagnostic writer rollout and rollback

Capture was stopped and restarted from 15:41:15 to 15:41:24 to load the bounded
asynchronous file writer. Configuration 118, database schema and SQLite runtime
were unchanged. Code/config backup is below; the coherent database backup at
`hybrid-checkpoint-20260929-135156` remains retained. Source manifest has 830 files.
170 Python/compile entrypoints and 34 JavaScript tests pass; replaying regression
as live load also passes. Both camera files decode. The writer isolation is
verified, but overall cadence still fails under load (28/30-second maxima).
[Evidence and remaining system-logging block](testing/evidence/hybrid-async-diagnostics-20260929.json).

```sh
python3 /home/eric/hybrid-async-diag-deploy.py --rollback /home/eric/hybrid-backups/hybrid-async-diag-20260929-154115
```

Requires clean tracked HEAD `96c2049d`; stops capture/timer, restores `1c25a823`
and restarts them. It does not restore the database or remove the SQLite
bootstrap/checkpoint settings. Prepared, not exercised; verify both cameras
following rollback. Earlier procedures apply only at their exact revision.

## System index rollback

The index uses the same sampled CPU provider as System Info; failed counters
show Unavailable. 169 Python and 34 JavaScript checks pass. Native index and
support navigation evidence is recorded separately from hardware effects.
[Evidence](testing/evidence/hybrid-system-index-20260929.json).

```sh
python3 /home/eric/hybrid-system-index-deploy.py --rollback /home/eric/hybrid-backups/hybrid-system-index-20260929-152712
```

Requires clean tracked HEAD `1c25a823`; restores `a3402d2e` and reloads web only.
Capture remains running. No database restore. Prepared, not exercised.

## Log controller rollback

The Log request-ordering and timeout fix passes 169 Python entrypoints and
34 JavaScript tests, plus isolated failure/recovery and production browser checks.
Web reload left capture PID 1512517 and config 118 unchanged.
[Evidence](testing/evidence/hybrid-log-controller-20260929.json).

```sh
python3 /home/eric/hybrid-log-controller-deploy.py --rollback /home/eric/hybrid-backups/hybrid-log-controller-20260929-151121
```

Requires clean tracked HEAD `a3402d2e`; returns to `9a526bc9` and reloads only
web. No database restore. Rollback is prepared, not exercised. Older rollbacks
below apply only after returning to their exact revision.

## Roll back the Settings/history/restore navigation update

This template-only update retains camera/profile selection through Full Settings,
history, detail and restore navigation. The complete 169-entrypoint regression
and two corrected pagination-assertion reruns pass; all 34 JavaScript tests pass.
The production camera-2 round trip, pagination and snapshot detail pass. Capture
PID 1512517 and configuration 118 are preserved; both latest images decode.
[Evidence](testing/evidence/hybrid-settings-chain-20260929.json).

```sh
python3 /home/eric/hybrid-settings-chain-deploy.py --rollback /home/eric/hybrid-backups/hybrid-settings-chain-20260929-144810
```

Requires clean tracked HEAD `9a526bc9`. Restores `fa85a221` and reloads web only;
no database/configuration restore or capture restart. Code/configuration backup
is retained; the earlier coherent checkpoint database backup remains available.
Rollback is prepared, not exercised. Only after this rollback can the older
shared-Settings rollback below apply. Verify navigation and fresh camera frames.

## Roll back the shared Settings navigation update

The web-only update retains camera/profile context through Timelapse and Storage
Protection links and save redirects. All 169 Python and 34 JavaScript tests pass;
production camera-2 navigation passes. Capture PID 1512517 and config revision 118
remain unchanged. Code/configuration backup and the exact-revision rollback are
prepared; no schema or persistence changes require a new database copy.
[Evidence](testing/evidence/hybrid-shared-settings-context-20260929.json).

```sh
python3 /home/eric/hybrid-shared-settings-context-deploy.py --rollback /home/eric/hybrid-backups/hybrid-shared-settings-context-20260929-142434
```

This requires clean tracked HEAD `fa85a221`, restores `f0d502fb` and reloads only
web. It does not restore the database, change configuration or restart capture.
The rollback is prepared, not exercised. Verify Settings navigation and both
camera frames afterward. Only then can the older checkpoint rollback below apply.

## Roll back the earlier checkpoint release

Use an authenticated SSH terminal as eric. The protected helper requires exactly
`f0d502fb` and a clean tracked checkout. It stops capture/web/socket activation,
removes the managed runtime bootstrap and checkpoint drop-in, returns code to
`3577fa82`, and restarts services. It does not restore the database or delete media.
The full production rollback is prepared, not exercised; isolated runtime removal
has been verified. Run with system Python, which the private runtime does not alter.

```sh
python3 /home/eric/hybrid-checkpoint-deploy.py --rollback /home/eric/hybrid-backups/hybrid-checkpoint-20260929-135156
```

Verify both camera frames, service status and the virtualenv SQLite version after
rollback. Do not merely reset Git: the bootstrap/drop-in must also be removed.
See [runtime installation details](HYBRID_CAPTURE_CADENCE.md).

## Historical Charts/Sensor rollback

Use only after checkpoint rollback has returned code to 3577fa82.

The protected helper requires exactly `3577fa82` and a clean tracked checkout.
It returns code to `35c1ba66` and reloads web without restarting capture or
restoring database/configuration/media. Prepared, not live exercised.

```sh
python3 /home/eric/hybrid-observatory-timeout-deploy.py --rollback /home/eric/hybrid-backups/hybrid-observatory-timeout-20260929-130159
```

Code/config backup only; no database migration. The coherent encoder-release
backup remains available.

## Historical Astropanel rollback

Use only after rolling Charts/Sensor back to `35c1ba66`.

The protected helper requires exactly `35c1ba66` and a clean
tracked checkout. It returns code to 07b2098d and reloads web, preserving capture,
database, configuration and media. This rollback is prepared, not live exercised.
Code/config backup:
`/home/eric/hybrid-backups/hybrid-astropanel-timeout-20260929-124538`.

```sh
python3 /home/eric/hybrid-astropanel-timeout-deploy.py --rollback /home/eric/hybrid-backups/hybrid-astropanel-timeout-20260929-124538
```

No database copy or migration was performed for this JS/template change. The
coherent encoder-release database backup remains available.

## Historical image publication rollback

Use this only after rolling Astropanel back to 07b2098d.

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
