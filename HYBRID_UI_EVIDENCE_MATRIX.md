# HYBRID UI EVIDENCE MATRIX

Audit date: 2026-06-26

Related plan: `HYBRID_UI_SIMPLIFICATION_PLAN.md`

Scope: evidence-backed static audit for Classic UI, Modern UI, routes,
templates, assets, API surfaces and critical configuration groups. This
document does not remove, rename, refactor or change runtime behavior.

## 1. Purpose

`HYBRID_UI_SIMPLIFICATION_PLAN.md` defines the architectural direction for
Modern UI consolidation and eventual Classic UI removal. This Evidence Matrix
adds repository-backed evidence for that plan.

The goal is to make each future cleanup claim testable:

- where a route is registered;
- which view/class owns it;
- which template renders it;
- which template or JavaScript calls an endpoint;
- which assets are loaded;
- which config keys are defined, read and written;
- whether the item is active, duplicated, shared, or only a future removal
  candidate.

No removal is recommended as immediate. Every removal candidate is explicitly
`REMOVAL CANDIDATE - NOT NOW`.

## 2. Methodology

Repository inspection used these searches:

- Flask route registration:
  - `rg -n "bp_allsky.add_url_rule|bp_auth_allsky.add_url_rule|bp_syncapi_allsky.add_url_rule|bp_actionapi_allsky.add_url_rule|@bp_allsky.route" indi_allsky/flask/*.py`
- Template rendering:
  - `rg -n "template_name=|render_template\\(" indi_allsky/flask/views.py indi_allsky/flask/*.py`
- Template inheritance/includes:
  - `rg -n "extends |include |import |from .* import" indi_allsky/flask/templates`
- Asset loading:
  - `rg -n "static\\(|modern-admin.css|style.css|DataTables|chart.umd|photoswipe|virtualsky|astropanel|clipboard" indi_allsky/flask/templates`
- JavaScript/API calls:
  - `rg -n "fetch\\(|axios|\\$\\.ajax|XMLHttpRequest|loadJS\\(|url_for\\('indi_allsky\\.|url_for\\(\"indi_allsky\\." indi_allsky/flask/templates indi_allsky/flask/static`
- Config definitions and references:
  - `rg -n "MULTI_CAMERA|CCD_EXPOSURE|TARGET_ADU|AUTO_GAIN|AUTO_EXPOSURE|IMAGE_SAVE_FITS|IMAGE_EXPORT_RAW|FRAME_METADATA|EVENT_CANDIDATE_TRIGGERS|TIMELAPSE|KEOGRAM|STARTRAILS|FILETRANSFER|S3UPLOAD|SYNCAPI|YOUTUBE|DETECT_METEORS" indi_allsky config.py testing`
- Modern wrapper detection:
  - `rg -n "ModernAdminContextMixin|ModernAdminSafeControlsMixin|template_name='modern_admin/safe_controls.html'" indi_allsky/flask/views.py`

Limitations:

- This is static analysis. It does not prove whether a route is used by a real
  user, bookmark, reverse proxy, upload target, or external script.
- Config analysis focuses on Hybrid-critical groups and high-risk legacy groups;
  `IndiAllskyConfigForm` contains hundreds of fields and needs an automated
  inventory before field-by-field removal decisions.
- Minified vendor assets contain internal `XMLHttpRequest` or source-map text;
  those are vendor internals, not app-specific consumers.
- `NO REFERENCES FOUND` means no repository reference was found with the searches
  above; it does not prove no external reference exists.

## 3. Route Evidence Matrix

Status values:

- `MODERN ACTIVE`
- `LEGACY ACTIVE`
- `SHARED ACTIVE`
- `DUPLICATED`
- `NO REFERENCES FOUND`
- `NEEDS VERIFICATION`
- `REMOVAL CANDIDATE - NOT NOW`

| Route | File Python | Function/view | Template | API or page | Classic/Modern/Shared | Consumer known | Evidence found | Status | Removal risk | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `/images/<path:path>` | `indi_allsky/flask/views.py:20122` | `images_folder` | none | media file fallback | Shared/public | templates use `images_folder` in Modern VirtualSky | `modern_admin/virtualsky.html:50` | SHARED ACTIVE | High | Backup media serving path. |
| `/ajax/status_update` | `views.py:20128` | `AjaxStatusUpdateView` | JSON | API | Shared | base/status code likely | route registered | SHARED ACTIVE | High | Needs consumer instrumentation. |
| `/`, `/index_img`, `/index_canvas` | `views.py:20133-20135` | `IndexImgView`, `IndexCanvasView` | `index_img.html`, `index_canvas.html` | page | Classic/public | public browser users | templates extend `base.html` | LEGACY ACTIVE | High | Public surface, not admin-only. |
| `/js/latest` | `views.py:20136` | `JsonLatestImageView` | JSON | API | Classic/public | `index_img.html` | `index_img.html:66` calls latest endpoint variable | SHARED ACTIVE | High | Public latest image API. |
| `/panorama*`, `/js/latest_panorama` | `views.py:20137-20140` | panorama latest views | `index_img.html`, `index_canvas.html` | page/API | Classic/public | public/latest panorama | route registered | LEGACY ACTIVE | Medium | Modern media has panorama list, not full public replacement. |
| `/raw*`, `/js/latest_rawimage` | `views.py:20141-20144` | raw latest views | `index_img.html`, `index_canvas.html` | page/API | Classic/public | public/latest raw | route registered | LEGACY ACTIVE | Medium | Scientific source UX not replacement. |
| `/realtime_keogram` | `views.py:20145` | `RealtimeKeogramView` | `realtime_keogram.html` | page | Classic | Modern equivalent exists | Modern route `20233`; template exists | DUPLICATED | Medium | Modern page active but parity needs verification. |
| `/loop*`, `/js/loop` | `views.py:20147-20150` | loop views | `loop_img.html`, `loop_canvas.html` | page/API | Classic/public | loop pages; Modern VirtualSky calls image loop | `sqm.html:209`, `modern_admin/virtualsky.html:66` | SHARED ACTIVE | High | Modern depends on legacy JSON loop endpoint. |
| `/looppanorama*`, `/js/looppanorama` | `views.py:20151-20154` | panorama loop views | `loop_img.html`, `loop_canvas.html` | page/API | Classic | unknown | route registered | LEGACY ACTIVE | Medium | Needs runtime usage check. |
| `/loopraw*`, `/js/loopraw` | `views.py:20155-20158` | raw loop views | `loop_img.html`, `loop_canvas.html` | page/API | Classic | unknown | route registered | LEGACY ACTIVE | Medium | Needs runtime usage check. |
| `/sqm` | `views.py:20160` | `SqmView` | `sqm.html` | page | Classic | Modern wrapper exists | `ModernAdminSqmView(ModernAdminContextMixin, SqmView)` at `views.py:12688` | DUPLICATED | Medium | Modern depends on legacy class. |
| `/charts`, `/js/charts` | `views.py:20162-20163` | `ChartView`, `JsonChartView` | `chart.html`, JSON | page/API | Shared | Classic chart, Modern chart | `modern_admin/charts.html:87` fetches `js_chart_view` | SHARED ACTIVE | High | Keep until Modern has separate analytics API. |
| `/imageviewer`, `/ajax/imageviewer`, `/ajax/exclude` | `views.py:20165-20167` | image viewer views | `imageviewer.html`, JSON | page/API | Classic | Classic template | `imageviewer.html` calls ajax internally | LEGACY ACTIVE | Medium | Modern media list is not full image viewer parity. |
| `/fitsimageviewer`, `/ajax/fitsimageviewer`, `/fits2jpeg` | `views.py:20169-20171` | FITS viewer/converter | `fitsimageviewer.html`, JSON | page/API | Classic | Classic FITS viewer | route registered | LEGACY ACTIVE | High | Scientific source review may need this until replaced. |
| `/gallery`, `/ajax/gallery` | `views.py:20173-20174` | gallery views | `gallery.html`, JSON | page/API | Classic | PhotoSwipe gallery | `gallery.html` loads PhotoSwipe | DUPLICATED | Medium | Modern gallery exists; compare feature parity before removal. |
| `/videoviewer`, `/ajax/videoviewer` | `views.py:20176-20177` | video viewer | `videoviewer.html`, JSON | page/API | Classic | Classic video template | `videoviewer.html:497,558` AJAX | DUPLICATED | Medium | Modern timelapse list exists; upload/links parity unknown. |
| `/minivideoviewer`, `/ajax/minivideoviewer` | `views.py:20179-20180` | mini video viewer | `minivideoviewer.html`, JSON | page/API | Classic | Classic mini viewer | `minivideoviewer.html:311,351` AJAX | DUPLICATED | Medium | Modern mini list exists; parity unknown. |
| `/modern-admin/media/*` | `views.py:20182-20189` | `ModernAdminMedia*` | `modern_admin/media_list.html` | page/page API | Modern | Modern media pages | `media_list.html` fetches page URL at lines 320/396 | MODERN ACTIVE | Low | Canonical future media list. |
| `/view_*`, `/watch_*` | `views.py:20191-20200` | media object views | `view_image.html`, `watch_video.html` | page | Classic/shared | Classic/Modern media links may open direct URLs | templates use clipboard | SHARED ACTIVE | High | Preserve external media links. |
| `/generate`, `/ajax/generate` | `views.py:20202-20203` | generator views | `generate.html`, JSON | page/API | Shared through Modern safe control | Classic template and Modern wrapper | `ModernAdminGenerateView` uses safe controls at `views.py:15069,20242` | SHARED ACTIVE | High | Do not remove until native Modern generation. |
| `/minigenerate`, `/ajax/minigenerate` | `views.py:20205-20206` | mini generator | `mini_generate.html`, JSON | page/API | Classic | Classic template | `mini_generate.html:289` AJAX | LEGACY ACTIVE | Medium | No native Modern equivalent found. |
| `/config`, `/ajax/config` | `views.py:20208-20209` | `ConfigView`, `AjaxConfigView` | `config.html`, JSON | page/API | Shared | Classic config, Modern Full Settings | `settings_full.html:154,251` fetches `ajax_config_view` | SHARED ACTIVE | Critical | Core config save path. |
| `/config/list`, `/config/download`, `/config/restore`, `/ajax/config/restore` | `views.py:20210-20213` | config history/restore | `config_list.html`, `config_restore.html` | page/API | Classic | Classic config pages | links in `config.html:5295-5304` | LEGACY ACTIVE | High | Config history/restore parity unclear. |
| `/modern-admin` | `views.py:20215` | `ModernAdminView` | `modern_admin/index.html` | page | Modern | Modern users | template includes dashboard, analytics, Event Foundation | MODERN ACTIVE | Low | Canonical Hybrid dashboard. |
| `/modern-admin/capture/service` | `views.py:20216` | `ModernAdminCaptureServiceActionView` | JSON | API | Modern | shell header | `_shell_header.html:107,135` fetches it | MODERN ACTIVE | Medium | Runtime action API. |
| `/modern-admin/cameras*` | `views.py:20217-20223` | Modern camera views | Modern templates | page/API | Modern | Modern camera workflow | templates and routes registered | MODERN ACTIVE | Low | Canonical multicamera/profile surface. |
| `/modern-admin/storage*` | `views.py:20224-20225,20252` | storage/file-space/drives | Modern templates/safe controls | page | Modern/wrapper | Modern nav | `ModernAdminDriveManagerView` safe control | MODERN ACTIVE | Medium | Drives still legacy wrapped. |
| `/modern-admin/uploads` | `views.py:20226` | `ModernAdminUploadsView` | `modern_admin/uploads.html` | page | Modern | Modern nav | route/template registered | MODERN ACTIVE | Medium | Upload config parity unclear. |
| `/modern-admin/observatory*` | `views.py:20227-20234` | Modern observatory views | Modern templates | page | Modern/wrapper | Modern nav | several classes use `ModernAdminContextMixin` | MODERN ACTIVE | Medium | Some pages wrap legacy data/classes. |
| `/modern-admin/system*` | `views.py:20235-20238,20250-20253` | system/log/config/network/GPIO | Modern templates/safe controls | page/API | Modern/wrapper | Modern nav | safe control routes registered | MODERN ACTIVE | Medium | Network/GPIO/config are wrappers. |
| `/modern-admin/tools/*` | `views.py:20241-20245` | simulator/generate/focus/process/circle | `safe_controls.html` | page | Modern wrapper | Modern nav | `ModernAdminSafeControlsMixin` evidence | MODERN ACTIVE | Medium | Not native parity. |
| `/modern-admin/settings*` | `views.py:20246-20249` | inventory/full/capture/cameras | Modern templates | page/API | Modern | Modern settings | Camera Settings profile-first template | MODERN ACTIVE | Low | Future canonical settings. |
| `/modern-admin/classic/<classic_page>` | `views.py:20256` | placeholder | `modern_admin/placeholder.html` | page | Transitional | Modern mode bridge | route registered | NEEDS VERIFICATION | Low | Remove only after Classic removal complete. |
| `/modern-admin/mode/<mode>` | `views.py:20257` | mode switch | none | API/redirect | Shared mode switch | shell header | `_shell_header.html:32-33` | MODERN ACTIVE | Low | Supports Classic/Modern switch. |
| `/system`, `/ajax/system`, `/ajax/settime`, `/ajax/settimezone`, `/ajax/indiserver` | `views.py:20258-20262` | system views/actions | `system.html`, JSON | page/API | Classic/shared | Classic; Modern wrappers for system info | route registered; Modern system info wraps class | SHARED ACTIVE | High | Hardware/system actions. |
| `/focus`, `/js/focus`, `/ajax/focuscontroller` | `views.py:20264-20266` | focus views/actions | `focus.html`, JSON | page/API | Shared via Modern safe control | `focus.html`, `safe_controls.html` | `safe_controls.html:135` fetches `js_focus_view` | SHARED ACTIVE | High | Modern depends on legacy focus API. |
| `/manual_gpio`, `/ajax/manual_gpio` | `views.py:20268-20269` | GPIO views/actions | `manual_gpio.html`, JSON | page/API | Shared via Modern safe control | `manual_gpio.html:140` AJAX | SHARED ACTIVE | High | Hardware control. |
| `/log`, `/js/log`, `/log/*download` | `views.py:20271-20276` | log views/downloads | `log.html`, JSON | page/API | Shared | Modern log fetches `js_log_view` | `modern_admin/log.html:48` | SHARED ACTIVE | High | Keep downloads. |
| `/support`, `/js/support` | `views.py:20278-20279` | support | `support_info.html`, JSON | page/API | Shared | Modern support wrapper | `ModernAdminSupportInfoView` wraps `SupportInfoView` | SHARED ACTIVE | Medium | Support bundle. |
| `/user`, `/ajax/user` | `views.py:20281-20282` | user info | `user.html`, JSON | page/API | Classic | `user.html:190` AJAX | route/template evidence | LEGACY ACTIVE | Medium | Modern parity missing. |
| `/astropanel`, `/ajax/astropanel` | `views.py:20284-20285` | astropanel | `astropanel.html`, JSON | page/API | Shared | Modern astropanel fetches AJAX | `modern_admin/astropanel.html:72` | SHARED ACTIVE | Medium | Shared assets. |
| `/processing`, `/js/processing` | `views.py:20287-20288` | image processing | `imageprocessing.html`, JSON | page/API | Shared via safe control | `imageprocessing.html:2222` | safe control route exists | SHARED ACTIVE | High | Processing tool; no native Modern parity. |
| `/longtermkeogram`, `/js/longtermkeogram` | `views.py:20290-20291` | longterm keogram | `longterm_keogram.html`, JSON | page/API | Shared/duplicated | Classic and Modern route | `modern_admin/longterm_keogram.html` | DUPLICATED | Medium | Modern page exists but parity unknown. |
| `/camera`, `/lag`, `/adu`, `/darks`, `/mask`, `/filespaceusage` | `views.py:20293-20300` | camera utility views | classic templates | page | Shared via Modern wrappers | `ModernAdminCameraInfoView`, etc. | wrapper classes at `views.py:12668-12883` | SHARED ACTIVE | Medium | Do not remove legacy classes yet. |
| `/network`, `/ajax/network`, `/drives`, `/ajax/drives` | `views.py:20304-20308` | network/drive managers | classic templates/JSON | page/API | Shared via safe control | Modern safe control routes | `views.py:19620,19652` | SHARED ACTIVE | High | System control. |
| `/virtualsky` | `views.py:20310` | VirtualSky | `virtualsky.html` | page | Shared | Modern wrapper exists | `ModernAdminVirtualSkyView(..., VirtualSkyView)` | SHARED ACTIVE | Medium | Uses vendor assets. |
| `/ajax/notification` | `views.py:20312` | notification API | JSON | API | Classic | notifications page | route/template evidence | LEGACY ACTIVE | Medium | Modern notifications missing. |
| `/ajax/selectcamera` | `views.py:20313` | select camera | JSON | API | Classic/shared | needs verification | route registered | NEEDS VERIFICATION | Medium | Could be external/session-related. |
| `/ajax/uploadyoutube`, `/youtube/*` | `views.py:20314-20320` | YouTube upload/OAuth | direct/API | API/page | Classic | video templates and config links | `videoviewer.html:613`, `config.html:6756+` | LEGACY ACTIVE | High | External OAuth; port before removal. |
| `/latest*` redirects | `views.py:20323-20340` | latest redirect views | redirects | public/API-ish | Public/shared | external links/bookmarks likely | route registered | SHARED ACTIVE | High | Preserve as compatibility redirects. |
| `/cameras`, `/tasks`, `/notifications`, `/users` | `views.py:20343-20346` | hidden/admin views | classic templates | page | Classic | admin users | route registered; templates extend base | LEGACY ACTIVE | Medium | Task/users/notifications missing in Modern. |
| `/login`, `/logout` | `auth_views.py:160-161` | auth views | `login.html` | page/action | Shared/auth | all users | route registered | SHARED ACTIVE | Critical | Outside UI cleanup until auth redesign. |
| `/sync/v1/*` | `syncapi_views.py:816-827` | sync API views | JSON | API | External/shared | upload/sync consumers | route registered | SHARED ACTIVE | Critical | Not a UI removal candidate. |
| `/action/pause`, `/action/unpause` | `actionapi_views.py:155-156` | action API views | JSON | API | External/shared | external/action users | route registered | SHARED ACTIVE | High | Keep separate from UI cleanup. |

## 4. Template Evidence Matrix

| Template | Path | Extends | Includes used | Includes received | Route rendering it | Assets loaded | Classic/Modern/Shared | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `base.html` | `indi_allsky/flask/templates/base.html` | none | none found | almost all Classic and Modern templates extend it | common base | Bootstrap, `css/style.css`, jQuery, `indi-allsky-tabs.js` | Shared | SHARED ACTIVE | Modern still extends Classic base. |
| `login.html` | `templates/login.html` | none | none | none | `/login` | Bootstrap, `css/style.css`, jQuery | Shared/auth | SHARED ACTIVE | Auth page outside removal. |
| `index_img.html` | `templates/index_img.html` | `base.html` | none | none | `/`, `/index_img`, panorama/raw variants | inline JS | Classic/public | LEGACY ACTIVE | Public latest image. |
| `index_canvas.html` | `templates/index_canvas.html` | `base.html` | none | none | `/index_canvas`, panorama/raw canvas | inline JS | Classic/public | LEGACY ACTIVE | Public latest canvas. |
| `loop_img.html`, `loop_canvas.html` | `templates/loop_*` | `base.html` | none | none | loop routes | inline JS | Classic/shared | SHARED ACTIVE | Modern VirtualSky uses loop JSON, not template. |
| `gallery.html` | `templates/gallery.html` | `base.html` | none | none | `/gallery` | PhotoSwipe UMD, PhotoSwipe CSS | Classic | DUPLICATED | Modern media gallery exists. |
| `imageviewer.html` | `templates/imageviewer.html` | `base.html` | none | none | `/imageviewer` | inline JS | Classic | LEGACY ACTIVE | Advanced media actions not fully mapped. |
| `fitsimageviewer.html` | `templates/fitsimageviewer.html` | `base.html` | none | none | `/fitsimageviewer` | inline JS | Classic | LEGACY ACTIVE | Scientific source/FITS review may need it. |
| `videoviewer.html`, `minivideoviewer.html` | `templates/*videoviewer.html` | `base.html` | none | none | video routes | inline JS | Classic | DUPLICATED | Modern lists exist; upload links remain Classic. |
| `generate.html`, `mini_generate.html` | `templates/*generate.html` | `base.html` | none | none | `/generate`, `/minigenerate` | DataTables, inline JS | Classic/shared | SHARED ACTIVE | `/generate` has Modern safe wrapper. |
| `config.html` | `templates/config.html` | `base.html` | none | none | `/config` | huge inline JS | Classic/shared | SHARED ACTIVE | Modern Full Settings uses same save endpoint. |
| `config_list.html`, `config_restore.html` | templates | `base.html` | none | none | config history/restore | DataTables for list | Classic | LEGACY ACTIVE | Restore parity unknown. |
| `system.html`, `log.html`, `support_info.html` | templates | `base.html` | none | none | system/log/support | inline JS, clipboard for support | Shared/wrapped | SHARED ACTIVE | Modern wrappers exist. |
| `focus.html`, `manual_gpio.html`, `imageprocessing.html` | templates | `base.html` | none | none | tools | Chart.js/inline JS | Shared via safe controls | SHARED ACTIVE | Not native Modern. |
| `network.html`, `drive_manager.html` | templates | `base.html` | none | none | network/drives | inline JS/DataTables | Shared via safe controls | SHARED ACTIVE | System control risk high. |
| `user.html`, `users.html`, `notifications.html`, `taskqueue.html` | templates | `base.html` | none | none | user/admin hidden pages | DataTables/inline JS | Classic | LEGACY ACTIVE | Modern parity missing. |
| `astropanel.html`, `virtualsky.html` | templates | `base.html` | none | none | astro/virtual sky | Astropanel/VirtualSky/html2canvas | Shared | SHARED ACTIVE | Modern wrappers exist. |
| `modern_admin/_shell_header.html` | Modern partial | n/a | none | included by Modern templates | n/a | inline fetch JS | Modern | MODERN ACTIVE | Header quick/capture actions. |
| `modern_admin/index.html` | Modern dashboard | `base.html` | `_shell_header.html` | none | `/modern-admin` | `modern-admin.css`, inline charts | Modern | MODERN ACTIVE | Hybrid dashboard. |
| `modern_admin/cameras.html` | Modern cameras | `base.html` | `_shell_header.html` | none | `/modern-admin/cameras` | `modern-admin.css` | Modern | MODERN ACTIVE | Profile/multicamera page. |
| `modern_admin/settings_cameras.html` | Modern camera settings | `base.html` | `_shell_header.html` | none | `/modern-admin/settings/cameras` | `modern-admin.css`, inline JS | Modern | MODERN ACTIVE | Profile-first settings. |
| `modern_admin/settings_full.html` | Modern full settings | `base.html` | `_shell_header.html` | none | `/modern-admin/settings/full` | `modern-admin.css`, fetch `/ajax/config` | Modern/shared API | MODERN ACTIVE | Uses shared config save. |
| `modern_admin/settings_capture.html` | Modern capture settings | `base.html` | `_shell_header.html` | none | `/modern-admin/settings/capture` | `modern-admin.css` | Modern | MODERN ACTIVE | Notes global fallback in multicamera. |
| `modern_admin/media_list.html` | Modern media | `base.html` | `_shell_header.html` | none | `/modern-admin/media/*` | `modern-admin.css`, fetch page URL | Modern | MODERN ACTIVE | Gallery pagination/filter. |
| `modern_admin/safe_controls.html` | Modern safe wrapper | `base.html` | `_shell_header.html` | none | tools/system wrappers | `modern-admin.css`, focus fetch | Modern wrapper | MODERN ACTIVE | Evidence of partial parity, not native port. |
| `modern_admin/placeholder.html` | Modern placeholder | `base.html` | `_shell_header.html` | none | `/modern-admin/classic/*` | `modern-admin.css` | Modern transitional | NEEDS VERIFICATION | Transitional only. |

## 5. JavaScript Evidence Matrix

| JS file/source | Path | Loaded by template | Endpoint calls | Dependencies | Classic/Modern/Shared | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| jQuery | `static/js/jquery-3.7.1.min.js` | `base.html`, `login.html` | n/a | Bootstrap/legacy inline JS | Shared | SHARED ACTIVE | Modern inherits `base.html`; removal blocked. |
| Bootstrap bundle | `static/bootstrap/bootstrap.bundle.min.js` | `base.html`, `login.html` | n/a | Bootstrap CSS | Shared | SHARED ACTIVE | Used by base/login. |
| Classic tabs | `static/js/indi-allsky-tabs.js` | `base.html` | n/a | jQuery | Classic/shared | SHARED ACTIVE | Modern inherits base, needs verification before removal. |
| Chart.js | `static/js/chart.umd.js` | `focus.html`, `chart.html`, `modern_admin/charts.html`, Modern dashboard patterns | `/js/focus`, `/js/charts` through inline scripts | Chart.js | Shared | SHARED ACTIVE | Used by both worlds. |
| Clipboard | `static/js/clipboard.min.js` | `support_info.html`, `view_image.html`, `watch_video.html`, `camera_simulator.html` | n/a | clipboard lib | Classic/shared | LEGACY ACTIVE | Modern support may use simpler links but Classic active. |
| DataTables min JS | `static/DataTables/datatables.min.js` | `config_list.html`, `adu.html`, `filespaceusage.html`, `taskqueue.html`, `users.html`, `generate.html`, `drive_manager.html`, `cameras.html`, `darks.html`, `notifications.html` | inline DataTables | jQuery | Classic | LEGACY ACTIVE | Removal candidate only after table parity. |
| DataTables non-min JS | `static/DataTables/datatables.js` | NO REFERENCES FOUND | none | n/a | vendor | NO REFERENCES FOUND | Candidate after vendor policy check. |
| PhotoSwipe UMD | `static/photoswipe/dist/umd/*.js` | `gallery.html` | gallery internals | PhotoSwipe | Classic | LEGACY ACTIVE | Modern gallery does not use it. |
| PhotoSwipe ESM | `static/photoswipe/dist/photoswipe.esm*.js` | NO REFERENCES FOUND | none | n/a | vendor | NO REFERENCES FOUND | REMOVAL CANDIDATE - NOT NOW; verify package policy. |
| VirtualSky | `static/virtualsky/virtualsky.min.js`, `stuquery.min.js` | `virtualsky.html` | vendor internal XHR | VirtualSky | Shared | SHARED ACTIVE | Modern wraps VirtualSky. |
| html2canvas | `static/html2canvas/html2canvas.min.js` | `virtualsky.html` | none | screenshot/export | Shared | SHARED ACTIVE | Used in Classic VirtualSky; Modern wrapper may inherit. |
| Modern inline header JS | `modern_admin/_shell_header.html` | included by Modern pages | `/modern-admin/capture/service`, quick action URL | fetch | Modern | MODERN ACTIVE | Evidence lines `_shell_header.html:107,135,174`. |
| Modern full settings inline JS | `modern_admin/settings_full.html` | full settings | `/ajax/config` | fetch | Modern/shared API | MODERN ACTIVE | Evidence `settings_full.html:154,251`. |
| Modern media inline JS | `modern_admin/media_list.html` | media pages | page URL self endpoint | fetch | Modern | MODERN ACTIVE | Evidence `media_list.html:320,396`. |
| Classic config inline JS | `config.html` | `/config` | `/ajax/config` | jQuery/AJAX | Classic/shared API | SHARED ACTIVE | Evidence `config.html:10635`. |
| Classic network inline JS | `network.html` | `/network` | `/ajax/network` | jQuery/AJAX | Classic/shared wrapper | SHARED ACTIVE | Multiple AJAX calls in template. |

## 6. CSS Evidence Matrix

| CSS file | Path | Loaded by template | Classic/Modern/Shared | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| Classic style | `static/css/style.css` | `base.html`, `login.html` | Shared through base | SHARED ACTIVE | Cannot remove while Modern extends `base.html`. |
| Modern style | `static/modern_admin/modern-admin.css` | nearly all `modern_admin/*.html` | Modern | MODERN ACTIVE | Canonical Modern CSS. |
| Bootstrap | `static/bootstrap/bootstrap.min.css` | `base.html`, `login.html` | Shared | SHARED ACTIVE | Base dependency. |
| DataTables min CSS | `static/DataTables/datatables.min.css` | Classic table templates | Classic | LEGACY ACTIVE | Remove only after DataTables pages ported. |
| DataTables non-min CSS | `static/DataTables/datatables.css` | NO REFERENCES FOUND | vendor | NO REFERENCES FOUND | Candidate after vendor policy check. |
| PhotoSwipe CSS | `static/photoswipe/dist/photoswipe.css` | `gallery.html` | Classic | LEGACY ACTIVE | Remove only after Classic gallery removal. |
| Astropanel CSS | `static/astropanel/css/style.css` | `astropanel.html` | Shared | SHARED ACTIVE | Modern wrapper exists. |
| QUnit/highlight CSS | `static/virtualsky/extra/*.css` | NO REFERENCES FOUND | vendor extra | NO REFERENCES FOUND | Likely vendor examples; verify before cleanup. |

## 7. API Evidence Matrix

| Endpoint API | File Python | Function | HTTP method | Consumer JS/template | Data returned/action | Equivalent/duplicate | Classic/Modern/Shared | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `/ajax/config` | `views.py:20209` | `AjaxConfigView` | likely POST | `config.html:10635`, `settings_full.html:251` | save config | Modern full settings uses same endpoint | Shared | SHARED ACTIVE | Critical. |
| `/js/charts` | `views.py:20163` | `JsonChartView` | GET | `chart.html:897`, `modern_admin/charts.html:87` | chart data | Modern dashboard has separate metadata analytics | Shared | SHARED ACTIVE | Keep until API split. |
| `/js/log` | `views.py:20272` | `JsonLogView` | GET | `log.html:80`, `modern_admin/log.html:48` | log data | duplicate page only | Shared | SHARED ACTIVE | Keep. |
| `/js/focus` | `views.py:20265` | `JsonFocusView` | GET | `focus.html:122`, `safe_controls.html:135` | focus chart data | safe control wrapper | Shared | SHARED ACTIVE | Keep. |
| `/ajax/generate` | `views.py:20203` | `AjaxTimelapseGeneratorView` | POST | `generate.html:194` | queue generation task | Modern safe generate wrapper | Shared | SHARED ACTIVE | Keep until native Modern generation. |
| `/ajax/imageviewer` | `views.py:20166` | `AjaxImageViewerView` | unknown | `imageviewer.html` | image rows/actions | Modern media list partial | Classic | LEGACY ACTIVE | Candidate after parity. |
| `/ajax/gallery` | `views.py:20174` | `AjaxGalleryViewerView` | unknown | `gallery.html` | gallery rows | Modern media page route | Classic | DUPLICATED | Future convergence to Modern media API. |
| `/ajax/videoviewer` | `views.py:20177` | `AjaxVideoViewerView` | unknown | `videoviewer.html:497,558` | video rows | Modern timelapse list | Classic | DUPLICATED | Needs feature comparison. |
| `/ajax/minivideoviewer` | `views.py:20180` | `AjaxMiniVideoViewerView` | unknown | `minivideoviewer.html:311,351` | mini video rows | Modern mini timelapse list | Classic | DUPLICATED | Needs feature comparison. |
| `/ajax/network` | `views.py:20305` | `AjaxNetworkManagerView` | POST/action | `network.html` multiple calls | network actions | Modern safe wrapper | Shared | SHARED ACTIVE | High risk. |
| `/ajax/drives` | `views.py:20308` | `AjaxDriveManagerView` | POST/action | `drive_manager.html` | drive actions | Modern safe wrapper | Shared | SHARED ACTIVE | High risk. |
| `/ajax/manual_gpio` | `views.py:20269` | `AjaxManualGpioView` | POST/action | `manual_gpio.html:140` | GPIO action | Modern safe wrapper | Shared | SHARED ACTIVE | High risk. |
| `/ajax/uploadyoutube` | `views.py:20314` | `AjaxUploadYoutubeView` | POST | `videoviewer.html:613`, `minivideoviewer.html:405` | upload video | no Modern native | Classic | LEGACY ACTIVE | Port if YouTube kept. |
| `/sync/v1/*` | `syncapi_views.py:816-827` | Sync API views | GET/POST/PUT/DELETE | external/unknown | sync CRUD | no UI duplicate | External/shared | SHARED ACTIVE | Not UI cleanup. |
| `/action/pause`, `/action/unpause` | `actionapi_views.py:155-156` | action views | POST | external/unknown | pause/unpause | Modern capture action separate | External/shared | SHARED ACTIVE | Keep. |

## 8. Configuration Evidence Matrix

| Config key/group | Definition | Backend reads | Backend writes | UI exposes | Profile/camera aware | Modern equivalent | Status | Future proposal |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `MULTI_CAMERA`, `MULTI_CAMERA_CAPTURE_ENABLE` | `indi_allsky/config.py`, `views.py` config save | `allsky.py:100+`, `capture_profiles.py`, Modern views | Modern camera toggle/settings | Modern Cameras/Camera Settings | yes | Camera Profiles | KEEP | Basic/Advanced profile-first. |
| `CCD_EXPOSURE_*` | `config.py:79-83`, `forms.py:4353-4357` | `capture_profiles.py:599-603`, camera/capture runtime | `AjaxConfigView` lines `3314-3318` | Classic config, Modern Full/Capture | fallback only in profile mode | profile exposure limits | MOVE TO CAMERA PROFILE | Keep as Legacy fallback/Developer. |
| `TARGET_ADU*` | `config.py:157-160`, `forms.py` validators | `capture_profiles.py:616-644`, controllers | `views.py:3374-3377` | Classic/Modern Full and profile Camera Settings | yes via profile resolver | profile `target_adu` | MOVE TO CAMERA PROFILE | Basic/Advanced per profile. |
| `AUTO_EXPOSURE_*` | config/resolver | `capture_profiles.py:347-383` and controllers | Modern profile settings | Camera Settings/Full | yes | profile `auto_exposure` | MOVE TO CAMERA PROFILE | Basic/Advanced per profile. |
| `AUTO_GAIN_*` | config/resolver | `capture_profiles.py:425+`, controllers | Modern profile settings | Camera Settings/Full | yes | profile `gain`/`auto_gain` | MOVE TO CAMERA PROFILE | Advanced/Developer depending field. |
| `CFA_PATTERN`, `CCD_BIT_DEPTH`, WB | `forms.py:4358,4370+`, profile processing | `capture_profiles.py` processing resolver | Camera Settings | Camera Settings/Full | yes | profile `processing` | MOVE TO CAMERA PROFILE | Hardware-specific, non-syncable. |
| `IMAGE_SAVE_FITS*` | `config.py:359-362`, `forms.py:4515,4566-4568` | `image.py`, `capture_profiles.py`, metadata linking | `/ajax/config` and Modern Full | Classic/Modern Full | currently global; scheduling profile-aware | Scientific Source UX planned | NEEDS MIGRATION | Redesign as Scientific Source mode. |
| `IMAGE_EXPORT_RAW` | `config.py:363`, `forms.py:3653,1458` | image export and metadata linking | `/ajax/config` | Classic/Modern Full | global | Scientific Source UX planned | NEEDS MIGRATION | Advanced source persistence. |
| `FRAME_METADATA_PATH`, rotation | config/runtime | `frame_metadata.py`, Modern dashboard context | Full settings | Modern dashboard uses result | global | Metadata/Analytics | KEEP | Storage/Developer placement. |
| `EVENT_CANDIDATE_TRIGGERS` | `config.py:272`, `forms.py:267`, `views.py:3386-3387` | image shadow integration/dashboard | `/ajax/config` | Modern Full | global shadow | Event Foundation controls | DEVELOPER | Keep disabled default. |
| `TIMELAPSE_ENABLE`, `DAYTIME_TIMELAPSE`, `TIMELAPSE.*` | `config.py:177-190`, `forms.py:4442-4454` | `capture_profiles.py:195-200`, allsky/video | `/ajax/config` | Classic/Modern Full; media pages | partially profile-output aware | Media Products | ADVANCED | Modern product settings needed. |
| `REALTIME_KEOGRAM`, `LONGTERM_KEOGRAM` | `config.py:228-236`, forms | keogram views/tasks | `/ajax/config` | Classic/Modern observatory | mostly global | Observatory products | ADVANCED | Keep but clarify. |
| `STARTRAILS_*` | `config.py:241-252`, forms | startrail generation | `/ajax/config` | Classic/Modern Full/media | partially camera scoped by output | Media Products | ADVANCED | Needs Modern product parity. |
| `IMAGE_STRETCH`, `IMAGE_CIRCLE_MASK` | config/forms, `views.py:3232-3236,3420-3432` | image processing/rendering | `/ajax/config`, Camera Settings partial | Classic/Modern Full/Camera Settings | partial | Display Rendering | NEEDS MIGRATION | Separate display from source. |
| `FILETRANSFER`, `S3UPLOAD`, `SYNCAPI`, `YOUTUBE` | `config.py:461+`, forms, uploader | `uploader.py:257+`, sync views | `/ajax/config`, OAuth routes | Classic/Modern Full, uploads placeholder | mostly global | Uploads/Reporting | NEEDS VERIFICATION | Redesign provider-based UI. |
| `DETECT_METEORS`, `DETECT_METEORS_THOLD` | `detectLines.py:38`, `views.py:3382-3383` | legacy line detection | `/ajax/config` | Classic/Modern Full | no | none | LEGACY ONLY | Developer only; not real meteor detector. |
| hooks `IMAGE_SAVE_HOOK_*`, `CAPTURE_HOOK_*` | forms/config | runtime hooks | `/ajax/config` | Classic/Modern Full | global | Developer | DEVELOPER | Dangerous to remove. |

## 9. Classic to Modern Coverage Matrix

| Classic route/template | Function | Modern equivalent | Coverage | Missing blocks | Prerequisites before removal | Priority |
| --- | --- | --- | --- | --- | --- | --- |
| `/config` / `config.html` | full config | `/modern-admin/settings/full`, `/settings/cameras`, `/settings/capture` | 80% | Basic/Advanced/Developer redesign; config history/restore parity | Settings architecture, migration labels | High |
| `/gallery` / `gallery.html` | image gallery | `/modern-admin/media/gallery` | 80% | advanced viewer/actions comparison | Usage logging, feature comparison | Medium |
| `/imageviewer` | image browser/exclude | Modern media list | 50% | exclude/actions/detail parity | Native Modern media actions | Medium |
| `/fitsimageviewer` | FITS viewer/conversion | Modern FITS media list | 50% | conversion/review/scientific source details | Scientific Source UX | High |
| `/videoviewer` | video/timelapse viewer/upload | Modern timelapse list | 50% | YouTube/upload and full action parity | Native media/product page | Medium |
| `/generate` | manual generation | Modern safe control | 50% | native Modern controls | Product settings/generation UI | High |
| `/focus` | focus controller | Modern safe control | 50% | native tool parity | decide keep/port/drop | Medium |
| `/network`, `/drives`, `/manual_gpio` | system controls | Modern safe controls | 50% | native safe UX | route usage and safety review | Medium |
| `/tasks` | task queue | none | 0% | full page | Modern task queue | High |
| `/users`, `/user` | user/admin | none | 0% | auth/user management | Modern user/admin pages | High |
| `/notifications` | notifications | none | 0% | notification management | Modern notification page | Medium |
| `/youtube/*` | YouTube OAuth/upload | none | 0% | OAuth flow in Modern | Upload/reporting redesign | Medium |
| public `/`, `/loop`, `/latest*` | public display/redirects | not equivalent | UNKNOWN | public page strategy | public compatibility policy | High |

## 10. Orphan Candidate Matrix

| File/item | Type | Why it seems orphaned | Search performed | Risk | Action recommended |
| --- | --- | --- | --- | --- | --- |
| `static/DataTables/datatables.js` | JS vendor | min version referenced, non-min not referenced | asset rg for filename | Low | REMOVAL CANDIDATE - NOT NOW; verify vendor policy. |
| `static/DataTables/datatables.css` | CSS vendor | min CSS referenced, non-min not referenced | asset rg for filename | Low | REMOVAL CANDIDATE - NOT NOW. |
| `static/photoswipe/dist/photoswipe.esm*.js` | JS vendor | Classic gallery references UMD, not ESM | asset rg for filename | Low | REMOVAL CANDIDATE - NOT NOW after package policy. |
| `static/photoswipe/dist/*map` | source map | no template references found | asset rg | Low | Keep until asset policy decided. |
| `static/virtualsky/extra/*` | vendor examples | no template references found | asset rg | Low | REMOVAL CANDIDATE - NOT NOW. |
| `modern_admin/placeholder.html` | template | transitional route only | route/template rg | Low | Keep until Classic mode removal. |
| `/ajax/selectcamera` | API | no direct template consumer found in current search output | route/API rg | Medium | NEEDS VERIFICATION with route usage logs. |

## 11. Duplication Matrix

| Duplicated functionality | Classic route/API | Modern route/API | Config duplicated | JS duplicated | Differences | Canonical future | Strategy |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Full settings | `/config`, `/ajax/config` | `/modern-admin/settings/full`, `/ajax/config` | many global fields | Classic inline vs Modern fetch | same backend, different UX | Modern settings | keep shared API until redesign. |
| Camera configuration | `/camera`, global config | `/modern-admin/cameras`, `/settings/cameras` | global vs profile | different templates | Modern profile-first | Modern Camera Settings | migrate operational settings to profiles. |
| Gallery/media | `/gallery`, `/ajax/gallery` | `/modern-admin/media/gallery/page` | n/a | PhotoSwipe vs custom fetch | Modern profile filter | Modern media | compare actions, then deprecate Classic. |
| Charts | `/charts`, `/js/charts` | `/modern-admin/observatory/charts`, dashboard | chart labels | Chart.js both | Modern subset plus dashboard analytics | Modern analytics API | split shared API later. |
| Logs/support/system | `/log`, `/support`, `/system` | `/modern-admin/system/*` | n/a | classic loadJS vs Modern fetch/wrapper | Modern wraps legacy | Modern native pages | port native before removal. |
| Tool controls | `/focus`, `/processing`, `/manual_gpio`, `/network`, `/drives` | `/modern-admin/tools/*`, safe controls | tool configs | legacy inline | Modern wrapper only | TBD | decide keep as safe controls or native port. |
| Product generation | `/generate`, `/minigenerate` | `/modern-admin/tools/generate` | timelapse settings | legacy inline | mini generation missing | Modern product UI | port base generation first. |

## 12. Updated Simplification Plan

### Phase 0 - Audit complete

Verified:

- Classic and Modern routes coexist in `views.py`.
- Modern Admin is active and broad.
- Modern uses native pages plus wrappers plus safe controls.
- Several Classic endpoints are shared by Modern wrappers.
- Config save endpoint `/ajax/config` is shared.

### Phase 0.5 - Evidence complete

Still uncertain:

- actual runtime/user traffic on Classic routes;
- external scripts using `/ajax/*`, `/latest*`, `/sync/v1/*`, `/action/*`;
- exact feature parity of media viewers and generation tools;
- field-by-field config orphan status;
- whether non-min/vendor assets are intentionally retained for debugging.

### Phase 1 - Safe instrumentation / mapping

Create a route/template/API inventory command or test that emits machine-readable
classification:

- Classic page;
- Modern native;
- Modern wrapper;
- shared API;
- external API;
- public compatibility route;
- unknown.

No removals.

### Phase 2 - Complete Modern parity

Recommended order:

1. Task queue.
2. User/current user/admin users.
3. Notifications.
4. FITS/scientific source viewer/report surface.
5. Generation tools for timelapse/keogram/startrail.
6. Upload/YouTube/reporting surfaces.
7. Network/drives/GPIO/focus/process-FITS native or intentionally retained
   wrappers.

### Phase 3 - Settings redesign

Move from raw key-first config to:

- Basic: daily operation, profile-first acquisition, source mode, display basics.
- Advanced: product generation, CFA/WB, scientific source details, uploads.
- Developer: raw config, legacy fallback, hooks, Event Candidate triggers,
  legacy line detection.

### Phase 4 - Legacy deprecation

- Add non-functional warnings on Classic pages.
- Link each Classic page to its Modern equivalent.
- Add route usage diagnostics.
- Keep fallbacks and redirects.

### Phase 5 - Legacy removal

Remove by blocks only after parity and observed-safe usage:

1. duplicated media pages;
2. duplicated chart/log/support pages;
3. duplicated config sections;
4. safe-controls tools if replaced;
5. final Classic base and assets.

### Phase 6 - Cleanup

- Delete unused templates.
- Delete unused CSS/JS/vendor extras.
- Split shared APIs into stable Modern API namespaces.
- Retire legacy-only config keys only after migration.

## 13. First Safe Micro-Step

Implement a documentation-generating route inventory script/test.

Requirements:

- no UI behavior change;
- no route removal;
- no config change;
- read Flask route registrations and view/template metadata;
- output Markdown or JSON with route, endpoint, view class, template, family and
  status;
- fail only on broken introspection, not on unknown migration status.

Why this is first:

- It converts this manual evidence matrix into a repeatable safety net.
- It prevents accidental removal of shared endpoints used by Modern wrappers.
- It gives a baseline before adding deprecation warnings.

## 14. Final Answers

### 1. Quali parti dell'audit iniziale sono confermate dalle evidenze?

- Modern Admin is active and central: `/modern-admin*` routes and templates are
  registered and broad.
- Classic UI is still active: many Classic routes render templates directly.
- Modern parity is partial: many Modern classes inherit legacy views or use
  `ModernAdminSafeControlsMixin`.
- Shared endpoints are real: `/ajax/config`, `/js/charts`, `/js/log`,
  `/js/focus` and several system APIs are consumed by Modern or wrappers.
- Settings are duplicated: global config remains exposed while profile-first
  Camera Settings exist.

### 2. Quali parti sono incerte?

- Real external usage of Classic URLs.
- Full parity of Modern media/generation/viewer tools.
- Whether `DataTables`/PhotoSwipe non-used variants are intentionally retained.
- Exact unused config keys across all hundreds of form fields.
- Whether `/ajax/selectcamera` has indirect consumers.

### 3. Quanto manca realisticamente per eliminare Classic UI?

Classic cannot be removed yet. The architecture is Modern-first, but operational
parity is incomplete. The largest blockers are task queue, user/admin,
notifications, FITS/media viewer parity, generation tools, upload/YouTube, and
system tools currently wrapped by safe controls.

### 4. Quale porting ha priorita' massima?

Task queue and user/admin/notification parity are the highest priority because
they are admin-operational surfaces with no clear Modern native replacement.
FITS/scientific source viewer/report UX is also high priority because it blocks
future detector work clarity.

### 5. Quali route/template/API sono i candidati piu' probabili alla futura rimozione?

Only after parity:

- `/gallery`, `gallery.html`, PhotoSwipe UMD.
- `/videoviewer`, `/minivideoviewer`, video viewer templates.
- Classic table pages using DataTables after Modern replacements.
- `/config` and `config.html` after Basic/Advanced/Developer settings.
- Classic wrappers for system/tool pages after native Modern parity or explicit
  retention decision.

### 6. Quali config devono diventare profile-first o camera-profile-first?

- `CCD_EXPOSURE_*`
- global `TARGET_ADU*`
- `AUTO_EXPOSURE_*`
- `AUTO_GAIN_*`
- CFA/Debayer/WB/bit depth fields
- camera-specific display/source persistence policy where appropriate

Global versions should remain Developer/Legacy fallback until migrations are
safe.

### 7. Quale deve essere il prossimo micro-step?

Create the route/template/API inventory script or test. It is small,
reversible, verification-oriented, and prepares every later deprecation/removal
step without changing behavior.

