# DATA003 - Current Capture Status Review

## Verdict

**COMPLETE WITH MINOR RISKS**

Current Capture Status is integrated into Now as a bounded, metadata-only product fact. It improves the user's ability to answer "is the system acquiring?" without turning Now into a technical dashboard.

## Product Value

Now can now summarize:

- whether capture appears running, idle, paused, error, or unknown;
- whether the camera policy allows normal acquisition;
- whether the latest frame evidence is consistent enough with the capture state;
- whether day/night context may affect interpretation.

This directly improves the first-glance product experience.

## Safety Value

The integration preserves the safety model:

- no filesystem access;
- no image/media reads;
- no RAW/FITS reads;
- no preview;
- no service/process probing;
- no systemd calls;
- no INDI/libcamera calls;
- no hardware checks;
- no polling;
- no POST/fetch/AJAX;
- no actions or mutations;
- no Classic changes.

The product builder remains framework-free. Flask reads bounded primitive state and injects it into a framework-free repository.

## Architecture Review

The architecture follows the DATA001/DATA002 pattern:

- source discovery;
- audit;
- adapter;
- runtime wiring;
- review.

The important design decision was to avoid reusing the HTML-oriented `get_indi_allsky_status()` payload directly. Instead, Flask reads the primitive misc-state values and supplies a status map to the product adapter.

This keeps domain language out of the template and avoids raw HTML/presentation coupling.

## UI Review

The Now UI remains product-first.

The Current Capture Status card is compact and answers the user-facing question before exposing evidence. It does not show status codes, watchdog timestamps, service output, or low-level runtime diagnostics.

The UI is still cautious: it uses "consistent enough" language because capture status and latest frame metadata are evidence, not absolute proof of hardware acquisition.

## Test Coverage Review

Tests cover:

- default fallback summary;
- running mapping;
- pause policy precedence;
- error mapping;
- watchdog stale source status;
- latest frame coherence;
- invalid capture state validation;
- unsafe metadata rejection;
- JSON serialization;
- product module framework separation.

Missing:

- real Flask/DB/misc-state integration test;
- performance test for misc-state access;
- exact end-to-end status behavior when runtime state is stale or inconsistent.

These are acceptable minor risks because fallback behavior is safe.

## Observatory Decision Review

It was correct not to wire Observatory in DATA003.

Observatory is about readiness across camera, capture, source preservation, storage, generation, and integrations. DATA003 is narrower: "what is capture doing now?"

Connecting Observatory now would risk introducing service checks, hardware probes, or broader readiness semantics too early.

## Residual Risks

- Persisted `STATUS` can be stale if runtime state is not updated correctly.
- Watchdog age is evidence, not a guarantee of capture health.
- Latest frame availability is not proof of live acquisition.
- Status mapping is intentionally coarse.
- Current Capture Status does not yet explain cadence or next expected frame.

## Stop List

Do not add next:

- systemd status;
- process checks;
- hardware checks;
- INDI/libcamera connection checks;
- latest image file checks;
- filesystem reads;
- polling;
- preview/media;
- RAW/FITS reads;
- capture actions;
- restart/start/stop controls;
- technical Observatory readiness by stealth.

## Next Data Recommendation

Recommended next data: **source trust summary discovery**.

Reason:

- Now now has current state, latest frame, and latest generated output.
- The next product question is "can I trust the sources behind this?"
- It should remain discovery/audit-first because source trust risks pulling in filesystem, RAW/FITS coverage, and lineage semantics too early.

Alternative:

- Observatory readiness can follow, but only after a separate readiness contract forbids live probes in request paths.
