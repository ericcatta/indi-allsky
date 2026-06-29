# HYBRID PRODUCT ARCHITECTURE V1

## 1. Product Vision

Hybrid AllSky is a 24/7 sky-cycle console.

It records the sky, preserves the original sources, detects meaningful moments,
generates beautiful derived outputs, and explains the health of the observatory.

The product is not organized around configuration pages. It is organized around
attention, trust, and the continuous sky cycle:

Now -> Highlights -> Moment / Output / Observatory Issue
    -> Sky Cycle Context -> Library

The product should help a user answer three questions quickly:

- What is happening now?
- What deserves attention?
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

### Highlight

A curated attention object.

A Highlight is not the Moment, Output, Sky Cycle, Source, or Observatory issue
it points to. It is the product-level selection that says: this deserves
attention, here is why, here is the evidence, here is the source/output/health
context, and here is where to go next.

Highlights may be suggested by Hybrid, confirmed or favorited by the user, or
proposed by future AI. They must remain explainable. A Highlight without a
reason is only noise.

Highlights are the connective tissue between Now, Moments, Outputs, Sky Cycles,
Observatory Health, and Library.

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
startrail, report, social/share render, or scientific render.

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
- Highlights
- Sky Cycles
- Moments
- Outputs
- Library
- Observatory
- Looks
- Insights
- Automation
- Engine Room

### Now

The 24/7 live home. It shows current sky state, current phase, capture health,
latest source/output state, recent Highlights, source preservation, and
warnings.

Now is a triage surface. It should not force the user through a complete Sky
Cycle report before showing what deserves attention.

### Highlights

The attention layer. Highlights surface what Hybrid or the user believes is
worth reviewing now: a meteor candidate, a strong timelapse, an aurora window,
an all-clear cycle, a source preservation warning, or an observatory issue.

Highlights can point to Moment, Output, Sky Cycle, Source, Observatory issue, or
future insight objects. They must explain why they were selected and whether the
underlying source/output/health context can be trusted.

### Sky Cycles

Reports and history for complete sky cycles. A Sky Cycle report contains day,
night, transition phases, moments, outputs, source coverage, and observatory
health.

Sky Cycle is context and archive. It is not always the mandatory second step
after Now.

### Moments

The meaningful things Hybrid detected or selected. Moments are not limited to
meteors and are not limited to night.

### Outputs

Generated derived media and reports, always linked back to Source and Look.

Outputs can be highlighted, but an Output is not itself a Highlight. The
Highlight explains why this output deserves attention.

### Library

Search and browse across Highlights, cycles, moments, outputs, source
availability, Looks, cameras, profiles, and generated artifacts. Library exists
because users remember phenomena and results more often than exact dates.

### Observatory

Cameras, profiles, capture state, storage, sensors, connectivity, upload, and
overall health.

Observatory is both a section and a trust layer. Observatory issues may become
Highlights when they affect source preservation, output validity, or capture
reliability.

### Looks

Rendering presets and future custom Look management. Looks are non-destructive
and apply only to derived outputs.

### Insights

Sky quality, brightness, cloudiness, signal stability, SQM/ADU, trends, source
coverage, and explainable analytics.

### Automation

Capture policies, generation policies, retention policies, upload policies, and
future safe-action workflows.

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

### Highlights

The first attention layer. It should prove that Hybrid can select what deserves
review before asking the user to browse Sky Cycles, Moments, Outputs, or
Observatory pages.

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

## 13. Revised Product Flow

The official product flow is no longer a strict line:

```text
Now -> Sky Cycle -> Moment -> Output -> Observatory
```

That line is too slow for common user intent. Users often want the meteor, the
best timelapse, the observatory warning, or the all-clear result before they
want to read the full cycle report.

The official flow becomes:

```text
Now
-> Highlights
-> Moment / Output / Observatory Issue
-> Source / Lineage / Trust
-> Sky Cycle Context
-> Library
```

Sky Cycle remains essential. It explains the complete observation period. It is
not demoted; it is repositioned as context, report, and archive instead of a
mandatory hallway.

Highlights are not perfect by default. They can become noisy if the selection
logic is weak, if AI suggestions are unexplained, or if Favorites are confused
with product attention. Therefore Highlights must remain explainable,
stateful, suppressible, searchable, and source-aware.
