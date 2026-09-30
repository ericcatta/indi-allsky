# Hybrid: deployment and rollback

## Current application

The latest application change deployed on 30 September is `85d9f04c`.
Later documentation/test commits do not change the running application.
Read the actual checkout revision with `git rev-parse HEAD`; do not use an older
release heading as proof of the installed version.
Classic frontend is removed. Hybrid requires login; shared backend and public
compatibility handlers remain. Configuration revision is 118.

The current application passed 175 Python/compile entrypoints and 34 JavaScript
tests. The last deployment reloaded only Gunicorn; capture PID 1565 remained
active with zero restarts and both images decoded in the native browser.
[Regression and deployment](testing/evidence/hybrid-ajax-json-admission-20260930.json).
This is bounded acceptance, not full-product or 24-hour certification.
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
