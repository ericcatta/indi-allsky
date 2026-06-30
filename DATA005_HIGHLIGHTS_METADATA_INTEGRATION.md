# DATA005 - Highlights Metadata Integration

## Summary

DATA005 connects first-pass Highlights metadata to the Product UI.

Highlights now can receive bounded, metadata-only image rows and convert them into explainable Highlight candidates. No detector runtime, AI ranking, media read, preview, filesystem access, or mutation is introduced.

## Adapter

Added:

- `HighlightsMetadataRepository`

The adapter is framework-free and receives:

- query object;
- camera id;
- camera id field;
- ordering expressions;
- max item count.

It returns product-safe Highlight items, not raw metadata rows.

## Runtime Wiring

Added:

- `ModernAdminHighlightsView.get_highlights_repository()`

The Flask layer builds a repository using:

- `IndiAllSkyDbImageTable.query`
- current camera id
- `IndiAllSkyDbImageTable.camera_id`
- `detections.desc()`
- `stars.desc()`
- `sqm.desc()`
- `createDate.desc()`
- `max_items=4`

## Highlight Rules

Rules are simple and explainable:

- detections metadata -> meteor candidate;
- aurora environment metadata -> aurora candidate;
- smoke/sky condition metadata -> sky quality attention item;
- stars/SQM metadata -> clear window candidate;
- unstable frame metadata -> observatory issue.

Every generated Highlight includes evidence such as:

- `detections=2`
- `stars=45`
- `sqm=19.5`
- `kpindex=6`
- `image_metadata_id=50`

## Product Boundary

The UI must present these as metadata candidates, not confirmed events.

Microcopy was updated to say:

- metadata rules only;
- every recommendation must stay explainable;
- no detector runtime or AI ranking is connected.

## Explicitly Excluded

Still excluded:

- detector runtime;
- AI ranking;
- filesystem;
- RAW/FITS reads;
- media reads;
- preview URL;
- download/share;
- generated media;
- polling;
- POST/fetch/AJAX;
- mutations;
- Classic changes.

## Fallback Behavior

If camera context is missing, query construction fails, query execution fails, or no row produces an explainable Highlight, the page falls back to the existing static/fake Highlight contract.

## Tests

Added tests for:

- explainable candidate generation;
- bounded query calls;
- no candidate fallback;
- query error fallback;
- `build_highlights_view()` with repository;
- forbidden metadata not exposed;
- JSON safety;
- no paths, secrets, or callables.

## Remaining Work

Future work should avoid adding detector or AI ranking before a dedicated evidence contract exists.

The next safest step is a post-integration review and then possibly bounded Sky Cycle metadata, not media previews.
