# Hybrid: deployment and rollback

## Active configuration — 4 October

Configuration 119 enables SD-only night FITS/day JPEG, lossless compression,
24-hour image protection under storage pressure (5 GiB trigger, 8 GiB target),
and five-day timelapse expiry. The updated cleanup priority is described below.
Both cameras resumed after capture restart; day JPEG cadence is 15 seconds.
Night source-only capture acceptance is still open.
[Evidence](testing/evidence/hybrid-sd-policy-20261004.json).

### Daytime-first storage recovery

Activated as `677afbab` at 21:39 CEST on 5 October; both cameras resumed,
fresh FITS files were verified and the updated Settings page was checked.
[Tests and release evidence](testing/evidence/hybrid-storage-priority-20261005.json).

The 5 October cleanup update changes the priority of eligible assets:
daytime images, night images, daytime generated outputs, then night generated
outputs (including timelapses). Each group is ordered oldest first across cameras.
FITS backing an expired display record are reclaimed at that record's priority,
after its references are removed. Pending uploads/generations still protect files.

The free-space trigger and target remain configurable in Storage Protection.
Image protection uses `STORAGE_PRESSURE.KEEP_DAYS` (currently one day). Generated
outputs use `TIMELAPSE_EXPIRE_DAYS`, with a five-day minimum for pressure cleanup.
Cleanup stops at the target and never shortens these protection periods to force
recovery. This supersedes the earlier policy excluding every video from pressure
cleanup. No schema, configuration-key or default-setting migration is required.

The previous configuration is retained as revision 118 and in the private
`/home/eric/hybrid-backups/hybrid-sd-policy-20261004/config-before.json`.
Restore configuration through the revision service if needed, then restart capture;
keep the deployed source-aware readers for any new FITS-only frames. Do not use
an older code rollback that cannot read source-backed images.

## Current application — 5 October, worker release activated

The worker repair release `db5fc9c0` (included in current `677afbab`) contains mini-FITS thumbnail repair `7641e966`,
capture-notification contention repair `d53c72f4`, and stable per-frame day/night
context `2f850d7d`. The combined candidate passed 200 Python/compile checks;
JavaScript was unchanged from the 35-check run. Installed application hashes were
verified before restart at 21:24:26 CEST. Both cameras published fresh FITS; mini
outputs 9/10 passed worker/file/thumbnail checks and native playback, preserving
original source hashes. [Release evidence](testing/evidence/hybrid-worker-release-20261005.json).

The previous tracked application is preserved at
`/home/eric/hybrid-backups/worker-repairs-20261005/tracked-code.tar.gz`, with revision
and SHA-256 files. The database/configuration were not replaced. A controlled
capture stop allowed existing retention cleanup to restore 8 GiB before activation.
The old 24-hour observation cannot certify this corrected runtime.

### Worker release procedure

The collector stopped after 24 hours. The user authorized a new maintenance
window after the original 19:15 cutoff; the release above used these steps.
Future runtime changes require their own validation and live checks.

1. Confirm the observer's final record, installed Git revision, configuration
   revision 119, free space, capture/web service state and running video tasks.
   Wait for active generation or cleanup to finish before the controlled restart.
2. Preserve the currently installed tracked code in a private backup outside the
   checkout, with its commit and checksums. No schema or configuration change is
   required. Preserve the existing database and all untracked local files; do not
   start another large online database copy on the busy SD card.
3. Fetch and fast-forward `main`, checking the actual diff against the tested
   release before activation. A newer unrelated application change needs its own
   validation; a Git pull alone is not evidence that the running worker changed.
4. Restart `indi-allsky.service` through the user service manager to load the new
   Python worker. The coordinator forks imported modules, so restarting only a
   video child does not reliably activate this change. Record the interruption,
   old/new PIDs and installed revision. Reload the web service if its code changed.
5. Check fresh source-backed frames from both cameras. Generate bounded mini
   timelapses from recorded night FITS for each camera, then verify task success,
   the output file, thumbnail, playback and download. Preserve original FITS.
   Do not claim 24 hours of the newly activated worker from the earlier period.
6. Inspect child-worker PIDs and journal errors, not just the parent service's
   restart counter. Do not deliberately lock the live database. Observe a natural
   day/night transition if it falls inside the new window; otherwise explicitly
   retain the automated-only qualification for that transition. Do not force night
   or extend the window to manufacture live coverage.

### Roll back a worker fix if necessary

Keep the current source-aware archive readers and configuration 119. Revert only
`7641e966`'s application change in `indi_allsky/video.py` (or restore that exact
file from the pre-deploy private backup), then restart capture in a controlled
window and verify both cameras. This restores the known mini-generation defect;
report that limitation. Do not restore an old database, delete archived media or
use a pre-source-aware application snapshot. Repository history should reflect
any rollback through a new commit, without rewriting published history.
For the SQLite or phase fixes, independently revert the application change in
`capture.py` or `image.py`, respectively, using the preserved pre-deploy revision.
Record the reintroduced defect; do not revert unrelated source-aware functionality.

## Release history — not current deployment instructions

### Scientific archive, 3 October

On 3 October `3d87c9aa` deployed the scientific archive implementation, disk UUID
protection and fast lossless FITS compression. All 198 Python/compile and 35
JavaScript checks passed; installed source hashes match exactly. Capture restarted
as PID 1631805 with zero automatic restarts and fresh frames from both cameras;
Gunicorn reloaded. Configuration remains revision 118: the new format policy is
not yet activated, and scheduled FITS remains every 7200 seconds.

New real FITS 986/987 contain complete rendering context. Their reconstructed
previews have exactly the same decoded pixels as saved images 207493/207494;
scientific digests remain unchanged. Native Now and Storage Protection checks
passed. This proves those two exposures, not sustained source-only acquisition.
[Deploy evidence](testing/evidence/hybrid-scientific-archive-release-20261003.json).

Rollback before activating the new policy: stop capture, restore the prior tracked
code from `/home/eric/hybrid-backups/hybrid-scientific-archive-20261003/code.tar.gz`
(baseline `0cf2de6e`), reload Gunicorn and restart capture. Verify both fresh frames.
Preserve untracked local files and the current database. Once source-only capture
is activated, do not roll back to a reader lacking source-backed media support.

Previous deployments:


On 2 October `dda3eeff` added exposure-matched FITS/RAW options to Highlights
and renamed the processed download accurately. All 182 Python/compile and 35
JavaScript tests passed; installed source hashes match. Gunicorn was reloaded;
capture PID 840928 continued without restart. Native labels and absent-source
states passed for both cameras. FITS saving remains every 7200 seconds; RAW
export remains disabled. [Evidence](testing/evidence/hybrid-highlights-sources-release-20261002.json).
Rollback: restore the three application files preserved with their paths in
`/home/eric/hybrid-backups/hybrid-highlights-sources-20261002`, then reload
Gunicorn. No database/configuration restoration or capture restart is needed.

Previous deployment:


On 1 October at 22:37 local time, checkout `48c2eddb` was deployed after the
user revoked the 20:00 cutoff. Its application changes are `05d6e7d6` (libcamera
child output uses an anonymous temporary file for every profile) and `584f066f`
(Keogram links retain camera/profile). All 182 Python/compile entrypoints and
35 JavaScript tests passed; production sources match the tested manifest.
Capture restarted as PID 840928 with zero automatic restarts, and Gunicorn
reloaded. Configuration remains 118. Both cameras produced decoded fresh frames;
all four Keogram destination clicks passed. Mini-video task 14234 succeeded and
played to its natural end; both cameras captured during its 37.7-second encode.
This is bounded validation, not proof of the earlier timeout's root cause.
[Release evidence and limits](testing/evidence/hybrid-combined-release-20261001.json).

Rollback copies of `indi_allsky/camera/libcamera.py` and
`indi_allsky/flask/templates/modern_admin/keograms.html` are in
`/home/eric/hybrid-backups/hybrid-combined-release-20261001` with a private
manifest and Flask configuration copy. Restore only these two code files,
restart capture and reload Gunicorn, then verify fresh frames from both cameras.
No schema/configuration was migrated; **do not restore an older database** to
undo this release. A new online database copy to the same SD filesystem was
interrupted after filesystem write waits and stale frames; its incomplete copy
was removed. The prior coherent cold-start backup is retained. Both cameras
recovered after terminating that backup process, before the deployment restart.

The preceding application change `117d22fb` removed redundant panorama preview
fsync calls while retaining atomic publication and archive synchronization.
[Measurement and rollback](testing/evidence/hybrid-panorama-preview-sync-20261001.json).

The preceding application change is `365f77e5`: VirtualSky
export availability follows frame loading, including preview redraws. The browser
loads virtualsky-003 and the native refresh/export check passes.
[Verification and rollback](testing/evidence/hybrid-virtualsky-alignment-20261001.json).
The preceding HTTP Settings concurrency fix is `04388e02`.
The preceding worker recovery change is `ffb4335c`.
The previous `f21f87d5` change corrected Observatory disk usage.
Geometry now rejects invalid azimuth before copy/review; the updated asset version is verified in production. 175 Python checks and 35 JavaScript tests passed. [Validation and deployment](testing/evidence/hybrid-geometry-validation-20261001.json).

The geometry-to-Keogram link now preserves camera/profile. Its 175 Python and 34 JavaScript checks passed; native source-to-Settings navigation now passes for both cameras/profiles after network recovery. Both recent frames decoded on 1 October at 13:05:00 / 13:05:07. [Latest change](testing/evidence/hybrid-geometry-scope-20261001.json).

Later documentation/test commits do not change the running application.
Read the actual checkout revision with `git rev-parse HEAD`; do not use an older
release heading as proof of the installed version.
Classic frontend is removed. Hybrid requires login; shared backend and public
compatibility handlers remain. Configuration revision is 118.

See [current status and open gates](HYBRID_ACCEPTANCE_STATUS.md).

## Deployment locations

- Checkout: `/home/eric/indi-allsky`.
- Python: `/home/eric/indi-allsky/virtualenv/indi-allsky/bin/python`.
- Runtime database: `/var/lib/indi-allsky/indi-allsky.sqlite`.
- Media: `/var/www/html/allsky/images`.
- Web unit: `gunicorn-indi-allsky.service` in the deployment user's systemd manager.
- Capture unit: `indi-allsky.service` in that manager.

The database copy in the checkout is not the runtime database. Preserve local
user files, including untracked files; do not use `git clean` to make production
appear clean. Keep backups private and public assets readable by Apache.

## Before and after a release

Pin the tested commit and exact changed files. Check Git state, disk space,
active tasks, services and configuration revision. Prepare an appropriate
backup and rollback for that exact change before deployment. Backend/schema
changes require a coherent database backup; never restore an older database
merely to undo a code-only change.

The latest recorded coherent cold-start backup is
`/home/eric/hybrid-backups/hybrid-cold-start-20260930`: database integrity passed,
Flask configuration was saved privately, and media were not copied.
[Backup and cold-start evidence](testing/evidence/hybrid-cold-start-20260930.json).
Verify the backup is suitable for the next change; this is not a promise that
it contains data acquired afterward. Earlier backup activity coincided with
I/O stalls, so watch queue growth and actual frame recovery during maintenance.

Use a fast-forward pull only after checking local changes. For the latest
web-only changes, reload `gunicorn-indi-allsky.service`; acquisition need not
restart. Changes to capture/workers require a separately controlled restart.
Afterward verify installed source, authentication, the affected UI/request/effect,
and fresh decoded frames from both cameras. A running unit alone is insufficient.

## Rollback of the latest code-only changes

For AWB sync validation `db205760`, revert that commit or restore only
`indi_allsky/flask/views.py` from `457e3e21`, then reload Gunicorn.
The verified backup is `/home/eric/hybrid-backups/hybrid-profile-sync-20261001/views.py`.
No capture restart or database/configuration restore is required.

For worker commit recovery `ffb4335c`, revert that commit or restore only
`indi_allsky/video.py` and `indi_allsky/uploader.py` from `a4c84df5`.
Verified copies also exist in `/home/eric/hybrid-backups/hybrid-worker-rollback-20261001`.
Restart capture and verify both cameras. No database/configuration restore is needed.

For disk usage consistency `f21f87d5`, revert that commit or restore only
`indi_allsky/observatory_runtime.py` from `87dfc0ce`, then reload Gunicorn.
No data/configuration restore or capture restart is needed.

For upload failure handling `3a058fae`, revert that commit or restore only
`indi_allsky/uploader.py` from `d3872802`. Restart capture in a controlled window
and verify both cameras. No database/configuration restore is required.

For video task failure handling `81fa7805`, revert that commit or restore only
`indi_allsky/video.py` from `e2404cfd`. Restart capture in a controlled window
and verify new decoded frames from both cameras. No schema/configuration changes
were made; do not restore an older database to undo this code change.

For AJAX object admission `85d9f04c`, revert that code change: restore
`indi_allsky/flask/views.py` from `306c5235` and remove its newly introduced
`indi_allsky/flask/json_request.py` module, then reload Gunicorn. This preserves
the preceding Full Config validation. No database/configuration rollback is needed.

For catalog retirement `a5e4b7e0`, the previous complete
`indi_allsky/modern_safe_action.py` is at `e3c1e8fa`.
For Full Config input validation `4d2e08fa`, the previous complete
`indi_allsky/flask/views.py` is at `5bb258c6`.
These are independent web-only changes; neither migrated data or configuration.

Inspect the diff against the installed version before restoring either file.
Restore only the intended file from its stated reference, then reload Gunicorn
and repeat the affected checks. Record/reconcile that rollback in Git; do not
leave an undocumented working-tree override. Do not roll back input validation
unless necessary: doing so restores the malformed-request failure.

Older rollback scripts are release-specific. Their commands and complete chain
are preserved at `a2d53040`:
`git show a2d53040:HYBRID_DEPLOYMENT.md`.
They are not generic rollback commands for current production. In particular,
capture/SQLite/image-publication changes require their own coordinated procedure.
The private SQLite 3.51.3 runtime remains installed; OS SQLite is unchanged.

## Automatic startup

Capture uses enabled `indi-allsky.timer`; INDI uses its configured timer/service;
Gunicorn uses its enabled socket. A service may correctly report `disabled`
while its timer/socket is enabled. Do not add duplicate startup paths.
User lingering permits startup without an SSH login.

On 30 September, orderly shutdown followed by physical power disconnect/reconnect
passed: web, INDI and capture started automatically and both new frames decoded
before the first SSH login. This does not test abrupt power-loss durability.
[Cold-start evidence](testing/evidence/hybrid-cold-start-20260930.json).

Read-only checks as the deployment user:

```sh
loginctl show-user "$USER" -p Linger
systemctl --user is-enabled indi-allsky.timer indiserver.timer indiserver-asi678mc.service gunicorn-indi-allsky.socket
systemctl --user is-active indi-allsky.service indiserver-asi678mc.service gunicorn-indi-allsky.socket
systemctl is-enabled apache2
```

After restart, verify actual fresh frames from both cameras. Storage Protection
settings control automatic cleanup; one-off test-media cleanup does not change
that saved policy. Never assume previous deletion permission covers new data.

## Historical backup storage

Some older snapshots are archived as `indi-allsky.sqlite.gz` to recover space.
Their `compressed-storage.json` records the original byte length and SHA-256;
complete decompression is verified before removing the uncompressed copy.
The historical coherent checkpoint backup (`hybrid-checkpoint-20260929-135156`)
remains uncompressed; configuration and code archives are preserved. Older
release database snapshots, including storage-estimate, may now be compressed. On 29 September four older database snapshots were
compressed and fully verified, reclaiming 3,219,880,401 bytes; free space was
8.53 GiB afterward. See [archival evidence](testing/evidence/hybrid-backup-archival-20260929.json).

Before using an archived database snapshot, ensure space for `original_bytes`,
run `gzip -dk indi-allsky.sqlite.gz` in its backup directory, then compare
`sha256sum indi-allsky.sqlite` with `original_sha256` in the marker file.
This reconstructs a backup file; it does not restore the live database.
The same instructions are retained privately on the Raspberry in
`/home/eric/hybrid-backups/COMPRESSED_BACKUPS.md`.

## Acceptance limits

The control/effect matrix and export receipts remain open. Hardware without
configured drivers and unavailable external integrations remain explicitly
untested; do not enable them merely to manufacture a passed test.
The 24-hour observation and detector/AI work are deferred by the user.
[Status and evidence](HYBRID_ACCEPTANCE_STATUS.md) are authoritative for these limits.

## FITS preview context — 2 October 2026

Application `994ac136` was fast-forwarded to production with an exact tested-source
manifest match and web-only reload. Capture PID 840928 stayed active. Both camera
FITS previews decoded in the native administrator browser. Configuration and media
were unchanged. For this code-only release, rollback is the retained
`/home/eric/hybrid-backups/hybrid-fits-context-20261002/source_media_views.py` copied
back to `indi_allsky/flask/source_media_views.py`, followed by a Gunicorn reload.
No old database restore is needed. [Test/deploy evidence](testing/evidence/hybrid-fits-preview-context-20261002.json).

## Archive disk protection (candidate, not deployed)

Storage Protection can pin the currently configured archive directory to its
filesystem UUID. This does not mount, format, or migrate a disk. For external
storage, first configure a persistent UUID-based operating-system mount and copy
existing archive contents with capture stopped. Preserve relative paths, source
FITS, thumbnails and the shared rendering assets together. Set IMAGE_FOLDER to
the mounted archive directory, rerun setup to update the web path, and enable
“Require this filesystem before using archive” in Storage Protection. Restart
capture to load the saved policy. Do not remove the previous archive until file
counts, source previews/downloads and both cameras have been verified.

The protection requires a block filesystem UUID; a network share without one
cannot use this guard. Setup checks an already pinned volume before rewriting
storage paths. A missing or different disk stops guarded archive access and
cleanup. Capture waits for the configured disk and resumes after it returns;
the Storage Protection page remains available to administrators for recovery.
Do not disable protection merely to silence an absent-disk error: doing so permits
use of the directory on the underlying filesystem. When intentionally changing
disks, stop capture, update the storage configuration and mount, then pin the new
filesystem and restart capture.

Automated absence/reconnection checks are simulations. No external disk is
currently connected to this installation, so physical external-storage recovery
remains unverified. This candidate does not change production archive formats or
retention. Capacity and retention must be agreed before enabling every-frame FITS.
