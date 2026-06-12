# Modern Admin V1

## Files involved

- `indi_allsky/flask/views.py` registers the authenticated route.
- `indi_allsky/flask/templates/modern_admin/index.html` contains the modern admin page markup.
- `indi_allsky/flask/static/modern_admin/modern-admin.css` contains isolated modern admin styling.

## Prototype port update

The approved static prototype from `allsky-hybrid/prototype/admin-dashboard-v0` has been ported into the real Flask template using placeholder-only content.

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

The visual dashboard prototype from `allsky-hybrid/prototype/admin-dashboard-v0` has been ported into this template with placeholder-only content:

- large latest image hero;
- camera, capture, storage, and upload/sync status cards;
- recent warnings and activity panels;
- always-visible links back to the classic admin UI;
- responsive single-column mobile layout.

The prototype's remote image was replaced with a CSS-only placeholder sky frame. No binary assets or external media were added.

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

Confirm that the modern admin page renders with placeholder data and that the classic admin link opens the existing config page.

## Future work

- Replace placeholder values with read-only dashboard data.
- Keep all write actions out of the initial modern admin page.
- Keep modern admin CSS/JS isolated under `indi_allsky/flask/static/modern_admin/`.
- Decide later whether to expose the route in classic navigation.
- Add any future mutating endpoints separately with admin checks, CSRF, and admin-network checks where existing comparable actions require them.
