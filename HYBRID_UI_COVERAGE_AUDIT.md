# Hybrid UI Coverage Audit

## Scope

This pass expands the Hybrid Sky Console shell to the template-rendered
`/modern-admin` surface without changing backend behavior, providers, DATA001-DATA006
wiring, media access, or Classic routes.

The goal is visual and navigational consistency:

- keep Now as the Hybrid home;
- keep Home/Now always reachable;
- keep the Hybrid shell around Product, Operations, Observatory Tools, and System pages;
- make Day mode actually light across panels, cards, badges, drawers, tables, and frame cards;
- leave operational functionality intact.

## Pages Covered By The Hybrid Shell

All template-rendered endpoints whose request endpoint starts with
`indi_allsky.modern_admin` now receive the Hybrid shell from `base.html`.

Important covered groups:

- Product: Now, Highlights, Moment, Output, Sky Cycle, Library, Observatory.
- Operations: Cameras, Gallery, Images, Loop, Timelapses, Mini Timelapses, Keograms,
  Startrails, Startrail Videos, Panoramas, Panorama Loop, RAW Source, FITS Source.
- Observatory Tools: Sky Quality, Charts, Sensor Panel, Astropanel, VirtualSky,
  Focus, Camera Simulator.
- System: Storage, Uploads, YouTube, Drives, Logs, Tasks, Users, Notifications,
  System Info, System Index, Settings, Updates.

## Legacy Operational Pages

No operational page was removed. Some pages still contain legacy inner content
patterns, Bootstrap table classes, existing forms, or existing inline scripts.
They are treated as legacy operational pages inside the Hybrid shell rather than
fully redesigned Product UI pages.

This is intentional for the release-candidate path:

- it avoids changing runtime behavior;
- it avoids touching Classic;
- it preserves existing operational tools;
- it keeps risky cleanup/refactor work out of this pass.

## Left Outside The Hybrid Shell

These surfaces remain outside this pass:

- Classic UI routes.
- AJAX/API/action endpoints.
- Public media endpoints that do not render `base.html`.
- Backend media helpers and filesystem/media routes.

They are not removed or modified.

## Day Mode Fix

Day mode now overrides the main shell and legacy-compatible content layers:

- app background and top shell;
- drawer/menu;
- `modern-admin-shell` content wrapper;
- table panels;
- status cards;
- status pills and badges;
- links inside status cards;
- tables and `table-dark` variants;
- Bootstrap dark/secondary blocks inside Hybrid content;
- frame cards and latest camera image panels;
- fallback frame cards;
- code labels and muted text.

Dark/Night mode remains the default and keeps the existing Hybrid Sky Console
visual direction.

## Safety Boundary

This pass is visual/navigation only.

No new:

- DB query;
- provider;
- adapter;
- route;
- POST/fetch/AJAX call;
- backend mutation;
- filesystem scan;
- RAW/FITS read;
- media generation;
- Classic behavior change.

## Residual Risk

Some operational pages still have dense legacy content and may need targeted
visual polish later. That work should stay page-scoped and should not change
runtime behavior without a separate audit.
