# Hybrid Shell Redesign

## Implemented architecture

The Modern Admin UI uses a single Hybrid Sky Console shell. At desktop widths of 1040 px and above, navigation is a persistent sidebar. Below 1040 px it becomes an accessible drawer controlled from the top bar. The same page content and destinations are available in both layouts.

The sidebar is intentionally small:

- **Observation:** Now, Highlights, Library, Observatory
- **Management:** Cameras, Settings, System

Highlights remains a first-class observation view. The capture-cycle report is reached contextually from Library, and specialized tools live in the hub where they are used: media tools in Library, scientific tools in Observatory, camera tools in Cameras, and operational tools in System. This keeps global navigation stable without removing useful destinations.

Now presents saved camera images first and labels the page as a snapshot. Saved images and timestamps are historical records; they do not claim that capture is currently live. Technical capture, output, and source metadata remains available in a disclosure.

The header exposes capture controls through a disclosure. Reboot is shown only within the System family. Existing permission checks still govern every action; moving a control in the interface does not broaden access.

## Page ownership

Library owns archive browsing, generated media, image and panorama loops, and the Sky Cycle report. Archive filters retain their existing query parameters and behavior, with secondary filters grouped under “More filters.”

Observatory owns sky-quality and scientific views, including charts, sensors, AstroPanel, VirtualSky, and keograms. Operational storage, task, and integration summaries remain available as supporting details.

Cameras owns camera inventory, configuration entry points, focus, simulation, calibration, and image diagnostics. System is the hub for diagnostics, storage and publication, user administration, notifications, updates, configuration history, restore, network, and GPIO functions.

Settings is organized by subject. Each subject page presents the common controls first and keeps less frequently used options under “Technical details.” The canonical Settings entry remains the route to the full configuration surface.

## Compatibility and safety

This work changes presentation and navigation ownership only. Backend routes, data providers, form fields, query parameters, runtime commands, authorization checks, and administrator requirements keep their existing semantics. Classic compatibility routes and underlying operational endpoints are unchanged.

The shell and navigation contracts are covered by:

- `testing/hybrid_shell_test.py`
- `testing/hybrid_navigation_browser_test.js`
- `testing/hybrid_navigation_redirect_test.py`
- `testing/hybrid_navigation_access_audit.py`
- `testing/hybrid_ui_structure_test.py`
- `testing/hybrid_settings_navigation_flow_test.py`

The deployed Linux candidate passed eight isolated runtime flows before activation. The Raspberry Pi was then fast-forwarded and gunicorn alone was reloaded; capture PID 6521, its zero restart count, and configuration revision 121 remained unchanged. Seven main HTTP routes, three served assets, and fresh decoded frames from both cameras passed bounded production checks. Access-policy coverage was verified in the isolated candidate. See [the 24 October release evidence](testing/evidence/hybrid-ui-redesign-20261024.json). No authenticated production browser was exercised, and the unavailable user journal prevents a clean-journal claim.
