# DATA004 - Source Trust Summary Integration

## Summary

DATA004 adds a first real/bounded Source Trust Summary to Now.

The integration is metadata-only. It checks for latest RAW/FITS source metadata rows for the current camera, but it does not verify files, read source data, generate previews, or claim output lineage.

## Adapter

Added framework-free product-domain components:

- `SourceTrustDescriptor`
- `SourceTrustRepository`

The repository accepts descriptor-injected queries and remains independent of Flask, request state, and database session globals.

## Runtime Wiring

Now wiring is created in `ModernAdminNowView.get_source_trust_repository()`.

Descriptors:

- `fits_source` using `IndiAllSkyDbFitsImageTable`
- `raw_source` using `IndiAllSkyDbRawImageTable`

Each descriptor uses:

- current camera id;
- `camera_id` filter;
- `createDate.desc()`;
- `limit(1).first()` inside the repository.

## Now Contract

`build_now_view()` now accepts:

- `source_trust_repository=None`

`source_confidence_summary` remains the public NowView section. With a repository connected, it summarizes:

- whether source metadata exists;
- source types found;
- preservation confidence based on metadata only;
- risk level;
- evidence;
- source gaps;
- lineage limitation.

## Allowlisted Source Metadata

The adapter may expose:

- `source_type`
- `source_label`
- `id`
- `camera_id`
- `timestamp`
- `day_date`
- `night`
- `uploaded`
- `exposure`
- `gain`
- `binmode`
- `file_size`
- `width`
- `height`

## Explicitly Excluded

Still excluded:

- filename;
- path;
- URL;
- preview;
- `remote_url`;
- `s3_key`;
- `thumbnail_uuid`;
- raw ORM row;
- raw JSON data;
- filesystem;
- `exists()`;
- `stat()`;
- `open()`;
- RAW/FITS reads;
- media reads;
- media generation;
- download/share;
- detector/AI/ranking;
- polling;
- hardware/service checks;
- POST/fetch/AJAX;
- mutations;
- Classic changes.

## UI Behavior

Now already had a Source Confidence card. The card now receives bounded metadata when available and remains cautious:

- "Source metadata available" when RAW/FITS rows exist;
- "Source metadata not found" when no bounded source row is present;
- "Source trust is based on metadata only; no filesystem verification was performed."

No preview, source opening, download, or source-path information is shown.

## Fallback Behavior

If camera context is missing, descriptor construction fails, query fails, or no source rows exist, Now still renders.

Fallback states are product-safe and do not expose raw exceptions.

## Tests

Added tests for:

- allowlisted source metadata;
- no source rows;
- partial descriptor failure;
- source confidence built from repository;
- prudent no-source summary;
- forbidden metadata not exposed;
- JSON-safe payload;
- no paths, secrets, callables.

## Remaining Work

Future DATA work should not add filesystem verification until a dedicated source lineage/preservation contract exists.

The next safe step is likely a bounded Source Lineage discovery, not preview/media wiring.
