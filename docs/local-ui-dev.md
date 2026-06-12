# Local UI Development on macOS

This note describes the easiest realistic way to run this fork locally for UI development only. It does not require the capture service, INDI server, real camera hardware, upload workers, or systemd timers, but it still needs enough of the Flask app configuration and database schema to let templates render.

No install commands are included here.

## 1. Current project runtime architecture

indi-allsky has two broad runtime halves:

- Capture/runtime services: camera access, image acquisition, image processing, file generation, uploads, sensors, system service controls, and task processing.
- Web UI: a Flask application served under the `indi_allsky` blueprint at `/indi-allsky`.

The Flask app is created by `indi_allsky/flask/__init__.py:create_app()`.

Important web app expectations:

- It reads `INDI_ALLSKY_FLASK_CONFIG`, defaulting to `/etc/indi-allsky/flask.json`.
- It needs `SQLALCHEMY_DATABASE_URI`.
- It needs `MIGRATION_FOLDER`.
- It initializes Flask-Login, Flask-WTF CSRF, SQLAlchemy, and Flask-Migrate.
- The main UI blueprint is registered with `url_prefix='/indi-allsky'`.
- Static assets are served from `indi_allsky/flask/static`.
- Templates are loaded from `indi_allsky/flask/templates`.

The modern admin route is currently:

```text
/indi-allsky/modern-admin
```

It is a normal authenticated Flask page using the existing app/session/database setup.

## 2. What services are required

For UI development only, the minimum runtime service is:

- Flask web app process.

The web app still expects these local resources:

- A valid Flask JSON config file.
- A database with the current schema, SQLite being the simplest local target.
- A migrations directory path in config.
- An image root path in config.
- Python dependencies already available in the active environment.

Not required for visual UI iteration:

- Real camera hardware.
- INDI server.
- Capture daemon.
- Upload/sync workers.
- MQTT broker.
- Apache or NGINX reverse proxy.
- systemd services/timers.
- Sensor hardware.

Apache/NGINX/Gunicorn are production deployment pieces. For local UI work, a direct Flask development server or direct Gunicorn process is enough, assuming the Python environment already has the required dependencies.

## 3. What can be stubbed or mocked

For modern-admin UI work, these can be stubbed:

- Camera rows: the app can fall back to `FakeCamera` when no camera exists, as long as the DB schema exists.
- Latest image: if no recent image exists, modern-admin falls back to the CSS-only sky placeholder.
- Capture status: missing watchdog/status state resolves to existing unknown/fallback behavior.
- Storage card: currently placeholder.
- Upload/sync card: currently placeholder.
- Recent events: currently placeholder.

Useful local-only stubs:

- Empty SQLite database with migrated schema.
- One fake camera row, if testing camera identity display.
- One fake image row plus a small local image file, if testing the latest-image hero.
- `LOGIN_DISABLED=true` in a local-only Flask config, if avoiding user/session setup for UI iteration. This should never be used for a real deployment.

## 4. Can modern-admin render without a camera?

Yes, if the Flask app can start and the database schema exists.

`TemplateView.setupSession()` catches the no-camera case and uses `FakeCamera`. The modern admin page can then render with:

- CSS placeholder image;
- fallback camera identity;
- fallback/unknown capture status;
- remaining placeholder cards.

The likely failure mode is not "no camera"; it is missing config, missing dependencies, missing database schema, or an invalid DB path.

## 5. Can modern-admin render with fake data?

Yes.

Fake data can be supplied through the existing database models without creating new APIs:

- Add a camera row to populate camera name/friendly name/driver.
- Add an image row in `IndiAllSkyDbImageTable` for that camera.
- Point the image row at a small local test image under the configured image folder.
- Ensure the image timestamp is recent enough for the inherited latest-image freshness window.

Modern-admin already uses:

- selected camera from `TemplateView.cameraSetup()`;
- `self.latest_image_entry` from the existing latest-image query;
- `IndiAllSkyDbImageTable.getUrl()` for image URL generation;
- existing `get_indi_allsky_status()` state handling.

Without fake DB rows, the page still renders, but the hero image uses the CSS placeholder.

## 6. Smallest local development setup

The smallest practical setup is a web-only SQLite setup:

1. Use an existing Python environment that already has the project dependencies.
2. Create a local Flask config JSON outside production paths, based on `flask.json_template`.
3. Set `INDI_ALLSKY_FLASK_CONFIG` to that local config path.
4. Point `SQLALCHEMY_DATABASE_URI` at a local SQLite file.
5. Point `MIGRATION_FOLDER` at a local writable migrations folder.
6. Point `INDI_ALLSKY_IMAGE_FOLDER` at a local writable image folder.
7. Use a migrated database schema.
8. For fastest local-only iteration, either create a local user or set `LOGIN_DISABLED=true` in the local config.
9. Run only the Flask web app.

Expected local path shape:

```text
tmp/local-ui/
  flask.json
  indi-allsky.sqlite
  migrations/
  images/
```

Expected route:

```text
http://127.0.0.1:<port>/indi-allsky/modern-admin
```

If using normal auth, login first through:

```text
http://127.0.0.1:<port>/indi-allsky/login
```

## 7. Recommended workflow for rapid UI iteration

Recommended workflow:

1. Keep a dedicated local Flask config for UI development.
2. Keep the local DB small and disposable.
3. Use the CSS fallback for layout work.
4. Add one fake camera and one fake latest image only when testing real hero-image rendering.
5. Run the Flask app with template reload enabled.
6. Edit only isolated modern-admin files:

```text
indi_allsky/flask/templates/modern_admin/index.html
indi_allsky/flask/static/modern_admin/modern-admin.css
docs/modern-admin-v1.md
```

7. Avoid changing classic templates or shared static files.
8. Use browser refresh for most template/CSS changes.
9. Restart Flask only when changing Python view code.

This gives fast iteration while keeping classic admin behavior untouched.

## 8. Risks

- macOS dependency friction: modules such as `dbus`, OpenCV, astropy, pycurl, and other Linux-oriented dependencies may be hard to satisfy locally.
- Import-time dependencies: the Flask views import several heavy modules even when only rendering UI.
- Database schema is required; an empty missing SQLite file is not enough unless migrations/schema have been applied.
- Auth can block local UI testing unless a user exists or `LOGIN_DISABLED` is set in a local-only config.
- The app's default config path points at `/etc/indi-allsky/flask.json`, which usually will not exist on macOS.
- Some inherited base-template JavaScript still calls existing status/notification endpoints.
- Some classic pages and system controls assume Linux/systemd behavior; avoid them during macOS UI-only work.
- Using `LOGIN_DISABLED=true` is dangerous outside a private local development environment.
- Fake latest-image rows must match configured image paths and URL behavior.

## Summary

Local UI development is realistic, but only as a web-only Flask setup with a valid local config and database schema. Running the full indi-allsky stack on macOS is not the easiest path because capture, INDI, sensors, system services, and several dependencies are Linux-oriented.

Minimum setup:

- existing working Python dependency environment;
- local Flask config;
- local SQLite DB with schema;
- local image folder;
- either a dev user or local-only `LOGIN_DISABLED=true`;
- Flask web process only.

Blockers:

- missing Python dependencies;
- missing `INDI_ALLSKY_FLASK_CONFIG`;
- missing DB schema;
- missing auth user when login is enabled;
- Linux-specific dependencies or service assumptions when trying to run more than the web UI.
