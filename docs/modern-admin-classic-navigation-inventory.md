# Classic navigation replacement map

Verified against candidate `fc926129` on 14 September 2026. This replaces the
obsolete read-only migration proposal previously stored here. Settings writes,
media generation, camera tools and operational actions now have Hybrid entries;
they must not be redirected back to Classic based on that old proposal.

The optional Classic frontend registers **56 navigation URLs**, mapped below to
**44 Hybrid destinations**. The `/indi-allsky` prefix applies to every URL.
The source of truth is `flask/navigation_redirects.py`, checked against all
registrations in `flask/classic_views.py`. Public media/latest, AJAX/JSON, Sync API,
Action API and integration callbacks are separate contracts, not obsolete UI.

## Navigation coverage

| Old navigation URLs | Hybrid destination |
| --- | --- |
| `/`, `/index_canvas`, `/index_img` | `/modern-admin/now` |
| `/panorama`, `/panorama_canvas`, `/panorama_img` | `/modern-admin/media/panorama` |
| `/raw`, `/raw_canvas`, `/raw_img` | `/modern-admin/media/raw` |
| `/loop`, `/loop_canvas`, `/loop_img` | `/modern-admin/loop` |
| `/looppanorama`, `/looppanorama_canvas`, `/looppanorama_img` | `/modern-admin/media/panorama-loop` |
| `/loopraw`, `/loopraw_canvas`, `/loopraw_img` | `/modern-admin/media/raw-loop` |
| `/sensor_panel` | `/modern-admin/observatory/sensor-panel` |
| `/realtime_keogram` | `/modern-admin/observatory/realtime-keogram` |
| `/sqm` | `/modern-admin/observatory/sqm` |
| `/charts` | `/modern-admin/observatory/charts` |
| `/imageviewer` | `/modern-admin/media/images` |
| `/fitsimageviewer` | `/modern-admin/fits` |
| `/gallery` | `/modern-admin/media/gallery` |
| `/videoviewer` | `/modern-admin/media/timelapses` |
| `/minivideoviewer` | `/modern-admin/media/mini-timelapses` |
| `/generate` | `/modern-admin/tools/generate` |
| `/minigenerate` | `/modern-admin/tools/mini-generate` |
| `/config` | `/modern-admin/settings/full` |
| `/config/list` | `/modern-admin/config-history` |
| `/config/restore` | `/modern-admin/config-restore` |
| `/system` | `/modern-admin/system/info` |
| `/focus` | `/modern-admin/tools/focus` |
| `/manual_gpio` | `/modern-admin/system/gpio-control` |
| `/log` | `/modern-admin/system/log` |
| `/support` | `/modern-admin/system/support` |
| `/user` | `/modern-admin/account` |
| `/astropanel` | `/modern-admin/observatory/astropanel` |
| `/processing` | `/modern-admin/tools/process-fits` |
| `/longtermkeogram` | `/modern-admin/observatory/long-term-keogram` |
| `/camera` | `/modern-admin/cameras/info` |
| `/lag` | `/modern-admin/cameras/image-lag` |
| `/adu` | `/modern-admin/cameras/adu-history` |
| `/darks` | `/modern-admin/cameras/dark-library` |
| `/mask` | `/modern-admin/cameras/mask-base` |
| `/camerasimulator` | `/modern-admin/tools/camera-simulator` |
| `/imagecirclehelper` | `/modern-admin/tools/image-circle-helper` |
| `/filespaceusage` | `/modern-admin/storage/file-space-usage` |
| `/network` | `/modern-admin/system/network` |
| `/drives` | `/modern-admin/storage/drives` |
| `/virtualsky` | `/modern-admin/observatory/virtualsky` |
| `/cameras` | `/modern-admin/cameras` |
| `/tasks` | `/modern-admin/tasks` |
| `/notifications` | `/modern-admin/notifications` |
| `/users` | `/modern-admin/users` |

## What is proved

`testing/hybrid_navigation_redirect_test.py` checks exact coverage of the 56
Classic registrations with no duplicates or missing aliases. With Classic
imports forbidden, it exercises GET and HEAD for administrator, ordinary user
and anonymous sessions; camera/profile, timestamps and repeated query parameters
are preserved. Redirect destinations remain local even with hostile navigation
parameters. Public endpoint handlers remain independent of navigation redirects.
Selected followed routes also exercise the destination authentication behavior.

These checks prove navigation continuity, **not that every control or hardware
effect on each destination has passed acceptance**. The full automatic regression
for the candidate is recorded in
[Astropanel independence evidence](../testing/evidence/hybrid-astropanel-independence.json).
Per-control historical evidence is linked from
[the acceptance route register](hybrid-acceptance-route-register.md); its baseline
and coverage limits remain explicit and it is not a completion certificate.

## Remaining removal gates

- Install and accept the prepared candidate in a newly agreed maintenance window;
  see [the release runbook](../HYBRID_STORAGE_RELEASE_RUNBOOK.md).
- Finish the page/control matrix and direct acceptance of real effects. Native
  browser checks currently require an unlocked Mac; production certificate
  approval remains unresolved. Hardware actions require the agreed physical
  recovery arrangements. Blocked checks are not passes.
- Remove Classic-only classes, templates/assets and the temporary flag in
  separate commits after parity and live acceptance, then repeat essential tests.
- Keep these navigation redirects and independent public/API contracts when
  removing Classic. Retain useful shared workers, drivers and backend services.

Classic is still physically present. The deferred 24-hour observation is a
separate future activity and is not restarted by this map.
