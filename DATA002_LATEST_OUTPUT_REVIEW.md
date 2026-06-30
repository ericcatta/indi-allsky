# DATA002 - Latest Generated Output Metadata Review

## 1. Verdict

**COMPLETE WITH MINOR RISKS**

DATA002 successfully connects bounded, metadata-only latest generated output data into Now. The implementation improves product value without crossing the safety boundary into previews, file access, media reads, rendering, downloads, sharing, or mutations.

The remaining risks are mostly operational and test-depth related: seven bounded queries may be acceptable but should be watched on RPi5, and there is no full Flask/DB integration test for the runtime descriptor factory.

## 2. Product Value

Now is more useful because it can answer one more concrete product question:

**What did Hybrid generate most recently?**

The user can see a compact summary of the latest generated result type, timestamp, sky day, generation status, upload/success flags where available, frame count/framerate where available, dimensions, and stored size metadata.

This helps Now feel less like a static prototype and more like the first page of a real all-sky console. It also supports the product mission: trustworthy knowledge and generated results, without forcing the user into a media gallery.

## 3. Safety Value

The integration preserves the important boundaries:

- no filename exposure;
- no path exposure;
- no direct URL exposure;
- no preview URL;
- no remote URL;
- no storage key;
- no thumbnail identifier;
- no raw ORM row;
- no raw data blob;
- no filesystem access;
- no media read;
- no RAW/FITS read;
- no generation job;
- no download/share behavior;
- no POST/fetch/AJAX;
- no mutation.

The Product view model remains framework-free. Flask creates descriptors and a repository, while the product builder receives sanitized repository output.

## 4. Multi-Source Query And Fallback Review

The multi-source strategy is acceptable for this phase.

Runtime descriptors cover:

- `timelapse`;
- `mini_timelapse`;
- `keogram`;
- `startrail`;
- `startrail_video`;
- `panorama_image`;
- `panorama_video`.

Each descriptor is bounded through the repository:

- filter by camera id;
- order by `createDate DESC`;
- `limit(1)`;
- `first()`;
- no join;
- no list;
- no pagination;
- no media helper.

Fallback behavior is correct:

- no camera context -> no connected metadata summary;
- descriptor construction failure -> Now still renders;
- row absent -> safe empty summary;
- one table failure -> partial failure tolerated;
- all failures -> safe unavailable summary;
- unsafe values -> omitted or rejected before reaching the template.

The main tradeoff is query count. Seven small bounded queries are defensible for v1, but this should be reviewed if Now becomes slower on RPi5.

## 5. UI Review

The Now UI remains product-first.

The latest generated output card is compact and informational. It does not become a media browser, gallery, technical table, or output management panel. It answers "what was generated?" without inviting unsafe actions.

The card still shows raw-ish metadata such as bytes. That is acceptable for this phase but should eventually become a product label such as "Stored size" with formatted values from the backend.

## 6. Test Coverage Review

Coverage is good for a bounded metadata integration:

- Now payload includes `latest_generated_output_summary`;
- repository with output metadata;
- no output;
- repository error;
- unsafe metadata validation failure;
- descriptor adapter behavior;
- partial failure;
- all failures;
- JSON serialization;
- no absolute path payload;
- product module stays free of Flask/request/db/session/open patterns.

Missing coverage:

- no full Flask request integration test;
- no real DB fixture test;
- no performance test for seven descriptors on RPi5;
- no regression test proving every descriptor maps to the intended real table at runtime.

These are acceptable minor risks for DATA002 because the runtime path is fallback-safe.

## 7. Output Detail Decision Review

It was correct **not** to connect Output Detail.

Reason:

- `/modern-admin/output` is not identifier-specific;
- Output Detail should describe one selected output, not the latest output globally;
- wiring latest output there would confuse product semantics;
- no preview/file/media behavior is allowed yet;
- a future Output Detail runtime contract should define how an output is selected before data is connected.

Output Detail should remain static/fake until it has a route or view model that can represent a specific output safely.

## 8. Residual Risks

- Seven bounded queries may still be noticeable on a constrained RPi5 under load.
- `createDate` is consistent enough for latest metadata, but it is not the same as sky-cycle semantic date.
- `file_size` is a raw byte value and may need backend formatting later.
- Missing Flask/DB integration tests could hide descriptor construction regressions.
- Future edits might be tempted to reuse media serializers or route helpers; that must remain forbidden.

## 9. Stop List

Do not do next as part of DATA002:

- preview URL;
- open output behavior;
- media rendering;
- file reads;
- RAW/FITS reads;
- detector integration;
- generation jobs;
- share/download behavior;
- media route helper reuse;
- filename/path/URL exposure;
- broad output gallery behavior inside Now.

## 10. Next Data Recommendation

Recommended next data: **current capture status**.

Reason:

- it directly improves Now;
- it is likely smaller and safer than source trust, highlights, or sky-cycle metadata;
- it can potentially come from already available service/status context;
- it should not require filesystem access, media reads, RAW/FITS reads, detector data, or output generation;
- it keeps the next real-data step focused on operational truth rather than inference.

Not recommended next:

- source trust summary: valuable, but likely needs source coverage semantics and lineage definitions;
- observatory readiness metadata: valuable, but risks becoming live health checks too early;
- highlight metadata: requires selection reasons and ranking safety;
- sky cycle metadata: broader and easier to over-scope.

Proceed with a discovery/audit step for current capture status before implementation.
