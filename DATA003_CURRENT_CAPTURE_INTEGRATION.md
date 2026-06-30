# DATA003 - Current Capture Status Integration

## Summary

DATA003 integrates Current Capture Status into Now as a bounded, metadata-only product summary.

The integration is read-only, framework-separated, and does not use filesystem access, service checks, process probing, camera hardware probes, INDI/libcamera calls, polling, POST/fetch/AJAX, media reads, RAW/FITS reads, or mutations.

## Adapter Created

Implemented in:

- `indi_allsky/product_view_models.py`

New adapter:

- `CurrentCaptureStatusRepository`

The repository accepts primitive inputs:

- status code;
- injected status map;
- watchdog age in seconds;
- local/remote camera flag;
- focus mode flag;
- capture pause flag;
- daytime capture flag;
- daytime save flag;
- camera label.

It returns only JSON-safe metadata.

## NowView Contract

Now now includes:

- `current_capture_summary`

Fields:

- `status`;
- `capture_state`;
- `is_acquiring`;
- `camera_label`;
- `phase`;
- `policy_label`;
- `last_frame_status`;
- `coherence_label`;
- `source_status`;
- `note`;
- `evidence`.

Allowed `capture_state` values:

- `running`;
- `idle`;
- `paused`;
- `error`;
- `unknown`.

## Runtime Wiring

Implemented in:

- `ModernAdminNowView.get_current_capture_repository()`

The Flask layer reads:

- misc state `STATUS`;
- misc state `WATCHDOG`;
- already-loaded camera flags;
- current config `FOCUS_MODE`;
- current camera label.

The Flask layer injects a status-code mapping built from existing `constants.STATUS_*` values.

The product builder remains framework-free.

## UI Update

Now's Current Sky section now includes a compact Current Capture Status card.

It shows:

- capture state;
- policy explanation;
- camera label;
- current phase;
- latest-frame evidence;
- coherence label;
- source status.

It does not show numeric status codes, raw watchdog timestamps, service manager output, process state, or hardware diagnostics.

## Observatory Decision

Observatory was not connected in DATA003.

Reason:

- Observatory needs a broader readiness contract;
- DATA003 is intentionally narrow and Now-focused;
- connecting Observatory now would risk pulling in service/process/hardware health semantics too early.

## Fallback Behavior

Fallbacks:

- missing camera -> repository not connected;
- missing status -> `unknown`;
- missing watchdog -> watchdog age unavailable;
- invalid status -> `unknown`;
- adapter failure -> Now renders unavailable state;
- latest frame absent -> capture status still renders with reduced evidence.

No raw exception text is exposed.

## Excluded

Still excluded:

- preview;
- images;
- filesystem;
- RAW/FITS;
- media generation;
- detector data;
- AI/ranking;
- polling;
- hardware probing;
- INDI/libcamera calls;
- process probing;
- systemd checks;
- POST/fetch/AJAX;
- mutations;
- Classic changes.

## Test Coverage

Updated:

- `testing/product_view_models_test.py`

Coverage includes:

- default Now current capture summary;
- running status mapping;
- pause policy precedence;
- error status mapping;
- watchdog stale label;
- current phase / latest frame coherence;
- invalid capture state validation;
- unsafe metadata validation;
- JSON serialization;
- product module framework-free checks.

## Residual Risks

- Misc state freshness depends on the capture runtime updating `STATUS` and `WATCHDOG`.
- Running state plus latest-frame evidence is still a summary, not a proof of hardware capture.
- No full Flask/DB integration test exercises real misc state reads.
- Observatory readiness remains separate and unresolved.

## Review Recommendation

DATA003 should receive a post-integration review focused on:

- whether Now remains product-first;
- whether status mapping is too coarse;
- whether watchdog age should become a user-facing label later;
- whether Observatory should get a separate readiness contract next.
