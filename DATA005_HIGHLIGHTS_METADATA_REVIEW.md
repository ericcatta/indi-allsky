# DATA005 - Highlights Metadata Review

## Verdict

COMPLETE WITH MINOR RISKS.

DATA005 successfully turns Highlights from fully static examples into bounded, explainable metadata suggestions. It preserves the Product Architecture and does not introduce detector runtime, AI, media access, previews, or actions.

## Product Value

The user can now see why an item deserves attention:

- detection metadata present;
- aurora-context metadata elevated;
- sky-quality metadata suggests a clear window;
- environmental metadata suggests reduced transparency;
- frame stability metadata suggests operational attention.

This is a meaningful step because Highlights now behaves like an attention layer, not only a contract demo.

## Safety Value

The integration remains:

- metadata-only;
- camera-scoped;
- bounded;
- allowlisted;
- JSON-safe;
- read-only;
- RPi5-first.

No paths, filenames, URLs, previews, raw rows, raw JSON data, or media helpers are exposed.

## Query Review

The query is bounded:

```text
WHERE camera_id = current_camera_id
ORDER BY detections DESC, stars DESC, sqm DESC, createDate DESC
LIMIT 4
```

The Product adapter converts rows into Highlight items and drops anything unsafe.

## UI Review

Highlights now reads more honestly:

- no longer purely static;
- no longer claims detector data;
- recommendations are described as metadata-rule suggestions;
- every candidate includes a selection reason and evidence.

The page still avoids becoming a gallery or event detector dashboard.

## Test Coverage Review

Tests cover:

- metadata Highlight candidate generation;
- bounded query calls;
- no candidate fallback;
- query error fallback;
- forbidden fields not exposed;
- full Highlights payload validation;
- JSON safety;
- no paths, secrets, or callables.

Missing:

- full Flask/DB integration test;
- real DB row smoke test;
- detector evidence contract tests.

These are acceptable omissions for DATA005.

## Residual Risks

- `detections` metadata is not confirmed meteor evidence.
- Aurora context metadata is not visual aurora proof.
- Stars/SQM metadata is not full cloud classification.
- Bounded ordering is useful but not a product-quality ranking.
- Some installations may have sparse metadata, causing fallback to static examples.

## Stop List

Do not add next:

- AI ranking;
- detector runtime;
- image preview;
- media reads;
- output opening;
- automatic confirmation;
- favorite mutation;
- share/download;
- source file access.

## Next DATA Recommendation

Recommended next DATA: Sky Cycle Metadata Discovery.

Reason: Now and Highlights now have bounded real metadata. The next product value is context: what cycle or phase these candidates belong to. That should be discovered before connecting Moment Detail or Output Detail to identifier-specific records.
