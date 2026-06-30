# DATA004 - Source Trust Summary Review

## Verdict

COMPLETE WITH MINOR RISKS.

DATA004 successfully integrates a first bounded Source Trust Summary into Now. It is useful and safe, but still intentionally limited: it proves source metadata exists, not that source files are present or readable.

## Product Value

Now can now answer the trust question more honestly:

- source metadata found or not found;
- RAW/FITS source types represented by metadata;
- preservation is partially known or unknown;
- generated output lineage is not connected yet;
- no filesystem verification was performed.

This improves the user experience because the product no longer treats source trust as a purely fake placeholder.

## Safety Value

The integration preserves the DATA001/DATA002/DATA003 safety model:

- metadata-only;
- camera-scoped;
- bounded per table;
- allowlist output;
- no filenames;
- no paths;
- no URLs;
- no source file reads;
- no filesystem checks;
- no preview/media access;
- no actions.

## Query and Fallback Review

Each source descriptor performs at most one latest-row query:

```text
WHERE camera_id = current_camera_id
ORDER BY createDate DESC
LIMIT 1
```

The repository accepts partial failure. FITS can fail while RAW succeeds, and vice versa. If both fail or camera context is unavailable, Now renders with a safe unknown/not-found summary.

## UI Review

The Now Source Confidence card remains product-first. It does not become a storage dashboard and does not display raw table names, paths, or file handles.

The language is deliberately cautious:

- "metadata found";
- "file presence was not verified";
- "lineage is not connected yet".

This is the correct tone for the current evidence level.

## Moment and Output Detail Decision

Moment Detail and Output Detail were not wired in DATA004.

Reason: those pages need identifier-specific source lineage. Reusing latest-camera source metadata there would imply a relationship that has not been proven.

## Observatory Decision

Observatory was not wired.

Reason: source trust in Observatory would quickly become retention/storage/health readiness. That should be a separate bounded contract.

## Test Coverage Review

Tests cover:

- source trust repository with source row;
- source trust repository with no row;
- partial descriptor failure;
- Now source confidence using source metadata;
- prudent unknown/no-source fallback;
- forbidden fields dropped;
- JSON safety;
- no paths/secrets/callables;
- framework-free product module.

Missing tests:

- full Flask/database integration test;
- real DB schema smoke test;
- identifier-specific lineage tests.

Those are acceptable blockers for this metadata-only phase.

## Residual Risks

- Source row existence does not prove file existence.
- RAW and FITS metadata may be stale.
- Configuration may intentionally disable RAW or FITS, but the summary does not yet explain policy.
- There is no output-to-source lineage relationship.
- Multiple cameras depend on correct camera context.

## Stop List

Do not add next:

- preview URL;
- source file open;
- FITS/RAW read;
- filesystem existence check;
- output-to-source claim without lineage;
- download/share;
- media generation;
- AI/detector ranking;
- POST/fetch/AJAX;
- mutative source repair actions.

## Next DATA Recommendation

Recommended next DATA: Source Lineage Discovery.

Reason: DATA004 can say source metadata exists, but cannot explain which output or moment derives from which source. The next product value comes from discovering whether existing DB/task metadata can support safe lineage, not from reading files or showing previews.
