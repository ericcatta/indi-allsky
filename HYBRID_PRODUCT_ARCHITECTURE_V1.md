# HYBRID PRODUCT ARCHITECTURE V1

## 1. Product Vision

Hybrid AllSky is a 24/7 sky-cycle console.

It records the sky, preserves the original sources, detects meaningful moments,
generates beautiful derived outputs, and explains the health of the observatory.

The product is not organized around configuration pages. It is organized around
the continuous sky cycle:

Now -> Sky Cycle -> Phase -> Moment -> Source -> Output -> Look -> Observatory

The product should help a user answer three questions quickly:

- What is happening now?
- What happened during this sky cycle?
- Is the observatory working well and preserving the original data?

## 2. Non-Goals

Hybrid AllSky is not:

- an admin panel;
- a clone of indi-allsky or its Classic UI;
- a complete Lightroom-style photo editor;
- a settings-first interface;
- a heavy frontend application that assumes desktop/server resources.

Existing Classic and Modern pages are technical evidence, not the product
definition.

## 3. Domain / Object Model

### Sky Cycle

The primary reporting unit. A Sky Cycle represents the continuous observation
cycle across day, sunset, night, sunrise, weather changes, generated media, and
observatory health. It is not night-only.

### Phase

A named segment inside a Sky Cycle, such as day, sunset, twilight, night,
sunrise, storm window, clear window, or another future sky-state segment.

### Moment

Something meaningful that happened in the sky or observatory. Moments may be
daytime or nighttime: clouds, storms, lightning, rainbows, sunrise, sunset, Sun,
Moon, meteors, aurora, stars, anomalies, sky-quality changes, or future AI
candidates.

### Source

The original preserved data: RAW, FITS, frame, frame range, or other source
material. Source data is never modified by product UI or rendering.

### Output

A derived artifact generated from Source data: image, timelapse, keogram,
startrail, highlight, report, social/share render, or scientific render.

### Look

A non-destructive rendering preset or recipe. Looks control how derived outputs
are rendered. They do not replace or modify Source data. Users may create custom
Looks.

### Observatory

The physical and operational system: cameras, profiles, storage, sensors,
connectivity, integrations, workers, and health.

### Source Lineage

The trace from Output back to Source. Every generated output should know which
source frame, source range, or source dataset produced it.

### Output Recipe

The reproducible rendering/generation description for an Output: output type,
source range, Look, generation settings, version, and future regeneration
requirements.

### Observatory Health

The product-level summary of whether capture, source preservation, storage,
generation, upload, sensors, profiles, and workers are healthy.

## 4. Frontend / Backend Boundary

The backend owns:

- domain objects and truth;
- permissions and safe action authorization;
- source lineage;
- rendering jobs and output recipes;
- source preservation rules;
- audit records;
- safe action contracts;
- data validation and redaction.

The frontend owns:

- layout;
- interaction;
- presentation;
- visualization;
- responsive behavior;
- progressive enhancement.

Templates must receive sanitized view models. Templates should not contain
domain logic, permission logic, source lookup logic, rendering logic, or
business rules.

## 5. Navigation Proposal

The product navigation should be domain-first:

- Now
- Sky Cycles
- Moments
- Outputs
- Observatory
- Looks
- Insights
- Automation
- Library
- Engine Room

### Now

The 24/7 live home. It shows current sky state, current phase, capture health,
latest source/output state, recent moments, source preservation, and warnings.

### Sky Cycles

Reports and history for complete sky cycles. A Sky Cycle report contains day,
night, transition phases, moments, outputs, source coverage, and observatory
health.

### Moments

The meaningful things Hybrid detected or selected. Moments are not limited to
meteors and are not limited to night.

### Outputs

Generated derived media and reports, always linked back to Source and Look.

### Observatory

Cameras, profiles, capture state, storage, sensors, connectivity, upload, and
overall health.

### Looks

Rendering presets and future custom Look management. Looks are non-destructive
and apply only to derived outputs.

### Insights

Sky quality, brightness, cloudiness, signal stability, SQM/ADU, trends, source
coverage, and explainable analytics.

### Automation

Capture policies, generation policies, retention policies, upload policies, and
future safe-action workflows.

### Library

Search and browse across cycles, moments, outputs, source availability, Looks,
and generated artifacts.

### Engine Room

Developer-level internals: logs, task queue, audit, APIs, raw config, legacy
fallbacks, detector internals, and safe action registry.

## 6. Basic / Advanced / Developer

Basic summarizes, it does not hide. It should answer what happened, what matters,
what was generated, whether sources were preserved, and whether the observatory
is healthy.

Advanced exposes control. It should provide profile-aware camera behavior,
source and retention policies, rendering/Look policies, analytics details,
automation policy, and integration status.

Developer exposes internals. It should provide raw diagnostics, task/log/audit
views, API and legacy compatibility information, raw settings, and safe-action
plumbing.

## 7. Rendering Model

Rendering is non-destructive.

- RAW/FITS/source data is preserved.
- Source data is never modified or overwritten.
- Outputs are derived from Source.
- Looks are presets/recipes applied to derived outputs.
- Users can create custom Looks.
- Future regeneration is a safe action, not an implicit UI mutation.

Example Looks may include Natural, Scientific, Daylight, Sunset, Aurora, Storm,
Moonlight, High Contrast, and user-defined custom Looks.

Hybrid should not become a full photo editor. It should generate good automatic
outputs, preserve originals, and let users export special source files to
external tools when desired.

## 8. Raspberry Pi 5 First Constraints

Hybrid AllSky remains Raspberry Pi 5 first.

Product UI should be:

- server-rendered first;
- progressively enhanced;
- lazy-loaded where data is large;
- paginated for lists;
- conservative with polling;
- careful with chart rendering;
- cache-friendly for cycle reports;
- queue-based for heavy processing.

Avoid:

- aggressive live dashboards;
- unbounded filesystem scans;
- non-paginated large tables;
- on-demand FITS/video conversion outside controlled jobs;
- heavy frontend bundles as a requirement.

## 9. Product Language

Basic product language should use sky and observatory concepts, not raw config
names.

Prefer:

- Source preserved
- Current phase
- Sky Cycle
- Look applied
- Generated from source frames
- RAW retention
- FITS source available
- Observatory healthy
- Needs attention

Avoid first-level display of:

- raw config key names;
- implementation route names;
- AJAX/API names;
- database table names;
- absolute paths;
- secrets, tokens, or credentials.

Technical details remain available in Advanced and Developer contexts.

## 10. First Prototypes

### Now

The first product page. It proves Hybrid is a 24/7 sky-cycle console, not a
night-only report or an admin dashboard.

### Sky Cycle Report

The first historical/reporting page. It shows day, night, phases, moments,
outputs, source coverage, and observatory health.

### Moment Detail

The first object-detail page. It proves one model can support lightning,
clouds, sunrise, meteors, aurora, Moon, anomalies, quality changes, and future
AI candidates.

## 11. Reuse From Current Work

The current work remains valuable as foundation:

- Modern shell;
- settings ownership map;
- final read-only settings pages as reference material;
- Safe Actions infrastructure;
- audit layer;
- media/source metadata pages;
- profile-first and multicamera work;
- protected Modern work;
- read-only task/log/notification/user pages;
- analytics, quality, metadata, and scientific source concepts.

These are foundations and evidence. They should not force the final product to
remain settings-first or Classic-parity-first.

## 12. Explicit Product Decision

Stop expanding `/modern-admin/settings/*` as the main product direction.

Settings pages helped consolidate ownership and product language, but the next
phase should move toward product-domain-first pages:

- Now;
- Sky Cycle Report;
- Moment Detail;
- Outputs;
- Observatory;
- Looks;
- Insights.

Future pages should be designed around domain objects and user outcomes, not
around configuration groups or Classic UI parity.
