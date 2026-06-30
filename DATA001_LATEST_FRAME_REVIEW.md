# DATA001 Latest Frame Metadata Review

## 1. Verdict

COMPLETE WITH MINOR RISKS.

Data 001 successfully connected one real, bounded, metadata-only data source to Now:

- source: `IndiAllSkyDbImageTable`;
- adapter: `LatestFrameImageTableRepository`;
- provider: `LatestFrameSummaryProvider`;
- surface: `/modern-admin/now`;
- payload: `latest_frame_summary.frame_metadata`.

The integration is safe enough to consider Data 001 complete, with the caveat that full Flask/DB runtime integration tests remain unavailable.

## 2. Product Value

Latest Frame Metadata improves Now because it turns the Current Sky area from a mostly placeholder briefing into the first trustworthy product fact.

The user can now understand, at a glance:

- whether a latest frame metadata row exists;
- which camera context supplied it;
- when it was captured;
- how old it is;
- exposure, gain and binning;
- day/night hint;
- ADU/SQM/stars/detections when present;
- frame dimensions when present.

This is useful without becoming an image viewer. It answers "is the observatory producing frames?" before asking the user to inspect media.

## 3. Safety Value

The integration preserves the main Product UI safety boundaries:

- no preview URL;
- no filename;
- no filesystem path;
- no `remote_url`;
- no `s3_key`;
- no `thumbnail_uuid`;
- no raw `data` blob;
- no raw ORM row;
- no filesystem helper;
- no RAW/FITS read;
- no media read/generation;
- no POST/fetch/AJAX;
- no mutation.

The adapter exposes only allowlisted primitive metadata and validates the final Now payload before rendering.

## 4. Query / Fallback Review

Query shape is appropriate for RPi5-first runtime:

```text
IndiAllSkyDbImageTable.query
  -> filter(camera_id == current_camera_id)
  -> order_by(createDate DESC)
  -> limit(1)
  -> first()
```

Safety properties:

- single row;
- camera-scoped;
- no join;
- no list materialization;
- no pagination;
- no media/file helper call.

Fallback behavior is acceptable:

- missing camera/camera id returns no provider and Now falls back safely;
- provider construction failure returns no provider;
- missing row returns a no-frame summary;
- query error returns a redacted repository error summary;
- unsafe metadata is rejected and not rendered.

No raw exception text is exposed to Product UI.

## 5. UI Review

The Now UI remains product-first enough for this phase.

What works:

- metadata appears inside Current Sky rather than as a technical table;
- values are compact and readable;
- there is no media preview;
- the page still points the user toward Highlights rather than turning into a dashboard.

Minor risk:

- exposure/gain/ADU/SQM/stars are technical terms. They are acceptable for an all-sky/astrophoto product, but should stay compact and not grow into a full camera diagnostics panel.

Guard:

- keep latest frame metadata as a short confidence/status block;
- move deeper camera diagnostics to Observatory or Developer if it grows.

## 6. Test Coverage Review

Coverage is good for the current phase.

Covered:

- adapter with complete fake row;
- adapter with missing fields;
- adapter with no row;
- adapter with query error;
- forbidden row fields not exposed;
- non-primitive values handled safely;
- datetime serialization;
- bounded query calls;
- JSON-safe payload;
- `safe_preview_url` remains `None`;
- template renders metadata without form, POST, fetch, AJAX, or preview URL reference;
- product module has no Flask/request/db session/open dependency.

Still missing:

- full Flask integration test with real app/session/DB fixtures;
- real database row behavior across supported DB engines;
- timezone semantics for `createDate`;
- browser-render verification of the Now page.

These gaps do not block Data 001 completion, but they should remain visible.

## 7. Residual Risks

Residual risks:

- `createDate` timezone/naive datetime semantics are not fully modeled.
- Full Flask/DB integration tests are still blocked.
- Existing `IndiAllSkyDbImageTable` contains dangerous file/media behavior, so future edits must preserve the adapter allowlist.
- UI could drift technical if more frame fields are added.
- Multicamera correctness depends on safe camera context.

Risk level: Low to Medium.

The risk is acceptable because fallback is safe and the integration is metadata-only.

## 8. Stop List

Do not do next as part of Data 001:

- no preview URL;
- no image rendering;
- no latest image display;
- no RAW/FITS read;
- no detector integration;
- no media generation;
- no share/download;
- no filesystem checks;
- no path exposure;
- no filename exposure;
- no broad media joins;
- no output regeneration;
- no mutative safe actions.

Preview/media work requires a separate discovery/audit/adapter/integration sequence.

## 9. Next Data Recommendation

Recommended next data: latest generated output metadata.

Reason:

- It is the next safest product value after latest frame metadata.
- It supports Now's "Generated results" block and Output Detail without requiring previews.
- It can remain metadata-only.
- It can follow the same discovery -> audit -> adapter -> integration -> review pattern.
- It is safer than real Highlights because it does not require ranking or explanation quality yet.
- It is safer than source trust because source coverage may tempt filesystem/RAW/FITS reads.
- It is safer than Observatory readiness because real readiness can drift into live hardware/network/filesystem probes.
- It is safer than Sky Cycle metadata because cycle boundaries may require broader time-window logic.

Recommended scope for the next data sequence:

- discover existing generated output models/tables;
- identify one latest generated output metadata source;
- forbid preview URL, filename, path, media read, download, generation, and filesystem access;
- expose only type, timestamp/date, generation status metadata, look/recipe placeholder if already safe, and source-lineage status as not evaluated.

## Final Decision

DATA001 is complete with minor risks.

The first real data integration improved Now without breaking the Product UI safety model. The project can proceed to the next one-data-at-a-time real data sequence.
