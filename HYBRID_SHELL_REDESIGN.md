# Hybrid Shell Redesign

## Decision

Product UI routes now use a dedicated Hybrid Sky Console shell instead of the legacy left admin sidebar.

The shell is conditional in `base.html` and applies only to:

- Now
- Highlights
- Sky Cycle
- Moment
- Output
- Library
- Observatory

Classic and non-product Modern/Admin routes keep the existing layout and behavior.

## Navigation Model

The new shell uses:

- a sticky top app bar;
- a persistent Home/Now link;
- primary Product navigation in the top bar;
- a lightweight hamburger drawer for full navigation;
- separate drawer sections for Product, Operations, and System.

Product navigation includes:

- Now
- Highlights
- Moment
- Output
- Sky Cycle
- Library
- Observatory

Operational/System navigation keeps access to cameras, media, loop, generated media, sky quality, charts, sensors, system info, and settings without presenting Classic/Modern as the product identity.

## Latest Frames Fix

Now latest camera frames accept safe local web routes that contain `/images/`, including deployments mounted under a prefix such as `/indi-allsky/images/...`.

The image source remains conservative:

- latest image metadata row per camera;
- maximum two cameras;
- existing web image route only;
- no filesystem scan;
- no `getFilesystemPath()`;
- no RAW/FITS read;
- no media generation;
- fallback cards if image metadata or safe route is unavailable.

## Theme Modes

The Product shell supports:

- Night mode, default;
- Day mode, client-side only.

The toggle stores only a UI preference in `localStorage`. It does not call the backend and does not mutate server state.

If JavaScript is unavailable, the Product UI remains usable in default Night mode and the hamburger remains CSS-first through a checkbox/label control.

## Safety Boundary

This redesign does not change:

- Product Architecture;
- DATA001-DATA006 providers or contracts;
- backend mutations;
- Classic runtime;
- media generation;
- filesystem access;
- RAW/FITS access;
- route behavior except the already existing `/modern-admin -> /modern-admin/now` redirect.

No POST/fetch/AJAX is added for the Product shell.
