# Hybrid Highlight Domain v1

## Purpose

This document defines the Product Architecture meaning of `Highlight`.

It does not design a page. It does not define implementation, routes, database
schema, templates, builders, or UI components.

It answers a product question:

What is the object that lets a user think, "That important thing Hybrid found
or produced was one of the Highlights"?

## Executive Definition

A Highlight is a curated attention object.

It is not the thing itself.

It is a product-level selection that points to something worth attention and
explains why it matters.

A Highlight may point to:

- a Moment;
- an Output;
- a Sky Cycle;
- a Source or source range;
- an Observatory issue;
- a future insight, prediction, or AI finding.

A Highlight answers:

- why should I look at this?
- what is it connected to?
- how confident is Hybrid?
- is the source trustworthy?
- what can I do next?

## What A Highlight Is

A Highlight is best understood as an attention layer above the domain objects.

It is:

- an object, because it has identity, state, lifecycle, metadata, and history;
- a selection, because it chooses something from a larger set;
- an aggregate pointer, because it can reference one or more underlying domain
  objects;
- a result, because it represents Hybrid's judgment that something matters;
- a view entry, because it is how the product brings important things forward.

It is not merely a view.

If Highlights are only a view, the product cannot support confirmation,
favorites, ignored suggestions, historical retrieval, user curation, future AI,
or multi-object highlights.

It is not merely a tag.

A tag describes something. A Highlight promotes something.

It is not merely a Moment.

Some Highlights are Moment-centered, but many are Output-centered,
Cycle-centered, Source-centered, or Observatory-centered.

## Who Can Create A Highlight

Highlights can be created by multiple actors.

### Hybrid-created

Hybrid should create suggested Highlights automatically from deterministic or
future AI signals:

- likely meteor;
- aurora candidate;
- lightning/storm event;
- unusually clear sky window;
- best generated timelapse;
- excellent startrail;
- source preservation warning;
- camera anomaly;
- observatory health issue;
- unusually good sky quality.

### User-created

Users should be able to promote something to a Highlight:

- a favorite image;
- a personally meaningful sunrise;
- a storm clip;
- a manually spotted meteor;
- a cycle they want to remember;
- a source range they intend to process externally.

### AI-created

Future AI can create or rank suggested Highlights:

- "This looks like aurora";
- "This frame has unusual color";
- "This timelapse has a lightning sequence";
- "This night is visually stronger than normal";
- "This camera anomaly affects output trust."

AI Highlights must remain explainable. AI is a creator/ranker, not an
unquestioned authority.

### Coexistence

All creators must coexist.

A Highlight should carry `created_by` and `selection_basis` concepts:

- system rule;
- user;
- AI suggestion;
- imported/external;
- promotion from Moment;
- promotion from Output;
- promotion from Observatory issue.

The user must be able to distinguish:

- Hybrid suggested this;
- I confirmed this;
- I favorited this;
- AI suggested this with limited confidence;
- this was archived or ignored.

## What Can Become A Highlight

### Moment

Example:

- meteor candidate;
- aurora candidate;
- lightning sequence;
- clear window;
- camera anomaly;
- sunrise/sunset event.

This is the most obvious Highlight type.

### Output

Example:

- best image;
- best timelapse;
- best keogram;
- unusually strong startrail;
- storm highlight video;
- generated summary clip.

This supports the user who wants something beautiful to view or share.

### Sky Cycle

Example:

- exceptional cycle;
- all-clear cycle;
- failed cycle;
- cycle with unusually high source coverage;
- cycle with rare weather/sky behavior.

This supports daily/monthly review and long-term memory.

### Source Or Source Range

Example:

- preserved source range around a meteor;
- high-quality RAW/FITS sequence;
- source range worth external processing;
- source gap or corruption risk.

This supports scientific trust and external editing.

### Observatory Issue

Example:

- storage risk;
- camera disconnected;
- capture gap;
- generation failure;
- upload failure;
- source preservation warning.

This supports operational trust.

### Future Objects

Highlights must support future object types:

- AI finding;
- prediction;
- external event correlation;
- weather/sky-quality insight;
- community/share package;
- custom user collection.

If Highlights only support today's objects, the model will age badly.

## Mutability

A Highlight is not fully immutable.

It has two layers:

### Stable Core

The core should remain stable:

- identity;
- creation time;
- creator;
- initial target;
- initial reason;
- original evidence snapshot;
- source references if known.

This preserves history.

### Mutable State

The state may change:

- suggested;
- confirmed;
- favorite;
- ignored;
- archived;
- superseded;
- stale;
- invalidated;
- resolved.

Importance may change over time.

Examples:

- a meteor candidate may be confirmed;
- an AI aurora suggestion may be rejected;
- a generated output may be superseded by a better render;
- a storage warning may be resolved;
- a cycle once considered ordinary may become interesting later after a new
  detector finds something.

## Can A Highlight Be Regenerated?

The Highlight itself should not be "regenerated" in the same way an Output is.

Outputs can be regenerated.

Highlights can be re-evaluated, re-ranked, or re-linked.

If a Highlight points to an Output, the Output may be regenerated with a
different Look. The Highlight can then point to the new preferred Output while
preserving its history.

The right language is:

- re-evaluate Highlight;
- update Highlight ranking;
- replace preferred Output;
- preserve original evidence;
- supersede previous suggestion.

## Highlight vs Favorite

Highlight and Favorite are not the same.

### Highlight

A Highlight means:

Hybrid or the user believes this deserves attention.

It may be suggested, confirmed, ignored, or archived.

It carries reason, confidence, evidence, source trust, and links.

### Favorite

A Favorite means:

The user personally wants to keep this visible or easy to retrieve.

Favorite is a user preference state.

A Highlight can become a Favorite.

A Favorite does not have to be a Highlight. For example, the user may favorite a
routine but personally meaningful sunset that Hybrid would not have selected.

### Rule

Highlight is product attention.

Favorite is user affection or utility.

Do not merge them.

## Highlight vs Moment

A Moment is something that happened.

A Highlight is something worth attention.

Many Moments are not Highlights.

Examples:

- every cloud transition may be a Moment;
- only the most meaningful clear window becomes a Highlight;
- every detected meteor candidate may be a Moment;
- only high-confidence or visually strong candidates become Highlights.

A Highlight can point to one Moment, multiple Moments, or no Moment.

Example without Moment:

- "Best timelapse of the month" may be Output-centered.

Example with multiple Moments:

- "Storm sequence" may group clouds, lightning, rain, and camera exposure
  changes.

## Highlight vs Output

An Output is a generated artifact.

A Highlight is an attention object.

An Output can be highlighted because it is visually strong, scientifically
useful, newly generated, share-ready, or tied to a meaningful Moment.

But not all Outputs are Highlights.

Examples:

- every timelapse is an Output;
- only the best or most meaningful timelapse becomes a Highlight;
- a routine keogram may be an Output but not a Highlight;
- a failed generation may create an Observatory issue Highlight rather than an
  Output Highlight.

The Highlight explains why the Output matters and whether it is trustworthy.

## Highlight vs Sky Cycle

A Sky Cycle is an observation period.

A Highlight is a selected thing within, about, or derived from one or more
cycles.

A Sky Cycle can be highlighted if the entire cycle is notable:

- excellent observing conditions;
- rare aurora cycle;
- storm-heavy cycle;
- failed capture cycle;
- unusually complete source coverage;
- visually exceptional output set.

Most Sky Cycles are not Highlights.

Sky Cycle is context.

Highlight is attention.

## Library Integration

Highlights are central to Library.

Over years, users remember attention objects more naturally than raw dates.

Search should support:

- highlight type;
- target type;
- sky phenomenon;
- confidence;
- creator;
- state;
- camera/profile;
- Sky Cycle;
- time range;
- Look;
- source availability;
- output type;
- favorite status;
- archived/ignored status.

Natural searches:

- "aurora highlights";
- "favorite timelapses";
- "confirmed meteors";
- "storm clips";
- "source preserved highlights";
- "camera anomalies";
- "ignored AI suggestions";
- "high-confidence lightning";
- "best images from Camera North";
- "all highlights from winter 2027".

Library should not force users to remember:

- database IDs;
- raw file names;
- exact dates;
- config state.

## How Users Reach A Highlight

### Now

Now should surface the most relevant current/recent Highlights.

Natural path:

```text
Now -> Highlight -> Moment/Output/Source/Issue detail
```

Now should not require the user to open a Sky Cycle first.

### Sky Cycle

Sky Cycle should show Highlights inside the cycle.

Natural path:

```text
Sky Cycle -> Cycle Highlights -> Highlight detail
```

Sky Cycle gives context but should not monopolize discovery.

### Search / Library

Library is the long-term route.

Natural path:

```text
Library -> Highlight search/filter -> Highlight detail
```

### Notification

Notifications should point to Highlights when possible.

Example:

```text
Notification: "Possible meteor detected" -> Meteor Highlight
```

The Highlight can then explain evidence, confidence, source, and outputs.

### Telegram / Email / Integrations

External notifications should also point to Highlights.

Reason:

The user should not receive a blind output link. They should receive a
share-safe product object with explanation and trust.

### Output Detail

An Output may show:

- "This output is highlighted";
- "Make this a Highlight";
- "Linked Highlights".

### Moment Detail

A Moment may show:

- "Suggested as Highlight";
- "Confirmed Highlight";
- "Ignored Highlight";
- "Related Highlights".

## Must A Highlight Explain Why?

Yes.

A Highlight without an explanation is just a recommendation with no trust.

Every Highlight should answer:

- why selected;
- selected by whom or what;
- confidence;
- evidence;
- target object;
- source preservation status;
- related output status;
- camera/profile;
- cycle/time context;
- next useful action or destination.

This is especially important for:

- AI suggestions;
- detector candidates;
- operational warnings;
- shareable outputs;
- long-term search.

Explanation can be brief in Basic mode and detailed in Advanced/Developer mode.

## Metadata Model

This is conceptual only.

A Highlight should carry:

- stable highlight ID;
- title;
- short summary;
- type;
- target type;
- target references;
- parent Sky Cycle reference;
- camera/profile references;
- source references or source availability summary;
- output references;
- Moment references;
- Observatory issue references;
- created time;
- updated time;
- creator;
- selection basis;
- reason;
- confidence label;
- confidence score or bucket when available;
- evidence summary;
- evidence references;
- source preservation status;
- source lineage status;
- output readiness status;
- Look applied if output-centered;
- state;
- priority/rank;
- user flags;
- favorite state;
- archived/ignored state;
- superseded-by reference;
- invalidation reason;
- visibility/share readiness;
- safe actions available as metadata only;
- audit metadata for future mutations.

Forbidden in Basic Highlight metadata:

- raw absolute paths;
- secrets;
- raw detector dumps;
- raw stack traces;
- unbounded source lists;
- direct mutating endpoint URLs.

## Highlight Types

Suggested type vocabulary:

- moment;
- output;
- cycle;
- source;
- observatory_issue;
- insight;
- collection;
- unknown.

Suggested phenomenon vocabulary:

- meteor;
- aurora;
- lightning;
- storm;
- clouds;
- clear_window;
- sunrise;
- sunset;
- moon;
- sun;
- rainbow;
- sky_quality;
- camera_anomaly;
- storage_issue;
- generation_issue;
- source_gap;
- best_image;
- timelapse;
- keogram;
- startrail;
- custom.

These vocabularies should be allowlisted and extendable.

## Highlight States

Recommended states:

- `suggested`: Hybrid proposes this deserves attention.
- `confirmed`: user or trusted rule confirms it matters.
- `favorite`: user wants it easy to retrieve.
- `ignored`: user says this is not useful.
- `archived`: retained for history but not active.
- `superseded`: replaced by a better Highlight or Output.
- `invalidated`: evidence was wrong, source unavailable, or detector result was
  rejected.
- `resolved`: operational Highlight has been addressed.
- `stale`: generated from old logic or superseded detector/AI version.

These states should be composable where necessary.

For example:

- a Highlight can be `confirmed` and `favorite`;
- a Highlight can be `archived` and `favorite`;
- a Highlight should not be both `ignored` and `favorite` unless the product
  explicitly supports user contradictions.

## Lifecycle

### 1. Candidate Signal

Something produces a signal:

- detector;
- output generation;
- observatory health;
- source preservation;
- user action;
- AI;
- imported/external event;
- future analytics.

### 2. Suggested Highlight

Hybrid creates a suggested Highlight with:

- target;
- reason;
- confidence;
- evidence;
- source/output/health context.

### 3. Surfacing

The Highlight appears in:

- Now;
- Highlights;
- Sky Cycle;
- Notification;
- Library.

### 4. User Decision

The user may:

- open;
- confirm;
- favorite;
- ignore;
- archive;
- link to output;
- use it as a source for future actions.

### 5. Evolution

The Highlight may change:

- new output generated;
- better Look applied;
- AI re-evaluates confidence;
- source lineage becomes known;
- observatory issue is resolved;
- detector model changes;
- user edits classification.

### 6. Retention

Highlights should persist longer than transient notifications.

They become memory anchors.

They should not disappear silently.

Old suggested Highlights may become archived or stale, but should remain
searchable if they were confirmed, favorited, shared, or connected to source
data.

### 7. Expiry

Some Highlights can expire from active views:

- low-confidence suggestions ignored by the user;
- routine "all clear" summaries;
- resolved operational warnings;
- superseded output suggestions.

Expiry should remove active noise, not delete meaningful history.

## Long-Term Future Compatibility

Highlights can survive future detectors, AI, rendering, and outputs if they are
modeled as attention objects, not as a specific detector result.

Future-proof requirements:

- target references must support multiple object types;
- selection basis must be versioned or explainable;
- confidence must allow unknown/estimated/model-specific values;
- evidence must be extensible;
- output references must allow supersession;
- user decisions must remain separate from machine suggestions;
- source lineage must be attachable later;
- Highlights must support re-evaluation without losing history.

If Highlights are hard-coded to "Moment with thumbnail", they will fail.

If Highlights are "attention object with explainable target and state", they
will remain valid.

## How Product Architecture Changes

Current architecture:

```text
Now -> Sky Cycle -> Phase -> Moment -> Source -> Output -> Look -> Observatory
```

Recommended architecture:

```text
Now -> Highlight -> Moment / Output / Source / Observatory Issue
              -> Sky Cycle Context
              -> Library Memory
              -> Look / Recipe when output-centered
```

Domain model should become:

- Now
- Highlight
- Sky Cycle
- Phase
- Moment
- Source
- Output
- Look
- Observatory
- Library
- Source Lineage
- Output Recipe
- Observatory Health

Highlight should sit above Moment and Output in the experience, but not replace
them in the domain.

In product language:

- Now tells what needs attention.
- Highlights are what deserve attention.
- Moments explain what happened.
- Outputs show what was produced.
- Sources prove what was preserved.
- Observatory explains whether the system can be trusted.
- Sky Cycles provide period context.
- Library makes it findable later.

## New Ideal Product Flow

### Morning Flow

```text
Open Hybrid
-> Now
-> Recent Highlights
-> Open the most relevant Highlight
-> See Moment/Output/Source/Health context
-> Optionally inspect full Sky Cycle
```

### Exceptional Cycle

```text
Now
-> Highlights
-> Best Moment / Best Output
-> Source confidence
-> Share/export readiness in future
```

### Boring Cycle

```text
Now
-> All-clear Highlight or Source/Health summary
-> Optional Sky Cycle Report
```

A boring but successful cycle can still have a Highlight:

> "Clean capture cycle: sources preserved, no warnings."

This is not exciting, but it is useful.

### Meteor

```text
Now / Notification / Library
-> Meteor Highlight
-> Moment Detail
-> Evidence + Source + Related Output
```

### Timelapse

```text
Now / Highlights / Outputs
-> Timelapse Highlight
-> Output Detail
-> Look / Source / Share readiness
```

### Long-Term Search

```text
Library
-> Highlights
-> Filter: aurora, favorite, confirmed, camera, year
-> Highlight
-> Moment / Output / Sky Cycle
```

### Observatory Problem

```text
Now Warning
-> Observatory Issue Highlight
-> Affected Sources / Outputs / Cycle
-> Observatory Diagnosis
```

## Ten Rules A Highlight Must Respect

1. A Highlight must explain why it deserves attention.

2. A Highlight must point to at least one underlying product object or clearly
   state that its target is pending.

3. A Highlight must not replace Moment, Output, Source, Sky Cycle, or
   Observatory; it connects attention to them.

4. A Highlight must distinguish system suggestion, user confirmation, user
   favorite, AI suggestion, and operational warning.

5. A Highlight must preserve source trust: unknown source state must be shown as
   unknown, not assumed safe.

6. A Highlight must support multi-camera and profile context.

7. A Highlight must be searchable over years.

8. A Highlight must allow state changes without losing its original evidence.

9. A Highlight must avoid exposing raw paths, secrets, raw detector dumps, or
   unbounded source lists.

10. A Highlight must remain useful even when future detectors, AI models, Looks,
    and output types are added.

## Differences Summary

### Highlight vs Moment

Moment:

- something happened;
- event/condition object;
- may be mundane;
- may have evidence.

Highlight:

- something deserves attention;
- selection/attention object;
- may point to a Moment;
- must explain why it matters.

### Highlight vs Output

Output:

- generated artifact;
- derived from Source;
- may have Look and recipe;
- can be regenerated in the future.

Highlight:

- attention wrapper;
- may point to an Output;
- explains why this output matters;
- can track confidence, source trust, and user decision.

### Highlight vs Favorite

Favorite:

- user preference;
- personal retrieval marker;
- may apply to many objects.

Highlight:

- product attention object;
- system/user/AI can create it;
- carries reason, confidence, evidence, and state.

### Highlight vs Sky Cycle

Sky Cycle:

- observation period;
- context/report container;
- contains phases, moments, outputs, source confidence, health.

Highlight:

- attention object;
- can live inside or across Sky Cycles;
- can point to a whole Sky Cycle if the period itself is notable.

## Evaluation

If Highlights become central, Hybrid becomes better.

Why:

- the product becomes intent-first instead of hierarchy-first;
- users can jump directly to what matters;
- boring cycles still produce useful confidence Highlights;
- long-term memory becomes natural;
- Moment and Output remain clean domain objects;
- Sky Cycle becomes context instead of mandatory navigation;
- Observatory issues become actionable without turning the product into an
  admin panel.

Risks:

- Highlights could become too broad and meaningless;
- poor ranking could make the product noisy;
- unclear state could confuse Highlight, Favorite, and Moment;
- AI-generated Highlights could reduce trust if not explainable;
- too many Highlights could recreate notification fatigue.

The solution is strict rules:

- every Highlight needs reason and target;
- every suggestion needs confidence/evidence;
- user decisions must be preserved;
- low-value suggestions must be suppressible;
- Library must support retrieval without clutter.

Final judgment:

Highlights should become a first-class domain object.

Not a page first.

Not a UI decoration.

A product object that tells the user what deserves attention and why.
