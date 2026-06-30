# DATA002 - Latest Generated Output Metadata Audit

## Verdict

**GO WITH GUARDS**

The generated-output table family is the right source family for future Product UI latest generated output metadata, but it must not be consumed through existing media routes, redirect helpers, serializers, or filesystem-aware helpers.

There is no single canonical table for "latest generated output". A future adapter should use a descriptor-based, multi-source, metadata-only strategy across the allowlisted generated-output tables, with one bounded query per table and a conservative fallback if any source fails.

## Allowed Tables

| Table | Output Type | Status | Notes |
| --- | --- | --- | --- |
| `IndiAllSkyDbVideoTable` | `timelapse` | Allowed | Canonical timelapse output records. |
| `IndiAllSkyDbMiniVideoTable` | `mini_timelapse` | Allowed | Mini timelapse output records with target/start/end metadata. |
| `IndiAllSkyDbKeogramTable` | `keogram` | Allowed | Canonical keogram output records. |
| `IndiAllSkyDbStarTrailsTable` | `startrail` | Allowed | Canonical startrail image output records. |
| `IndiAllSkyDbStarTrailsVideoTable` | `startrail_video` | Allowed | Canonical startrail video output records. |
| `IndiAllSkyDbPanoramaImageTable` | `panorama_image` | Allowed | Generated panorama image records. Mapping stays explicit to avoid confusing panorama images with panorama videos. |
| `IndiAllSkyDbPanoramaVideoTable` | `panorama_video` | Allowed | Generated panorama video records. |

## Not Allowed As DATA002 Sources

| Source | Reason |
| --- | --- |
| `IndiAllSkyDbTaskQueueTable` | Represents jobs/tasks, not completed generated-output records. `data` and `result` are internal job payloads. |
| `IndiAllSkyDbLongTermKeogramTable` | Analytics/time-series data, not latest generated media output metadata. |
| Existing latest redirect/watch/view routes | They intentionally resolve URLs, previews, or media views. Product UI metadata must not inherit that behavior. |
| Existing Modern media serializers | They mix metadata with filenames, source labels, URLs, preview URLs, or media-facing fields. |
| Filesystem reconstruction/migration code | Scans files and uses filenames/stat-like metadata; not safe for request-time Product UI. |

## Output Type Mapping

| Output Type | Table | Confidence |
| --- | --- | --- |
| `timelapse` | `IndiAllSkyDbVideoTable` | High |
| `mini_timelapse` | `IndiAllSkyDbMiniVideoTable` | High |
| `keogram` | `IndiAllSkyDbKeogramTable` | High |
| `startrail` | `IndiAllSkyDbStarTrailsTable` | High |
| `startrail_video` | `IndiAllSkyDbStarTrailsVideoTable` | High |
| `panorama_image` | `IndiAllSkyDbPanoramaImageTable` | High |
| `panorama_video` | `IndiAllSkyDbPanoramaVideoTable` | High |

The adapter must derive `output_type` from the table descriptor, never from filename, path, URL, or row content.

## Allowed Fields

Allowed fields are primitive, JSON-safe metadata only. They may be exposed only after allowlist extraction and serialization.

Common allowed fields:

- `id`
- `camera_id`
- `createDate` as serialized `timestamp`
- `dayDate` as serialized `day_date`
- `night`
- `uploaded`
- `fileSize` as `file_size`
- `width`
- `height`
- derived `output_type`

Allowed where present:

- `success`
- `frames`
- `framerate`
- `targetDate`
- `startDate`
- `endDate`
- `exposure`
- `gain`
- `binmode`
- `exclude`

## Conditional Fields

These fields are not forbidden, but should not be included in the first adapter unless there is a clear product need and a test proving safe sanitization.

- `sync_id`: integration/internal synchronization metadata. Useful later for diagnostics, not needed for Product UI latest output.
- `note`: free-text mini video note. Only safe if length-limited, sanitized, and checked for paths, URLs, and secrets.
- Date part columns such as `dayDate_year`, `dayDate_month`, `dayDate_day`, `createDate_year`, `createDate_month`, `createDate_day`, `createDate_hour`: useful for indexing/grouping, but redundant for the product payload.
- `data`: raw JSON/blob metadata. Treat as forbidden by default; future use requires a nested allowlist.

## Forbidden Fields And Behaviors

Always forbidden for DATA002 Product UI latest generated output metadata:

- `filename`
- path values
- `remote_url`
- `s3_key`
- `thumbnail_uuid`
- preview URLs
- direct URLs
- download/share links
- raw ORM rows
- raw `data` blobs
- relationship objects such as `camera`
- `getUrl()`
- `getFilesystemPath()`
- `getRelativePath()`
- file validation helpers
- media serializers that include filename, source path, URL, preview, or download fields
- filesystem checks, stat calls, media reads, RAW/FITS reads, or generated media reads

## Bounded Query Strategy

### Options Considered

**A. Multi-source bounded queries**

Run one metadata-only, bounded query per allowlisted table:

- filter by current `camera_id`;
- order by `createDate DESC`;
- `LIMIT 1`;
- `first()`;
- no joins;
- no list queries;
- no pagination;
- no media/file helpers;
- sanitize each returned row through an allowlist;
- select the latest sanitized record in Python by serialized timestamp.

**B. Single-table pilot**

Start with only one generated-output table, for example timelapse, and defer the rest.

### Chosen Strategy

**Choose A: multi-source bounded queries, with strict guards.**

Reason:

- It is the only strategy that honestly answers "latest generated output" across the generated-output family.
- The table family is intentionally split by output type, so a single-table pilot would produce incomplete product semantics.
- The maximum query count is small and fixed by descriptor count.
- Each query must return at most one row.
- Partial failure can be contained per table.

Pseudo-query per descriptor:

```text
query(table)
  .filter(table.camera_id == current_camera_id)
  .order_by(table.createDate.desc())
  .limit(1)
  .first()
```

After each row is sanitized, the adapter may choose the latest record by `timestamp`. Rows with missing or invalid timestamps must be skipped or ranked last.

## Risk Audit

| Risk | Severity | Mitigation |
| --- | --- | --- |
| Multiple queries on RPi5 | Medium | Fixed descriptor list, one row per table, no joins, no `.all()`, no filesystem. |
| Timestamp semantics differ by output type | Medium | Use `createDate` consistently for "latest generated record"; do not claim it is the sky-cycle date. |
| Existing routes order some videos by `dayDate` | Medium | Product UI latest output should use `createDate`; `dayDate` may be displayed as cycle context only. |
| Missing or inconsistent `camera_id` | Medium | Require camera context; if missing, return safe fallback instead of querying all cameras. |
| Path/URL leak from raw row or serializers | High | Never expose raw rows; never reuse media serializers or redirect helpers. |
| Accidental use of filename-derived labels | High | Output type must come from descriptor mapping only. |
| Partial table failure | Medium | Catch per table, continue with other descriptors, expose only redacted status. |
| Invalid datetime values | Medium | Serialize safely; skip/rank last if unsafe. |
| Raw `data` blob leakage | High | Treat `data` as forbidden unless a future nested allowlist is audited. |
| Flask/Product coupling | Medium | Product builder remains framework-free; Flask/service layer supplies descriptors or repository instance. |
| Test complexity | Medium | Use fake descriptor/query objects; no real DB required for adapter tests. |

## Adapter Requirements For Step 3

The Step 3 adapter should be descriptor-driven and framework-free.

Expected interface shape:

```text
LatestGeneratedOutputRepository(descriptors).get_latest_generated_output_metadata(camera_id)
```

Input:

- `camera_id` from a safe caller context;
- injected table/query descriptors;
- no Flask request object;
- no global `db.session` access inside the product model layer.

Descriptor requirements:

- `output_type`;
- injected query object or model query;
- `camera_id` field expression;
- `createDate` field expression;
- allowlisted field map;
- optional field names by table.

Output requirements:

- JSON-safe dictionary;
- one selected latest generated output record or safe empty/fallback status;
- metadata only;
- `safe_preview_url` absent or `None`;
- no filenames, paths, URLs, thumbnails, raw rows, raw data, or relationship objects.

Error handling:

- missing `camera_id` -> safe `not_evaluated`/fallback status;
- no rows in all tables -> safe `not_found`/empty metadata status;
- one table failure -> continue and record redacted partial status if needed;
- all table failures -> safe fallback without raw error text;
- missing optional fields -> omit or set `None`;
- invalid datetime -> skip/rank last, never crash the Product UI.

## Tests Required For Step 3

Adapter tests must cover:

- descriptor mapping for all allowed tables;
- bounded query calls: filter by `camera_id`, order by `createDate DESC`, limit 1, first;
- no `.all()`;
- no joins;
- row present for each output type;
- mixed rows choose the latest safe timestamp;
- row absent from one or more tables;
- all rows absent;
- per-table query error;
- missing `camera_id`;
- row with forbidden fields present does not expose them;
- URL/path-looking values are rejected or omitted;
- raw `data` blob is not exposed;
- raw ORM row is not exposed;
- output is JSON serializable;
- safe preview remains absent or `None`;
- product module remains free of Flask/request/db.session/open/filesystem helpers.

## Stop Conditions

Do not proceed to runtime integration if the adapter requires any of the following:

- filename/path/URL/thumbnail values;
- media route helpers;
- `getUrl()`, `getFilesystemPath()`, or `getRelativePath()`;
- filesystem checks or media reads;
- unbounded query, `.all()`, or pagination;
- joins to build the product payload;
- querying without camera context;
- exposing raw ORM rows;
- exposing raw `data`;
- raw DB errors reaching the Product UI;
- inability to unit-test descriptor behavior without a real DB.

## Final Recommendation

Proceed to Step 3 Adapter with **GO WITH GUARDS**.

Build a multi-source, descriptor-based, metadata-only adapter. Keep it disconnected from Product UI runtime until tests prove that all generated-output tables are queried with strict bounds and that forbidden media/file fields cannot leak into the payload.
