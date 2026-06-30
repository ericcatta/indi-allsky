# DATA005 - Highlights Metadata Audit

## Verdict

GO WITH GUARDS.

Hybrid can create first-pass Highlight candidates from bounded image metadata already persisted in `IndiAllSkyDbImageTable`. These are not detector results, AI rankings, or visual classifications. They are explainable metadata suggestions.

## Product Question

DATA005 should help the user understand:

- why something may deserve attention;
- which metadata caused the suggestion;
- what is still not proven;
- where to review the item next.

## Chosen Source

### `IndiAllSkyDbImageTable`

Useful metadata:

- `id`
- `camera_id`
- `createDate`
- `dayDate`
- `night`
- `detections`
- `stars`
- `sqm`
- `adu`
- `kpindex`
- `ovation_max`
- `smoke_rating`
- `moonmode`
- `stable`
- `exclude`
- `width`
- `height`

Reasons:

- canonical image metadata table;
- already camera-scoped;
- existing indexes include camera/date/detection-related fields;
- metadata is already produced by existing capture/processing flows;
- no filesystem or media access is required.

## Rejected Sources

### Detector runtime

Rejected for DATA005.

Reason: it would introduce detector execution, classification semantics, and higher performance risk.

### AI ranking

Rejected for DATA005.

Reason: Product Principles require explainability, and no AI ranking contract exists.

### Filesystem/media helpers

Rejected for DATA005.

Reason: they can expose filenames, paths, URLs, previews, file reads, or storage behavior.

### Generated output metadata

Not used as primary Highlight source in DATA005.

Reason: output metadata is useful, but without source lineage and quality signals it is weaker than image metadata for explainable attention.

## Rule Mapping

Allowed rule mappings:

- `detections > 0` -> `meteor_candidate`
- elevated `ovation_max` or `kpindex` -> `aurora_candidate`
- `smoke_rating > 0` -> `sky_quality`
- high `stars` or high `sqm` -> `clear_window`
- `stable == false` -> `observatory_issue`

Each Highlight must include the exact evidence value that triggered it.

## Bounded Query Strategy

The runtime may request a small bounded set:

```text
SELECT allowlisted metadata
FROM image
WHERE camera_id = current_camera_id
ORDER BY detections DESC, stars DESC, sqm DESC, createDate DESC
LIMIT 4
```

The Product adapter must still sanitize every row and must not expose raw rows.

## Forbidden Fields and Behaviors

Forbidden:

- filename;
- path;
- URL;
- remote URL;
- S3/storage key;
- thumbnail id;
- raw JSON data;
- raw ORM row;
- filesystem checks;
- media reads;
- preview URLs;
- detector execution;
- AI ranking;
- polling;
- POST/fetch/AJAX;
- mutations.

## Risk Audit

- `detections` is only metadata, not a confirmed meteor.
- `kpindex`/`ovation_max` indicate aurora context, not visual aurora proof.
- `stars`/`sqm` suggest clear-sky potential, not full cloud analysis.
- `smoke_rating` may represent environmental quality, not a precise phenomenon.
- Ordering can favor metadata-rich frames over user-interest frames.
- Multiple cameras depend on correct camera context.

## Integration Scope

DATA005 integrates Highlights v1 only.

Now already links to Highlights and should not duplicate the Highlights queue in this step.

## Stop Conditions

Stop or fallback if implementation requires:

- detector runtime;
- AI ranking;
- image/media reads;
- source file reads;
- filesystem access;
- preview URL;
- unbounded query;
- route/API changes;
- mutative actions.
