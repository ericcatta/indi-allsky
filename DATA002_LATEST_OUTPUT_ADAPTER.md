# DATA002 - Latest Generated Output Metadata Adapter

## Summary

Step 3 created a framework-free, descriptor-based adapter for latest generated output metadata.

The adapter is intentionally **not wired** to Now or any Product UI runtime route. It prepares the safe repository contract for a future integration step.

## Adapter Created

Implemented in:

- `indi_allsky/product_view_models.py`

New objects:

- `GeneratedOutputDescriptor`
- `LatestGeneratedOutputRepository`

The repository accepts injected descriptors and fake/query-like objects. It does not import Flask, does not use `db.session`, does not access the filesystem, and does not call media helpers.

## Descriptor Strategy

Each descriptor represents one generated-output source table and defines:

- `output_type`
- `query`
- `order_by_expression`
- optional `camera_id_field`
- `source_table_label`
- optional `field_map`
- optional `status_label`

This keeps table-specific details outside the selection logic and allows tests to run with fake queries instead of a real database.

## Exposed Fields

The selected output item may expose only metadata-safe fields:

- `output_type`
- `id`
- `camera_id`
- `timestamp`
- `day_date`
- `night`
- `uploaded`
- `success`
- `frames`
- `framerate`
- `file_size`
- `width`
- `height`
- `status_label`
- `source_table_label`

Missing fields are omitted or represented as `None` after sanitization.

## Excluded Fields

The adapter does not expose:

- filename/path values;
- remote URLs;
- object storage keys;
- thumbnail identifiers;
- preview URLs;
- raw ORM rows;
- raw data blobs;
- relationship objects;
- media helper output;
- filesystem-derived metadata.

Forbidden values present on rows are ignored because the adapter extracts only allowlisted fields.

## Query Behavior

For each descriptor, the repository applies a bounded query pattern:

```text
query
  .filter(camera_id_field == camera_id)   when camera_id_field is provided
  .order_by(order_by_expression)          when provided
  .limit(1)
  .first()
```

The adapter never calls list-style retrieval, pagination, joins, or media serializers.

## Multi-Source Selection Behavior

The repository collects one sanitized candidate per descriptor and selects the latest candidate by safe timestamp label.

Behavior:

- one descriptor can fail without breaking the entire result;
- failed descriptors increment `partial_failures`;
- descriptors with no row are skipped;
- if no descriptor returns a row, the result is safe empty metadata;
- if all available descriptors fail, the result is a redacted unavailable status.

## Fallback Behavior

Safe fallback cases:

- missing camera context;
- descriptor without query;
- query error;
- row absent;
- missing timestamp;
- non-primitive values;
- unsafe path/URL/secret-like values.

No raw exception details are returned to Product UI callers.

## Test Coverage

Updated:

- `testing/product_view_models_test.py`

Added coverage for:

- one descriptor with a valid row;
- multi-descriptor latest selection;
- partial table failure with another table succeeding;
- no rows;
- query error;
- missing camera context;
- forbidden row fields not exposed;
- datetime serialization;
- bounded query calls;
- JSON serialization;
- path/URL/callable/non-primitive sanitization;
- product module remaining framework-free.

## Step 4 Integration Remaining

Step 4 may wire this adapter into Now only after creating real descriptors in the Flask/service layer.

The integration must still preserve:

- no preview URL;
- no file or media access;
- no RAW/FITS read;
- no generated media read;
- no route/template behavior change beyond displaying already-sanitized metadata;
- safe fallback if DB/model/camera context is unavailable.

Recommended Step 4 shape:

- Flask/service layer builds descriptors for the generated-output tables;
- product repository receives descriptors and camera context;
- Now builder receives sanitized metadata through an injected provider/summary contract;
- Product UI never receives raw rows, filenames, paths, URLs, or helper output.
