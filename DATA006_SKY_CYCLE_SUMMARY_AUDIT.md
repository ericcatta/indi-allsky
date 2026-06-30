# DATA006 - Sky Cycle Summary Audit

## Verdict

GO WITH GUARDS.

Hybrid can expose a first bounded Sky Cycle Summary from image metadata. It cannot yet reconstruct a full day/night cycle, compute twilight, prove complete coverage, or connect moments/outputs to cycle boundaries.

## Product Goal

The summary should answer:

- which Sky Cycle the current data belongs to;
- whether the cycle appears current or completed;
- what the current phase is;
- what metadata supports the answer;
- what remains unknown.

## Chosen Source

### `IndiAllSkyDbImageTable`

Allowed fields:

- `id`
- `camera_id`
- `createDate`
- `dayDate`
- `night`

Reasons:

- canonical image metadata table;
- camera-scoped;
- `createDate` and `dayDate` are indexed;
- already used by video/timelapse code to group day/night outputs;
- no filesystem, media, detector, or source-file access is required.

## Rejected Sources

### Generated output tables

Rejected for DATA006 primary summary.

Reason: generated outputs are derived artifacts and may lag behind capture. They are useful context, but they should not define the cycle.

### RAW/FITS tables

Rejected for DATA006 primary summary.

Reason: source metadata is useful for trust but not guaranteed to exist for every image/cycle.

### Runtime astronomy / twilight calculation

Rejected for DATA006.

Reason: the current phase engine is not implemented. DATA006 must not add astronomical calculations in request paths.

### Filesystem/media helpers

Rejected.

Reason: forbidden by the real-data phase.

## Bounded Query Strategy

Two bounded queries are allowed:

```text
latest:
SELECT allowlisted metadata
FROM image
WHERE camera_id = current_camera_id
ORDER BY createDate DESC
LIMIT 1

cycle start:
SELECT allowlisted metadata
FROM image
WHERE camera_id = current_camera_id
  AND dayDate = latest.dayDate
ORDER BY createDate ASC
LIMIT 1
```

No count, scan, aggregation, joins, media reads, or filesystem checks are allowed.

## Derived Fields

Allowed derived summary fields:

- `cycle_label`
- `cycle_status`
- `cycle_started_label`
- `latest_frame_label`
- `time_range_label`
- `coverage_label`
- `confidence_label`
- `evidence`

Allowed statuses:

- `in_progress`
- `completed`
- `incomplete`
- `unknown`

## Risk Audit

- `dayDate` is a capture grouping field, not a full astronomical boundary.
- A first/latest image row does not prove complete coverage.
- Current date comparison can mislead if timezone context is wrong.
- Missing first row reduces confidence.
- Twilight remains unsupported.
- Moments, outputs, source lineage, and health remain out of scope.

## Integration Scope

DATA006 integrates Sky Cycle Report first.

Now is not changed in this step because duplicating the summary there would add surface area without improving the core Sky Cycle page enough.

## Stop Conditions

Stop or fallback if implementation requires:

- detector or AI;
- filesystem/media reads;
- RAW/FITS reads;
- preview URLs;
- unbounded queries;
- cycle reconstruction;
- twilight calculation;
- polling;
- mutations.
