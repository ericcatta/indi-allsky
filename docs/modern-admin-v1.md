# Modern Admin V1

## Files involved

- `indi_allsky/flask/views.py` registers the authenticated route.
- `indi_allsky/flask/templates/modern_admin/index.html` contains the modern admin page markup.
- `indi_allsky/flask/templates/modern_admin/cameras.html` contains the read-only camera management page.
- `indi_allsky/flask/templates/modern_admin/_shell_header.html` contains the shared modern admin header, navigation, mode switch, and classic fallback link.
- `indi_allsky/flask/static/modern_admin/modern-admin.css` contains isolated modern admin styling.
- `docs/modern-admin-information-architecture.md` defines the future product navigation structure used by the modern shell.

## Prototype port update

The approved static prototype from `allsky-hybrid/prototype/admin-dashboard-v0` has been ported into the real Flask template.

## Route added

The new route is registered on the existing `indi_allsky` Flask blueprint:

```text
/modern-admin
/modern-admin/cameras
/modern-admin/mode/<mode>
```

Because that blueprint uses the `/indi-allsky` URL prefix, the browser path is:

```text
/indi-allsky/modern-admin
/indi-allsky/modern-admin/cameras
/indi-allsky/modern-admin/mode/modern
/indi-allsky/modern-admin/mode/classic
```

`/modern-admin/mode/<mode>` is an authenticated redirect-only helper. It stores the preferred admin mode in the Flask session:

- `modern` redirects to `/indi-allsky/modern-admin`
- `classic` redirects to the existing classic config/admin route

No classic admin route behavior is changed.

## Template added

The route renders:

```text
indi_allsky/flask/templates/modern_admin/index.html
indi_allsky/flask/templates/modern_admin/cameras.html
```

Both templates extend the existing `base.html`, define the `camera_id` JavaScript variable expected by the inherited shell, and link back to the classic admin dashboard.

Both templates include `modern_admin/_shell_header.html`, which provides:

- a visible Modern / Classic switch;
- a modern navigation shell for Dashboard, Cameras, Storage, Uploads, Observatory, System, and Updates;
- enabled links for Dashboard and Cameras;
- disabled placeholder links for sections that do not have modern routes yet;
- an always-visible "Open Classic Admin" fallback link.

The navigation structure follows `docs/modern-admin-information-architecture.md`.

The header was refined from the first large control treatment into a calmer product shell inspired by the approved mockup:

- the Modern / Classic control is a compact segmented switch;
- Dashboard and Cameras are emphasized as application navigation rather than secondary buttons;
- the header uses a subtle app-frame treatment so the latest image remains the primary visual focus;
- duplicated classic-admin navigation is reduced while keeping an always-visible fallback link.

The visual dashboard prototype from `allsky-hybrid/prototype/admin-dashboard-v0` has been ported into this template:

- large latest image hero, now backed by the current latest image when one is available;
- real camera identity and capture status fields;
- real storage capacity, used/free space, and percentage used;
- placeholder upload/sync status card;
- recent warnings and activity panels;
- always-visible links back to the classic admin UI;
- responsive single-column mobile layout.

The prototype's remote image was replaced with either the current latest image or a CSS-only placeholder sky frame. No binary assets or external media were added.

## Data source

The modern admin route uses `ModernAdminView`, which inherits from `TemplateView`.

`TemplateView` already selects the active camera from the session, calls `cameraSetup()`, and queries `self.latest_image_entry` from `IndiAllSkyDbImageTable` for the selected camera. `ModernAdminView.get_context()` reuses that existing entry and the model's `getUrl()` helper to populate:

- `latest_image_url`
- `latest_image_updated`
- `latest_image_age`
- `latest_image_status`

The camera card uses the selected camera from `TemplateView.cameraSetup()`:

- `camera.friendlyName` or `camera.name` for the display name
- `camera.driver` as the model/driver label when available

The camera card links to `/indi-allsky/modern-admin/cameras`, a read-only future camera-management entry point. The camera page uses existing `IndiAllSkyDbCameraTable` rows for the available camera list and existing `IndiAllSkyDbImageTable` latest-image rows for per-camera last image age.

The capture card uses the existing `get_indi_allsky_status()` status source and normalizes its current state into:

- `Running`
- `Idle`
- `Paused`
- `Unknown`

The storage card uses the configured Flask image folder from `INDI_ALLSKY_IMAGE_FOLDER`, resolves to the nearest existing filesystem path, and reads capacity with `psutil.disk_usage()`. This matches the existing system-info style of filesystem usage collection and avoids adding a new API or background scan.

This keeps the first data connection server-rendered and avoids adding a new API.

The Modern / Classic mode switch uses the existing Flask session. Visiting a modern admin page sets `session['admin_mode']` to `modern`; choosing Classic sets it to `classic` and redirects to the existing classic admin route. This is only a navigation preference and does not change capture, configuration, or classic admin behavior.

## Limitations

- The hero image, image age, camera identity, capture status, and image-filesystem storage usage are connected to real data.
- The camera management page lists configured non-hidden cameras when existing camera rows are available.
- Upload/sync and recent event sections still use placeholder content.
- The camera management page includes a placeholder-only "Add Camera" area; no add, edit, or delete actions exist yet.
- Camera model is represented by the camera driver because there is no dedicated model field in the camera table.
- Storage reports filesystem capacity for the configured image folder, not per-camera media totals.
- If the configured image folder does not exist locally, the route measures the nearest existing parent path.
- The latest image query is inherited from `TemplateView` and only considers recent images in its existing freshness window.
- If no recent image URL can be resolved, the CSS-only placeholder remains visible.
- The modern navigation shell only has real modern routes for Dashboard and Cameras. Storage, Uploads, Observatory, System, and Updates are disabled placeholders until their read-only pages are designed.
- The admin mode preference is session-scoped. It is not a user profile setting and may reset when the Flask session changes.

## Static assets

Modern admin CSS is isolated under:

```text
indi_allsky/flask/static/modern_admin/modern-admin.css
```

No classic admin templates or shared classic CSS files are changed by the modern admin styling.

## How to access it

Open:

```text
http://<host>:<port>/indi-allsky/modern-admin
http://<host>:<port>/indi-allsky/modern-admin/cameras
```

The route requires an authenticated Flask-Login session through `login_required`. Unauthenticated users should be redirected through the existing login flow.

## How to test

Run:

```text
python3 -m py_compile indi_allsky/flask/views.py
git diff --check
```

Then start the existing application normally, sign in, and open:

```text
http://<host>:<port>/indi-allsky/modern-admin
```

Confirm that the modern admin page renders the latest image when one is available, shows image age, camera identity, capture status, and storage usage, links the Camera card to the read-only camera management page, falls back to the CSS placeholder otherwise, and that the classic admin link opens the existing config page.

Also confirm:

- Dashboard in the modern navigation opens `/indi-allsky/modern-admin`.
- Cameras opens `/indi-allsky/modern-admin/cameras`.
- Storage, Uploads, Observatory, System, and Updates are visibly present but disabled.
- Modern mode redirects to `/indi-allsky/modern-admin`.
- Classic mode redirects to the existing classic admin/config page.

## Future work

- Replace remaining placeholder values with read-only dashboard data.
- Design the add/edit/delete camera flows before implementing any write actions.
- Add explicit read-only fields for storage, upload/sync, and recent events.
- Consider adding per-camera media totals from the existing file-space usage queries alongside filesystem capacity.
- Add storage thresholds and clearer normal/warning/critical labels.
- Keep all write actions out of the initial modern admin page.
- Keep modern admin CSS/JS isolated under `indi_allsky/flask/static/modern_admin/`.
- Decide later whether to expose the route in classic navigation.
- Add dedicated read-only modern pages for Storage, Uploads, Observatory, System, and Updates following `docs/modern-admin-information-architecture.md`.
- Add any future mutating endpoints separately with admin checks, CSRF, and admin-network checks where existing comparable actions require them.
