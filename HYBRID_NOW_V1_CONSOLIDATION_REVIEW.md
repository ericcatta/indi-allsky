# HYBRID NOW V1 CONSOLIDATION REVIEW

## Purpose

This review decides whether Now v1 is consolidated enough to pause further Now
expansion and begin the next product surface.

It reviews `/modern-admin/now` after these additions:

- backend-owned NowView;
- validation;
- latest frame metadata with bounded DB provider and safe fallback;
- current phase summary from existing `context['night']`;
- source confidence summary as a fake/static contract;
- product-first template;
- no preview URL;
- no actions;
- no JavaScript/fetch.

## Executive Verdict

Now v1 is consolidated enough to pause.

It is not finished, but it has achieved its purpose:

1. prove the Product UI direction;
2. prove backend-owned sanitized view models;
3. prove bounded runtime data can enter safely;
4. show the right product questions without becoming an admin panel.

More Now work is possible, but the next higher-value move is to start the first
Sky Cycle Report surface.

## 1. Now v1 As Product

### First 10 Seconds

Score: 8/10.

The page now gives the user three immediate signals:

- current phase: day, night, or unknown;
- latest frame metadata availability;
- source confidence is a known product concern, even if not evaluated yet.

That is enough to stop feeling like a pure mockup.

The page still does not answer:

- how the current/previous sky cycle went;
- what was worth reviewing;
- whether generated outputs are ready;
- whether observatory health is actually good.

### Utility For Astrophiles

Score: 7.5/10.

Useful:

- current phase;
- latest frame metadata;
- Notable Moments area as a clear future destination.

Missing:

- real moments;
- best media;
- cycle summary;
- weather/sky quality context.

### Utility For Astrophotographers

Score: 7.5/10.

Useful:

- non-destructive output language;
- source confidence direction;
- latest frame metadata.

Missing:

- output readiness;
- Look applied;
- source lineage;
- source preservation proof.

### Utility For Science Users

Score: 7/10.

Useful:

- explicit evidence/confidence model;
- bounded/latest metadata discipline;
- no invented claims.

Missing:

- coverage metrics;
- quality metrics;
- moment evidence;
- source lineage.

### Value Versus Old Modern/Admin UI

Score: 8.5/10.

Now is a meaningful break from admin-first UI. It is organized around product
questions:

- What is happening now?
- Can I trust the sources?
- What is worth reviewing?
- Is the observatory healthy?

This is more valuable than another settings/status page, even while much of the
data is still placeholder.

### Tone

Score: 8/10.

The tone is mostly correct:

- scientific;
- operational;
- astrophoto-aware;
- not poetic;
- not consumer-photo;
- not a Classic copy.

Remaining weakness: several labels still sound like implementation scaffolding:

- `pending backend contract`;
- `placeholder answers`;
- `not evaluated`.

Those are acceptable in v1, but final product copy should become more natural
once backend truth exists.

### What Remains Too Placeholder

The most placeholder-heavy areas are:

- Current / Morning Briefing verdict;
- Sky Cycle briefing;
- Notable Moments;
- Generated Outputs;
- Observatory Health;
- Source Confidence.

That is acceptable because Now v1 is a foundation. It is not acceptable to keep
adding more placeholder sections to Now instead of beginning the next product
object.

## 2. Now v1 As Architecture

### Frontend / Backend Separation

Score: 9/10.

The architecture is healthy:

```text
Flask view/context -> provider/factory -> product view model -> validation -> template
```

The template renders sanitized data. It does not perform domain lookup, source
path resolution, permission decisions, filesystem checks, or business logic.

### Product View Model

Score: 9/10.

NowView has become a real contract candidate:

- framework-free builder;
- explicit payload sections;
- JSON-safe output;
- validation before template rendering;
- provider injection for bounded runtime data.

The contract is still early, but the shape is correct.

### Validation

Score: 8.5/10.

Strong:

- required sections;
- allowed data statuses;
- phase allowlist;
- risk allowlist;
- secret/path/callable rejection;
- `safe_actions_available` remains metadata-only.

Missing:

- schema version enforcement;
- stricter type checks for every nested field;
- integration tests for rendered payloads.

### Provider / Fallback Pattern

Score: 8.5/10.

The latest-frame provider is a good first runtime pattern:

- bounded;
- camera-scoped;
- metadata-only;
- fallback-safe;
- no path/filename/preview URL.

Do not repeat provider construction directly inside the Flask view for many
more fields. The next runtime data source should probably move toward a small
Now service/factory.

### RPi5-First

Score: 9/10.

Now remains light:

- server-rendered;
- no frontend framework;
- no polling;
- no filesystem scan;
- no media processing;
- one bounded metadata query;
- fake/static source confidence.

### Coupling Risks

Risk: medium.

The main risk is not current code. The risk is future growth:

- adding more direct query construction to `ModernAdminNowView`;
- turning Now into a technical dashboard;
- adding preview/media/source checks too early;
- adding unbounded lists;
- adding frontend refresh before backend summaries exist.

## 3. Now v1 As Future Base

### What Can Become Real Later

Safe future candidates:

- latest frame profile label;
- source confidence from a bounded/cached backend summary;
- output readiness from bounded generated-media metadata;
- current verdict derived from small summary statuses;
- attention items from safe notification summaries;
- observatory health from bounded status services.

### What Not To Touch Yet

Do not add yet:

- preview URL;
- image rendering;
- RAW/FITS reads;
- source filesystem inspection;
- media generation;
- moment detection;
- actions;
- downloads;
- task queue mutation;
- polling/live refresh.

### Remaining Blockers

Blockers before Now becomes final:

- real Flask integration tests for `/modern-admin/now`;
- full app/session/DB test fixture;
- source coverage backend contract;
- Sky Cycle object/boundary;
- Moment object/source;
- Output readiness contract;
- observatory health summary contract;
- final product route outside `modern-admin`.

### Ready To Pass To Sky Cycle Report?

Yes, with limits.

We are ready to start Sky Cycle Report as a product surface prototype and
backend-owned contract.

We are not ready to connect real Sky Cycle runtime data yet.

The first Sky Cycle mission should be static/fake-safe and contract-oriented,
similar to the original Now mission, but informed by the lessons from Now:

- backend-owned view model from the start;
- validation from the start;
- clear placeholder/status fields;
- no DB/filesystem/media generation;
- no heavy UI.

## 4. Final Now v1 Score

Final Now v1 score: 8.2/10.

Why not higher:

- most product answers remain placeholder;
- no real cycle report;
- no real moment evidence;
- no real output readiness;
- no real observatory health;
- no Flask integration tests.

Why high enough:

- strong product direction;
- real bounded latest-frame metadata;
- real bounded day/night phase signal;
- source confidence contract;
- clean frontend/backend boundary;
- validation;
- RPi5-first implementation;
- no unsafe actions or source access.

Now v1 is good enough to serve as the first product surface foundation.

## 5. Next Direction

Recommendation: start Sky Cycle Report.

Do not continue adding placeholder-only sections to Now.

Do not start Moment Detail yet. Moment Detail needs a Moment object and evidence
model, which does not exist yet.

Do not start Output Detail yet. Output Detail needs output recipe/source lineage
contracts.

Sky Cycle Report is the right next surface because it is the natural answer to:

```text
How did the current or previous cycle go?
```

It also gives Now something meaningful to link to later.

## 6. Mission 020 Proposal

Mission 020 should create the first Sky Cycle Report product prototype.

It must be static/fake-safe and contract-first.

Recommended route:

```text
/modern-admin/sky-cycle
```

Recommended backend-owned builder:

```text
build_sky_cycle_report_view()
validate_sky_cycle_report_payload()
```

Recommended sections:

- Cycle summary;
- Phase timeline;
- Source coverage;
- Notable moments;
- Generated outputs;
- Observatory health;
- Attention items;
- Links back to Now.

No real DB, no filesystem, no RAW/FITS, no media generation, no actions.

## Mission 020 Prompt

```text
Mission 020 — Create read-only Sky Cycle Report product prototype

Objective:
Create the first read-only Sky Cycle Report product surface as the next product
object after Now v1.

Do not connect real DB, filesystem, RAW/FITS, media generation, actions, or
polling.

Tasks:
1. Add a backend-owned fake/static SkyCycleReport view model builder, for
   example `build_sky_cycle_report_view()`.
2. Add validation for required sections, data_status, no secrets, no absolute
   paths, no callables, and JSON safety.
3. Add a read-only route, for example `/modern-admin/sky-cycle`.
4. Add a lightweight server-rendered template.
5. Render sections:
   - Cycle summary
   - Phase timeline
   - Source coverage
   - Notable moments
   - Generated outputs
   - Observatory health
   - Attention items
6. Use explicit placeholder/not_evaluated/future_backend_contract language.
7. Add lightweight tests for the view model builder and validation.
8. Add links between Now and Sky Cycle Report.
9. Update governance/review document if needed.

Constraints:
- no mutations;
- no actions;
- no unbounded DB;
- no DB for this mission;
- no filesystem scan;
- no RAW/FITS read;
- no media generation;
- no preview URL;
- no fetch/JS/POST;
- no Classic changes;
- product builder remains framework-free;
- RPi5-first.
```

## Final Recommendation

Pause Now v1.

Start Sky Cycle Report as the next product surface, but only as a static,
validated, backend-owned contract and read-only product prototype.

This keeps momentum without overfitting Now or pretending the project already
has full cycle/moment/output truth.
