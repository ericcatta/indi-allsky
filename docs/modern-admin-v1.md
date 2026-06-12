# Modern Admin V1

## Files changed

- `indi_allsky/flask/views.py`

## Files added

- `indi_allsky/flask/templates/modern_admin/index.html`
- `docs/modern-admin-v1.md`

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

## How to access it

Open:

```text
http://<host>:<port>/indi-allsky/modern-admin
```

The route requires an authenticated Flask-Login session through `login_required`. Unauthenticated users should be redirected through the existing login flow.

## Future work

- Add read-only dashboard cards.
- Keep all write actions out of the initial modern admin page.
- Add isolated modern admin CSS/JS under `indi_allsky/flask/static/modern_admin/` if needed.
- Decide later whether to expose the route in classic navigation.
- Add any future mutating endpoints separately with admin checks, CSRF, and admin-network checks where existing comparable actions require them.
