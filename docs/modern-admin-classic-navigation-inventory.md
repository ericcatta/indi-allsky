# Classic navigation replacement map

Classic frontend files have been removed. The remaining **56 navigation URLs**
redirect to **44 Hybrid destinations**, preserving bookmarks and query scope.
The `/indi-allsky` prefix applies to every URL. Current source is
[`navigation_redirects.py`](../indi_allsky/flask/navigation_redirects.py); the
frozen prior registrations are in
[`classic_frontend_contract.json`](../testing/classic_frontend_contract.json).
Public media/latest, AJAX/JSON, Sync API, Action API and integration callbacks
retain independent handlers and must not be deleted as obsolete navigation.

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
effect on each destination has passed acceptance**. Current installed version,
regression evidence and rollback are in [the deployment runbook](../HYBRID_DEPLOYMENT.md).
Per-control evidence is linked from [the route register](hybrid-acceptance-route-register.md).

## Remaining acceptance

Classic removal is complete; product acceptance is not. See
[the current status](../HYBRID_ACCEPTANCE_STATUS.md) for the remaining control,
effect, download and hardware checks. The 24-hour observation is deferred.
Do not reintroduce Classic or remove shared backend/API handlers to close these
checks artificially.
