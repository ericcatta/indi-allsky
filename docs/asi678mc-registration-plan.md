# ASI678MC Registration Plan

Date: 2026-06-13

## Goal

Register the ZWO ASI678MC in the indi-allsky database and make it appear in Modern Admin Cameras, without losing the existing Camera Module V3 Wide configuration.

This plan assumes the ASI678MC has already been successfully detected through INDI with `indi_asi_ccd` or `indi_asi_single_ccd`.

For a dedicated user systemd service on port `7625`, see `docs/indiserver-systemd-plan.md`.

## Summary

The safest practical path is a short temporary camera switch:

1. Back up the current DB, Flask config, and current camera-related settings.
2. Stop the active V3 Wide capture service.
3. Temporarily configure indi-allsky for the ASI678MC through the existing INDI path.
4. Start capture only long enough for indi-allsky to connect to the ASI camera and create/update its `camera` DB row.
5. Verify the ASI camera row and Modern Admin Cameras inventory.
6. Roll back the active config to the V3 Wide setup.

The current indi-allsky runtime does not provide a normal "register another local camera without switching capture" workflow. A temporary switch is required because camera rows are created by the capture pipeline after a real camera connection.

## Why a Temporary Camera Switch Is Required

indi-allsky registers cameras during capture startup, not during passive discovery.

The relevant flow is:

1. `indi_allsky/capture.py` selects one camera backend from `CAMERA_INTERFACE`.
2. For the ASI678MC, that backend is `indi`.
3. The capture worker connects to `INDI_SERVER` and `INDI_PORT`.
4. It calls `findCcd(camera_name=INDI_CAMERA_NAME)`.
5. It builds camera metadata from the connected device.
6. It calls `miscDb.addCamera(camera_metadata)`.
7. `miscDb.addCamera()` inserts or updates a row in the `camera` table.
8. Capture stores the active camera id in the `state` table as `DB_CAMERA_ID`.

Because this path is tied to one active capture backend, the ASI678MC will not be registered in the indi-allsky DB merely by plugging it in or by running a separate temporary `indiserver` test. indi-allsky itself must briefly run against the ASI camera.

## Exact Configuration Changes Required

Capture config changes for the ASI registration window:

| Setting | Temporary ASI value | Notes |
| --- | --- | --- |
| `CAMERA_INTERFACE` | `indi` | Switches capture from libcamera to INDI. |
| `INDI_SERVER` | `localhost` | Use local indiserver. |
| `INDI_PORT` | `7625` when using `indiserver-asi678mc.service`; otherwise the configured production INDI port | Must match the indiserver service port used by indi-allsky during the ASI registration window. |
| `INDI_CAMERA_NAME` | Exact detected ASI device name, if known | Example: `ZWO CCD ASI678MC`. Leave blank only if the ASI is the only CCD exposed by that indiserver. |

INDI server driver changes for the ASI registration window:

| Setting | Temporary ASI value | Notes |
| --- | --- | --- |
| Camera server/driver | `indi_asi_ccd` | Preferred ZWO ASI driver if available. |
| Camera server/driver fallback | `indi_asi_single_ccd` | Use only if this was the driver that worked in the INDI test. |
| GPS driver | Keep existing value | Do not change unless required by the current install. |
| INDI restart | Yes, after driver change | Required for the ASI driver to be active. |

Rollback V3 Wide values to restore after registration:

| Setting | V3 Wide value | Notes |
| --- | --- | --- |
| `CAMERA_INTERFACE` | `libcamera_imx708` | Existing Camera Module V3 Wide backend. |
| `LIBCAMERA.CAMERA_ID` | previous value, usually `0` | Record this before the test. |
| `INDI_SERVER` / `INDI_PORT` / `INDI_CAMERA_NAME` | previous values | Restore exactly as found, even if not used by libcamera. |
| INDI server driver | previous value | If V3 setup did not rely on indiserver, restore the previous service state/settings. |

Do not change image folder, upload settings, storage settings, authentication, location, lens settings, or processing settings for this registration test.

## Pre-Registration Backup

Run these before changing anything.

### Back up production files

```bash
mkdir -p ~/indi-allsky-asi-registration-backup

cp -a /etc/indi-allsky/flask.json \
  ~/indi-allsky-asi-registration-backup/flask.json.pre-asi.$(date +%Y%m%d-%H%M%S)

sqlite3 /var/lib/indi-allsky/indi-allsky.sqlite \
  ".backup '$HOME/indi-allsky-asi-registration-backup/indi-allsky.pre-asi.$(date +%Y%m%d-%H%M%S).sqlite'"
```

If the install uses a user-level indiserver unit, also back it up:

```bash
cp -a ~/.config/systemd/user/indiserver.service \
  ~/indi-allsky-asi-registration-backup/indiserver.service.pre-asi.$(date +%Y%m%d-%H%M%S)
```

If the install uses a system-level unit, inspect and back up the correct unit path before editing.

### Record current latest config rows

```bash
sqlite3 /var/lib/indi-allsky/indi-allsky.sqlite \
  "select id, createDate, note, json_extract(data, '$.CAMERA_INTERFACE'), json_extract(data, '$.INDI_SERVER'), json_extract(data, '$.INDI_PORT'), json_extract(data, '$.INDI_CAMERA_NAME'), json_extract(data, '$.LIBCAMERA.CAMERA_ID') from config order by createDate desc limit 5;"
```

### Record current camera rows

```bash
sqlite3 /var/lib/indi-allsky/indi-allsky.sqlite \
  "select id, name, friendlyName, driver, connectDate, hidden from camera order by id;"
```

### Record current active DB camera id

```bash
sqlite3 /var/lib/indi-allsky/indi-allsky.sqlite \
  "select key, value from state where key = 'DB_CAMERA_ID';"
```

## Registration Procedure

### 1. Stop active capture

For a user service install:

```bash
systemctl --user stop indi-allsky.service
```

For a system service install:

```bash
sudo systemctl stop indi-allsky.service
```

Leave the web UI running if possible. It is useful for changing config and checking Modern Admin.

### 2. Configure indiserver for ASI

Use classic admin System > INDI Drivers if available:

1. Set camera server/driver to `indi_asi_ccd`.
2. If the successful INDI test used `indi_asi_single_ccd`, use that instead.
3. Leave GPS driver unchanged.
4. Enable restart indiserver.
5. Apply the change.

If using commands instead of the UI, avoid replacing service files blindly. The effective `indiserver.service` should run the ASI driver on the same port used by the indi-allsky config.

Expected effective command shape for the dedicated ASI service:

```text
indiserver -v -p 7625 -u /tmp/indiserver-modern-admin-7625 indi_simulator_telescope indi_asi_ccd
```

The helper script can create this user service:

```bash
./misc/setup_asi678mc_indiserver.sh
systemctl --user daemon-reload
systemctl --user enable --now indiserver-asi678mc.service
systemctl --user status indiserver-asi678mc.service --no-pager
```

### 3. Temporarily configure capture for ASI

Use classic admin System > Config.

Change only:

- `CAMERA_INTERFACE`: `indi`
- `INDI_SERVER`: `localhost`
- `INDI_PORT`: `7625` when using `indiserver-asi678mc.service`, otherwise the configured indiserver port
- `INDI_CAMERA_NAME`: exact detected ASI device name, for example `ZWO CCD ASI678MC`

If only one CCD is exposed by the ASI indiserver, `INDI_CAMERA_NAME` may be blank. Setting it explicitly is safer because it prevents the wrong INDI CCD from being selected if another CCD driver is exposed.

Save the config.

### 4. Start capture briefly

For a user service install:

```bash
systemctl --user start indi-allsky.service
journalctl --user -u indi-allsky.service -f
```

For a system service install:

```bash
sudo systemctl start indi-allsky.service
sudo journalctl -u indi-allsky.service -f
```

Watch for:

- successful connection to indiserver,
- ASI camera name in logs,
- no repeated service restart loop,
- camera metadata being detected,
- first exposure starting or completing.

Let it run only long enough to connect and register the camera. Capturing a single frame is useful but not required if the camera row is created.

## How the New Camera Row Is Created

The new row is created by capture startup, not by Modern Admin.

When the ASI backend connects successfully:

- `capture.py` reads metadata from the connected INDI CCD.
- `capture.py` calls `miscDb.addCamera(camera_metadata)`.
- `miscDb.addCamera()` looks for an existing camera by `name`, `name_alt1`, or `name_alt2`.
- If no match exists, it inserts a new row in the `camera` table.
- If a match exists, it updates that existing row.
- The active connected camera id is written to the `state` table as `DB_CAMERA_ID`.

Important implication:

- If the ASI camera uses a stable unique device name, it should create one persistent ASI row.
- If the INDI driver reports a generic or changing name, the row may be ambiguous or duplicated.
- The V3 Wide camera row should not be deleted by this test.

## Verify DB Registration

Run:

```bash
sqlite3 /var/lib/indi-allsky/indi-allsky.sqlite \
  "select id, name, friendlyName, driver, width, height, bits, connectDate, hidden from camera order by connectDate desc, id desc;"
```

Expected:

- A row appears for the ASI678MC.
- `connectDate` is recent.
- `name`, `friendlyName`, or `driver` indicates ZWO/ASI/INDI.
- Existing V3 Wide row is still present.

Check current active DB camera id:

```bash
sqlite3 /var/lib/indi-allsky/indi-allsky.sqlite \
  "select key, value from state where key = 'DB_CAMERA_ID';"
```

During the ASI test, `DB_CAMERA_ID` should point to the ASI row.

If one image was captured:

```bash
sqlite3 /var/lib/indi-allsky/indi-allsky.sqlite \
  "select i.id, i.camera_id, c.name, i.createDate, i.filename from image i join camera c on c.id = i.camera_id order by i.createDate desc limit 10;"
```

## Verify in Modern Admin Cameras

Open:

```text
/indi-allsky/modern-admin/cameras
```

Expected:

- ASI678MC appears as its own camera card.
- Camera Module V3 Wide remains listed.
- ASI card shows the best available friendly name or a technical fallback.
- ASI metadata shows the INDI/ZWO driver or interface if available.
- During the temporary ASI run, ASI may appear active.
- After rollback, V3 Wide should return to active/latest capture, and ASI should remain as an inventory/historical camera.

Also verify the classic sidebar camera selector still lists the expected cameras. If classic shows the ASI but Modern Admin Cameras does not, the registration succeeded and the issue is Modern Admin display logic.

## Rollback Procedure

Rollback should restore active V3 Wide capture. It does not need to delete the ASI camera row. Keeping the row is useful because the goal is registration.

### 1. Stop capture again

User service:

```bash
systemctl --user stop indi-allsky.service
```

System service:

```bash
sudo systemctl stop indi-allsky.service
```

### 2. Restore V3 Wide capture config

Use classic admin System > Config.

Restore:

- `CAMERA_INTERFACE`: `libcamera_imx708`
- `LIBCAMERA.CAMERA_ID`: previous recorded value, usually `0`
- `INDI_SERVER`: previous recorded value
- `INDI_PORT`: previous recorded value
- `INDI_CAMERA_NAME`: previous recorded value

Save the config.

### 3. Restore indiserver state if changed

If V3 Wide did not depend on the ASI indiserver:

- restore previous INDI driver settings, or
- stop/disable indiserver only if that was the previous known-good state.

If the service file was changed manually and the UI cannot restore it, copy back the saved `indiserver.service` backup and reload systemd:

```bash
systemctl --user daemon-reload
```

Or with system scope:

```bash
sudo systemctl daemon-reload
```

### 4. Start V3 Wide capture

User service:

```bash
systemctl --user start indi-allsky.service
systemctl --user status indi-allsky.service --no-pager
```

System service:

```bash
sudo systemctl start indi-allsky.service
sudo systemctl status indi-allsky.service --no-pager
```

### 5. Verify rollback

```bash
sqlite3 /var/lib/indi-allsky/indi-allsky.sqlite \
  "select id, name, friendlyName, driver, connectDate from camera order by connectDate desc, id desc limit 5;"

sqlite3 /var/lib/indi-allsky/indi-allsky.sqlite \
  "select key, value from state where key = 'DB_CAMERA_ID';"
```

Expected:

- V3 Wide reconnects and gets the most recent `connectDate`.
- `DB_CAMERA_ID` returns to the V3 Wide row after capture reconnects.
- Modern Admin Dashboard shows V3 Wide latest image again.
- Modern Admin Cameras still lists the ASI678MC.

## Emergency Rollback

Use this only if the UI rollback fails or services cannot be restored.

1. Stop capture and web services:

```bash
systemctl --user stop indi-allsky.service
systemctl --user stop gunicorn-indi-allsky.service
```

Or system scope equivalents.

2. Restore `/etc/indi-allsky/flask.json` from backup.

3. Restore the DB backup only if the config table or camera table is corrupted. Restoring the DB will remove the ASI camera row if it was created after the backup.

4. Restore `indiserver.service` from backup if it was manually changed.

5. Reload systemd and restart services:

```bash
systemctl --user daemon-reload
systemctl --user start gunicorn-indi-allsky.service
systemctl --user start indi-allsky.service
```

Or system scope equivalents.

## Recommended Safest Path

Use a planned short maintenance window.

Recommended sequence:

1. Back up DB/config/service.
2. Record current V3 Wide config values.
3. Switch indiserver to `indi_asi_ccd`.
4. Switch capture config to `CAMERA_INTERFACE=indi`.
5. Start capture and wait for ASI DB row.
6. Verify ASI in DB and Modern Admin Cameras.
7. Stop capture.
8. Restore `CAMERA_INTERFACE=libcamera_imx708` and previous V3 values.
9. Restart capture.
10. Verify V3 latest image and Modern Admin Cameras.

Do not try to keep both cameras active from this normal install. The goal here is registration only.
