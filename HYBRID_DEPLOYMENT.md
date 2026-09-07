# Hybrid: deployment and rollback

## Installed release, 7 September 2026

The Raspberry checkout `/home/eric/indi-allsky` runs
`b65cd8560715b8878fbd44af7a8818f94cd67533`, deployed at 09:42:33 CEST.
The previous installed revision was `faf53d8653b6c62588025e954688c8ee220a6ce8`.
Classic is still enabled; this release does not remove it.

The new 24-hour observation starts at 09:42:33. A service restart or capture/
scheduling correction requires a new observation period. Passing isolated tests
and a fresh frame after deployment do not complete that requirement.

Release evidence: `testing/evidence/hybrid-release-b65cd856-2026-09-07.json`.
On the Raspberry, detailed test logs are in
`/home/eric/hybrid-release-evidence-b65cd856`.

## Recovery assets

Protected backup directory:
`/home/eric/hybrid-backups/release-b65cd856-20260907-093949`.
It contains the online SQLite backup, copied Flask configuration, manifest and
both deployment-attempt records. SQLite integrity was checked. Backup size is
828,977,152 bytes. These files may contain credentials; keep their existing
restricted permissions and do not attach them to public reports.

Preserve untracked user files: `HYBRID_ROADMAP.local.md`,
`ZWO CCD ASI678MC.CCD1.CCD1.fits`, `audit/`, and `indi-allsky.sqlite` in the checkout.
Never use `git clean` for deployment. The runtime database remains at
`/var/lib/indi-allsky/indi-allsky.sqlite`; the checkout copy is not the live DB.

## Roll back code if this release fails

Use an authenticated SSH terminal as `eric`. Check for tracked edits first and
save any new work before rollback. Authenticate sudo **before** stopping services.
Stop the timer as well as the capture service so it cannot restart during checkout.
The following assumes the currently recorded timer/service were active; if that
operational state has changed, preserve the actual state instead.

```sh
cd /home/eric/indi-allsky
(
  set -e
  git diff --exit-code
  git diff --cached --exit-code
  sudo -v
  sudo -n true
  trap 'sudo -n systemctl start apache2; systemctl --user start indi-allsky.service; systemctl --user start indi-allsky.timer' EXIT
  systemctl --user stop indi-allsky.timer
  systemctl --user stop indi-allsky.service
  sudo -n systemctl stop apache2
  git reset --hard faf53d8653b6c62588025e954688c8ee220a6ce8
  /home/eric/indi-allsky/virtualenv/indi-allsky/bin/python -m compileall -q indi_allsky
  sudo -n /usr/sbin/apache2ctl configtest
)
```

Then inspect `systemctl --user status indi-allsky.service`, timer and Apache state,
check Now, and verify newly created image files for **both** cameras. Review the
journal with `_SYSTEMD_USER_UNIT=indi-allsky.service`. Confirm the resulting Git
revision and restart the observation baseline. A failed restart requires immediate
manual recovery; do not infer success from the checkout command alone.

This is a code rollback; it has not been drilled by reverting the live release.
It does **not** restore the old database automatically, because doing so would
remove records acquired since the backup. Restore database/configuration only
for a diagnosed need, with all writers stopped and a fresh copy of current data
saved first. No schema migration was part of this deployment.

## Next acceptance checks

- Confirm completed automatic backup and a real readable compressed database file.
- Confirm aurora/smoke/TLE/health task results; expired or empty queues are not success.
- Complete the UI interaction matrix and real effects using dedicated test data.
- Complete day/night stability and check recovery for both camera profiles.
- Remove Classic only after parity, then repeat the essential checks.
