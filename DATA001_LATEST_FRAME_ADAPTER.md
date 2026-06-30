# DATA001 Latest Frame Metadata Adapter

## Scope

This document records Step 3 Adapter work for Latest Frame Metadata.

The adapter remains not wired to any new Product UI route/template and does not introduce preview, media, filesystem, RAW/FITS, download, or mutation behavior.

## Adapter Created / Strengthened

Adapter: `LatestFrameImageTableRepository`

Location:

- `indi_allsky/product_view_models.py`

Existing provider boundary:

- `LatestFrameSummaryProvider`

What changed:

- The repository adapter now extracts an allowlisted metadata block from the latest image row.
- The adapter can optionally apply a camera filter when a camera id and injected camera id field are supplied.
- The adapter still supports already-filtered injected queries.
- The provider continues to return a JSON-safe `latest_frame_summary`.
- The `latest_frame_summary` payload now includes `frame_metadata`.

The adapter is still dependency-injected and framework-free:

- no Flask import;
- no request access;
- no `db.session`;
- no filesystem access;
- no media helper calls;
- no raw ORM row exposure.

## Exposed Fields

The adapter allows only these row-derived metadata fields:

- `id`
- `camera_id`
- `timestamp`
- `exposure`
- `gain`
- `binmode`
- `temp`
- `night`
- `adu`
- `sqm`
- `stars`
- `detections`
- `file_size`
- `width`
- `height`

Each value must be JSON-safe and primitive:

- string;
- integer;
- float;
- boolean;
- `None`.

Missing or non-primitive values are converted to `None` or omitted by the safety path instead of exposing unsafe objects.

## Excluded Fields

The adapter must not expose:

- `filename`
- `remote_url`
- `s3_key`
- `thumbnail_uuid`
- raw `data`
- raw ORM row
- camera relationship object
- filesystem path
- preview URL
- media URL
- source RAW/FITS path
- any callable
- any secret/token/password-like key or value

The adapter must not call:

- `getUrl()`
- `getRelativePath()`
- `getFilesystemPath()`
- `validateFile()`
- filesystem `exists()` or `stat()`
- image/media readers

## Query Behavior

The adapter enforces bounded behavior:

- optional injected camera filter;
- optional injected ordering expression;
- `limit(1)`;
- `first()`;
- no list materialization;
- no pagination;
- no join requirement;
- no filesystem/media helper.

If the caller injects an already-filtered query, the adapter still applies `limit(1)` and `first()`.

If the caller injects a camera id and a camera id field, the adapter applies the camera filter before ordering and limiting.

## Fallback Behavior

The adapter/provider boundary handles:

- missing camera context through already-safe caller fallback or injected-query behavior;
- query errors;
- missing row;
- missing optional row attributes;
- datetime formatting;
- non-primitive values;
- unsafe metadata.

Failures return safe Product UI summaries:

- no raw exception text;
- no path/URL/filename;
- `safe_preview_url` remains `None`;
- `frame_metadata` is `{}` when no safe metadata is available.

## Test Coverage

Updated tests cover:

- complete row metadata extraction;
- camera filter call tracking;
- bounded query calls;
- row with missing fields;
- row absent;
- query error;
- forbidden row fields not exposed;
- non-primitive values not exposed;
- datetime formatted safely;
- JSON serializable payloads;
- validation failure for forbidden frame metadata keys;
- validation failure for callable frame metadata values;
- validation failure for URL-like frame metadata values;
- product module remaining free of Flask/request/db session/open usage.

## Step 4 Integration Remaining Work

Step 4 may decide whether to wire this adapter into runtime Product UI. That step must still prove:

- runtime camera context is safe;
- real query construction remains bounded;
- no raw ORM row reaches templates;
- no preview URL is introduced;
- no media/file helper is called;
- fallback behavior is user-safe;
- existing Flask integration test limitations are documented.

Step 4 must remain a separate decision. This adapter step does not connect new runtime data to any new surface.
