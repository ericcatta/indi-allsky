# ASI678MC Test Plan for Pi 5

Date: 2026-06-13

## Goal

Connect a ZWO ASI678MC to Eric's Raspberry Pi 5 and prove that it can be detected by INDI and registered by indi-allsky, without permanently disrupting the existing Camera Module V3 Wide setup.

The safest practical approach is a two-phase test:

1. Non-disruptive USB/INDI detection while the V3 Wide setup keeps running.
2. Optional short maintenance-window registration test, where indi-allsky is temporarily pointed at the ASI678MC long enough to create/update the camera row, then rolled back to the V3 Wide configuration.

Do not use this as a simultaneous dual-camera setup. The current runtime is one active capture camera per normal indi-allsky instance.

## Assumptions

- Pi 5 is already running indi-allsky with Camera Module V3 Wide through `libcamera_imx708`.
- Existing web UI and Modern Admin are reachable.
- ASI678MC should use the INDI/ZWO path, typically `indi_asi_ccd` or `indi_asi_single_ccd`.
- The default SQLite DB path is `/var/lib/indi-allsky/indi-allsky.sqlite`.
- The Flask config path is normally `/etc/indi-allsky/flask.json`.
- Existing services are normally named:
  - `indi-allsky.service`
  - `indiserver.service`
  - `gunicorn-indi-allsky.service`

## Safety Rules

- Do not run a full setup script over the working V3 Wide install just to test the ASI camera.
- Do not replace the existing `indiserver.service` during the non-disruptive detection phase.
- Use a separate temporary INDI port for detection, for example `7625`, so the existing service on `7624` is not touched.
- Back up the DB and config before any registration test.
- Treat DB registration as a maintenance-window operation because indi-allsky must briefly capture from the ASI camera to add/update the `camera` row.
- Keep rollback steps prepared before changing config.

## Phase 0: Baseline Snapshot

Before plugging in the ASI678MC, record the current healthy V3 Wide state.

### Record service state

```bash
systemctl --user status indi-allsky.service --no-pager
systemctl --user status indiserver.service --no-pager
systemctl --user status gunicorn-indi-allsky.service --no-pager
```

If the install uses system services instead of user services, use:

```bash
sudo systemctl status indi-allsky.service --no-pager
sudo systemctl status indiserver.service --no-pager
sudo systemctl status gunicorn-indi-allsky.service --no-pager
```

### Record current camera rows

```bash
sqlite3 /var/lib/indi-allsky/indi-allsky.sqlite \
  "select id, name, friendlyName, driver, connectDate, hidden from camera order by id;"
```

### Record current active camera state

```bash
sqlite3 /var/lib/indi-allsky/indi-allsky.sqlite \
  "select key, value from state where key in ('DB_CAMERA_ID');"
```

### Back up config and DB

```bash
mkdir -p ~/indi-allsky-asi-test-backup
cp -a /etc/indi-allsky/flask.json ~/indi-allsky-asi-test-backup/flask.json.$(date +%Y%m%d-%H%M%S)
sqlite3 /var/lib/indi-allsky/indi-allsky.sqlite \
  ".backup '$HOME/indi-allsky-asi-test-backup/indi-allsky.$(date +%Y%m%d-%H%M%S).sqlite'"
```

Also export or screenshot the classic System > Config page if that is Eric's normal way to manage config changes.

## Phase 1: Hardware Steps

1. Leave the Camera Module V3 Wide connected.
2. Connect the ASI678MC directly to a stable USB 3 port on the Pi 5, or to a powered USB 3 hub if power stability is uncertain.
3. Avoid long or thin USB cables for the first test.
4. If the camera has any accessory power requirement, satisfy that before testing.
5. Confirm the camera does not physically strain the Pi USB connector.

## Phase 2: Verify USB Detection

These checks should not affect the running V3 Wide capture.

```bash
lsusb
dmesg --follow
```

Expected result:

- `lsusb` should show a ZWO/ASI device.
- `dmesg` should show USB enumeration without repeated disconnect/reconnect loops.

Optional useful checks:

```bash
ls -l /dev/bus/usb
groups
```

If the device repeatedly disconnects:

- switch cable,
- use a powered hub,
- avoid testing through a keyboard/monitor hub,
- retest before touching indi-allsky config.

## Phase 3: Verify INDI/ZWO Driver Availability

Check whether the ZWO INDI driver is already installed:

```bash
command -v indiserver
command -v indi_asi_ccd
command -v indi_asi_single_ccd
```

Expected result:

- `indiserver` should exist.
- At least one ASI driver should exist, preferably `indi_asi_ccd`.

If neither ASI driver exists, stop here. The next step would require installing INDI/ZWO packages or rerunning setup with INDI support, which is outside a no-disruption experiment.

## Phase 4: Non-Disruptive INDI Detection on Temporary Port

Start a temporary INDI server manually on a different port from the production service.

Use port `7625` to avoid the normal `7624` service:

```bash
indiserver -p 7625 indi_asi_ccd
```

If `indi_asi_ccd` is not available but `indi_asi_single_ccd` is available:

```bash
indiserver -p 7625 indi_asi_single_ccd
```

Leave this terminal running during the detection test.

In another terminal, inspect the INDI server with one of the available local tools. Depending on installed packages, use whichever exists:

```bash
indiserver --help
indi_getprop -h localhost -p 7625
```

Expected result from `indi_getprop`:

- properties for an ASI camera device appear,
- the device name is visible, often something like `ZWO CCD ASI678MC`,
- no repeated driver crash appears in the `indiserver` terminal.

Stop the temporary INDI server with `Ctrl-C`.

This phase proves the Pi can see the ASI678MC without changing the existing V3 Wide config, services, or DB.

## Phase 5: Optional indi-allsky DB Registration Test

This is the only disruptive phase. Do it only if Eric wants to prove that indi-allsky itself can create/update the ASI camera row.

### Maintenance-window intent

The current capture service normally runs one active camera interface. To register ASI678MC in the indi-allsky DB, the capture pipeline must briefly run with:

- `CAMERA_INTERFACE = indi`
- `INDI_SERVER = localhost`
- `INDI_PORT = 7624` or another chosen production test port
- `INDI_CAMERA_NAME` set to the detected ASI device name if known
- indiserver using `indi_asi_ccd` or `indi_asi_single_ccd`

This temporarily replaces the active V3 Wide capture path. It is not intended to become the final state.

### Pre-change backup

Repeat the DB/config backup immediately before the test:

```bash
mkdir -p ~/indi-allsky-asi-test-backup
cp -a /etc/indi-allsky/flask.json ~/indi-allsky-asi-test-backup/flask.json.pre-asi.$(date +%Y%m%d-%H%M%S)
sqlite3 /var/lib/indi-allsky/indi-allsky.sqlite \
  ".backup '$HOME/indi-allsky-asi-test-backup/indi-allsky.pre-asi.$(date +%Y%m%d-%H%M%S).sqlite'"
```

### Record current latest config

```bash
sqlite3 /var/lib/indi-allsky/indi-allsky.sqlite \
  "select id, createDate, note, json_extract(data, '$.CAMERA_INTERFACE'), json_extract(data, '$.INDI_CAMERA_NAME') from config order by createDate desc limit 5;"
```

Save the current latest config id and note.

### Stop capture cleanly

Use the correct service scope for the install.

User service install:

```bash
systemctl --user stop indi-allsky.service
```

System service install:

```bash
sudo systemctl stop indi-allsky.service
```

Do not stop the web UI unless needed.

### Switch only the camera test config

Preferred safest UI path:

1. Open classic admin System > Config.
2. Save/export or screenshot the current camera-related settings.
3. Change only the camera interface fields needed for ASI:
   - camera interface: `indi`
   - INDI server: `localhost`
   - INDI port: normal configured test port
   - INDI camera name: detected ASI device name, if known
4. Open System > INDI Server only if the driver must be changed.
5. Set camera server/driver to `indi_asi_ccd` or `indi_asi_single_ccd`.
6. Restart indiserver only if the page requires it.

Avoid changing image folder, upload settings, storage settings, or other unrelated options.

### Start capture for registration

```bash
systemctl --user start indi-allsky.service
systemctl --user status indi-allsky.service --no-pager
```

Or, for system service install:

```bash
sudo systemctl start indi-allsky.service
sudo systemctl status indi-allsky.service --no-pager
```

Watch logs briefly:

```bash
journalctl --user -u indi-allsky.service -f
```

Or:

```bash
sudo journalctl -u indi-allsky.service -f
```

Expected result:

- capture connects to the ASI camera,
- no repeated startup crash,
- logs mention the ASI camera name or INDI CCD connection,
- a new or updated `camera` row appears.

Let it run only long enough to connect and, if desired, capture one frame. Then proceed to verification and rollback.

## Verify Camera Registration in the DB

Query the `camera` table:

```bash
sqlite3 /var/lib/indi-allsky/indi-allsky.sqlite \
  "select id, name, friendlyName, driver, width, height, bits, connectDate, hidden from camera order by connectDate desc, id desc;"
```

Expected result:

- ASI678MC appears as a camera row.
- `connectDate` is updated.
- `driver` or `name` indicates ZWO/ASI/INDI.
- width/height may be populated after the driver reports metadata.

Check current DB camera id:

```bash
sqlite3 /var/lib/indi-allsky/indi-allsky.sqlite \
  "select key, value from state where key = 'DB_CAMERA_ID';"
```

During the ASI test, `DB_CAMERA_ID` may point to the ASI row. After rollback to V3 Wide, it should return to the V3 row once capture reconnects.

If one test frame was captured, verify image linkage:

```bash
sqlite3 /var/lib/indi-allsky/indi-allsky.sqlite \
  "select i.id, i.camera_id, c.name, i.createDate, i.filename from image i join camera c on c.id = i.camera_id order by i.createDate desc limit 10;"
```

## Verify Appearance in Modern Admin Cameras

1. Open `/indi-allsky/modern-admin/cameras`.
2. Confirm the ASI678MC appears in the camera inventory.
3. Confirm the V3 Wide camera row is still present.
4. Confirm the ASI card shows a sensible friendly name or technical fallback.
5. Confirm driver/interface metadata identifies the ASI/INDI path if available.
6. Confirm active status is not misleading after rollback:
   - during ASI test, ASI may appear active,
   - after rollback, V3 Wide should be the active/latest capture camera again,
   - ASI may remain as available/offline/historical.

If the ASI row appears in classic sidebar camera selector but not Modern Admin Cameras, that is a Modern Admin display bug, not a capture registration failure.

## Rollback Procedure

Rollback should restore the V3 Wide path and keep the ASI camera row as historical inventory unless the DB backup is restored.

### Stop capture

```bash
systemctl --user stop indi-allsky.service
```

Or:

```bash
sudo systemctl stop indi-allsky.service
```

### Restore V3 Wide config through UI

Preferred:

1. Open classic admin System > Config.
2. Restore the recorded V3 Wide settings:
   - camera interface: `libcamera_imx708`
   - libcamera camera id: the previous value, usually `0`
   - INDI fields as they were before, if relevant
3. Save config.
4. If indiserver was changed for ASI and V3 Wide does not need it, restore the previous indiserver settings or leave it stopped if that was the previous state.

### Start capture

```bash
systemctl --user start indi-allsky.service
systemctl --user status indi-allsky.service --no-pager
```

Or:

```bash
sudo systemctl start indi-allsky.service
sudo systemctl status indi-allsky.service --no-pager
```

### Verify V3 Wide is active again

```bash
sqlite3 /var/lib/indi-allsky/indi-allsky.sqlite \
  "select id, name, friendlyName, driver, connectDate from camera order by connectDate desc, id desc limit 5;"

sqlite3 /var/lib/indi-allsky/indi-allsky.sqlite \
  "select key, value from state where key = 'DB_CAMERA_ID';"
```

Open:

- `/indi-allsky/modern-admin`
- `/indi-allsky/modern-admin/cameras`
- classic Latest page

Expected result:

- latest image updates from V3 Wide again,
- Modern Admin dashboard loads,
- Modern Admin Cameras still lists both cameras,
- V3 Wide is active/latest after reconnect.

### Emergency DB/config rollback

Use only if config rollback through UI fails or the DB is left in a bad state.

1. Stop services:

```bash
systemctl --user stop indi-allsky.service
systemctl --user stop gunicorn-indi-allsky.service
```

Or system scope equivalents.

2. Restore the saved config:

```bash
cp -a ~/indi-allsky-asi-test-backup/flask.json.pre-asi.YYYYMMDD-HHMMSS /etc/indi-allsky/flask.json
```

3. Restore the DB backup only if necessary:

```bash
cp -a ~/indi-allsky-asi-test-backup/indi-allsky.pre-asi.YYYYMMDD-HHMMSS.sqlite /var/lib/indi-allsky/indi-allsky.sqlite
```

4. Start services again:

```bash
systemctl --user start gunicorn-indi-allsky.service
systemctl --user start indi-allsky.service
```

Or system scope equivalents.

## Success Criteria

Minimum safe success:

- ASI678MC appears in `lsusb`.
- Temporary `indiserver -p 7625 indi_asi_ccd` can see the camera.
- Existing V3 Wide capture remains healthy after unplugging the ASI camera.

Full registration success:

- ASI678MC appears in the indi-allsky `camera` table.
- The row has a recent `connectDate`.
- Modern Admin Cameras displays the ASI camera.
- Rollback restores V3 Wide as the active/latest capture camera.

## Stop Conditions

Stop the experiment and roll back if:

- USB disconnects repeat in `dmesg`.
- `indi_asi_ccd` is missing and package installation would be required.
- temporary indiserver crashes repeatedly.
- indi-allsky capture fails to start after the ASI config change.
- the web UI becomes unavailable.
- latest V3 Wide capture does not resume after rollback.

## Recommended Path for Eric

Do Phase 1 through Phase 4 first. That proves the Pi, USB path, and INDI/ZWO driver stack can see the ASI678MC without touching the V3 Wide setup.

Only do Phase 5 if Eric specifically wants the ASI678MC to appear in the indi-allsky DB and Modern Admin Cameras. Keep that test short, backed up, and reversible.

Do not attempt simultaneous V3 Wide plus ASI678MC capture from the current normal install yet. Treat that as a future multi-instance or capture-profile project.
