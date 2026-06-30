# DATA001 Latest Frame Metadata Audit

## Verdict

GO WITH GUARDS.

`IndiAllSkyDbImageTable` is acceptable as the source for Product UI Latest Frame Metadata only behind a strict metadata-only adapter.

The table is canonical and indexed, but it also inherits file/path/URL behavior through `IndiAllSkyDbFileBase`. A future adapter must never expose the ORM row directly and must never call file or media helpers.

## Source Under Audit

Source: `IndiAllSkyDbImageTable`

Location:

- `indi_allsky/flask/models.py`
- Base file behavior: `IndiAllSkyDbFileBase`

Relevant safety observation:

- The image table contains useful capture metadata.
- The same object also has `filename`, `remote_url`, `s3_key`, `getUrl()`, `getRelativePath()`, `getFilesystemPath()`, and `validateFile()`.
- Therefore the source is usable, but only with an explicit allowlist.

## Allowed Fields

These fields are safe for Product UI Latest Frame Metadata if converted to JSON-safe primitive values and never exposed as raw ORM state.

| Field | Allowed Use | Notes |
| --- | --- | --- |
| `id` | Internal row identity | Safe if used only as opaque metadata. Do not build URLs from it in this step. |
| `createDate` | Latest frame timestamp | Must be formatted safely; timezone handling must be explicit or marked unknown. |
| `camera_id` | Camera association | Safe as numeric metadata; user-facing label should come from a safe camera context, not a join in this step. |
| `exposure` | Capture metadata | Numeric only. |
| `exp_elapsed` | Capture timing metadata | Numeric or `None`. |
| `process_elapsed` | Processing timing metadata | Numeric or `None`; do not imply media generation status. |
| `gain` | Capture metadata | Numeric only. |
| `binmode` | Capture metadata | User-facing label should be `binning` or `bin mode`. |
| `temp` | Sensor/camera temperature | Numeric or `None`; unit must be labeled later if shown. |
| `night` | Day/night phase hint | Boolean only; not a twilight classifier. |
| `adu` | Signal/brightness metadata | Numeric only. |
| `stable` | Capture stability hint | Boolean only; definition should be documented before UI use. |
| `moonmode` | Capture mode metadata | Boolean only. |
| `moonphase` | Moon metadata | Numeric or `None`; must not be overexplained without domain context. |
| `adu_roi` | Analytics metadata | Boolean only. |
| `sqm` | Sky brightness metadata | Numeric or `None`; label as not evaluated if missing. |
| `stars` | Detection/count metadata | Integer or `None`; avoid claiming detector confidence. |
| `uploaded` | Integration status hint | Boolean only; not enough for share readiness. |
| `calibrated` | Calibration status hint | Boolean only. |
| `detections` | Detection count hint | Integer only; not a full Moment/Highlight contract. |
| `kpindex` | Space weather metadata | Numeric or `None`; conditional display in later product contexts. |
| `ovation_max` | Aurora metadata hint | Numeric or `None`; conditional display in later product contexts. |
| `smoke_rating` | Environmental metadata hint | Integer or `None`; conditional display in later product contexts. |
| `exclude` | Curation/exclusion hint | Boolean only; do not expose mutative behavior. |
| `fileSize` | File size metadata | Numeric or `None`; safe only as a value already in DB, not from filesystem stat. |
| `width` | Image dimension metadata | Numeric or `None`; safe if from DB. |
| `height` | Image dimension metadata | Numeric or `None`; safe if from DB. |

## Conditional Fields

These fields may be useful later, but must not be used in Step 3 unless there is a clear sanitizer and product reason.

| Field | Condition | Risk |
| --- | --- | --- |
| `dayDate` | Use only as a date label for grouping/reporting. | Can confuse latest frame timestamp if mixed with `createDate`. |
| `createDate_year` / `createDate_month` / `createDate_day` / `createDate_hour` | Use only for grouping/index verification, not primary display. | Duplicate derived time fields can drift from product language. |
| `data` | Use only with a nested allowlist of known safe keys. | JSON blob can contain mixed sensor/provider metadata and future unknown keys. |
| `sync_id` | Use only for internal sync diagnostics in Developer contexts. | Could expose integration internals. |
| `thumbnail_uuid` | Avoid for latest metadata; only consider in a future preview-specific audit. | Can become a preview/media identifier. |
| `remote_url` | Do not use in Latest Frame Metadata; only future preview/download audits may consider it. | Direct URL exposure. |
| `s3_key` | Do not use in Latest Frame Metadata; only future storage/integration audits may consider it. | Storage internals and object key leak. |
| `camera` relationship | Avoid in Step 3 unless already safely available in caller context. | Relationship access can add joins/lazy loads. |

## Forbidden Fields and Behaviors

These must not appear in Product UI Latest Frame Metadata.

Forbidden fields:

- `filename`
- `remote_url`
- `s3_key`
- raw `data` blob without an allowlist
- raw ORM object
- camera relationship object
- any storage path
- any RAW/FITS/source path
- any preview URL
- any generated media URL

Forbidden methods/helpers:

- `getUrl()`
- `getRelativePath()`
- `getFilesystemPath()`
- `validateFile()`
- `deleteFile()`
- `Path(...)` construction from image row data
- filesystem existence checks
- filesystem stat calls
- image/media readers
- RAW/FITS readers

Forbidden behavior:

- exposing `repr(row)` because it includes `filename`
- serializing `row.__dict__`
- passing the ORM row to Jinja/Product UI
- reading image bytes
- generating previews
- deriving live filesystem state
- doing joins for non-essential labels
- performing unbounded list queries

## Bounded Query

Allowed query shape for Step 3 Adapter:

```text
SELECT allowlisted metadata columns
FROM image
WHERE camera_id = current_camera_id
ORDER BY createDate DESC
LIMIT 1
```

Required properties:

- Single query.
- Bounded to one row.
- Metadata-only.
- Filtered by camera when camera context is available.
- Ordered by `createDate DESC`.
- `LIMIT 1`.
- No join.
- No relationship loading requirement.
- No file/path/media helper calls.
- No preview URL.
- No raw ORM object returned to Product UI.

If camera context is not available:

- The adapter must not silently perform an all-camera latest query unless explicitly approved in a later audit.
- Preferred behavior: return a safe `not_evaluated`/fallback payload.

## Risk Audit

### Path and filename leak

Risk: High if raw ORM rows or file helpers are exposed.

Guard:

- Never include `filename`.
- Never call `getUrl()`, `getRelativePath()`, `getFilesystemPath()`, or `validateFile()`.
- Validate payload for absolute paths and suspicious URL/path-like strings.

### URL/storage leak

Risk: Medium to High through `remote_url`, `s3_key`, thumbnail identifiers, or URL helpers.

Guard:

- No preview URL in Data 001.
- No storage keys in Product UI Latest Frame Metadata.
- Treat preview/media as a separate future audit.

### Timezone and naive datetime

Risk: Medium.

`createDate` is a DB datetime and may be naive depending on database/session behavior.

Guard:

- Adapter must format timestamp conservatively.
- If timezone cannot be proven, expose `timestamp_status` or note as local/unknown rather than overclaiming.

### Missing camera context

Risk: Medium.

Without a camera filter, latest image could come from another camera in multicamera setups.

Guard:

- Require camera id input for real metadata.
- Fall back safely if missing.

### Row absent

Risk: Low.

Expected when capture has not produced an image or DB is empty.

Guard:

- Return `status: no_frame` or `not_evaluated`.
- Do not raise to Product UI.

### DB error

Risk: Medium.

Guard:

- Catch adapter-level errors.
- Return fallback/not evaluated metadata.
- Do not leak raw DB exception text to Product UI.

### Query accidentally unbounded

Risk: Medium to High on Raspberry Pi 5.

Guard:

- Adapter test must prove one-row bounded behavior.
- Avoid `.all()`.
- Avoid list materialization.
- Avoid joins.

### Flask/Product coupling

Risk: Medium.

Guard:

- Product view model remains framework-free.
- Flask/service layer may supply camera id/query dependency later.
- Adapter output must be plain JSON-safe metadata.

### RPi5 performance

Risk: Low with guards, High without guards.

Guard:

- Use indexed fields.
- Query one row only.
- No filesystem checks.
- No media reads.
- No preview generation.

### Fallback behavior

Risk: Medium if fallback masks errors forever.

Guard:

- Product UI should show safe `not_evaluated`/fallback status.
- Logs may record operational errors, but raw errors must not be user-visible.

## Adapter Requirements for Step 3

Step 3 may create an adapter only if it follows these requirements.

Interface:

```text
get_latest_frame_metadata(camera_id) -> dict
```

Input:

- Required: `camera_id`
- Optional safe context: camera label provided by caller if already available.
- No request object.
- No Flask import inside product/domain module.
- No implicit global session in framework-free code.

Output:

The adapter must return only JSON-safe, allowlisted fields. Suggested output:

```text
{
  status,
  data_status,
  frame_id,
  camera_id,
  timestamp,
  timestamp_status,
  image_available,
  exposure,
  gain,
  binning,
  width,
  height,
  file_size,
  night,
  adu,
  sqm,
  stars,
  detections,
  source_status,
  note,
  evidence
}
```

Output requirements:

- `safe_preview_url` must remain `None`.
- No filename.
- No path.
- No URL.
- No raw `data` blob.
- No ORM object.
- No callable.
- No secrets/tokens/passwords.
- No filesystem-derived values.

Error handling:

- Missing camera id: safe fallback/not evaluated.
- No row: safe no-frame result.
- DB/query error: safe fallback/not evaluated.
- Missing optional fields: set `None` or explicit unknown labels.

Adapter must never expose:

- `filename`
- `remote_url`
- `s3_key`
- `thumbnail_uuid`
- filesystem path
- source RAW/FITS path
- media URL
- preview URL
- raw DB errors
- raw ORM row
- unfiltered JSON blob

## Tests Required for Step 3

Minimum adapter tests:

- Returns metadata for one fake row.
- Returns safe no-frame payload when no row exists.
- Returns safe fallback on query error.
- Requires camera id or safely falls back when missing.
- Uses bounded query behavior: camera filter, `createDate DESC`, `LIMIT 1`/first-row behavior.
- Does not call joins.
- Does not call `.all()`.
- Does not expose `filename`, `remote_url`, `s3_key`, `thumbnail_uuid`, or raw `data`.
- Does not call `getUrl()`, `getRelativePath()`, `getFilesystemPath()`, `validateFile()`, `exists()`, or `stat()`.
- JSON serializable output.
- Rejects or strips absolute paths.
- Rejects or strips secrets/tokens/password-like strings.
- Handles missing optional row attributes.
- Handles naive datetime conservatively.
- Does not import Flask/request/db session in framework-free product modules.
- NowView validation passes when supplied with adapter output through the existing provider boundary.

Minimum documentation/test notes:

- Real Flask/DB integration tests remain separate if the environment is unavailable.
- Preview/media URL tests are explicitly out of scope for Data 001.

## Stop Conditions

Do not proceed to Step 3 Adapter if any of these are true:

- The adapter would need to expose `filename`, path, URL, `remote_url`, `s3_key`, or `thumbnail_uuid`.
- The adapter would need filesystem access.
- The adapter would need preview/media generation.
- The adapter would need RAW/FITS reads.
- The adapter would need an unfiltered all-camera latest query.
- The adapter would pass raw ORM rows to Product UI.
- The adapter would import Flask/request into framework-free product modules.
- The adapter would require heavy joins.
- The adapter would require `.all()` or list materialization.
- The adapter would show raw DB errors to users.
- The tests cannot prove bounded metadata-only behavior.

## Final Decision

`IndiAllSkyDbImageTable` is approved for the next Adapter step only under strict guards.

The source is good. The dangerous part is not the table; it is accidental leakage of file/media behavior attached to the same ORM object.
