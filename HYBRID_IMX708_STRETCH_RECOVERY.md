# IMX708 night preview recovery — 2026-09-06

## Diagnosis

At 22:16 CEST, camera 1 (`libcamera_imx708`, profile `imx708-wide`) had
no new JPEG since 20:24:03. Its FITS at 22:16:52 proved capture continued.
Camera 2 (`ZWO CCD ASI678MC`) continued producing JPEGs. Free space was 86 GiB.

The image worker repeatedly terminated in `mode1_stddev_cutoff._get_image_stddev`:
`MaskError: data size is 11943936, mask size is 8294400`.
Mode 1 cached its NumPy mask only by binning; both cameras use binning 1,
but their image dimensions differ. The switch to night processing exposed it.
A service restart alone would recreate the same error on alternating cameras.

After fixing the mask, the second mixed-camera cycle exposed an additional
OpenCV error in star template matching. `_select_image_processor` isolated state
only when `images_only_diag` was true. Full-output profiles therefore shared the
processor: the 16-bit ZWO range promoted the IMX708 stretch to uint16, while its
8-bit source header caused display conversion to return that uint16 unchanged.
This was a processing-context defect, not a detector algorithm defect.

## Change and tests

Full-output multicamera profiles now select the existing per-profile/camera
processor, isolating bit depth, configuration, stacks and shared arrays.
The cache also includes binning, width and height. An external mask with the wrong
shape uses the existing SQM ROI fallback and logs the mismatch. Gamma, level
adjustment, exposure, gain, saved settings and the acquisition scheduler are unchanged.

`python3 testing/stretch_multicamera_mask_test.py` reproduces alternating color
and mono sizes, binning, 8/12-bit images, valid external masks and mismatched-mask
fallback. Shared processing must match a fresh independent instance pixel for
pixel. The original implementation reproduces the same MaskError. The test passes
locally and with the Raspberry's installed Python/NumPy. Full Book 2 regression
and the FITS preview parser/pipeline parity tests also pass.
`testing/multicamera_processor_isolation_test.py` exercises real processors with
16-bit/8-bit/16-bit/8-bit frames, Mode 1 stretch and OpenCV star detection;
checks profile/config/stack isolation and preserves legacy/images-only behavior.

## Production application and rollback

Production baseline: `9e721647`. This emergency applies **only**
`indi_allsky/stretch/mode1_stddev_cutoff.py` and `indi_allsky/image.py`,
not the unfinished UI migrations.
The production checkout therefore retains a deliberate tracked hotfix until the
next controlled repository deployment. Existing untracked files are preserved.

Backup directory:
`/home/eric/hybrid-backups/imx708-stretch-20260906-221955`.
It contains the original Python files, an online SQLite backup, Flask configuration
and SHA-256 manifest. No acquired media are deleted or rewritten.

Rollback on the Pi, only if this correction causes a regression:

```sh
cp /home/eric/hybrid-backups/imx708-stretch-20260906-221955/mode1_stddev_cutoff.py /home/eric/indi-allsky/indi_allsky/stretch/mode1_stddev_cutoff.py
cp /home/eric/hybrid-backups/imx708-stretch-20260906-221955/image.py /home/eric/indi-allsky/indi_allsky/image.py
systemctl --user restart indi-allsky.service
```

A code rollback does not require restoring the database. Restoring that backup
would discard newer metadata and is not part of this procedure.

## Live acceptance

- SQLite backup integrity check passed before changing production code.
- First restart at 22:23 exposed the additional full-output processor defect;
  the single returned IMX708 frame was not treated as successful recovery.
- Complete correction loaded at **22:28:24 CEST**, main PID3184687,
  image worker PID3184700.
- At22:30:37, three new JPEGs from each camera: IMX708 timestamps22:28:54,
  22:29:39,22:30:25; ZWO22:28:54,22:29:33,22:30:18. Latest files existed
  with2,562,538 and683,133 bytes respectively. No Traceback/MaskError since
  the final restart; image worker remained the same process.
- Production Now reloaded through the actual browser. Both images decoded:
  IMX7084608×2592 and ZWO3840×2160. The old IMX70820:24 timestamp was replaced.
- Available memory after initialization:6370MiB. No full-day stability claim:
  the24-hour day/night acceptance remains open and restarts from this runtime fix.
