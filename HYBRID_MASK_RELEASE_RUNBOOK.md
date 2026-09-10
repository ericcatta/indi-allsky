# Mask Base: next worker release

Status: prepared locally, **not deployed**. The live acceptance window ended on
10 September 2026 before 20:00 Europe/Zurich. Wait for the user's next window;
this document does not start a deployment or a 24-hour observation.

## Exact release

- Expected installed code: `3590a3ee4621e01b23043ac415de499d79f7c9e3`.
- Candidate code: `5cf365bba6ce5915c017e5b479d7b4ac7813f946`.
- Checkout: `/home/eric/indi-allsky`.
- Runtime database: `/var/lib/indi-allsky/indi-allsky.sqlite`.
- Flask configuration: `/etc/indi-allsky/flask.json`.
- Runtime media directory: resolve `IMAGE_FOLDER` from the active configuration;
  do not infer it from the checkout's database or sample configuration.

Application delta: `image.py`, `mask_frames.py`, `flask/views.py` and
`flask/templates/modern_admin/mask.html`. Other changes are tests and documentation.
Revalidate this list and both revisions before running the release. Stop if the
installed revision or tracked work differs; preserve untracked files.

The candidate publishes `mask-camera-<camera_id>.png` and keeps `mask_base.png`
for historical consumers. Hybrid selects only the scoped file. No schema,
configuration-key, exposure-target or processing-algorithm migration is needed.
The generation trigger remains exposure stability, once per worker camera state.
A failed write now leaves generation pending without aborting frame processing.

## Preflight and recovery assets

1. Confirm the new live window and its end time. Confirm SSH access and recovery
   access before restarting capture; the previous production browser security
   review remains unresolved and must not be bypassed.
2. Record the actual checkout revision, tracked/untracked state, active capture
   and web units, their process identities, both camera IDs/profile bindings,
   current frame freshness and queue state. Keep private details on the device.
3. Check free space for an online SQLite backup, previous-code archive and safe
   operating headroom. Do not delete acquisition data to make room.
4. Create a protected release backup containing an online SQLite backup with
   successful `integrity_check`, previous-code archive, Flask configuration and
   a release record. Record the current configuration revision without changing it.
5. Prepare rollback for **both capture and web**, and verify the unit names and
   installed unit definitions. The previous `hybrid-focus-controls-deploy.py`
   restarts only web and is not a worker-release deployment procedure.

Relevant repository unit: `service/indi-allsky.service`. Its stop command sends
TERM; `sigterm_handler_main` sets the termination flag. A capture restart may
interrupt an in-flight exposure or worker operation. Do not promise uninterrupted
acquisition, purge pending tasks, or repeatedly restart to force a mask to appear.

## Controlled installation

Record the start of maintenance. Stop the web activation socket and web service
and stop capture in the agreed window. Confirm they stopped before changing code.
Install the exact candidate with a fast-forward from the expected revision,
compile the application, then start capture and the previously active web units.
Keep `HYBRID_ENABLE_CLASSIC_UI=false` and verify Flask configuration is unchanged.

Write a protected release-state record with previous/candidate revisions,
backup location, prior unit states, installation result and acceptance status.
Mark the result awaiting acceptance until the observations below are complete.
Do not reuse the previous web-only assertion that the capture PID is unchanged:
this release intentionally restarts capture to load the new publisher.

## Required bounded acceptance

| Requirement | Evidence needed |
| --- | --- |
| Correct code loaded | Candidate revision, clean tracked checkout and new capture/web processes after installation |
| Acquisition recovered | New nonempty frame from each configured camera after maintenance, with the expected camera/profile association |
| Camera-specific mask publication | Worker publication log for each camera and a decodable, nonempty scoped PNG whose modification time is after maintenance |
| Correct generation provenance | Files produced by the running worker after exposure stability; do not manually seed files or force exposure settings to manufacture a pass |
| Hybrid selection | Select each camera/profile in Mask Base; decode the corresponding scoped image and verify the heading and download target |
| Download | Receive and decode the selected camera's PNG; merely seeing the link or HTTP success is insufficient |
| Configuration preserved | Same Flask configuration bytes and expected saved configuration revision; Classic remains disabled |
| Runtime healthy | No new capture/encoding failures, no unexplained queue accumulation, both cameras continue acquiring within the bounded window |

A missing scoped base while exposure has not stabilized is an open acceptance
case, not permission to substitute the ambiguous historical file. Finish at the
agreed deadline; record missing evidence without extending observation silently.
Production browser checks remain open if the browser security review is unresolved.

## Rollback if the release fails

Capture and web must both load the same previous code. In the agreed recovery
window, stop their active units, verify the checkout still matches the candidate
and has no tracked edits to preserve, restore the exact previous code, and start
the previously active units. Verify fresh frames from both cameras and web recovery.
Record the rollback result separately from the original installation result.

Do not restore the database or configuration for this code-only rollback. Preserve
new images, queue records, configuration revisions and scoped mask PNGs. The old
code ignores the scoped files and continues using the compatibility file. Never
use `git clean` to remove them or other user files.

After a rollback to `3590a3ee`, earlier rollback instructions remain in
`HYBRID_DEPLOYMENT.md`. Classic remains disabled unless a separately justified
recovery explicitly restores its mode. No rollback has been drilled for this
candidate and no production acceptance is claimed here.

## Existing evidence

- `testing/evidence/hybrid-mask-camera.json`: isolated publication, failure,
  camera/profile, policy and native browser selection checks.
- `testing/evidence/hybrid-mask-recovery.json`: failed publication retries without
  interrupting frame processing; 138 Python and 34 JavaScript entrypoints passed.

After live acceptance, update the installed-release record and attach aggregate
results. The whole product matrix, physical Classic removal and final cleanup
remain separate outstanding requirements; the 24-hour observation stays deferred.
