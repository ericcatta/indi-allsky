# DATA006 - Sky Cycle Summary Integration

## Summary

DATA006 connects a first bounded Sky Cycle Summary to the Sky Cycle Report page.

The integration uses image metadata only. It does not reconstruct the full cycle, calculate twilight, inspect files, read media, or connect moments/outputs/source lineage.

## Adapter

Added:

- `SkyCycleSummaryRepository`

The repository is framework-free and receives:

- latest image query;
- cycle-start image query;
- camera id;
- camera id field;
- day-date field;
- latest ordering expression;
- cycle-start ordering expression;
- current date.

## Runtime Wiring

Added:

- `ModernAdminSkyCycleView.get_sky_cycle_repository()`

Runtime descriptors use:

- `IndiAllSkyDbImageTable.query`
- current camera id
- `IndiAllSkyDbImageTable.camera_id`
- `IndiAllSkyDbImageTable.dayDate`
- `createDate.desc()` for latest frame
- `createDate.asc()` for cycle start
- `self.camera_now.date()` for current date comparison

## Product Contract

`build_sky_cycle_report_view()` now accepts:

- `sky_cycle_repository=None`
- `current_phase_night=None`

`cycle_summary` now includes:

- `cycle_status`
- `cycle_started_label`
- `latest_frame_label`
- `coverage_label`
- `confidence_label`
- `evidence`

## UI

The Sky Cycle page now shows:

- current phase;
- cycle status;
- confidence;
- start/latest timestamps;
- coverage label;
- evidence items.

The rest of the page remains static/fake until later bounded data steps.

## Fallback Behavior

If repository construction fails, camera context is unavailable, latest row is missing, or query execution fails, Sky Cycle Report falls back to the existing safe placeholder summary.

If the latest row exists but cycle-start metadata is missing, the summary is marked `incomplete` with lower confidence.

## Explicitly Excluded

Still excluded:

- detector;
- AI/ranking;
- media reads;
- filesystem;
- preview URL;
- RAW/FITS reads;
- media generation;
- twilight calculation;
- full cycle reconstruction;
- POST/fetch/AJAX;
- mutations;
- Classic changes.

## Tests

Added tests for:

- current/in-progress cycle metadata;
- completed cycle metadata;
- incomplete cycle metadata;
- unknown/missing metadata fallback;
- bounded query calls;
- JSON safety;
- no paths, secrets, or callables.

## Remaining Work

Future DATA work can discover bounded Sky Cycle outputs/moments/source coverage, but only after identifier-specific relationships are defined.
