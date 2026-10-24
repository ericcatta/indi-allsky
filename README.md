# indi-allsky Hybrid

A Linux all-sky camera system for continuous sky imaging, scientific archives,
timelapses and observatory monitoring, with **Hybrid as its only web interface**.

This repository is [Eric Cattaneo's Hybrid fork](https://github.com/ericcatta/indi-allsky)
of [Aaron Morris's indi-allsky](https://github.com/aaronwmorris/indi-allsky).
It retains the upstream camera drivers, processing workers and integration
contracts while providing a different interface and additional archive,
multicamera and storage workflows. The Classic frontend has been removed.

Open **`https://<camera-host>/indi-allsky/modern-admin/now`** after installation.
Hybrid requires login; use the account you create during setup. There are no
shared default production credentials.

![An all-sky exposure of SpaceX Cargo Dragon over Georgia](content/20210930_224951.jpg)

*SpaceX Cargo Dragon headed toward splashdown off the coast of Florida.*

## Contents

- [Project status](#project-status)
- [What the system does](#what-the-system-does)
- [Requirements and supported systems](#requirements-and-supported-systems)
- [Install on Linux](#install-on-linux)
- [First login and commissioning](#first-login-and-commissioning)
- [Docker and other installation layouts](#docker-and-other-installation-layouts)
- [Configuration and data locations](#configuration-and-data-locations)
- [Services and logs](#services-and-logs)
- [Storage, backup and recovery](#storage-backup-and-recovery)
- [Update an existing installation](#update-an-existing-installation)
- [Camera and processing reference](#camera-and-processing-reference)
- [Optional hardware and integrations](#optional-hardware-and-integrations)
- [Security and remote access](#security-and-remote-access)
- [Troubleshooting](#troubleshooting)
- [Development and verification](#development-and-verification)
- [Documentation map](#documentation-map)
- [Dependencies and architecture](#dependencies-and-architecture)
- [Contributing, support and license](#contributing-support-and-license)

## Project status

Hybrid is deployed on the project's Raspberry Pi installation. This does **not**
mean that every supported camera, integration, operating system or clean-install
combination has been tested with this fork.

As recorded on **24 October 2026**, whole-product runtime acceptance remains open:
intermittent IMX708 acquisition timeouts and storage/SQLite contention have required
repairs and bounded verification. Recent recovery checks do not establish that
all intermittent failures are resolved. The current work does not include another
24-hour observation. See [remaining acceptance work](docs/HYBRID_ACCEPTANCE_REMAINING.md)
and [deployment evidence and rollback](HYBRID_DEPLOYMENT.md).

The existing line detector identifies candidate trails; it does not reliably
classify meteors, aircraft and satellites. Separate Event Detector/AI development
is not part of the standard installation described here.

This README describes repository behavior and defaults. Machine-specific paths,
configuration revisions, retention policies and historical test counts in release
reports are examples from that installation, not defaults for a new system.

## What the system does

| Area | Capabilities |
| --- | --- |
| Acquisition | INDI CCD/CMOS cameras, Raspberry Pi libcamera interfaces, selected network/MQTT cameras, day/night and moon modes, exposure and gain control |
| Processing | Dark calibration, debayering, stretching, stacking, overlays, star counting, line detection, cropping, scaling and panorama conversion |
| Archive | Processed images, optional FITS/RAW sources, metadata, thumbnails and source-aware previews/downloads; source-based generation when the saved data and context support it |
| Outputs | Timelapses, mini timelapses, keograms, long-term/realtime keograms, star trails, star-trail videos and panoramas |
| Hybrid operations | Camera/profile selection, settings, task queue, notifications, user management, logs, storage protection and scientific-source workflows |
| Observatory | Sky brightness estimates, charts, sensors, sun/moon context, satellite information, weather and optional environmental controls |
| Integrations | Remote INDI, SyncAPI, file transfer, object storage, MQTT/Home Assistant, YouTube, GPS and optional GPIO devices |

The main navigation is organized around **Now**, **Highlights**, **Library** and
**Observatory**. Use Settings for capture, processing, storage and operational
configuration. Camera/profile context matters: verify it before saving changes.
Availability depends on configured devices, permissions and data actually captured.

## Requirements and supported systems

### Hardware and operating environment

- A Linux host with systemd, a normal login user with `sudo` access, and a supported
  camera. The native installer is not a macOS or Windows installer.
- Prefer **64-bit ARM (`aarch64`) or x86-64**, multicore CPU and **at least 2 GB RAM**.
  More memory is needed for high-resolution RAW processing, stacking, multiple
  cameras and video encoding. A 1 GB device is constrained; 512 MB is unsuitable
  for a complete capture-and-video workload.
- Start with **64 GB or more of reliable storage**, then size it for your actual
  formats, cadence and retention. This is a capacity starting point, not a promise
  of a fixed number of days. Every-frame FITS can use much more space than JPEG.
- Reliable power, appropriate USB/CSI connections, cooling and a weatherproof
  enclosure for outdoor use. Confirm the camera works in the operating system
  before commissioning unattended capture.
- Internet access during installation for OS packages, Python dependencies and
  INDI sources. Uploads, weather/orbital downloads and other network integrations
  also need connectivity; local acquisition does not require those integrations.
- Correct system time, timezone and geographic coordinates.

For planning, archive growth is roughly
`average bytes per saved frame × frames per day × retained days × cameras`, plus
videos, derived products, calibration files, databases and backups. Measure actual
files and leave free space for temporary encoding and database work.

### Distribution selection

The following table reflects branches in [setup.sh](setup.sh), not a certification
of every combination. Use a current 64-bit system for a new installation.

| Distribution | Installer path / qualification |
| --- | --- |
| Raspberry Pi OS / Debian 13 (Trixie) | Preferred baseline in this repository; build INDI first if absent |
| Raspberry Pi OS / Debian 12 (Bookworm) | Installer branch present; build INDI first if absent |
| Raspberry Pi OS / Debian 11 (Bullseye) | Older installer branch; build INDI first if absent |
| Ubuntu 24.04 (Noble) | Preferred Ubuntu baseline; INDI packages via `ppa:mutlaqja/ppa` on supported 64-bit architectures |
| Ubuntu 22.04 (Jammy) | Installer branch present; INDI PPA on supported 64-bit architectures |
| Linux Mint 22 / 21 | Mapped to Ubuntu 24.04 / 22.04 |
| LMDE 6 | Mapped to Debian 12; build INDI first if absent |
| Debian/Raspberry Pi OS 10, Ubuntu 20.04 | Legacy branches remain; avoid for new installations |
| Stellarmate / Astroberry 3 | Special-case handling exists; preserve the distribution's INDI installation and inspect port choices |
| Astroberry Server 2 | Explicitly unsupported by setup |
| Other distributions / Armbian | Recognition depends on `/etc/os-release`; inspect the installer and relevant upstream guidance before proceeding |

32-bit Python dependencies have known build/availability limitations, including
the `dask-image`/`pyarrow` chain on ARM. Do not infer that a 32-bit board is a
supported fresh-install target simply because an old installer branch exists.
Original Raspberry Pi/Zero boards are especially constrained. Raspberry Pi 4/5
with a 64-bit OS is a more suitable starting point for a full system.

### Memory for video generation

These inherited estimates are planning guidance, not measured guarantees for the
current multicamera workload. They exclude some concurrent capture/processing work.

| Output size | Suggested host RAM | Approximate FFmpeg process RAM |
| --- | --- | --- |
| 1280 × 960 | 2 GB | 0.4 GB |
| 1920 × 1080 | 2 GB | 0.6 GB |
| 3840 × 2160 | 4 GB | 1.7 GB |
| 4056 × 3040 | 4 GB or more | 2.5 GB |
| 6224 × 4168 | 8 GB | 5 GB |
| 9152 × 6944 | 16 GB | 12 GB |

Reduce output resolution and concurrent work if memory or I/O is constrained.
Swap can help avoid allocation failures but does not replace adequate RAM or
storage throughput.

## Install on Linux

These commands are for a **new native installation**. For an existing system,
follow [the update procedure](#update-an-existing-installation). Run commands in
an interactive terminal as the user who will own the installation. Do not run
`setup.sh` or `build_indi.sh` with `sudo`, from a root shell, or with an activated
Python virtual environment; the scripts request elevated privileges themselves.

### 1. Prepare and clone this repository

Install the OS, configure networking/SSH and time synchronization, and log in as
the intended service user. On the Debian/Ubuntu family:

```sh
sudo apt update
sudo apt install -y git ca-certificates whiptail
cd "$HOME"
git clone https://github.com/ericcatta/indi-allsky.git
cd indi-allsky
git status --short --branch
```

Keep this checkout at its final location: generated service definitions refer to
it. Review OS updates and reboot requirements before running installation.
The installer may offer OS package upgrades as well as application setup.

Setup requires at least 1 GB free on both `/` and `/var` and checks temporary
space. An INDI source build separately requires at least 5 GB free on `/home`
and `/usr/local`; allow additional space for downloads and build artifacts.
Check with `df -h / /var /home /usr/local /tmp`.

### 2. Prepare INDI and the camera interface

**Debian, Raspberry Pi OS and LMDE:** the current setup script requires an existing
`indiserver` in `/usr/bin` or `/usr/local/bin`, including when selecting a direct
libcamera interface. If INDI is absent, run:

```sh
./misc/build_indi.sh
```

The build script prompts for choices, installs build dependencies and compiles
INDI and selected third-party drivers. Its automatic versions are defined in
[the script](misc/build_indi.sh); it installs under `/usr/local` and keeps sources
under `$HOME/Projects`. Do not run it blindly over a package-managed INDI install:
it detects conflicting packages and may refuse to proceed. Review which driver
your camera needs and follow its reported remediation.

**Ubuntu / Mint on supported 64-bit architectures:** `setup.sh` can install INDI
from the configured PPA. An existing custom installation in `/usr/local/bin` is
detected. `INDIALLSKY_INSTALL_INDI=false ./setup.sh` suppresses package installation
where the installer supports that choice; it does not provide a missing INDI runtime.

**CSI/libcamera cameras:** confirm that the OS camera stack detects the sensor.
With current Raspberry Pi camera applications, a useful check is:

```sh
rpicam-still --list-cameras
```

Older systems may use `libcamera-still --list-cameras`. Run camera probes while
capture is stopped. Select the sensor-specific interface during setup, such as
`libcamera_imx477` or `libcamera_imx708`. Availability depends on OS, camera,
kernel and camera-stack versions; the old Bullseye-only restriction does not
describe this fork. See the [upstream libcamera guide](https://github.com/aaronwmorris/indi-allsky/wiki/libcamera-enablement)
and [optional build script](misc/build_libcamera.sh) when a source build is needed.

**USB astronomy cameras:** select `indi` and the correct installed CCD driver
(e.g. `indi_asi_ccd` for supported ZWO cameras). Remote INDI and multiple cameras
need explicit host/port/device configuration; do not assume that connecting a
second camera completes its configuration.

### 3. Run setup

From the repository root:

```sh
./setup.sh
```

Read each prompt. Setup installs OS/Python dependencies, creates
`virtualenv/indi-allsky`, initializes or migrates the database, configures logging,
the web server and user services, and creates the first administrator account.
It also configures permissions and user lingering for unattended startup.

Decisions include the camera interface and driver, local INDI server, web ports,
timezone, authentication, administrator credentials, automatic startup and optional
hardware/system features. Optional watchdog, LED, desktop and system optimization
changes affect the host; choose them deliberately. No email is sent just by
entering an account email address.

The inherited “authenticate all views” prompt is broader than Hybrid navigation:
**Hybrid itself always requires login**, regardless of that setting. Do not use
the old prompt wording as evidence of anonymous Hybrid access.

The defaults are Apache, HTTP **80**, HTTPS **443** and INDI **7624**. Special
appliance setups may select other ports; use the URL printed at completion.
Environment overrides are documented in the installer header, including
`INDIALLSKY_HTTP_PORT`, `INDIALLSKY_HTTPS_PORT`, `INDIALLSKY_TIMEZONE` and
`INDIALLSKY_CAMERA_INTERFACE`. They do not by themselves make every prompt
noninteractive. Avoid putting passwords into shell history or checked-in files.

If setup reports that capture is running, stop it first as shown below. If it
reports a missing user D-Bus session, follow its reboot/relogin instructions and
rerun as the deployment user. Do not work around this by running setup as root.

### 4. Open the interface and start capture

Visit the hostname or IP printed by setup, adding the Hybrid route:

```text
https://<camera-host>/indi-allsky/modern-admin/now
```

If HTTPS is on a custom port, include `:<port>`. The default certificate may be
self-signed: verify that you reached your own camera host and configure a trusted
certificate for ongoing remote access. If `.local` discovery fails, use its LAN IP.

Log in with the administrator account created during setup. If you declined
“start now”, start capture when configuration is ready:

```sh
systemctl --user start indi-allsky.service
systemctl --user status indi-allsky.service --no-pager
```

## First login and commissioning

Before leaving the system unattended:

1. Confirm the selected camera and profile, geographic location, timezone, image
   orientation and day/night thresholds. Verify camera/INDI connection settings.
2. Set exposure limits, gain and cadence appropriate to the camera. Check a real
   frame and its timestamp; a running service alone does not prove acquisition.
3. Focus the camera, then **leave Focus mode** when done. Focus mode is a special
   acquisition mode and does not save ordinary archive images.
4. Choose processed-image and scientific-source formats deliberately. FITS/RAW
   downloads only exist for exposures whose sources were saved. A processed JPEG
   is not an original scientific source.
5. Set archive location, retention and Storage Protection thresholds before
   enabling large-volume capture. Check available disk space and permissions.
6. Verify Library browsing and a small generated output, including actual playback
   or download. For multiple cameras, verify fresh, decoded frames for **each**.
7. Capture appropriate dark calibration frames with the lens covered, then uncover
   it and confirm normal capture resumes. Do not run dark acquisition alongside
   a second process competing for the same camera.
8. Check startup behavior after a planned reboot and review logs. Verify timer/socket
   activation and fresh frames without relying on an interactive SSH login.

See [capture cadence and exposure policy](HYBRID_CAPTURE_CADENCE.md),
[dark calibration guidance](https://github.com/aaronwmorris/indi-allsky/wiki/Dark-Calibration-Frames)
and [multicamera runtime notes](docs/multi-camera-runtime-plan.md). The latter
includes implementation history; inspect current configuration before applying
machine-specific examples.

## Docker and other installation layouts

Native Linux/systemd is the primary path documented above. Container assets and
split-host installers are also present; their existence is not clean-install
acceptance of every Hybrid operation. In particular, host service/GPIO/device
controls need a suitable deployment environment.

### Docker Compose

Use a Linux Docker host with the Compose plugin and camera-device access. The
manifest uses `additional_contexts`, so the installed Compose/BuildKit must support
that feature. Read [the compose manifest](docker/docker-compose.yaml),
[environment template](docker/env_template) and
[upstream Docker guide](https://github.com/aaronwmorris/indi-allsky/wiki/Docker).

From the cloned repository:

```sh
cd docker
./setup_env.sh
# Edit .env: timezone, camera driver/vendor and other deployment settings.
# Review docker-compose.yaml: exposed ports, devices and persistent volumes.
docker compose config --quiet
docker compose build
docker compose up -d
docker compose ps
docker compose logs --tail=100 capture.indi.allsky gunicorn.indi.allsky
```

`setup_env.sh` uses `apt`/`sudo` for its prerequisites and creates `.env` and TLS
material. Keep those files private. The template initially selects the **CCD
simulator** and `America/New_York`; change these for your installation.

The manifest includes INDI, capture, Gunicorn, web, MariaDB and MQTT containers.
Default host ports are HTTP **8080**, HTTPS **8443**, INDI **17624**, MariaDB
**13306**, MQTT TLS **18883** and MQTT WebSocket **18081**. Review bindings before
starting; database, broker and INDI do not need to be publicly reachable.
Open `https://<docker-host>:8443/indi-allsky/modern-admin/now`.

Images, database, migrations and broker state use named volumes. Back them up
before rebuilding/upgrading. `docker compose down` stops the stack;
**`docker compose down -v` also removes named volumes and is not an update step**.
For CSI cameras, review the libcamera device/privilege comments in the manifest.
No container deployment is performed by following the native service commands.

### Remote camera or web-only server

- [misc/indiserver_only_setup.sh](misc/indiserver_only_setup.sh) provisions an
  INDI-only host.
- [misc/web_only_setup.sh](misc/web_only_setup.sh) provisions a web-only receiver.
- SyncAPI can send images and outputs to another instance; configure authentication,
  receiving storage and matching API settings. A web-only receiver does not
  control the remote physical camera merely because it displays its images.

Read each script's options and the
[upstream getting-started guide](https://github.com/aaronwmorris/indi-allsky/wiki/Getting-Started)
before choosing a split deployment. Upstream screenshots/navigation may refer to
Classic; use Hybrid's current pages in this fork.

## Configuration and data locations

| Item | Native-install default |
| --- | --- |
| Source checkout | Wherever you cloned the repository, commonly `$HOME/indi-allsky` |
| Python environment | `<checkout>/virtualenv/indi-allsky` |
| Flask settings and keys | `/etc/indi-allsky/flask.json` |
| Service environment | `/etc/indi-allsky/indi-allsky.env` |
| Runtime database | `/var/lib/indi-allsky/indi-allsky.sqlite` |
| Database migrations | `/var/lib/indi-allsky/migrations` |
| Database backups | `/var/lib/indi-allsky/backup` |
| Archive | `/var/www/html/allsky/images`, unless `IMAGE_FOLDER` is changed |
| User systemd units | `~/.config/systemd/user/` |
| Capture / web logs | `/var/log/indi-allsky/indi-allsky.log` / `webapp-indi-allsky.log` |

Application configuration is versioned in the database. Most changes should be
made through Hybrid Settings in the correct camera/profile context. `flask.json`
contains application/bootstrap settings and secrets; it is not a replacement for
the database configuration. A similarly named SQLite file inside a checkout is
not necessarily the runtime database.

For CLI inspection and a private configuration export, from the checkout:

```sh
./virtualenv/indi-allsky/bin/python config.py list
umask 077
./virtualenv/indi-allsky/bin/python config.py dumpfile --outfile "$HOME/indi-allsky-config.json"
```

An export may contain credentials. Store it outside the checkout and do not attach
it unredacted to an issue. `config.py load -c <file>` and `revert --id <id>` change
configuration; review their effects and required capture reload/restart first.
Neither restores archived media or the whole database.

For account recovery, the installed service user can use an interactive password
prompt without passing the password on the command line:

```sh
./virtualenv/indi-allsky/bin/python misc/usertool.py list
./virtualenv/indi-allsky/bin/python misc/usertool.py resetpass --username '<your-login>'
```

## Services and logs

Run application service commands **as the installation user, without `sudo`**.
Apache/NGINX are system services. Do not start a second foreground capture process
while `indi-allsky.service` owns the camera.

```sh
# Inspect acquisition, web activation and boot behavior.
systemctl --user status indi-allsky.service gunicorn-indi-allsky.socket --no-pager
systemctl --user list-timers --all
loginctl show-user "$USER" -p Linger

# Stop or restart acquisition during planned maintenance.
systemctl --user stop indi-allsky.service
systemctl --user start indi-allsky.service

# Reload web workers after a compatible web-only code change.
systemctl --user reload gunicorn-indi-allsky.service

# Inspect recent capture and web service messages.
journalctl --user -u indi-allsky.service -u gunicorn-indi-allsky.service -n 100 --no-pager
tail -n 100 /var/log/indi-allsky/indi-allsky.log
```

Capture autostart is normally controlled by `indi-allsky.timer` (two minutes after
boot); INDI has its own timer/service; Gunicorn is socket-activated. Therefore a
service reporting `disabled` does not by itself mean startup is broken. Setup
uses user lingering so the user manager can run without an SSH login.

```sh
systemctl --user is-enabled indi-allsky.timer gunicorn-indi-allsky.socket
systemctl --user status indiserver.service --no-pager
systemctl status apache2 --no-pager
```

Use `nginx` in place of `apache2` when configured. Some distributions manage INDI
as a system service, and custom multicamera installations can have additional
unit names. Inspect the actual units before restarting INDI. Reloading web workers
does not activate changes in the capture coordinator or its forked workers; those
require a controlled capture restart.

CLI logs go to standard error; capture uses syslog local6 and the web application
uses local7, with the rotated files listed above. Avoid sharing logs without reviewing hostnames,
locations, account names and integration credentials.

## Storage, backup and recovery

### Archive and external disks

Use Storage Protection to review archive capacity and retention. Preserve original
scientific sources, thumbnails and shared rendering assets together; source-backed
previews may require more than the FITS file alone. Retention and generation/upload
protections are application policies, not reasons to delete archive files manually.

For an external archive disk: create a persistent OS mount, stop archive writers,
and migrate the archive preserving its structure. Keeping the same application
path avoids breaking historical absolute filenames in the database. If changing
paths, inspect and migrate those records as well; changing `IMAGE_FOLDER` alone
does not rewrite them. Update `IMAGE_FOLDER` and any existing `ARCHIVE_VOLUME.ROOT`
and UUID protection together, rerun setup to update web paths, then restart and
verify files/previews for every camera before removing the old copy.
The filesystem-UUID guard can require the configured block device before archive
access and cleanup. It does not mount or format a disk and cannot pin a network
share without a block filesystem UUID. Do not disable the guard merely to hide a
missing disk: that can redirect writes to the underlying root filesystem.
See [storage release runbook](HYBRID_STORAGE_RELEASE_RUNBOOK.md) and
[deployment notes](HYBRID_DEPLOYMENT.md).

### What a usable backup includes

Back up **all** of the following, preferably to another physical device:

- A consistent database snapshot, including image metadata, configuration and users.
- `/etc/indi-allsky/`, especially encryption keys and Flask settings. Without the
  original password-encryption key, stored integration secrets may be unusable.
- The archive and calibration files, plus any separately configured source/export
  directories. A database backup does not contain the image/video bytes.
- The source commit, local changes, custom service definitions and relevant web,
  storage-mount and device configuration.

The application has a database-backup task, and setup creates database backups
before migrations. These are not a complete off-device disaster-recovery plan.
Check task completion, free space and the resulting backup; do not treat a queued
request as a completed copy. Large backups on a busy SD card can stall acquisition.

### Example: consistent SQLite and configuration backup

This example uses the native defaults and a **planned maintenance window**. Replace
the backup directory with an existing mounted backup filesystem having enough
space. First wait for active generation/upload jobs to finish, record active
services and timers, and ensure no other processes write to the database.

```sh
cd "$HOME/indi-allsky"
backup_dir="/mnt/backup/indi-allsky-$(date +%Y%m%d-%H%M%S)"
umask 077
mkdir -p "$backup_dir"
git rev-parse HEAD > "$backup_dir/source-commit.txt"
git diff HEAD > "$backup_dir/local-changes.patch"

# Temporarily prevent timer/socket reactivation while making the checkpoint.
systemctl --user stop indi-allsky.timer indi-allsky.service
systemctl --user stop gunicorn-indi-allsky.socket gunicorn-indi-allsky.service

sqlite3 /var/lib/indi-allsky/indi-allsky.sqlite ".backup '$backup_dir/indi-allsky.sqlite'"
sqlite3 "$backup_dir/indi-allsky.sqlite" 'PRAGMA integrity_check;'
sudo tar -C / -czf "$backup_dir/etc-indi-allsky.tar.gz" etc/indi-allsky
sudo chmod 600 "$backup_dir/etc-indi-allsky.tar.gz"
```

The integrity result must be `ok`. Also copy required custom units, untracked
configuration and the archive during this same window if you need one coherent
recovery point; `git diff` does not include untracked files. Record what was and
was not copied. Protect the backup permissions and test reading it.

Restart only the units you recorded as active/enabled for normal operation, then
verify fresh images and login. For a normal capture installation this includes:

```sh
systemctl --user start gunicorn-indi-allsky.socket
systemctl --user start indi-allsky.timer indi-allsky.service
```

If a step fails, do not continue an update assuming the backup exists. Resolve the
failure and restore the intended service state. For MariaDB/container deployments,
use a database-native consistent dump or a coordinated volume snapshot instead
of copying these SQLite paths.

### Recovery and rollback

For a full recovery, stop all database writers **and web socket activation**,
preserve the current damaged state for diagnosis, restore a verified database
with its matching keys/media and compatible source revision, restore ownership
and permissions, and verify database integrity before starting services. SQLite
WAL/SHM sidecars belong to their original database: never combine stale sidecars
with a different restored snapshot. Keep them with the old database while all
writers are stopped. Validate migrations against a copy before upgrading a
restored installation.

A **code-only rollback usually must not restore an old database**: that would lose
new configuration/media records. Follow the release-specific rollback in
[HYBRID_DEPLOYMENT.md](HYBRID_DEPLOYMENT.md), preserving readers for any source-backed
archive formats already in use. Restoring an older reader that cannot handle new
FITS-backed records is not a safe rollback.

## Update an existing installation

Use this fork's `origin`; do not replace it with upstream as part of an ordinary
update. Keep local changes and private files intact. Review the incoming diff and
release notes, prepare a suitable backup, and schedule capture interruption before
running an installer or changing runtime workers.

From the existing checkout, inspect first:

```sh
git remote -v
git status --short --branch
git rev-parse HEAD
git fetch origin
git log --oneline HEAD..origin/main
git diff --stat HEAD..origin/main
```

If local tracked changes or divergent commits exist, reconcile them before
proceeding. Do not use `git reset --hard` or `git clean` as an upgrade shortcut.
For a clean checkout on `main`, after completing backups:

```sh
systemctl --user stop indi-allsky.timer indi-allsky.service
systemctl --user stop gunicorn-indi-allsky.socket gunicorn-indi-allsky.service
git pull --ff-only origin main
./setup.sh
```

Run setup outside a virtual environment. It can change dependencies, services and
schema; read its prompts and restore the intended autostart/start state afterward.
If setup fails, inspect the failure and schema/dependency state before restoring
services; do not blindly restart a partially updated application.
A documentation-only update does not need setup or a service restart. A tested
web-only update may need only a web reload; capture/worker changes require their
own restart. Use the actual diff to decide, not the age of the last installation.

After activation, verify the installed commit and file state, login, new decoded
frames for every camera, logs, task completion and affected outputs. A successful
`git pull` does not prove that Python workers loaded the new code.

[misc/unattended_upgrade.sh](misc/unattended_upgrade.sh) and
`upgrade-indi-allsky.service` exist for an explicitly prepared automated workflow.
Read the script before enabling it; automatic updates are not a substitute for
backups and release validation.

## Camera and processing reference

INDI support depends on the camera's driver, SDK and operating system. The source
builder records its selected versions; camera-specific minimum versions can differ.
See [upstream camera SDK notes](https://github.com/aaronwmorris/indi-allsky/wiki/indilib-3rdparty-SDK-versions)
and the driver documentation rather than assuming every INDI camera works unchanged.

The table below retains **upstream-reported hardware experience**, not a claim that
each model has been retested on Hybrid. Ratings are historical upstream labels.

| Vendor   | Model               | Rating | Notes |
| -------- | ------------------- | ------ | ----- |
| ZWO      | ASI120MC-S          | B      | https://github.com/aaronwmorris/indi-allsky/wiki/ASI120MC-S-Camera-Issues |
| ZWO      | ASI678MC            | A      |       |
| ZWO      | ASI676MC            | A      | This camera was designed for all sky systems |
| ZWO      | ASI585MC            | A      |       |
| ZWO      | ASI178MC/MM         | A      |       |
| ZWO      | ASI290MC/MM         | A      |       |
| ZWO      | ASI385MC            | A      |       |
| ZWO      | ASI174MM            | A      |       |
| ZWO      | ASI533MC/MM         | A      |       |
| ZWO      | ASI183MC/MM         | A      |       |
| QHY      | QHY5III485C         | A      | Needs newer [fxload](https://github.com/aaronwmorris/indi-allsky/wiki/Build-fxload-for-USB3-support) utility for firmware |
| QHY      | QHY5LII-M           | A      |       |
| Svbony   | SV305               | B      | ~20% of frames require double the configured exposure time to complete. Likely a firmware bug. |
| Altair   | Hypercam 178C       | A      | Needs [config](https://github.com/aaronwmorris/indi-allsky/wiki/INDI-custom-config#altair-hypercam-178c) for full resolution |
| Altair   | GPCAM3 290C         | A      | Needs [config](https://github.com/aaronwmorris/indi-allsky/wiki/INDI-custom-config#altair-290c-resolution) for full resolution |
| Altair   | GPCAM3 224C         | A      | Needs [config](https://github.com/aaronwmorris/indi-allsky/wiki/INDI-custom-config#altair-224c-resolution) for full resolution |
| Altair   | GPCAM2 290M         | A      |       |
| Touptek  | G3CMOS06300KPA (IMX178) | A  |       |
| Touptek  | G-1200-KMB          | A      |       |
| Player One        | Mars-C                        | A | |
| Player One        | Neptune-C                     | A | |
| Starlight Xpress  | Superstar                     | A | Fixed gain.  Using stretching and/or contrast enhance |
| Datyson           | T7C                           | A | Using indi_asi_ccd driver<br>Recommend ASI120MC Linux compatibility firmware |
| Raspberry Pi      | HQ Camera imx477 (libcamera)  | A | |
| Raspberry Pi      | CM3 imx708 (libcamera)        | A | Minimum 1GB of memory is needed to process RAW images with dark calibration frames |
| Raspberry Pi      | HQ Camera (indi_pylibcamera)  | A | https://github.com/scriptorron/indi_pylibcamera |
| Waveshare         | imx378 (libcamera)            | A | |
| ArduCam           | imx462 (libcamera)            | A | |
| ArduCam           | 64MP HawkEye                  | A | Recommend at least 4GB of RAM for full resolution 9152x6944.  [Options](https://github.com/aaronwmorris/indi-allsky/wiki/libcamera-enablement) available to reduce image size. |
| Canon    | 550D (Rebel T2i)    | A      | Camera resolution and pixel size have to be manually defined in config |
| Canon    | 1300D (Rebel T6)    | A      | Camera resolution and pixel size have to be manually defined in config |
| IP Cameras | indi_webcam_ccd   | C      | Needs [config](https://github.com/aaronwmorris/indi-allsky/wiki/INDI-custom-config) for operation |
| Webcams  | indi_v4l2_ccd       | B      | |
| Webcams  | indi_webcam_ccd     | D      | No gain controls.  Little control over image quality. |
| indi     | indi_simulator_ccd  |        | CCD Simulator.  Install GSC to generate sample images. |

Raspberry Pi interfaces also include additional sensor-specific implementations;
inspect [camera modules](indi_allsky/camera) and the setup selector for the current
list. A model appearing in a selector is not evidence of an end-to-end acceptance run.

### Calibration, stacking and sky products

- **Dark frames:** remove sensor thermal/hot-pixel signal using calibration frames
  appropriate to the camera and exposure conditions.
- **Stretching:** standard-deviation and midtone-transfer processing provide display
  contrast for high-bit-depth sources. Preserve original sources when needed.
- **Stacking:** maximum emphasizes stars/trails, average combines signal, minimum
  can suppress transient trails. It consumes additional RAM and can also suppress
  real short-lived events; choose it according to your scientific/display goal.
- **Keograms:** compile a narrow column from successive frames to show the night
  over time. Set orientation with `KEOGRAM_ANGLE`; see
  [rotation guidance](https://github.com/aaronwmorris/indi-allsky/wiki/Keogram-Rotation).
- **Star trails:** combine star motion over time into an image or video.
- **Star/line detection:** counts and candidate trails can be useful indicators,
  but clouds, obstructions, aircraft and satellites affect results. Configure
  [detection masks](https://github.com/aaronwmorris/indi-allsky/wiki/Detection-Masks).
- **Moon mode:** can reduce gain when the moon's illumination/altitude meets the
  configured thresholds. It is distinct from ordinary day/night selection.
- **Pseudo-SQM:** camera-derived brightness is an estimate, not a substitute for
  a calibrated dedicated sky-quality instrument without suitable calibration.

![Example keogram showing changes throughout the night](content/keogram_example.jpg)

![Example stacked star trails](content/startrails_example.jpg)

## Optional hardware and integrations

Enable only the integrations you use and install their optional dependencies where
required. Device support in code does not prove that an unconnected device works.

| Capability | Examples / setup reference |
| --- | --- |
| Environmental sensors | Temperature, humidity, pressure, light, sky temperature, air quality, current, rain and lightning; [sensor guide](https://github.com/aaronwmorris/indi-allsky/wiki/Sensors), [device implementations](indi_allsky/devices) |
| Dew heaters / fans | Standard/PWM/relay/MQTT controllers; [dew heaters](https://github.com/aaronwmorris/indi-allsky/wiki/Dew-Heater-Support), [fans](https://github.com/aaronwmorris/indi-allsky/wiki/Fan-Control) |
| Focusers | 28BYJ-48, A4988/NEMA17 and MotorKit implementations; [focuser guide](https://github.com/aaronwmorris/indi-allsky/wiki/Focuser-Device) |
| GPS | GPSd/INDI integration for supported receivers; [setup helper](misc/setup_gpsd.sh) |
| Weather | Provider-specific OpenWeather, Weather Underground, Astrospheric, Ambient Weather and Ecowitt integrations; account/API configuration may be required |
| MQTT / Home Assistant | Publish measurements and discovery data; also selected remote sensors/controllers; [publishing guide](https://github.com/aaronwmorris/indi-allsky/wiki/MQTT-Broker-Publishing) |
| Uploads | FTP/FTPS/FTPES, SFTP and HTTPS WebDAV implementations; [file-transfer guide](https://github.com/aaronwmorris/indi-allsky/wiki/File-transfers) |
| Object storage | AWS S3, compatible backends, Google Cloud and OCI implementations; inspect [transfer modules](indi_allsky/filetransfer) and provider credentials/permissions |
| YouTube | OAuth-based upload of supported videos; [Hybrid operations](HYBRID_YOUTUBE_OPERATIONS.md) |
| Satellite / sky context | CelesTrak orbital elements, sun/moon calculations and selected astronomical overlays |
| Aurora / smoke | NOAA-derived aurora/solar information and North-America-only smoke coverage; availability depends on external data |
| Aircraft | Optional ADS-B input; receiver/feed configuration is separate from camera capture |

Provider quotas, fees, authentication and service availability are external to this
project. Configure and verify a small upload before bulk transfers. Preserve the
originals until the remote copy is verified; remote storage alone is not a backup
if the same retention/deletion policy can remove both copies.

## Security and remote access

Hybrid pages require login and privileged changes require the appropriate role.
Selected public media/integration handlers remain for compatibility. Login protection
for Hybrid does not imply that every static image or API endpoint is private.
Review the web server, API authentication and archive exposure before publishing.

Use HTTPS with a trusted certificate and a deliberate network policy. Keep INDI,
databases, brokers and administrative device controls off the public Internet unless
you have explicitly designed and secured their access. A private network/VPN or a
properly configured authenticated proxy can provide remote access.

Protect `/etc/indi-allsky`, configuration exports, backups, `.env`, TLS keys and
OAuth/API credentials. Do not commit secrets or use the disposable test fixture's
accounts in production. Apply OS/application updates deliberately and consult
[upstream security considerations](https://github.com/aaronwmorris/indi-allsky/wiki/Security-considerations)
for backend guidance, bearing in mind this fork's different frontend.

## Troubleshooting

| Symptom | Checks and next action |
| --- | --- |
| Setup refuses to run | Use the installation user, leave the virtualenv, stop capture; check free space and the reported distro/architecture |
| Missing INDI on Debian/Pi OS | Run the INDI build step if no supported installation exists; inspect conflicting packages rather than mixing installs |
| Python dependency build fails | Preserve the first error, confirm 64-bit OS, memory, disk and selected requirements; do not randomly upgrade the global Python environment |
| `systemctl --user` cannot connect to the bus | Log in directly as the service user; follow setup's reboot/relogin instructions and check lingering |
| Site unreachable / HTTP 502 | Check selected port, hostname/IP, Apache/NGINX, Gunicorn socket/service and web log; review port conflicts |
| Cannot log in | Use the account created at setup; recover with `misc/usertool.py resetpass` as the installation user |
| Service active but no fresh image | Check frame timestamps, capture log, selected camera/driver, device access, storage guard and free space; a healthy parent process does not prove healthy children |
| CSI camera busy / capture timeout | Stop competing camera consumers; inspect the actual timeout and resource logs; intermittent IMX708 timeouts remain a documented runtime issue |
| `database is locked` / SQLite BUSY | Check concurrent generation/cleanup/backup work and I/O pressure; retain the timestamp/log context, avoid deleting the DB or arbitrarily raising timeouts |
| Capture lags during encoding | Review RAM, swap, disk latency, output resolution, number of cameras and queues; lower-priority encoding still shares physical resources |
| FITS/RAW download missing | Confirm that this exposure actually saved that source and retention has not removed it; JPEG-only captures cannot supply an original FITS |
| Archive unavailable after disk removal | Inspect the configured mount and filesystem UUID; reconnect the correct disk before bypassing protection |
| No capture after reboot | Check the capture/INDI timers, web socket, user lingering and actual configured unit names; allow the boot delay |
| `pip check` reports GPIO metadata conflict on Pi 5 | Read [the dependency review](docs/HYBRID_DEPENDENCIES.md); `rpi-lgpio` can provide the `RPi.GPIO` module without satisfying the old distribution metadata |

When reporting a problem, include the source commit, OS/architecture, camera/interface,
reproduction steps, expected/actual behavior and a short redacted log excerpt.
Do not post full databases, secrets or private astronomical/location data by default.

## Development and verification

Use an isolated **Linux** test environment with the project's dependencies. macOS
alone does not provide the complete D-Bus/camera runtime. The regression suite and
browser fixture do not require changing production capture settings.

List the current regression plan without running the suite:

```sh
python3 testing/run_hybrid_regression.py --list
```

A standard-library self-check for the runner is also available:

```sh
python3 testing/hybrid_regression_runner_test.py
```

On a prepared isolated Linux checkout, use its dependency-equipped interpreter,
Node and a **new output directory outside the source tree**:

```sh
python3 testing/run_hybrid_regression.py \
  --python /path/to/prepared/virtualenv/bin/python \
  --node node \
  --output /tmp/indi-allsky-regression-unique-run
```

Replace the interpreter and output paths before execution. Integration fixtures
read `/etc/indi-allsky/flask.json` to construct isolated state. Optional YouTube
coverage may require `--oauth-python` with its dependencies. See
[the regression guide](testing/HYBRID_REGRESSION.md) for exact prerequisites and
interpretation. Do not run the suite from the production checkout.

For disposable browser development:

```sh
python testing/hybrid_browser_sandbox.py \
  --runtime-config /etc/indi-allsky/flask.json --port 18110
```

The sandbox binds to loopback, creates temporary data and blocks external effects.
Follow [UI development](docs/local-ui-dev.md) for test accounts and SSH forwarding;
do not expose the fixture publicly. Automated tests, synthetic browser checks,
actual hardware operation and deployment verification are different forms of
evidence. Record which ones were performed instead of claiming a universal pass.

## Documentation map

| Purpose | Document |
| --- | --- |
| Maintained Hybrid documentation index | [Hybrid guide](docs/HYBRID_GUIDE.md) |
| Latest remaining runtime issues and verification | [Remaining acceptance work](docs/HYBRID_ACCEPTANCE_REMAINING.md) |
| Installed releases and release-specific rollback | [Deployment](HYBRID_DEPLOYMENT.md) |
| Earlier acceptance register and evidence | [Acceptance status](HYBRID_ACCEPTANCE_STATUS.md) |
| Acceptance procedure and control coverage | [Workflow](docs/HYBRID_ACCEPTANCE_WORKFLOW.md), [route register](docs/hybrid-acceptance-route-register.md) |
| Capture cadence and exposure policy | [Capture](HYBRID_CAPTURE_CADENCE.md) |
| Storage and masks | [Storage runbook](HYBRID_STORAGE_RELEASE_RUNBOOK.md), [mask runbook](HYBRID_MASK_RELEASE_RUNBOOK.md) |
| Dependencies and installer-check limits | [Dependency review](docs/HYBRID_DEPENDENCIES.md) |
| Automated and browser tests | [Regression](testing/HYBRID_REGRESSION.md), [UI development](docs/local-ui-dev.md) |
| Utility scripts | [misc README](misc/README.md) |
| Removed historical reports and recovery | [Historical documents](docs/HISTORICAL_DOCUMENTS.md) |
| Upstream technical reference | [Wiki](https://github.com/aaronwmorris/indi-allsky/wiki), [FAQ](https://github.com/aaronwmorris/indi-allsky/wiki/FAQ) |

Dated audit/design reports describe their own checkpoints. They do not override
later deployment evidence or current source code. The upstream wiki remains useful
for drivers and processing, but its Classic screenshots and navigation are not
instructions for restoring the removed interface.

## Dependencies and architecture

The installer selects requirements for the OS and architecture from
[requirements/](requirements). Do not replace that selection with an arbitrary
`pip install` of the newest packages. SQLite is the standard native-install
database. MariaDB/MySQL paths exist in the backend/container deployment, but native
setup marks its MySQL path as not ready; it is not an equivalent default.

| Function          | Software      | URL |
| ----------------- | ------------- | --- |
| Camera interface  | INDI          | https://indilib.org/ |
|                   | pyindi-client | https://github.com/indilib/pyindi-client |
|                   | libcamera     | https://libcamera.org/ |
| Image processing  | OpenCV        | https://opencv.org/ |
|                   | opencv-python | https://github.com/opencv/opencv-python |
|                   | Pillow        | https://pillow.readthedocs.io/ |
|                   | piexif        | https://piexif.readthedocs.io/ |
|                   | astropy       | https://www.astropy.org/ |
|                   | astroalign    | https://astroalign.quatrope.org/ |
|                   | ccdproc       | https://ccdproc.readthedocs.io/ |
|                   | numpy         | https://numpy.org/ |
| Video processing  | ffmpeg        | https://www.ffmpeg.org/ |
| Astrometry        | pyephem       | https://rhodesmill.org/pyephem/ |
| File transfer     | pycurl        | http://pycurl.io/ |
|                   | paramiko      | http://www.paramiko.org/ |
|                   | paho-mqtt     | https://www.eclipse.org/paho/ |
|                   | requests      | https://requests.readthedocs.io/en/latest/ |
| S3 Object Storage | boto3         | https://boto3.amazonaws.com/v1/documentation/api/latest/index.html |
|                   | apache-libcloud | https://libcloud.apache.org/ |
|                   | google-cloud-storage | https://cloud.google.com/python/docs/reference/storage/latest |
| Database          | SQLite        | https://www.sqlite.org/ |
|                   | SQLAlchemy    | https://www.sqlalchemy.org/ |
|                   | alembic       | https://alembic.sqlalchemy.org/ |
|                   | mysql-connector-python | https://dev.mysql.com/doc/connector-python/en/ |
|                   | PyMySQL       | https://pymysql.readthedocs.io/en/latest/ |
| GPS               | GPSd          | https://gpsd.gitlab.io/gpsd/ |
| Web interface     | Flask         | https://flask.palletsprojects.com/ |
|                   | WTForms       | https://wtforms.readthedocs.io/ |
|                   | flask-login   | https://flask-login.readthedocs.io/ |
|                   | Gunicorn      | https://gunicorn.org/ |
|                   | Apache        | https://httpd.apache.org/ |
|                   | NGINX         | https://www.nginx.com/ |
| Hardware Sensors  | Circuit Python | https://circuitpython.org/ [GitHub](https://github.com/adafruit) |

Capture, image processing, video/storage and upload work use separate processes.
This helps scheduling but cannot eliminate memory, CPU or storage contention.
The following inherited diagram provides backend context; it is not a map of
Hybrid's current navigation or a guarantee of every deployed topology.

![indi-allsky backend architecture](content/indi-allsky-arch.svg)

## Contributing, support and license

Report fork-specific issues at [ericcatta/indi-allsky issues](https://github.com/ericcatta/indi-allsky/issues).
Identify whether you run this fork or upstream, and include a reproducible example
with the revision and environment. Keep changes focused and validate them at the
appropriate level. Do not include production secrets, private backups or generated
media in a pull request.

The project retains the original authorship and is distributed under the
[GNU General Public License v3](LICENSE). See [licenses/](licenses) for bundled
third-party notices. A different frontend or repository location does not remove
upstream attribution or license obligations.

### Acknowledgements

Thanks to Aaron Morris and the indi-allsky contributors for the acquisition,
processing and integration foundation, and to the Hybrid contributors for this
fork's interface and operational work.

* [Thomas Jacquin](https://github.com/thomasjacquin) - indi-allsky is heavily inspired by his [allsky](https://github.com/thomasjacquin/allsky) software.
* [Marco Gulino](https://github.com/GuLinux) - His examples from [indi-lite-tools](https://github.com/GuLinux/indi-lite-tools) were key to understanding how to work with pyindi-client
* [PixInsight](https://www.pixinsight.com/) - Various algorithms were used that are in the PixInsight documentation
* [Radek Kaczorek](https://github.com/rkaczorek) - [astropanel](https://github.com/rkaczorek/astropanel/) has been integrated into indi-allsky
* [CelesTrak](https://celestrak.org/) - Satellite orbital data
* [Russell Valentine](https://github.com/bluthen) - [fish2pano](https://github.com/bluthen/fish2pano) Fish-eye to panoramic perspective conversion
* [Adafruit Industries](https://www.adafruit.com/) - [Adafruit Github](https://github.com/adafruit) Circuit Python modules enabled indi-allsky to quickly facilitate using many electronics sensors

Upstream development can be supported through
[Aaron Morris's donation link](https://paypal.me/aaronwmorris). This is the upstream
author's funding link, not a separate donation account for this fork.
