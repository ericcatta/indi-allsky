# Hybrid Design System Convergence

## Purpose

This pass converges the approved Hybrid Sky Console visual language across Product UI pages and migrated operational pages.

It is not a redesign. It does not change Product Architecture, routes, runtime behavior, DATA001-DATA006 integrations, or backend providers.

## Pages Audited

The audit covered template-rendered pages under the Hybrid shell, including:

- Product surfaces: Now, Highlights, Sky Cycle, Moment, Output, Library, Observatory.
- Operational surfaces: Cameras, Loop, Latest/Images, Media, Info, Tools, System, Storage, Uploads, Logs, Tasks, Users, YouTube, FITS/RAW, keograms, startrails, panoramas, videos, Dark Library, and Long Term Keogram.
- Migrated settings and read-only operational pages that use `modern-admin-*` components inside the Hybrid shell.

## Differences Found

### Product Pages

Product pages already used the approved Hybrid Sky Console identity:

- compact shell;
- dark/day theme tokens;
- product-first panels;
- restrained scientific/astrophoto tone;
- strong hierarchy for status, evidence, trust, and generated outputs.

### Migrated Operational Pages

Operational pages were functional inside the Hybrid shell, but still had visible variation from the older Modern Admin visual system:

- larger rounded panels and cards;
- heavier shadows and blur;
- uneven section spacing;
- inconsistent heading sizes;
- toolbar/filter controls that felt separate from the Product UI;
- data tables with old spacing and color rhythm;
- media/live frames with legacy radius and contrast;
- camera/media cards that did not visually match Product cards;
- message and empty states with inconsistent panel treatment;
- Day mode coverage that depended on local legacy styles.

## Components Unified

The convergence layer in `hybrid-product-ui.css` now defines shared Hybrid tokens for every page rendered in `.hybrid-app-content`.

### Shared Tokens

Unified tokens now cover:

- panel background;
- soft panel background;
- primary text;
- muted text;
- dim text;
- line colors;
- accent colors;
- shadow color;
- day/night equivalents.

These tokens are available to both Product pages and migrated operational pages.

### Panels and Cards

Unified component treatment was applied to:

- `modern-admin-table-panel`;
- `modern-admin-dashboard-section`;
- `modern-admin-management-panel`;
- `modern-admin-status-card`;
- `modern-admin-camera-card`;
- `modern-admin-media-card`;
- `modern-admin-event-panel`;
- `modern-admin-empty-state`;
- `modern-admin-placeholder-page`;
- `modern-admin-message-panel`.

The shared language now uses:

- 7px radius;
- consistent borders;
- lighter shadows;
- no legacy blur;
- Hybrid day/night backgrounds;
- tighter card padding.

### Heading and Section Rhythm

Unified:

- section heading spacing;
- divider treatment;
- heading scale;
- heading weight;
- paragraph and note color;
- uppercase micro-label styling.

This reduces the gap between Product pages and operational pages without changing content.

### Tables

Unified:

- table scroll container border/background;
- header typography;
- cell spacing;
- row dividers;
- hover treatment;
- day/night readability.

This is important for storage, users, config history, FITS/RAW, media metadata, and operational lists.

### Toolbars and Controls

Unified:

- filter bars;
- filter rows;
- control strips;
- media toolbar;
- input/select styling;
- action rows.

The result keeps legacy functionality intact while making controls feel native to Hybrid.

### Buttons and Links

Unified:

- link grid items;
- media buttons;
- inline links;
- placeholder links;
- Bootstrap `.btn` inside Hybrid content.

They now share Hybrid pill styling, border rhythm, hover state, and day/night color behavior.

### Media and Live Frames

Unified:

- live frame;
- dashboard preview;
- media preview;
- media viewer frame;
- captions;
- filename/caption metadata.

The goal is visual consistency only. No preview routes, filesystem access, media reads, or generation behavior changed.

### Empty and Message States

Unified:

- empty states;
- placeholder pages;
- success/error message panels.

They now read as part of the same Hybrid system instead of legacy admin alerts.

## Components Left Intentionally Different

### Product Hero Panels

Product page first panels remain more editorial and directional than operational panels. They are intentionally distinct because they orient the user in the Product flow.

### Operational Forms and Workflows

Existing operational forms, legacy controls, and page-specific JavaScript behaviors remain functionally unchanged. They are visually wrapped and normalized, but not redesigned or removed.

### Media Gallery Layout

Gallery grids, media viewers, loop views, and Long Term Keogram retain their page-specific layout requirements. The convergence pass normalizes frames, cards, captions, and toolbars without altering gallery behavior.

### Legacy Consumer Paths

Some pages still contain operational concepts that are not Product-first. They remain available because they are useful for Alpha and may have dynamic or external consumers. They are visually contained inside the Hybrid shell rather than deleted.

## Safety Boundary

This convergence pass is CSS/documentation only.

It does not:

- change backend behavior;
- add queries;
- modify DATA001-DATA006 wiring;
- add routes;
- add features;
- add POST/fetch/AJAX;
- read media or filesystem;
- access RAW/FITS;
- generate media;
- modify Classic.

## Result

The Hybrid shell now exposes a single visual language for both new Product pages and migrated operational pages.

Users should no longer be able to immediately infer whether a page is new Product UI or migrated operational UI based only on visual treatment. Functional differences remain where they are useful, but the surface language is now shared.
