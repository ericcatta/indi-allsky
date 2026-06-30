# Visual Redesign Pass 001 - Product UI Skin

This pass introduces a dedicated visual skin for the Product UI surfaces without
changing Product Architecture, routes, backend data providers, runtime behavior,
or Classic.

## Goal

Move the Product UI content area away from the older Modern/Admin card language
and toward a lighter, more deliberate Hybrid Sky Console:

- scientific / astro-observatory tone;
- stronger hierarchy;
- less uniform card rhythm;
- clearer status, evidence, trust, output, and readiness treatment;
- compact but useful hero sections;
- editorial sections with a subtle console grid;
- server-rendered and RPi5-first.

## Files Added

- `indi_allsky/flask/static/modern_admin/hybrid-product-ui.css`

The new stylesheet is intentionally scoped to `.hybrid-product-shell`, so it
does not affect Classic or the broader Modern/Admin UI.

## Templates Updated

The stylesheet is loaded only by Product UI surfaces:

- `indi_allsky/flask/templates/modern_admin/now.html`
- `indi_allsky/flask/templates/modern_admin/highlights.html`
- `indi_allsky/flask/templates/modern_admin/sky_cycle.html`
- `indi_allsky/flask/templates/modern_admin/moment_detail.html`
- `indi_allsky/flask/templates/modern_admin/output_detail.html`
- `indi_allsky/flask/templates/modern_admin/library.html`
- `indi_allsky/flask/templates/modern_admin/observatory.html`

Each target template now adds:

- the dedicated Product UI stylesheet;
- a scoped `hybrid-product-shell` class on the main Product UI container;
- a surface-specific class such as `hybrid-product-now` or
  `hybrid-product-sky-cycle` for future targeted polish.

## Visual Changes

The pass changes presentation only:

- wider Product UI content width;
- compact console-style hero with right-side link rail on desktop;
- darker graphite/black scientific surface with cyan, amber, green, and violet
  accents;
- subtle grid background inside Product UI only;
- tighter typography with larger product titles;
- section panels with finer borders and less Bootstrap/admin feel;
- card groups with varied accent lines so not every card feels identical;
- more readable status pills and links;
- responsive single-column behavior on smaller screens.

## What Stayed Unchanged

No backend or runtime behavior changed:

- no route changes;
- no Product Architecture changes;
- no Product View Model changes;
- no DATA001-DATA006 provider or adapter changes;
- no database query changes;
- no forms;
- no POST;
- no fetch/AJAX;
- no mutative actions;
- no media/file/RAW/FITS access;
- no Classic changes;
- no JavaScript.

## RPi5 Notes

The skin is CSS-only and lightweight.

It avoids:

- JavaScript;
- webfont downloads;
- image assets;
- media queries beyond simple responsive layout;
- heavy animations.

It uses simple gradients and borders. The only potentially notable visual cost
is the fixed subtle grid background and panel shadows; these should be checked
visually on Raspberry, but they do not affect backend workload.

## Risks

- The Product UI now visually diverges more from surrounding Modern/Admin pages,
  which is intended but may make sidebar/header contrast more obvious.
- The CSS uses existing generic Modern classes under a scoped wrapper; future
  Modern CSS changes could still affect Product UI if selectors become more
  specific.
- Browser visual QA was not performed in this pass.
- The skin improves hierarchy but does not solve remaining product limitations
  such as static Moment/Output/Library/Observatory data.

## Follow-up

Recommended next visual checks:

1. Browser screenshot of all seven Product UI routes.
2. Mobile-width screenshot of Now, Highlights, and Sky Cycle.
3. RPi5 browser check for scroll performance.
4. Small typography pass after real screenshot review.
