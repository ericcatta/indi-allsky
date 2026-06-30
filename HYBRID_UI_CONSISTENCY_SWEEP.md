# Hybrid UI Consistency Sweep

## Scope

This sweep audits all template-rendered `modern_admin` pages after the Hybrid
shell expansion. The visual direction is not redesigned; the goal is to remove
legacy shell residue inside the new Hybrid Sky Console.

## Pages Checked

Checked template-rendered pages:

- Product: `now.html`, `highlights.html`, `sky_cycle.html`, `moment_detail.html`,
  `output_detail.html`, `library.html`, `observatory.html`.
- Operations/media: `cameras.html`, `camera_add.html`, `camera_info.html`,
  `loop.html`, `media_list.html`, `image_detail.html`, `video_detail.html`,
  `keograms.html`, `startrails.html`, `startrail_videos.html`,
  `mini_timelapses.html`, `panoramas.html`, `raw_images.html`, `fits.html`,
  `fits_detail.html`, `dark_library.html`.
- Observatory/info/tools: `charts.html`, `sensor_panel.html`, `astropanel.html`,
  `virtualsky.html`, `realtime_keogram.html`, `longterm_keogram.html`,
  `mask.html`, `safe_controls.html`, `image_lag.html`, `adu_history.html`.
- System/settings: `storage.html`, `file_space_usage.html`, `uploads.html`,
  `upload_detail.html`, `youtube.html`, `system.html`, `system_info.html`,
  `support_info.html`, `log.html`, `log_detail.html`, `tasks.html`,
  `task_detail.html`, `users.html`, `user_detail.html`, `notifications.html`,
  `notification_detail.html`, `updates.html`, `config_history.html`,
  `config_restore.html`, `config_restore_detail.html`, all settings templates.

## Inconsistencies Found

Primary inconsistency:

- Most operational pages included `modern_admin/_shell_header.html`.
- That partial rendered a second legacy topbar inside the Hybrid shell.
- The nested topbar exposed global Start/Restart/Power controls.
- It also exposed a second Dashboard/Cameras/Storage/Settings style navigation.
- It exposed Modern/Classic as visible product identity.

Secondary inconsistency:

- Several operational templates used visible "Classic" / "Modern Admin" wording
  for fallback links or notes.
- These labels made Hybrid feel like a skin over the older admin UI.

## Fixes Applied

### Single Shell

`modern_admin/_shell_header.html` now suppresses the old topbar/nav/action header
when rendered inside the Hybrid shell. It still renders flash messages, so
existing operational feedback remains visible.

This removes the nested legacy navigation from pages such as:

- Cameras;
- Loop;
- Gallery/Images;
- Media lists/details;
- Settings;
- Storage;
- Uploads;
- System;
- Logs;
- Tasks;
- Users;
- YouTube.

### Product Language

Visible wording in `modern_admin` templates was normalized:

- "Modern Admin" / "Modern admin" visible labels became "Hybrid".
- "Open Classic ..." became "Open legacy ...".
- "Classic fallback" became "Legacy fallback".
- "Classic data" became "Legacy data".
- "Back to Modern ..." / "Open Modern ..." became neutral links.

Endpoint names, route targets, and backend behavior were not changed.

### Day/Night

The previous day-mode coverage from the shell expansion remains in place:

- panels;
- cards;
- tables;
- badges;
- form controls;
- drawer/menu;
- latest frame cards;
- fallback states.

This sweep did not redesign dark/night mode.

## Pages Left Partially Legacy

Several operational pages still contain legacy-domain inner content by design:

- configuration history/restore;
- task queue;
- user management;
- YouTube OAuth fallback;
- FITS inspection;
- RAW/FITS/media operational lists;
- camera add and camera management operations.

They are now visually contained in the Hybrid shell and no longer duplicate the
legacy navigation. Their actual workflows remain unchanged because changing
them would risk backend behavior, mutative actions, or Classic compatibility.

## Safety Boundary

No new:

- route;
- query;
- provider;
- adapter;
- DATA001-DATA006 behavior;
- POST/fetch/AJAX call;
- backend mutation;
- filesystem/media/RAW/FITS access.

Existing operational forms and existing page-level scripts remain where they
already existed; this sweep does not add new ones.

## Manual Test Targets

Recommended manual visual checks:

- `/modern-admin/now` in day/night mode;
- `/modern-admin/cameras`;
- `/modern-admin/loop`;
- `/modern-admin/media/gallery`;
- `/modern-admin/media/images`;
- `/modern-admin/settings`;
- `/modern-admin/observatory`.

Expected result: one Hybrid shell, one primary navigation model, no nested
Modern/Classic switch, no legacy global topbar inside the page body.

## Residual Risk

Some operational pages still have dense technical tables or legacy-specific
fallback links. Those should be handled with page-scoped UX passes after Alpha,
not by broad shell changes.
