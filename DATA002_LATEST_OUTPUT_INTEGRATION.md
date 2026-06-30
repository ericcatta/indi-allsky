# DATA002 - Latest Generated Output Metadata Integration

## Summary

DATA002 Step 4 wired latest generated output metadata into the Product UI starting with Now.

The integration is runtime-connected, read-only, metadata-only, and bounded. It does not expose preview URLs, filenames, paths, raw rows, raw data, media reads, filesystem helpers, downloads, sharing, or generation actions.

## Wiring Done

Runtime wiring was added in the Flask Modern Admin layer:

- `ModernAdminNowView.get_latest_generated_output_repository()`
- `build_now_view(latest_generated_output_repository=...)`

The Product view model remains framework-free. Flask builds the descriptors and repository; `build_now_view()` receives the repository and renders only the sanitized summary.

## Real Descriptors

Now builds descriptors for:

- `IndiAllSkyDbVideoTable` -> `timelapse`
- `IndiAllSkyDbMiniVideoTable` -> `mini_timelapse`
- `IndiAllSkyDbKeogramTable` -> `keogram`
- `IndiAllSkyDbStarTrailsTable` -> `startrail`
- `IndiAllSkyDbStarTrailsVideoTable` -> `startrail_video`
- `IndiAllSkyDbPanoramaImageTable` -> `panorama_image`
- `IndiAllSkyDbPanoramaVideoTable` -> `panorama_video`

Each descriptor uses:

- table query;
- `camera_id` field filter;
- `createDate.desc()` ordering;
- source label;
- no join;
- no media helper.

`LatestGeneratedOutputRepository` applies `limit(1)` and `first()` per descriptor.

## Fields Shown In Now

Now displays a compact `latest_generated_output_summary`:

- output type;
- timestamp;
- sky day;
- generation status label;
- uploaded status when available;
- success status when available;
- frames when available;
- framerate when available;
- file size metadata when available;
- dimensions when available;
- source table label;
- safety note.

## Fallback Behavior

Fallback is safe for:

- no camera context;
- missing camera id;
- descriptor construction failure;
- one table failing while another succeeds;
- all tables failing;
- no rows;
- missing fields;
- invalid or unsupported metadata values.

No raw exception text is exposed to the user.

## Output Detail

Output Detail was **not** connected in this step.

Reason:

- Output Detail is a result-specific surface.
- The current route has no output identifier.
- Wiring the latest output into Output Detail would blur "latest generated output" with "this output".
- A future step should add an explicit Output Detail data contract before runtime metadata is connected there.

## Excluded

Still excluded:

- preview URLs;
- filenames;
- paths;
- direct URLs;
- remote object keys;
- thumbnail identifiers;
- raw rows;
- raw data blobs;
- filesystem access;
- media reads;
- RAW/FITS reads;
- generated media reads;
- downloads/sharing;
- rendering or generation jobs;
- mutative actions.

## Test Coverage

Updated:

- `testing/product_view_models_test.py`

Coverage includes:

- Now payload includes `latest_generated_output_summary`;
- repository with output metadata;
- no output metadata;
- repository failure;
- unsafe metadata validation failure;
- adapter descriptor behavior from Step 3;
- JSON serialization;
- no absolute paths;
- product module remains free of Flask/request/db/session/open patterns.

Flask integration tests are not present in this repository path. Runtime wiring safety is covered by py_compile, static grep, and unit tests around the repository and Now builder contract.

## Residual Risks

- Multi-source querying means up to seven bounded DB queries on Now.
- Different output tables may use `createDate` semantics slightly differently.
- The current UI shows bytes directly instead of a formatted size label.
- No integration test exercises a real Flask request with live DB models.
- Output Detail remains fake/static until it has an identifier-aware contract.

## Step 5 Review Recommendation

Review whether DATA002 should be considered complete with minor risks.

Focus the review on:

- whether seven bounded queries are acceptable on RPi5;
- whether Now remains product-first;
- whether metadata labels are understandable;
- whether Output Detail should remain disconnected until a route-specific contract exists;
- whether a future formatted-size field should be added in the backend contract.
