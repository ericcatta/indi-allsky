# DATA001 Latest Frame Metadata Integration

## Scope

Step 4 connects the latest frame metadata adapter to Now runtime through the existing provider boundary.

This integration remains read-only and metadata-only.

It does not add preview URLs, filesystem access, media reads, RAW/FITS reads, downloads, sharing, POST/fetch/AJAX behavior, or mutations.

## Wiring Done

Runtime surface:

- `/modern-admin/now`

Wiring location:

- `ModernAdminNowView.get_latest_frame_provider()`
- `indi_allsky/flask/views.py`

Provider path:

```text
ModernAdminNowView
  -> LatestFrameImageTableRepository
  -> LatestFrameSummaryProvider
  -> build_now_view()
  -> now.html
```

The Flask view constructs the repository/provider from safe request context and passes the provider into the framework-free NowView builder.

The product view model remains framework-free:

- no Flask import;
- no request object;
- no `db.session`;
- no filesystem access;
- no media helper access.

## Query Behavior

The runtime repository receives:

- `IndiAllSkyDbImageTable.query`;
- `camera_id` from the current camera context;
- `camera_id_field` from `IndiAllSkyDbImageTable.camera_id`;
- `order_by_expression` from `IndiAllSkyDbImageTable.createDate.desc()`.

The adapter applies:

```text
filter(camera_id == current_camera_id)
order_by(createDate DESC)
limit(1)
first()
```

Properties:

- one row only;
- camera scoped;
- metadata-only;
- no join;
- no list materialization;
- no pagination;
- no file/media helper calls.

## Metadata Now Available

`latest_frame_summary.frame_metadata` can now contain:

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

The Now template renders a compact read-only summary:

- timestamp and age;
- exposure;
- gain;
- binning;
- day/night hint;
- ADU;
- SQM;
- stars;
- detections;
- frame size.

## Excluded

Still excluded:

- filename;
- path;
- URL;
- preview URL;
- `remote_url`;
- `s3_key`;
- `thumbnail_uuid`;
- raw `data`;
- raw ORM row;
- filesystem checks;
- media reads;
- RAW/FITS reads;
- media generation;
- download/share actions;
- mutative controls.

`safe_preview_url` remains `None`.

## Fallback Behavior

Now falls back safely when:

- camera context is missing;
- camera id is missing;
- provider construction fails;
- query construction fails;
- the latest row is absent;
- the query raises;
- metadata contains unsupported or unsafe values.

Failures do not expose raw exceptions to users. The Product UI payload remains JSON-safe and read-only.

## Test Coverage

Unit/static coverage includes:

- adapter with complete fake row;
- adapter with missing fields;
- adapter with no row;
- adapter with query error;
- forbidden row fields not exposed;
- timestamp serialization;
- bounded query calls;
- JSON-safe payloads;
- no absolute path or URL in latest frame metadata;
- `safe_preview_url` remains `None`;
- Now template renders frame metadata without form, POST, fetch, AJAX, or preview URL references.

Runtime Flask/DB integration tests remain blocked until a real Flask test environment with app/session/DB fixtures is available.

## Residual Risks

- Real database behavior is still covered indirectly by fake-query unit tests, not full Flask integration tests.
- `createDate` timezone semantics remain conservative and are not yet a full time model.
- Camera label/profile label remain limited by safe context availability.
- The Now page now shows useful metadata, but source confidence and output status are still largely placeholder contracts.

## Step 5 Review Recommendation

Step 5 should perform a post-integration safety and product review:

- confirm no path/URL/filename leaks in the rendered Now payload;
- review the product usefulness of the metadata shown;
- decide whether the next real-data integration should be bounded source preservation, latest generated output metadata, or a small Observatory readiness signal;
- keep preview/media integration out of scope until separately audited.
