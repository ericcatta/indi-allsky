# Modern Admin Integration Plan

## 1. Current Flask routing structure

The Flask application is constructed in `indi_allsky/flask/__init__.py`. `create_app()` creates the app, loads the JSON config, initializes CSRF, registers blueprints, initializes the database/migrations, then configures Flask-Login.

Current blueprint registration order:

- `bp_allsky` from `indi_allsky/flask/views.py`
- `bp_auth_allsky` from `indi_allsky/flask/auth_views.py`
- `bp_syncapi_allsky` from `indi_allsky/flask/syncapi_views.py`
- `bp_actionapi_allsky` from `indi_allsky/flask/actionapi_views.py`

The main UI blueprint is `bp_allsky`, defined in `indi_allsky/flask/views.py` with:

- name: `indi_allsky`
- template folder: `templates`
- static folder: `static`
- URL prefix: `/indi-allsky`
- static URL path: `static`

Most classic UI routes are class-based views registered at the bottom of `indi_allsky/flask/views.py` with `bp_allsky.add_url_rule(...)`. For example, the existing page routes include `/`, `/charts`, `/config`, `/system`, `/log`, `/network`, `/drives`, and hidden admin-style routes such as `/cameras`, `/tasks`, `/notifications`, and `/users`.

Because of the blueprint prefix, a new route registered as `/modern-admin` on `bp_allsky` will be served at:

```text
/indi-allsky/modern-admin
```

Adding a separate top-level `/modern-admin` route would require either changing the existing prefix strategy or registering another blueprint. That is not the smallest safe integration point.

## 2. Recommended route location

Register the future page in `indi_allsky/flask/views.py` near the existing authenticated/admin-like page route registrations, preferably near:

- `/config`
- `/system`
- `/log`
- `/cameras`
- `/tasks`
- `/notifications`
- `/users`

Recommended route registration:

```python
bp_allsky.add_url_rule(
    '/modern-admin',
    view_func=ModernAdminView.as_view(
        'modern_admin_view',
        template_name='modern_admin/index.html',
    ),
)
```

This keeps the route inside the current UI blueprint, reuses the existing template/static lookup, keeps classic admin untouched, and avoids modifying app initialization or blueprint registration.

## 3. Recommended view/function/class name

Use a class-based view matching the existing style:

```python
class ModernAdminView(TemplateView):
    decorators = [login_required]
    page_title = 'Modern Admin'
```

If the first page only needs the standard context from `TemplateView`, avoid overriding `dispatch_request()` or `get_context()` initially. If it needs dashboard cards, add a small `get_context()` override that calls `super()` and only reads existing model/config state.

Recommended endpoint name:

```text
modern_admin_view
```

Recommended URL builder:

```python
url_for('indi_allsky.modern_admin_view')
```

## 4. Recommended template location

Use a subdirectory under the existing Flask template folder:

```text
indi_allsky/flask/templates/modern_admin/index.html
```

This avoids crowding the already large flat `templates` directory and creates a clear namespace for future modern admin templates.

The first template can either:

- extend `base.html` to inherit the current login/session/camera/status shell; or
- use a new modern-admin-specific base template, such as `modern_admin/base.html`, while still receiving context from `TemplateView`.

For the smallest first implementation, extend `base.html`. That preserves classic navigation and provides a visible fallback path back to existing pages.

## 5. Recommended static CSS/JS location

Use a namespaced static directory:

```text
indi_allsky/flask/static/modern_admin/css/modern-admin.css
indi_allsky/flask/static/modern_admin/js/modern-admin.js
```

Include these only from the modern admin template with:

```jinja
{% block head %}
<link href="{{ url_for('indi_allsky.static', filename='modern_admin/css/modern-admin.css') }}" rel="stylesheet">
<script src="{{ url_for('indi_allsky.static', filename='modern_admin/js/modern-admin.js') }}" defer></script>
{% endblock %}
```

Do not modify `indi_allsky/flask/static/css/style.css` for the first milestone. Keeping assets isolated reduces the risk of changing classic admin behavior.

## 6. Authentication requirements

Reuse Flask-Login and the existing session behavior.

The safest first route should use:

```python
decorators = [login_required]
```

This matches existing authenticated pages such as config, system, log, network, drives, cameras, tasks, notifications, and users.

Do not make the first read-only page depend on `BaseView`'s default `login_optional` behavior, because `login_optional` allows anonymous access when `INDI_ALLSKY_AUTH_ALL_VIEWS` is disabled.

Admin-only checks are used in mutating or sensitive AJAX handlers with:

```python
if not current_user.is_admin:
    ...
```

Some destructive/system actions also check `verify_admin_network()`. The first modern admin milestone should not expose destructive actions, so it should not need admin-network checks. If the page later adds write actions, each write endpoint should require all applicable protections: `login_required`, `current_user.is_admin`, CSRF, and `verify_admin_network()` when matching the existing behavior for comparable classic actions.

## 7. Minimal first implementation plan

1. Add `ModernAdminView(TemplateView)` in `indi_allsky/flask/views.py`.
2. Set `decorators = [login_required]`.
3. Set `page_title = 'Modern Admin'`.
4. Register `/modern-admin` on `bp_allsky`.
5. Add `indi_allsky/flask/templates/modern_admin/index.html`.
6. Add optional isolated CSS at `indi_allsky/flask/static/modern_admin/css/modern-admin.css`.
7. Do not add write forms, POST handlers, AJAX mutators, config saves, task queue actions, system commands, or network/drive/GPIO controls.
8. Do not add the route to the classic sidebar in the first commit unless there is a deliberate product decision to expose it. Direct URL access is safer for the first integration test.

## 8. Files likely to change in the first code commit

Required:

- `indi_allsky/flask/views.py`
- `indi_allsky/flask/templates/modern_admin/index.html`

Optional:

- `indi_allsky/flask/static/modern_admin/css/modern-admin.css`
- `indi_allsky/flask/static/modern_admin/js/modern-admin.js`

Avoid changing in the first commit:

- `indi_allsky/flask/__init__.py`
- `indi_allsky/flask/templates/base.html`
- `indi_allsky/flask/static/css/style.css`
- API blueprints
- config files
- migrations
- remotes, branches, or dependency files

## 9. Risks

- `TemplateView.__init__()` performs session setup, camera setup, status lookups, latest image lookup, and config-notification checks. This is consistent with existing UI pages, but it means even a read-only page is not a zero-query route.
- Extending `base.html` includes existing global JavaScript that polls status, loads notifications, and posts camera changes when the camera selector changes. This preserves classic behavior, but the future page will inherit those side effects.
- A route named `/modern-admin` on `bp_allsky` becomes `/indi-allsky/modern-admin`, not a root-level `/modern-admin`.
- Adding a link to the existing sidebar may be more visible than desired and could be perceived as replacing classic admin. Keep first access direct-only unless explicitly exposing it.
- Reusing existing JSON/AJAX endpoints from the new page could accidentally surface mutating behavior. The first milestone should render server-side read-only content only, or fetch only clearly read-only endpoints.
- If future work introduces a new blueprint for modern admin, it must be carefully checked against auth, CSRF, template/static paths, URL prefix expectations, and existing deployment configs.

## 10. Exact first implementation milestone

Create a read-only authenticated placeholder dashboard at:

```text
/indi-allsky/modern-admin
```

The page should:

- require login with `login_required`;
- render `indi_allsky/flask/templates/modern_admin/index.html`;
- extend the existing `base.html`;
- show only read-only status/context already available from `TemplateView`;
- include no forms that save data;
- include no destructive buttons;
- include no new API endpoints;
- leave every classic admin route and template unchanged;
- be reachable by direct URL only, with no sidebar/nav change in the first milestone.

The smallest safe integration point is therefore:

```text
indi_allsky/flask/views.py
```

with a new `ModernAdminView(TemplateView)` and one `bp_allsky.add_url_rule('/modern-admin', ...)` registration on the existing `indi_allsky` blueprint.
