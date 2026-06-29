# HYBRID PRODUCT DOMAIN CONTRACT V1

## 1. Purpose

This document defines the conceptual frontend/backend contract for the future
Hybrid AllSky Product UI.

It does not define database migrations, routes, API endpoints, runtime behavior,
or implementation details. It describes the sanitized view models the backend
should eventually provide to product-domain-first UI pages.

The product model follows:

Now -> Highlight -> Moment / Output / Source / Observatory Issue
    -> Sky Cycle Context -> Library

## 2. Frontend / Backend Separation

The backend owns:

- domain objects and truth;
- product intelligence and explainable attention selection;
- source preservation state;
- source lineage;
- output recipes;
- permissions and safe-action availability;
- rendering jobs;
- observatory health evaluation;
- redaction and sanitization;
- pagination and query boundaries;
- audit metadata.

The frontend owns:

- layout;
- presentation;
- interaction;
- filtering of already-provided small datasets;
- progressive enhancement;
- responsive behavior;
- empty/loading/error states.

Templates and UI clients receive sanitized view models. They must not perform
domain lookup, permission decisions, source path resolution, rendering logic, or
business-rule inference.

`safe_actions_available` is always metadata. It must never be treated as a
direct action invocation.

## 3. Common View Model Rules

Every product view model should support:

- `id`: stable non-secret identifier;
- `label`: human-readable label;
- `status`: product-level status;
- `summary`: short human-readable explanation;
- `generated_at` or `updated_at` where relevant;
- `safe_actions_available`: list of safe-action descriptors, not executable UI
  commands;
- `warnings`: list of sanitized attention items;
- `links`: optional internal navigation hints, not raw file paths;
- `is_placeholder`: whether the model is synthetic or incomplete;
- `data_quality`: complete, partial, estimated, missing, or unknown.

Common forbidden data:

- absolute source paths unless explicitly redacted and required;
- tokens, API keys, passwords, OAuth payloads, secrets;
- raw config payloads;
- unbounded source lists;
- raw stack traces;
- direct mutating endpoint URLs;
- arbitrary filesystem paths.

## 4. View Models

### 4.1 NowView

Purpose:

The live 24/7 home model. It summarizes current sky state, current phase,
latest source/output state, recent Highlights, observatory health, and
attention items.

Primary fields:

- `current_phase`: PhaseSummary
- `current_cycle`: SkyCycleSummary
- `latest_source`: SourceSummary or null
- `latest_output`: OutputSummary or null
- `highlight_candidates`: bounded list of HighlightSummary
- `latest_moments`: paginated or limited list of MomentSummary
- `observatory_health`: ObservatoryHealth
- `source_preservation`: SourceSummary-like aggregate
- `attention_items`: list of Warning/AttentionItem
- `safe_actions_available`: metadata only

Forbidden data:

- live raw config values;
- filesystem paths;
- unredacted integration credentials;
- raw worker state dumps.

Privacy/safety notes:

NowView must be safe for Basic mode. It can show "source preserved" or
"upload configured" but not secrets or raw paths.

RPi5 notes:

Use cached or recently computed state. Avoid aggressive polling. Latest media
metadata should be bounded.

Placeholder today:

- current phase label;
- source preservation summary;
- generated output status;
- sky-cycle headline.

Can come from existing DB/code:

- latest image/media metadata;
- camera/profile status;
- notification summaries;
- task/status summaries;
- storage/status metadata where already available.

Requires future backend:

- canonical SkyCycle object;
- canonical Highlight selector;
- canonical Phase engine;
- moment detection summaries;
- source preservation aggregate.

### 4.2 HighlightSummary

Purpose:

A compact representation of something that deserves attention.

Highlight is a first-class domain object in the Product UI, but it is also an
attention layer. It does not replace Moment, Output, Source, Sky Cycle, or
Observatory. It points to them and explains why they matter.

Primary fields:

- `highlight_id`
- `title`
- `summary`
- `type`: moment, output, cycle, source, observatory_issue, insight, collection,
  unknown
- `phenomenon`: meteor, aurora, lightning, storm, clouds, clear_window,
  sunrise, sunset, moon, sun, sky_quality, camera_anomaly, source_gap,
  generation_issue, custom, unknown
- `state`: suggested, confirmed, favorite, ignored, archived, superseded,
  invalidated, resolved, stale
- `target_type`
- `target_refs`: bounded references, never raw paths
- `created_by`: system, user, ai, imported, unknown
- `selection_basis`
- `reason`
- `confidence_label`
- `evidence_summary`
- `source_preservation_status`
- `source_lineage_status`
- `output_readiness_status`
- `camera_profile_summary`
- `sky_cycle`: SkyCycleSummary or compact reference
- `primary_moment`: MomentSummary or compact reference
- `primary_output`: OutputSummary or compact reference
- `safe_actions_available`: metadata only

Forbidden data:

- raw detector payloads;
- unredacted AI chain-of-thought or debug payloads;
- absolute source paths;
- direct mutating endpoint URLs;
- unbounded evidence/source lists;
- secrets, tokens, credentials.

Privacy/safety notes:

Highlights must explain why they were selected. AI-created Highlights must be
clearly identified as suggestions unless confirmed by user or trusted policy.

Favorite is a state or user flag on a Highlight. It is not the same as a
Highlight. A Highlight is product attention; Favorite is user preference.

RPi5 notes:

Highlight lists should be bounded, ranked, and cacheable. Selection should not
trigger heavy detection, source scans, or rendering during page render.

Placeholder today:

- recent highlight cards;
- suggested meteor/output/health placeholders;
- all-clear cycle summary.

Can come from existing DB/code:

- notifications;
- latest frame metadata;
- generated media metadata;
- task/generation failures;
- bounded health/status metadata.

Requires future backend:

- canonical Highlight selector;
- explainable ranking;
- user confirmation/favorite/ignore state;
- source lineage and output linkage;
- AI/detector evidence adapters.

### 4.3 HighlightDetail

Purpose:

The explanation view model for a Highlight. It answers why this deserves
attention and what object(s) it points to.

Primary fields:

- `summary`: HighlightSummary
- `reason`
- `evidence`
- `confidence_explanation`
- `target_objects`
- `source_lineage`: SourceLineage or summary
- `related_outputs`: bounded list of OutputSummary
- `related_moments`: bounded list of MomentSummary
- `observatory_context`: ObservatoryHealth or compact issue summary
- `sky_cycle_context`: SkyCycleSummary or compact reference
- `user_state`: favorite, confirmed, ignored, archived where applicable
- `safe_actions_available`: metadata only

Forbidden data:

- raw paths;
- unbounded source/evidence lists;
- raw logs;
- unsafe action URLs;
- unredacted AI/debug payloads.

Privacy/safety notes:

Highlight Detail must not overclaim. Unknown confidence, missing source
lineage, or partial evidence must be shown as unknown or partial.

RPi5 notes:

Large evidence, output, and source lists must be summarized and lazy/paginated.

Placeholder today:

- static explanation;
- target placeholders;
- confidence labels.

Can come from existing DB/code:

- notification records;
- generated media metadata;
- bounded source/output metadata;
- status summaries.

Requires future backend:

- first-class Highlight storage/selector;
- explainable evidence model;
- user state persistence;
- multi-object target references.

### 4.4 SkyCycleSummary

Purpose:

A compact card/list representation of a full sky cycle.

Primary fields:

- `cycle_id`
- `label`
- `start_time`
- `end_time`
- `phase_count`
- `moment_count`
- `output_count`
- `highlight_count`
- `source_coverage`
- `health_status`
- `headline`
- `best_output`: OutputSummary or null
- `safe_actions_available`: metadata only

Forbidden data:

- raw frame lists;
- unbounded media lists;
- raw source paths.

Privacy/safety notes:

Cycle summaries should be share-safe unless explicitly in Developer mode.

RPi5 notes:

Summaries should be precomputed or cacheable.

Placeholder today:

- headline;
- score/status;
- source coverage estimate.

Can come from existing DB/code:

- image/video/timelapse/startrail counts;
- notification/task status;
- latest media timestamps.

Requires future backend:

- cycle boundaries;
- phase segmentation;
- source coverage calculation.

### 4.5 SkyCycleDetail

Purpose:

The report view for a complete sky cycle: day, night, transitions, moments,
outputs, source coverage, and observatory health.

Primary fields:

- `summary`: SkyCycleSummary
- `phases`: list of PhaseSummary
- `moments`: paginated MomentSummary collection
- `outputs`: paginated OutputSummary collection
- `highlights`: bounded HighlightSummary collection
- `source_lineage_summary`
- `observatory_health`: ObservatoryHealth
- `attention_items`
- `timeline_segments`
- `safe_actions_available`: metadata only

Forbidden data:

- full raw source inventories in one payload;
- absolute paths;
- raw logs;
- unredacted errors.

Privacy/safety notes:

Detail can expose more evidence than Summary but must remain redacted by
default.

RPi5 notes:

Moments, outputs, and source lists must be paginated or lazy-loaded.

Placeholder today:

- phase sections;
- timeline segments;
- moment groups.

Can come from existing DB/code:

- media records;
- task status;
- notification records;
- FITS/source metadata summaries.

Requires future backend:

- canonical sky-cycle report generator;
- Highlight aggregation for the cycle;
- phase-aware summaries;
- moment aggregation.

### 4.6 PhaseSummary

Purpose:

Represents a segment of a Sky Cycle: day, sunset, twilight, night, storm,
clear window, sunrise, or future phase.

Primary fields:

- `phase_id`
- `type`
- `label`
- `start_time`
- `end_time`
- `status`
- `source_count`
- `output_count`
- `moment_count`
- `quality_summary`
- `safe_actions_available`: metadata only

Forbidden data:

- raw frame paths;
- detector internals in Basic.

Privacy/safety notes:

Phase labels should be product language, not algorithm labels.

RPi5 notes:

Phase summaries should be cheap aggregates.

Placeholder today:

- day/night/twilight labels;
- simple current phase.

Can come from existing DB/code:

- sun/moon/day-night calculations if already present;
- capture timestamps;
- media timestamps.

Requires future backend:

- canonical phase segmentation.

### 4.7 MomentSummary

Purpose:

Compact representation of a meaningful sky or observatory moment.

Primary fields:

- `moment_id`
- `type`
- `label`
- `timestamp`
- `phase`
- `confidence`
- `thumbnail_output`: OutputSummary or null
- `source_available`
- `related_output_count`
- `highlight_state`: none, suggested, confirmed, favorite, ignored, archived
- `status`: candidate, confirmed, ignored, system
- `safe_actions_available`: metadata only

Forbidden data:

- raw detector payloads;
- source paths;
- unredacted AI/debug payloads.

Privacy/safety notes:

Confidence should be explainable and not overstate AI/detector certainty.

RPi5 notes:

List views must be paginated and thumbnail-light.

Placeholder today:

- best image;
- camera anomaly;
- generation failure;
- clear/storm placeholders.

Can come from existing DB/code:

- notifications;
- media records;
- existing event-like metadata if present;
- task failures.

Requires future backend:

- moment detector/selector;
- highlight promotion/selection model;
- event classification model;
- confidence explanations.

### 4.8 MomentDetail

Purpose:

Full detail for a Moment, connecting evidence, source, outputs, explanation,
and safe future actions.

Primary fields:

- `summary`: MomentSummary
- `description`
- `evidence`
- `source_lineage`: SourceLineage
- `related_outputs`: paginated OutputSummary collection
- `related_highlights`: bounded HighlightSummary collection
- `related_moments`
- `explanation`
- `attention_items`
- `safe_actions_available`: metadata only

Forbidden data:

- raw source paths;
- raw detector dumps in Basic/Advanced;
- executable action URLs.

Privacy/safety notes:

Moment Detail should explain "why this matters" without exposing sensitive
internals.

RPi5 notes:

Related outputs and source frames should lazy-load.

Placeholder today:

- evidence text;
- confidence explanation;
- related outputs.

Can come from existing DB/code:

- media metadata;
- FITS/source metadata;
- notifications;
- task records.

Requires future backend:

- canonical moment storage;
- Highlight target references;
- source-to-moment linkage.

### 4.9 SourceSummary

Purpose:

Compact representation of preserved source data.

Primary fields:

- `source_id`
- `type`: RAW, FITS, frame, frame_range, derived_source
- `label`
- `created_at`
- `camera_id`
- `profile_id`
- `availability`: available, missing, expired, partial, unknown
- `retention_status`
- `size_summary`
- `safe_actions_available`: metadata only

Forbidden data:

- absolute paths in Basic;
- raw headers containing secrets;
- unbounded frame lists.

Privacy/safety notes:

SourceSummary can say "available" without exposing where it lives.

RPi5 notes:

Do not stat or scan files synchronously for every row.

Placeholder today:

- source availability labels;
- retention labels.

Can come from existing DB/code:

- FITS image metadata;
- raw/source media metadata;
- camera/profile IDs;
- storage retention config metadata.

Requires future backend:

- source preservation index;
- path allowlist service;
- source coverage calculation.

### 4.10 SourceLineage

Purpose:

Traceability from Output/Moment back to Source.

Primary fields:

- `lineage_id`
- `source_refs`: bounded list or count with lazy link
- `source_range`
- `coverage_status`
- `derived_from`
- `missing_sources`
- `lineage_quality`
- `safe_actions_available`: metadata only

Forbidden data:

- full source paths;
- unbounded frame IDs;
- raw file inventories in a single model.

Privacy/safety notes:

Lineage must be truthful. If source is missing or partial, say so plainly.

RPi5 notes:

Large source ranges must be summarized, with optional paginated detail.

Placeholder today:

- "source available" / "source not tracked";
- generated-from counts.

Can come from existing DB/code:

- media timestamps;
- FITS/source metadata;
- task/result payloads if safe.

Requires future backend:

- first-class lineage index.

### 4.11 OutputSummary

Purpose:

Compact representation of a generated or displayable derived artifact.

Primary fields:

- `output_id`
- `type`: image, timelapse, keogram, startrail, report
- `label`
- `created_at`
- `thumbnail_url`
- `look`: LookSummary or null
- `source_lineage_status`
- `related_moment_count`
- `highlight_state`: none, suggested, confirmed, favorite, ignored, archived
- `availability`
- `safe_actions_available`: metadata only

Forbidden data:

- direct unvalidated download URLs;
- arbitrary file paths;
- raw generation payloads.

Privacy/safety notes:

OutputSummary can expose safe preview URLs only through existing public/media
rules.

RPi5 notes:

Use thumbnails and pagination. Do not compute previews synchronously.

Placeholder today:

- look used;
- source lineage status;
- related moments.

Can come from existing DB/code:

- images;
- videos;
- timelapse;
- keogram;
- startrail;
- public/latest media metadata.

Requires future backend:

- OutputRecipe linkage;
- Look association;
- Highlight target references;
- moment relationships.

### 4.12 OutputDetail

Purpose:

Full detail for an Output, including recipe, Look, lineage, related Moments,
and safe future regeneration/export metadata.

Primary fields:

- `summary`: OutputSummary
- `recipe`: OutputRecipe
- `source_lineage`: SourceLineage
- `related_moments`
- `related_highlights`: bounded HighlightSummary collection
- `quality_summary`
- `sharing_status`
- `safe_actions_available`: metadata only

Forbidden data:

- raw filesystem paths;
- direct unsafe download actions;
- unredacted worker errors.

Privacy/safety notes:

Export/download capability must be represented as safe-action metadata until
policy exists.

RPi5 notes:

Do not generate previews or regenerate outputs during detail rendering.

Placeholder today:

- recipe summary;
- Look label;
- source range summary.

Can come from existing DB/code:

- media metadata;
- task result metadata;
- FITS/source metadata.

Requires future backend:

- recipe persistence;
- Look association;
- source lineage.

### 4.13 LookSummary

Purpose:

Compact representation of a rendering preset.

Primary fields:

- `look_id`
- `label`
- `type`: built_in, custom
- `intent`: natural, scientific, daylight, sunset, aurora, storm, moonlight
- `compatible_output_types`
- `version`
- `preview_output`: OutputSummary or null
- `safe_actions_available`: metadata only

Forbidden data:

- arbitrary user scripts;
- unsafe rendering parameters;
- source mutation flags.

Privacy/safety notes:

Looks never modify source data.

RPi5 notes:

Look previews should use cached examples, not live rendering.

Placeholder today:

- built-in Look labels;
- compatibility notes.

Can come from existing DB/code:

- none required; can start as static product metadata.

Requires future backend:

- Look schema;
- custom Look persistence;
- rendering validation.

### 4.14 OutputRecipe

Purpose:

Reproducible description of how an Output was or will be generated.

Primary fields:

- `recipe_id`
- `output_type`
- `source_range`
- `look_id`
- `rendering_parameters_summary`
- `generator`
- `version`
- `created_at`
- `is_reproducible`
- `safe_actions_available`: metadata only

Forbidden data:

- raw source paths;
- secrets;
- arbitrary shell commands;
- full unredacted task payloads.

Privacy/safety notes:

Recipe summaries should be human-readable and redacted.

RPi5 notes:

Recipes describe work; they do not execute during page render.

Placeholder today:

- output type;
- source range unknown;
- Look unknown/default.

Can come from existing DB/code:

- task queue metadata;
- media generation timestamps;
- config ownership metadata.

Requires future backend:

- recipe schema;
- rendering job contract;
- regeneration safe action.

### 4.15 ObservatoryHealth

Purpose:

Product-level summary of system health.

Primary fields:

- `overall_status`
- `capture_status`
- `camera_status`
- `profile_status`
- `storage_status`
- `source_preservation_status`
- `generation_status`
- `upload_status`
- `connectivity_status`
- `sensor_status`
- `attention_items`
- `safe_actions_available`: metadata only

Forbidden data:

- credentials;
- raw logs;
- raw paths;
- unbounded task lists.

Privacy/safety notes:

Health should explain what needs attention without exposing internals in Basic.

RPi5 notes:

Use cached health checks. Avoid expensive filesystem scans and remote calls on
page load.

Placeholder today:

- overall health;
- generation status;
- upload status.

Can come from existing DB/code:

- camera/profile metadata;
- task queue;
- notifications;
- storage status pages;
- upload provider status.

Requires future backend:

- unified health evaluator.

### 4.16 Warning / AttentionItem

Purpose:

Standard warning/attention model used across Now, Sky Cycle, Moment, Output,
Source, and Observatory pages.

Primary fields:

- `attention_id`
- `severity`: info, notice, warning, critical
- `label`
- `message`
- `scope`
- `detected_at`
- `recommended_next_step`
- `safe_actions_available`: metadata only
- `developer_detail_available`

Forbidden data:

- raw exceptions in Basic;
- secret-bearing messages;
- direct mutating URLs.

Privacy/safety notes:

Attention items must be redacted and actionable without being dangerous.

RPi5 notes:

Keep attention lists bounded and grouped.

Placeholder today:

- no source coverage;
- generation pending;
- storage warning;
- safe action blocked.

Can come from existing DB/code:

- notifications;
- task errors;
- logs summarized safely;
- storage warnings.

Requires future backend:

- unified attention aggregation.

## 5. Safe Actions Metadata

Every model may include `safe_actions_available`, but this field is descriptive
metadata only.

Allowed shape:

- `action_id`
- `label`
- `state`: unavailable, dry_run_only, blocked, ready
- `reason`
- `risk_level`
- `requires_confirmation`

Forbidden:

- direct POST targets;
- embedded payloads with secrets;
- UI instructions that execute mutations;
- bypassing backend permission checks.

## 6. Placeholder Strategy

Product pages may launch with placeholder fields if the backend domain object is
not complete yet.

Placeholder rules:

- mark placeholders explicitly with `is_placeholder`;
- never fake source preservation;
- never fake successful generation;
- distinguish unknown from healthy;
- use product copy such as "Not tracked yet" or "Waiting for backend contract";
- avoid giving users false confidence.

## 7. Paginated / Lazy Data Strategy

RPi5-first data rules:

- lists of Highlights, Sky Cycles, Moments, Outputs, Sources, and
  AttentionItems must be paginated or bounded;
- thumbnails should be lazy-loaded;
- charts should be optional or lazy;
- source frame ranges should be summarized first;
- reports should be cacheable;
- heavy calculations should be queued, not performed during page rendering;
- polling must be slow, bounded, and explicitly justified.

## 8. First Contracts To Implement Later

### 1. NowView

Start here because it defines the product home and integrates current phase,
latest media, source preservation, and observatory health.

### 2. HighlightSummary / HighlightDetail

Implement next because it defines the attention layer: what deserves review,
why it matters, what it points to, and whether the underlying source/output or
health context is trustworthy.

### 3. SkyCycleSummary / SkyCycleDetail

Implement after Highlights because it defines the reporting context for
day-and-night cycles. Sky Cycle is essential, but it should not be the only
path to Moment or Output.

### 4. MomentSummary / MomentDetail

Implement fourth because it validates the core domain concept across day,
night, weather, anomalies, and future AI candidates.

## 9. Risks

- Treating placeholders as real product truth.
- Letting templates infer domain state.
- Reintroducing settings-first navigation through view-model names.
- Exposing source paths, secrets, OAuth data, or raw config payloads.
- Overloading Raspberry Pi 5 with live polling, scans, or synchronous charts.
- Adding safe-action UI before backend permission, audit, and Flask tests exist.
- Losing profile-first or multicamera ownership while simplifying Basic.
- Presenting "source preserved" without a trustworthy source index.
- Creating noisy or opaque Highlights that do not explain why they were
  selected.
- Confusing Highlight with Favorite, Moment, or Output.

## 10. Recommendation

Build product-domain contracts before building more final UI pages.

The first future implementation should be read-only product view models backed
by sanitized backend contracts. NowView remains the home, but Highlight is the
next connective contract because it explains what deserves attention before the
user explores reports or archives.

Contracts may begin with placeholders, but they must keep the model honest:

- source status must be truthful;
- unknown must be shown as unknown;
- safe actions must remain metadata;
- expensive data must be lazy or cached;
- templates must not own domain logic.

The product will stay coherent if the backend owns the sky-cycle domain and the
frontend focuses on presenting it beautifully and safely.
