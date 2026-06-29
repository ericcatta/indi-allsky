# HYBRID NOW RUNTIME SAFETY REVIEW

## Purpose

Mission 014 reviews the first real runtime wiring of `latest_frame_summary` into
`/modern-admin/now`.

This document is intentionally critical. Passing unit tests is not enough to
prove the runtime integration is safe.

## Wiring Reviewed

Runtime wiring added in Mission 013:

- `ModernAdminNowView.get_latest_frame_provider()`
- `IndiAllSkyDbImageTable.query.filter(IndiAllSkyDbImageTable.camera_id == camera_id)`
- `IndiAllSkyDbImageTable.createDate.desc()`
- `LatestFrameImageTableRepository`
- `LatestFrameSummaryProvider`
- fallback to the default static provider if provider construction fails

Explicitly still excluded:

- preview URL;
- filename;
- path;
- filesystem checks;
- RAW/FITS reads;
- media generation;
- fetch/POST/actions;
- Classic route changes.

## Safety Verdict

Verdict: acceptable as a bounded first runtime integration, but not fully
integration-verified.

The wiring is small and conservative. It reads at most one image metadata row,
does not expose media paths, and keeps the product builder framework-free.

However, it is not yet "proven safe" in the strongest sense because the current
environment still lacks true Flask integration tests with session/app/database
fixtures.

No rollback is recommended at this point.

## Review Questions

### 1. Frontend/backend separation

Score: 8/10.

The template still receives a sanitized NowView payload and remains render-only.
The product builder does not know about Flask, request/session, SQLAlchemy
models, or the database.

The integration does introduce more runtime concern into the Flask view, but
the boundary is still understandable:

```text
Flask view builds provider -> product builder consumes provider -> template renders dict
```

### 2. Is the Flask view doing too much?

Score: 7/10.

For one bounded field, the view method is acceptable. It constructs a query and
labels, then delegates execution/sanitization to the repository/provider.

Long term, this should move behind a small service/factory if Now accumulates
more data sources. Repeating this pattern for every Now section inside
`ModernAdminNowView` would become a maintenance problem.

### 3. Product builder framework-free

Score: 10/10.

`product_view_models.py` remains free of Flask imports, request/session,
`db.session`, filesystem access, and route awareness.

### 4. Query boundedness

Score: 9/10.

The query is filtered by `camera_id`. The repository applies:

```text
order_by(createDate.desc())
limit(1)
first()
```

This is the right RPi5-first shape.

Residual concern: the query is created in the view and not covered by a real DB
integration test, so SQL behavior is inferred from code rather than verified.

### 5. Path / filename leak risk

Score: 9/10.

The adapter only reads `createDate` from the row. It does not access:

- `filename`;
- `remote_url`;
- `s3_key`;
- `thumbnail_uuid`;
- `getUrl()`;
- `getFilesystemPath()`;
- file existence or stat calls.

The provider sanitization would reject unsupported/suspicious metadata if a
future adapter accidentally passed it through.

### 6. Import / DB coupling

Score: 7/10.

`views.py` already imports `IndiAllSkyDbImageTable`, so the new wiring does not
introduce a new kind of coupling in that file.

Still, the product direction should avoid turning `views.py` into the domain
service layer. The next Now data source should probably use a small
Flask/service factory rather than adding more direct query construction to the
view.

### 7. Fallback safety

Score: 8/10.

If camera context or query construction fails, the helper returns `None`, and
`build_now_view()` falls back to the static provider.

If query execution fails later, `LatestFrameSummaryProvider` catches the
repository exception and returns a redacted "metadata unavailable" summary.

Potential improvement: log with enough internal context for operators, but do
not expose it to the UI.

### 8. User-safe failure mode

Score: 8/10.

The user sees a normal Now page with placeholder or unavailable status. No raw
exception text is exposed.

Potential weakness: without integration tests, we cannot prove every Flask app
startup/session path reaches that fallback as intended.

### 9. RPi5 impact

Score: 9/10.

One indexed image metadata query per Now page render is acceptable.

Do not add polling. Do not refresh this with JavaScript. Do not add preview
image checks in the same path.

### 10. Missing tests

Missing:

- real Flask `test_client` request for `/modern-admin/now`;
- login/session behavior;
- app context behavior;
- real SQLAlchemy query against test DB;
- DB fixture with multiple image rows verifying newest row selection;
- missing camera behavior in a real view context;
- rendered template assertion that no path/preview URL appears;
- failure-path assertion for DB errors in real app context.

Existing tests still cover:

- product contract validation;
- repository fake query bounded behavior;
- provider sanitization;
- JSON safety;
- no framework imports in product builder.

## Updated Now Score

Now score after Mission 013: 8.0/10.

Why it improved:

- first real bounded metadata source is wired;
- latest-frame summary can now become truthful without exposing files;
- product-domain contract remains clean.

Why it is not higher:

- no real Flask/DB integration tests;
- only one data point is real;
- camera phase, source confidence, outputs, moments, and health remain
  placeholder;
- profile label remains placeholder;
- the view/service boundary should be formalized before more sources are added.

## Residual Risks

1. Direct view growth
   - More Now data sources should not be added as repeated query blocks inside
     `ModernAdminNowView`.

2. Integration test gap
   - Current tests prove the provider shape, not the real request/app/session
     flow.

3. Timezone ambiguity
   - `createDate` formatting remains conservative and does not state timezone.

4. Profile label placeholder
   - Accurate profile context is still not wired.

5. Query behavior inferred, not runtime-proven
   - The code path is simple, but a real DB fixture would provide stronger
     confidence.

6. Future preview temptation
   - Adding image preview URLs too early would reopen path/download/public route
     questions.

## Rollback / Guardrail Assessment

Rollback is not recommended.

Recommended guardrail before adding another runtime source:

- create a tiny Now runtime provider factory/service boundary, or at minimum
  keep every new source behind a method with bounded query and fallback;
- avoid adding more logic directly to the template;
- keep preview/source URLs out of Now until a separate URL policy exists.

## Next Real Data Candidate

Safest next data candidate: current sky phase from already available
view/runtime context, if it can be passed as sanitized label only.

Why:

- high product value;
- small payload;
- no media/file access;
- no query required if the view already has safe day/night/twilight context;
- helps Now answer "what is happening now" better than another admin metric.

Do not connect next:

- preview URL;
- source lineage;
- generated outputs;
- moments/detector evidence;
- storage filesystem status;
- frame metadata analytics files;
- public latest endpoints.

## Recommended Mission 015

Mission 015 should review and, if safe, wire a bounded `current_phase_summary`
from existing view/camera/astro context.

Constraints for Mission 015:

- no new DB query;
- no filesystem;
- no polling/fetch;
- no raw ephem data dump;
- no sunrise/sunset complexity unless already available in sanitized form;
- fallback to "unknown";
- product builder remains framework-free.

If the current phase cannot be obtained from already initialized view context,
Mission 015 should stop and document the blocker rather than adding new
astronomy calculations.
