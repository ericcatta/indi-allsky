# HYBRID PRODUCT PRINCIPLES

## Purpose

Hybrid AllSky is no longer defined by a Classic-to-Modern porting effort.

Hybrid AllSky is a product: a 24/7 sky-cycle console that records the sky,
preserves original source data, detects meaningful moments, generates beautiful
derived outputs, and explains the health of the observatory.

This document defines how product decisions should be made.

It is not an implementation plan. It is a governance manifesto.

## 1. Product First

The product comes before the technology.

Technology choices are only correct when they improve the user experience,
protect source data, preserve system reliability, or make the product easier to
reason about.

Do not ask first:

- What page exists today?
- What does Classic do?
- What is easiest to port?
- What implementation already exists?

Ask first:

- What is the user trying to understand?
- What does the sky-cycle story need?
- What source data must be protected?
- What is the simplest reliable product behavior?

If a feature is technically easy but product-weak, it should wait.

## 2. Experience First

Design the experience before the implementation.

The order of thinking is:

1. Experience
2. Domain
3. Backend
4. Frontend
5. Implementation detail

Do not begin with database tables, routes, templates, or existing screens.

Begin with the moment the user opens Hybrid AllSky and asks:

- What is happening now?
- What happened during this sky cycle?
- What is worth seeing?
- Were the sources preserved?
- Is the observatory healthy?

Only after the desired experience is clear should the domain model, backend
contract, and frontend presentation be designed.

## 3. Domain First

Every new capability must belong to a product domain object.

The core domain is:

- Now
- Sky Cycle
- Phase
- Moment
- Source
- Output
- Look
- Observatory
- Source Lineage
- Output Recipe
- Observatory Health

Features that do not clearly belong to the domain are not ready.

Avoid orphan features. Avoid pages that exist only because an old route existed.
Avoid controls that have no product story.

If a feature cannot answer "which domain object owns this?", stop and redesign
it.

## 4. Frontend / Backend Separation

The backend owns:

- domain objects;
- truth;
- permissions;
- source preservation;
- source lineage;
- output recipes;
- rendering jobs;
- safe actions;
- business rules;
- audit and redaction.

The frontend owns:

- presentation;
- interaction;
- visualization;
- navigation;
- responsive behavior;
- progressive enhancement.

Templates and UI clients receive sanitized view models.

No domain logic should live in templates.

No frontend should infer source truth, permissions, lineage, rendering state, or
safe-action readiness from raw implementation details.

## 5. Source Preservation Is Sacred

RAW, FITS, and source files are the digital negative.

They must never be modified by the UI.

They must never be silently overwritten.

They must never be treated as disposable unless the user has explicitly chosen a
retention policy and the system can explain it.

Every derived output should be traceable back to source data whenever possible.

If source preservation is unknown, the product must say unknown. It must not
pretend everything is safe.

## 6. Rendering Is Non-Destructive

Rendering is a pipeline stage, not editing of the source.

Source -> Analysis -> Moment -> Rendering -> Look -> Output

Looks are presets or recipes. They do not replace source data.

Outputs are derived. They can be regenerated. They can use different Looks.
They can be exported. They can be shared.

Hybrid AllSky should generate beautiful automatic outputs, but it must not try
to become a complete photo editor.

If an image is truly special, Hybrid should help the user find it, preserve its
source, and export it for external editing.

## 7. Raspberry Pi First

Hybrid AllSky must remain Raspberry Pi 5 first.

Performance is part of product quality.

Prefer:

- server-rendered pages;
- progressive enhancement;
- lazy loading;
- bounded lists;
- paginated data;
- cached reports;
- queued heavy processing;
- small charts;
- deliberate polling.

Avoid:

- heavy frontend bundles as a requirement;
- aggressive live dashboards;
- unbounded filesystem scans;
- synchronous FITS or video conversion during page render;
- large unpaginated tables;
- expensive background work without user value.

A beautiful UI that competes with capture, processing, or source preservation is
a failed UI.

## 8. Progressive Disclosure

Basic does not hide functionality. Basic removes noise.

Advanced exposes control.

Developer exposes internals.

Basic should summarize:

- what is happening now;
- what happened during the sky cycle;
- what is worth seeing;
- whether source data is preserved;
- whether the observatory is healthy.

Advanced should expose:

- profiles;
- acquisition behavior;
- source and retention policies;
- rendering and Looks;
- analytics;
- automation;
- integrations.

Developer should expose:

- logs;
- task queue;
- audit;
- raw configuration;
- safe-action internals;
- APIs;
- compatibility and legacy details.

Never remove a useful function merely because it is too advanced for Basic.
Move it to the right depth.

## 9. Product Language

The UI should speak the language of the sky observer.

Use product language whenever a human concept exists.

Prefer:

- Current phase
- Sky Cycle
- Source preserved
- RAW retention
- FITS source available
- Look applied
- Generated from source frames
- Observatory healthy
- Needs attention

Avoid first-level exposure of:

- raw config keys;
- route names;
- AJAX names;
- database tables;
- absolute paths;
- tokens and credentials;
- implementation jargon.

Technical names may exist in Developer mode, but they should not define the
product.

## 10. User Journeys Over Feature Lists

A feature is valuable only if it improves a real journey.

Primary journeys:

- Open Hybrid and understand the current sky.
- Review the last Sky Cycle.
- Find meaningful Moments.
- Inspect generated Outputs.
- Confirm source preservation.
- Understand Observatory Health.
- Adjust future behavior safely.
- Diagnose problems without damaging source data or runtime behavior.

Do not add features just because they exist in Classic.

Do not add controls without a journey.

Do not add pages that only expose implementation structure.

## 11. Product Over Porting

Classic UI is evidence. It is not the product definition.

Modern UI is also not automatically the product definition.

For every future feature, ask:

If Hybrid AllSky were born today, how should this work?

Only then look at Classic, Modern, database models, APIs, and existing code.

Porting is useful only when it preserves valuable capability while moving the
product toward the right experience.

Parity is not the goal. Product completeness is the goal.

## 12. Safe Actions Before Mutation

Every mutation must be safe-action based.

No destructive, remote, filesystem, restore, delete, upload, download,
regenerate, acknowledge, or hardware action should be exposed merely because a
legacy endpoint exists.

Before a mutative action reaches UI, it needs:

- a domain owner;
- permission policy;
- validation;
- dry-run where meaningful;
- audit;
- redaction;
- rollback or explicit no-rollback semantics;
- confirmation UX appropriate to risk;
- tests;
- clear disabled and blocked states.

The UI may show future actions as unavailable, but it must explain why.

## 13. Explainability Is Product Quality

Hybrid AllSky should not only show results. It should explain them.

Examples:

- Why was this Moment selected?
- Why is this output considered a highlight?
- Why is source preservation partial?
- Why is the observatory warning active?
- Why is this action disabled?

Explanations must be short in Basic, deeper in Advanced, and inspectable in
Developer.

If the system cannot explain a decision, it should be cautious about presenting
that decision as truth.

## 14. Build For Trust

The user must be able to trust Hybrid AllSky.

Trust comes from:

- preserved sources;
- honest unknown states;
- traceable outputs;
- clear lineage;
- visible health;
- safe actions;
- no hidden destructive behavior;
- no secret leakage;
- no false confidence.

Unknown is better than fake healthy.

Partial is better than pretending complete.

Blocked is better than unsafe.

## 15. Codex Collaboration Principles

Codex can work in four modes.

### Executor

Use Codex as executor when the scope is clear, small, safe, and already
decided.

Examples:

- add a read-only page;
- update a report;
- run inventory;
- implement a small tested helper.

### Designer

Use Codex as designer when the product shape is still open.

Examples:

- propose object models;
- design view models;
- define journeys;
- create product architecture documents.

### Critic

Use Codex as critic when a direction may be wrong.

Codex should challenge:

- settings-first drift;
- Classic parity thinking;
- heavy frontend assumptions;
- unsafe actions;
- missing source lineage;
- fake product completeness.

### Free Architect

Use Codex as free architect when the goal is product quality, not confirmation.

In this mode Codex should be allowed to discard prior assumptions, rename
concepts, reorganize navigation, and propose better models.

Codex should stop and ask only for true product decisions, safety decisions, or
external constraints that cannot be inferred.

## 16. Decision Framework

Every future product decision should pass this checklist.

### Product

- Does this improve a real user journey?
- Does it help explain Now, Sky Cycle, Moment, Source, Output, Look, or
  Observatory?
- Is it product-domain-first rather than route/config-first?

### Source Safety

- Does it preserve RAW/FITS/source data?
- Does it make lineage clearer?
- Does it avoid misleading source status?

### Rendering

- Is rendering non-destructive?
- Are Looks treated as presets/recipes?
- Are outputs clearly derived?

### Architecture

- Does the backend own truth?
- Does the frontend only present sanitized view models?
- Is domain logic kept out of templates?

### Raspberry Pi

- Is it lightweight?
- Are lists bounded or paginated?
- Is expensive work queued or cached?
- Is polling justified and limited?

### Disclosure

- Is the Basic experience simpler without being incomplete?
- Is Advanced control available where appropriate?
- Are Developer internals separated?

### Safety

- Are mutative actions safe-action based?
- Are disabled states explained?
- Are secrets, paths, and raw config protected?

### Product Language

- Does the UI use human sky/observatory language first?
- Are technical names reserved for Developer or detail views?

If a decision fails multiple sections, it is not ready.

## 17. The Standard Of Taste

Hybrid AllSky should feel calm, capable, and trustworthy.

It should not feel like:

- a pile of settings;
- a legacy admin tool;
- a developer console with thumbnails;
- a heavy SaaS dashboard;
- a photo editor pretending to be an observatory tool.

It should feel like:

- a sky-cycle console;
- a source-preserving observatory companion;
- a morning report;
- a moment finder;
- a media generator;
- a reliable health monitor.

## 18. Final Principle

The project should be judged by this question:

Does Hybrid AllSky help the user understand the sky, preserve the source, and
trust the observatory?

If yes, build it.

If no, redesign it.
