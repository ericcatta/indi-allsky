# Modern Admin QA Audit

Date: 2026-06-13

Scope: current Modern Admin routes, templates, header shell, classic sidebar mode routing, and isolated Modern Admin CSS. This audit is static/template-level QA plus Python compile checks; it does not start the full indi-allsky runtime.

## Summary

The Modern Admin shell is generally coherent across Dashboard, Cameras, P0 read-only pages, and the new Media batch. The biggest issue found was stale fallback routing: legacy Modern placeholder URLs for Media pages could still show "Coming later" even though real modern Media pages now exist. A small copy issue on the Dashboard also still described real dashboard areas as placeholders.

No obvious broken Modern Admin endpoint references were found in the templates inspected.

## Checks Performed

- Inspected Modern Admin view registration in `indi_allsky/flask/views.py`.
- Inspected Modern Admin templates under `indi_allsky/flask/templates/modern_admin/`.
- Inspected classic sidebar mode-aware links in `indi_allsky/flask/templates/base.html`.
- Compared shell/header usage against Dashboard and Cameras.
- Checked static `url_for('indi_allsky...')` endpoint references against registered view endpoint names.
- Ran `python3 -m py_compile indi_allsky/flask/views.py`.
- Ran `git diff --check`.

## Problems Found

### Fixed

1. Stale Media placeholder fallback URLs
   - Affected URLs:
     - `/indi-allsky/modern-admin/classic/gallery`
     - `/indi-allsky/modern-admin/classic/images`
     - `/indi-allsky/modern-admin/classic/timelapses`
     - `/indi-allsky/modern-admin/classic/mini-timelapses`
     - `/indi-allsky/modern-admin/classic/panorama`
     - `/indi-allsky/modern-admin/classic/panorama-loop`
     - `/indi-allsky/modern-admin/classic/fits-viewer`
   - Issue: these could still render the generic "Coming later" placeholder even though real modern Media pages exist.
   - Fix: added safe redirects from those legacy placeholder slugs to the real modern Media routes.

2. Media CSS cache-busting inconsistency
   - Issue: `modern_admin/media_list.html` loaded `modern-admin.css` without the same version query used by other Modern Admin templates.
   - Risk: stale CSS could make Media pages appear visually inconsistent after deploy.
   - Fix: aligned the stylesheet URL with the other Modern Admin templates.

3. Stale Dashboard placeholder copy
   - Issue: Dashboard still contained "Placeholder dashboard", "Placeholder system status", and "Latest image placeholder refreshed" text even though latest image/status fields are real.
   - Fix: changed copy/ARIA label to neutral real-dashboard wording.

### Open / Intentional

1. Top-level placeholder pages still exist
   - Routes:
     - `/indi-allsky/modern-admin/storage`
     - `/indi-allsky/modern-admin/uploads`
     - `/indi-allsky/modern-admin/observatory`
     - `/indi-allsky/modern-admin/system`
     - `/indi-allsky/modern-admin/updates`
   - Status: intentional shell placeholders. They link into real read-only pages where those exist.

2. Some sidebar items still route to modern placeholders by design
   - Examples: Realtime Keogram, Long Term Keogram, Dark Library, VirtualSky, AstroPanel, Generate, Focus, Process FITS, Image Circle Helper, Mask Base, Log, Config, Network, Drives, GPIO Control.
   - Status: expected until those batches are modernized or explicitly kept classic-only.

3. Some modern pages remain table-heavy
   - Examples: Image Lag, ADU History, File Space Usage, Sensor Panel, System Info.
   - Status: usable and responsive through `modern-admin-table-scroll`, but still closer to admin inventory than Dashboard/Cameras. This is a UX modernization task, not a small bug fix.

4. Dashboard Recent Events are still placeholder content
   - Status: known limitation. This should become real notification/event data in a future read-only batch.

5. Media pages have no dedicated top-level nav active state
   - Reason: the current IA top nav has Dashboard, Cameras, Storage, Uploads, Observatory, System, Updates, but no Media section.
   - Impact: Media pages use the Modern shell but no top tab clearly owns them.
   - Recommendation: decide whether Media belongs under Uploads, Dashboard, or a future top-level Media section before adding more Media UX.

6. Runtime QA was not performed
   - The full Flask runtime/database/camera stack was not started for this audit.
   - Remaining risk: database-specific render errors, missing media files, auth redirects, or environment-only issues may only appear in a live instance.

## Link / Route Notes

Modern routes inspected:

- `/indi-allsky/modern-admin`
- `/indi-allsky/modern-admin/cameras`
- `/indi-allsky/modern-admin/cameras/info`
- `/indi-allsky/modern-admin/cameras/image-lag`
- `/indi-allsky/modern-admin/cameras/adu-history`
- `/indi-allsky/modern-admin/storage`
- `/indi-allsky/modern-admin/storage/file-space-usage`
- `/indi-allsky/modern-admin/uploads`
- `/indi-allsky/modern-admin/observatory`
- `/indi-allsky/modern-admin/observatory/sqm`
- `/indi-allsky/modern-admin/observatory/charts`
- `/indi-allsky/modern-admin/observatory/sensor-panel`
- `/indi-allsky/modern-admin/system`
- `/indi-allsky/modern-admin/system/info`
- `/indi-allsky/modern-admin/system/support`
- `/indi-allsky/modern-admin/updates`
- `/indi-allsky/modern-admin/media/gallery`
- `/indi-allsky/modern-admin/media/images`
- `/indi-allsky/modern-admin/media/timelapses`
- `/indi-allsky/modern-admin/media/mini-timelapses`
- `/indi-allsky/modern-admin/media/panorama`
- `/indi-allsky/modern-admin/media/panorama-loop`
- `/indi-allsky/modern-admin/media/fits`

## Recommended Next QA Pass

When a local or Pi runtime is available:

1. Log in and set `admin_mode=modern`.
2. Click every classic sidebar item and confirm it either lands on a real modern page or an intentional modern placeholder.
3. Visit every Modern top tab on desktop and mobile widths.
4. Open Media pages with real image/video/FITS records and with empty database states.
5. Verify no Media preview overflows cards on mobile.
6. Check auth redirects from an anonymous session.
