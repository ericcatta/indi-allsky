# Modern Admin V1

## Files involved

- `indi_allsky/flask/views.py` registers the authenticated route.
- `indi_allsky/flask/templates/modern_admin/index.html` contains the modern admin page markup.
- `indi_allsky/flask/static/modern_admin/modern-admin.css` contains isolated modern admin styling.

## Prototype port update

The approved static prototype from `allsky-hybrid/prototype/admin-dashboard-v0` has been ported into the real Flask template.

## Route added

The new route is registered on the existing `indi_allsky` Flask blueprint:

```text
/modern-admin
```

Because that blueprint uses the `/indi-allsky` URL prefix, the browser path is:

```text
/indi-allsky/modern-admin
```

## Template added

The route renders:

```text
indi_allsky/flask/templates/modern_admin/index.html
```

The template extends the existing `base.html`, defines the `camera_id` JavaScript variable expected by the inherited shell, and links back to the classic admin dashboard.

The visual dashboard prototype from `allsky-hybrid/prototype/admin-dashboard-v0` has been ported into this template:

- large latest image hero, now backed by the current latest image when one is available;
- camera, capture, storage, and upload/sync status cards;
- recent warnings and activity panels;
- always-visible links back to the classic admin UI;
- responsive single-column mobile layout.

The prototype's remote image was replaced with either the current latest image or a CSS-only placeholder sky frame. No binary assets or external media were added.

## Data source

The modern admin route uses `ModernAdminView`, which inherits from `TemplateView`.

`TemplateView` already selects the active camera from the session, calls `cameraSetup()`, and queries `self.latest_image_entry` from `IndiAllSkyDbImageTable` for the selected camera. `ModernAdminView.get_context()` reuses that existing entry and the model's `getUrl()` helper to populate:

- `latest_image_url`
- `latest_image_updated`
- `latest_image_status`

This keeps the first data connection server-rendered and avoids adding a new API.

## Limitations

- Only the hero image and last-update text are connected to real data.
- The camera, capture, storage, upload/sync, and recent event sections still use placeholder content.
- The latest image query is inherited from `TemplateView` and only considers recent images in its existing freshness window.
- If no recent image URL can be resolved, the CSS-only placeholder remains visible.

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

Confirm that the modern admin page renders the latest image when one is available, falls back to the CSS placeholder otherwise, and that the classic admin link opens the existing config page.

## Future work

- Replace remaining placeholder values with read-only dashboard data.
- Add explicit read-only fields for camera state, capture freshness, storage, upload/sync, and recent events.
- Keep all write actions out of the initial modern admin page.
- Keep modern admin CSS/JS isolated under `indi_allsky/flask/static/modern_admin/`.
- Decide later whether to expose the route in classic navigation.
- Add any future mutating endpoints separately with admin checks, CSRF, and admin-network checks where existing comparable actions require them.
