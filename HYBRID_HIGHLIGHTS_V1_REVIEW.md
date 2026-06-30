# Hybrid Highlights v1 Review

## Purpose

This review evaluates the first read-only Highlights product prototype.

Highlights v1 is contract-first, fake/static, backend-owned, and RPi5-first.
It does not connect real detector data, database queries, filesystem access,
RAW/FITS reads, media reads, media generation, preview URLs, downloads, shares,
favorites, archive actions, or safe actions.

## What It Does

Highlights v1 introduces the first product surface for curated attention
objects.

It answers:

- what deserves attention;
- why it was selected;
- what it points to;
- how confident Hybrid is allowed to be today;
- whether source trust is known;
- whether the user decision state is available;
- what remains fake/static.

The prototype includes:

- `highlights_summary`;
- `highlight_items`;
- `source_trust_summary`;
- `review_queue_summary`;
- `selection_policy_summary`;
- `attention_items`;
- `metadata`.

## Why It Is Different

### Different From Moment

A Moment is something that happened.

A Highlight is something worth attention.

Highlights can point to Moments, but they can also point to Outputs, Sky Cycles,
Sources, or Observatory issues.

### Different From Output

An Output is a generated artifact.

A Highlight explains why an output may deserve attention and whether the source
or generation context can be trusted.

### Different From Favorite

A Favorite is a user preference.

A Highlight is product attention. It may become favorited later, but the two
concepts are not interchangeable.

## What Is Fake / Static

Everything in this prototype is fake/static.

The placeholder Highlight items include:

- possible meteor candidate;
- generated timelapse candidate;
- source preservation attention item;
- clear window candidate.

None of these are connected to:

- detector evidence;
- AI ranking;
- generated media metadata;
- source lineage;
- source coverage;
- observatory health;
- user favorite/confirm/ignore state;
- real Sky Cycle context.

## What Is Missing

Highlights v1 is not yet a useful daily attention surface because it has no real
selection source.

Missing:

- canonical Highlight selector;
- target references to Moment/Output/Source/Sky Cycle/Observatory issue;
- confidence explanations from real evidence;
- source trust and lineage;
- review queue persistence;
- user decision state;
- ranking/suppression policy;
- integration with Library;
- real notification/attention routing.

## Safety And Architecture

The architecture is correct for this stage.

Strengths:

- product view model is framework-free;
- Flask view only calls the builder;
- template renders sanitized data;
- validation enforces required sections;
- Highlight type, target kind, and origin are allowlisted;
- safe actions are metadata-only and empty;
- no runtime data evaluation is performed;
- no detector, filesystem, RAW/FITS, media, download, share, or mutation path is
  connected.

Residual risk:

- once real data is introduced, Highlights could become noisy;
- AI suggestions could reduce trust if not explainable;
- Favorite and Highlight could be confused;
- output-centered Highlights could drift toward a gallery;
- observatory issue Highlights could drift toward an admin panel.

## Product Score

Initial Highlights v1 score: 7.0/10.

Post-uplift Highlights v1 score: 7.5/10.

Why it scores above a mockup:

- it formalizes the missing attention layer;
- it distinguishes Highlight from Moment, Output, and Favorite;
- it defines allowed types, target kinds, origins, and safety boundaries;
- it is contract-first and testable.
- the page now presents a primary "Start here" recommendation before secondary
  items;
- it separates primary recommendation, also-worth-reviewing items, trust, and
  user decision language.

Why it remains at 7.5:

- all examples are static;
- there is no real selector;
- there are no real target references;
- source trust is not connected;
- user decision state is not connected;
- it does not yet prove the morning flow with real attention data.
- it is still more explanatory prototype than emotionally convincing daily
  briefing.

## Recommended Next Mission

Do not connect real detector, AI ranking, or media data yet.

The next Highlights-specific mission should review the safest bounded source
for a first explainable Highlight candidate, after source trust and target
reference rules are explicit.

Recommended focus:

- preserve the primary recommendation hierarchy;
- keep recommendations explainable and reversible;
- require bounded metadata only;
- avoid detector or AI integration until evidence and trust can be shown;
- keep everything read-only.

Only after that should the project review the safest bounded source for a first
real Highlight candidate.
