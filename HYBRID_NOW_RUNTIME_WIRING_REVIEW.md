# HYBRID NOW RUNTIME WIRING REVIEW

## Purpose

Mission 012 reviews how to wire `LatestFrameSummaryProvider` and
`LatestFrameImageTableRepository` into `/modern-admin/now` in a future mission.

This document does not implement runtime wiring, add queries, modify
`views.py`, add routes, read files, or connect the real database to Now.

## Current State

Existing product-domain pieces:

- `LatestFrameSummaryProvider`
- `StaticLatestFrameRepository`
- `LatestFrameImageTableRepository`
- `build_now_view(latest_frame_provider=None)`
- `latest_frame_summary`

Runtime state:

- `/modern-admin/now` is implemented by `ModernAdminNowView`.
- `ModernAdminNowView.get_context()` currently calls `build_now_view()` with no
  provider.
- Therefore Now still uses the static/fake latest-frame path.

## Import / Model Identified

`IndiAllSkyDbImageTable` lives in:

```text
indi_allsky/flask/models.py
```

It is already imported near the top of:

```text
indi_allsky/flask/views.py
```

Relevant import pattern:

```python
from .models import IndiAllSkyDbImageTable
```

`views.py` already imports the product builder:

```python
from ..product_view_models import build_now_view
```

Future wiring would need to import the provider/repository classes from
`product_view_models`, or better use a small local factory helper to isolate the
runtime wiring.

## Ordering Field

Use:

```python
IndiAllSkyDbImageTable.createDate.desc()
```

Reasons:

- `createDate` exists on `IndiAllSkyDbImageTable`.
- it is indexed;
- existing latest-image logic already orders by `createDate.desc()`;
- `TemplateView` and Modern Admin helpers use the same field for latest image
  selection;
- no additional join is required when filtering by `camera_id`.

Do not use:

- filename order;
- id order as primary source of truth;
- filesystem mtime;
- public latest redirect behavior;
- generated thumbnail timestamp.

## Safe Query Construction

Recommended query shape:

```python
query = IndiAllSkyDbImageTable.query.filter(
    IndiAllSkyDbImageTable.camera_id == self.camera.id
)

repository = LatestFrameImageTableRepository(
    query=query,
    order_by_expression=IndiAllSkyDbImageTable.createDate.desc(),
    camera_label=safe_camera_label,
    profile_label=safe_profile_label,
    clock=lambda: self.camera_now,
)

provider = LatestFrameSummaryProvider(repository)
context['modern_admin_now'] = build_now_view(latest_frame_provider=provider)
```

The repository itself applies:

```text
order_by(...)
limit(1)
first()
```

This remains one bounded query and does not list images, join tables, read
files, or inspect media.

## Camera / Profile Labels

Safe camera label candidate:

```python
safe_camera_label = str(
    self.camera.friendlyName or self.camera.name or 'Unknown camera'
)
```

This is already similar to Modern Admin context logic.

Safe profile label candidate:

```python
safe_profile_label = 'Profile not evaluated yet'
```

Reason: profile label derivation may require reading nested configuration or
profile mapping. That is outside the first wiring step unless an already-safe
field is available in the current view context without extra query or config
dumping.

## Recommended Wiring Option

Use a small factory/helper in the Flask/service boundary, not direct inline
construction inside the product builder.

Recommended option:

```text
ModernAdminNowView.get_latest_frame_provider()
```

or a nearby module-level helper in `views.py`:

```text
build_modern_now_latest_frame_provider(view)
```

Preferred shape:

```python
def get_latest_frame_provider(self):
    safe_camera_label = str(self.camera.friendlyName or self.camera.name or 'Unknown camera')
    safe_profile_label = 'Profile not evaluated yet'

    query = IndiAllSkyDbImageTable.query.filter(
        IndiAllSkyDbImageTable.camera_id == self.camera.id
    )

    repository = LatestFrameImageTableRepository(
        query=query,
        order_by_expression=IndiAllSkyDbImageTable.createDate.desc(),
        camera_label=safe_camera_label,
        profile_label=safe_profile_label,
        clock=lambda: self.camera_now,
    )

    return LatestFrameSummaryProvider(repository)
```

Then:

```python
context['modern_admin_now'] = build_now_view(
    latest_frame_provider=self.get_latest_frame_provider()
)
```

Why this option:

- product builder stays framework-free;
- Flask owns DB query construction;
- repository owns bounded query behavior;
- provider owns sanitization;
- template remains render-only;
- wiring remains easy to disable or fall back to static provider.

## Boundary Rules

Backend/product boundary:

- `product_view_models.py` must not import Flask, SQLAlchemy globals, app,
  request, session, or models.
- `views.py` or a Flask service helper may construct a repository from existing
  model/query objects.
- the template receives only sanitized NowView dicts.
- no domain logic in Jinja.

Runtime failure behavior:

- if query fails, `LatestFrameSummaryProvider` already returns a redacted
  repository error summary;
- no exception details should be exposed to the template;
- app logging may happen in a future Flask helper if needed, but not inside the
  product model.

## What Not To Do

Do not:

- call `/js/latest`;
- call `/latestimage`;
- use public redirects;
- call `getUrl()` for the first wiring step;
- set `safe_preview_url` to a real URL yet;
- access `filename`;
- call `getFilesystemPath()`;
- call file `exists()` or `stat()`;
- inspect RAW/FITS files;
- use `FrameMetadataAnalytics`;
- load recent frame lists;
- join camera table unless a later review proves it is required;
- dump `image.data`;
- add AJAX/fetch/polling;
- add any action or button.

## Test Strategy

Already possible without Flask runtime:

- `LatestFrameImageTableRepository` fake-query tests;
- provider sanitization tests;
- no-row behavior;
- query error behavior;
- missing `createDate`;
- no path/filename leakage;
- JSON safety;
- `build_now_view(latest_frame_provider=provider)`.

Recommended Mission 013 tests without Flask runtime:

- helper/factory test with a fake view object;
- fake image table/query object;
- verifies correct `camera_id` filter construction if feasible without
  SQLAlchemy, or isolates that as a runtime-only check;
- verifies provider injection into `build_now_view`;
- verifies fallback to static provider if camera context is missing.

Requires Flask/DB runtime and remains blocked in the current lightweight
environment:

- true `test_client` request to `/modern-admin/now`;
- login/session/CSRF behavior;
- real `IndiAllSkyDbImageTable.query` execution;
- real DB row ordering;
- SQL generated by SQLAlchemy against the project DB;
- template rendering against real provider;
- integration behavior when no database is available.

## Residual Risks

### Query heaviness

The planned query is small, but accidental additions such as `.all()`, joins,
or analytics reads would violate the RPi5-first goal.

### Import coupling

Importing provider/repository classes into `views.py` is acceptable, but moving
Flask/model imports into `product_view_models.py` would violate the domain
boundary.

### Path leakage

The image row contains `filename`, `remote_url`, `s3_key`, and potentially JSON
metadata. None should be passed through the adapter.

### Runtime failure

The provider handles repository exceptions as redacted status, but wiring code
must not raise before the provider is created.

### NoResultFound

The proposed query uses `first()`, so no `NoResultFound` should occur. If a
future adapter uses `.one()`, that would need explicit handling.

### Missing `createDate`

Adapter already returns "Not evaluated yet" for missing timestamps.

### Timezone formatting

Existing code appears to use naive datetimes in places. The first wiring should
format conservatively and avoid claiming exact timezone semantics.

### Profile label

Profile context is important but should remain placeholder until a safe,
bounded profile-label source is reviewed.

## Blockers Before Runtime Wiring

Hard blockers:

- no Flask-level integration test environment in the lightweight setup;
- no verified runtime test for `/modern-admin/now` with real app/session;
- no real DB fixture for latest image row ordering;
- no decision on whether profile label can be safely populated.

Soft blocker:

- whether to log repository errors at Flask layer or keep them only as redacted
  view-model status.

## Recommendation

Proceed with a very small runtime wiring mission only if the change is limited
to `ModernAdminNowView` or a local Flask helper/factory and keeps
`safe_preview_url` as `None`.

Do not connect preview URLs, thumbnails, public latest routes, analytics files,
or source lineage in the same step.

The first runtime wiring should be metadata-only:

- camera label;
- placeholder profile label;
- timestamp;
- age label;
- `image_available`;
- conservative source status.

## Mission 013 Proposed

Mission 013 should implement optional runtime wiring behind the existing
`build_now_view(latest_frame_provider=...)` injection point:

1. Import `LatestFrameSummaryProvider` and `LatestFrameImageTableRepository` in
   `views.py`.
2. Add `ModernAdminNowView.get_latest_frame_provider()`.
3. Build a query filtered by `self.camera.id`.
4. Use `IndiAllSkyDbImageTable.createDate.desc()` as the order expression.
5. Keep `safe_preview_url` as `None`.
6. Do not call `getUrl()`, `getFilesystemPath()`, public latest routes, or
   filesystem checks.
7. Add static/helper tests where possible.
8. Run existing product view model tests and inventory checks.

If any uncertainty appears around app context, session, camera setup, or DB
availability, abort wiring and keep Now static.

## Mission 013 Update

`ModernAdminNowView` now wires `LatestFrameSummaryProvider` through a small
Flask-layer helper:

```text
ModernAdminNowView.get_latest_frame_provider()
```

The helper builds a query filtered by the current camera id, passes
`IndiAllSkyDbImageTable.createDate.desc()` as the ordering expression, wraps the
query in `LatestFrameImageTableRepository`, and passes the repository through
`LatestFrameSummaryProvider` into `build_now_view(...)`.

Runtime behavior remains conservative:

- no preview URL is generated;
- no filename/path is read or exposed;
- no filesystem checks are performed;
- no RAW/FITS files are touched;
- no public latest route is called;
- no action or mutation is exposed.

If provider construction fails or camera context is unavailable, the helper
returns `None`, allowing `build_now_view()` to fall back to the static provider.

Remaining blocker: the lightweight environment still lacks true Flask
integration tests for `/modern-admin/now` with session/app/DB fixtures. The
current wiring should be treated as bounded but not fully integration-verified.
