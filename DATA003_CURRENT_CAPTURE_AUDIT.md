# DATA003 - Current Capture Status Audit

## Verdict

**GO WITH GUARDS**

Current Capture Status can be integrated safely if it is built from bounded persisted metadata and already-loaded camera policy fields.

Do not reuse presentation helpers directly. In particular, do not pass HTML status strings from `get_indi_allsky_status()` into Product UI. Use primitive persisted state values, camera policy flags, phase context, and latest-frame evidence.

## Allowed Sources

Primary source:

- persisted indi-allsky status value from misc state key `STATUS`;
- persisted watchdog timestamp from misc state key `WATCHDOG`.

Supporting sources:

- current camera row fields already available in the view:
  - `local`;
  - `capture_pause`;
  - `daytime_capture`;
  - `daytime_capture_save`;
  - camera label.
- existing `night` context already used by `current_phase_summary`;
- DATA001 latest frame summary as evidence only.

## Conditional Sources

- `BaseView.get_indi_allsky_status()` is acceptable as discovery evidence but should not be the adapter input because it returns HTML-oriented strings.
- `ModernAdminView.get_capture_status_label()` is safe but too lossy for the final adapter.

## Forbidden Sources

Forbidden for DATA003:

- systemd/service checks;
- subprocess/process probing;
- hardware checks;
- camera connection checks;
- INDI/libcamera calls;
- latest image JSON view logic;
- AJAX status response reuse;
- frame metadata analytics directories;
- task queue payloads;
- filesystem reads;
- media reads;
- RAW/FITS reads;
- polling;
- mutative actions.

## Allowed Status Mapping

The adapter may expose only product states:

- `running`;
- `idle`;
- `paused`;
- `error`;
- `unknown`.

Runtime status-code mapping should be supplied by the Flask/service layer, not hardcoded to Flask in the product builder.

Recommended mapping:

- `STATUS_RUNNING`, `STATUS_RELOADING`, `STATUS_STARTING` -> `running`;
- `STATUS_SLEEPING`, `STATUS_STOPPING`, `STATUS_STOPPED` -> `idle`;
- `STATUS_PAUSED` -> `paused`;
- `STATUS_NOCAMERA`, `STATUS_CAMERAERROR`, `STATUS_NOINDISERVER` -> `error`;
- missing/invalid values -> `unknown`.

## Adapter Requirements

The adapter must be framework-free and accept primitive values only:

- `status_code`;
- status code map;
- `watchdog_age_seconds`;
- `local_camera`;
- `focus_mode`;
- `capture_pause`;
- `daytime_capture`;
- `daytime_capture_save`;
- `camera_label`.

The output must be JSON-safe and include no raw misc state objects, HTML, DB rows, paths, URLs, or action metadata.

## Query / Runtime Bounds

The runtime layer may perform only bounded misc-state reads:

- read `STATUS`;
- read `WATCHDOG`;
- read camera fields already loaded by the base context.

No additional DB list query is required.

No systemd call, filesystem read, camera probe, or process probe is allowed.

## Fallback Requirements

Safe fallbacks:

- missing camera -> no current capture repository;
- missing `STATUS` -> `unknown`;
- missing `WATCHDOG` -> status still available, watchdog age unavailable;
- invalid status code -> `unknown`;
- adapter exception -> Now renders unavailable state;
- latest frame absent -> status still renders with lower evidence.

No raw exception text should reach Product UI.

## UI Boundary

Now may show:

- capture state;
- camera label;
- day/night phase;
- capture policy label;
- latest-frame coherence label;
- source status.

Now must not show:

- misc DB internals;
- numeric status codes;
- watchdog raw timestamp;
- service manager output;
- process state;
- hardware diagnostics.

## Observatory Decision

Do not wire Observatory in DATA003.

Reason:

- Observatory should eventually summarize broader readiness;
- DATA003 is specifically a Now-oriented "is capture happening?" fact;
- wiring Observatory now would invite service/process/hardware readiness semantics too early.

Observatory should receive a separate bounded readiness contract later.

## Stop Conditions

Stop or fall back if implementation requires:

- systemd;
- subprocess;
- filesystem;
- latest image file checks;
- INDI/libcamera;
- hardware probing;
- polling;
- task queue payload parsing;
- HTML status as final payload;
- raw DB/misc state objects;
- mutation or safe action.
