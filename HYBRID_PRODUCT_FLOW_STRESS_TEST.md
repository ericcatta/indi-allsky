# Hybrid Product Flow Stress Test

## Purpose

This document stress-tests the current Hybrid AllSky product flow.

It does not defend the existing architecture. It attempts to break it from the
point of view of an expert astrophotographer, an observatory operator, and a
science-minded user.

Current model under test:

```text
Now -> Sky Cycle -> Moment -> Output -> Observatory
```

Question under test:

Is this the natural way a user moves through the product, or is there a better
flow?

## Executive Verdict

The current model is directionally good, but the sequence is not quite natural.

`Now` is a strong entry point. `Moment` is the true center of meaning. `Output`
is often the user's desired result. `Observatory` is the trust layer.

`Sky Cycle` is important, but it should not always be the second step. It is a
reporting container, not always the user's next intent.

The product should become less linear.

The better model is:

```text
Now
-> Highlights
-> Moment or Output
-> Source / Lineage / Observatory Trust
-> Sky Cycle Report
-> Library
```

Sky Cycle remains essential, but as context and archive, not as the mandatory
bridge between Now and everything meaningful.

## Stress Test Assumptions

The user opens Hybrid because they want one of four things:

- understand what happened;
- see or share something worth looking at;
- trust that source data was preserved;
- know whether the observatory worked.

They do not naturally open Hybrid to inspect a domain model.

The domain model must serve the flow, not become the flow.

## Scenario 1: Exceptional Night

The user opens Hybrid in the morning after an exceptional night.

Natural user thought:

> Show me the best things immediately.

Expected behavior:

- top-level verdict;
- best image;
- best timelapse;
- notable moments;
- source confidence;
- any warnings that invalidate trust.

Current flow issue:

`Now -> Sky Cycle -> Moment -> Output` may be too slow. If the night was
exceptional, the user's first click is likely not "Sky Cycle". It is "show me
the highlights" or "show me the meteor/aurora/best timelapse".

Failure mode:

If Sky Cycle becomes a mandatory intermediate report, it adds cognitive tax.
The user already knows they want the artifact or event. Do not force them to
read the container first.

Better flow:

```text
Now -> Highlights -> Moment Detail or Output Detail
```

Sky Cycle should be available as context:

```text
Moment Detail -> View full Sky Cycle
Output Detail -> View source cycle
```

## Scenario 2: Boring Night

The user opens Hybrid after a quiet night.

Natural user thought:

> Was everything OK, and is there anything worth checking?

If nothing happened, the product still needs value.

Useful answers:

- capture completed;
- sources preserved;
- no major gaps;
- no observatory warnings;
- outputs generated normally;
- sky quality summary;
- storage risk absent;
- latest frame looks normal.

Current flow issue:

If Now is mostly a launchpad to Sky Cycle and Moments, a boring night becomes a
dead end. There are no moments, no exciting outputs, and therefore no reason to
continue.

Better product behavior:

For quiet cycles, Hybrid should become a confidence tool:

```text
Now -> "All clear" operational summary
```

The best click is not Moment or Output. It is probably "View health/source
confidence details" only if something looks suspicious.

Implication:

Sky Cycle must support a "boring but successful" narrative. A no-event cycle is
not empty. It is a verified observation period.

## Scenario 3: Meteor

The user had a meteor.

Natural user thought:

> Where is it? Show me the evidence and the clip/image.

Likely entry paths:

- alert/notification;
- Now highlight;
- Moment list;
- Sky Cycle report;
- Library search.

Current flow issue:

If the primary route is `Now -> Sky Cycle -> Moment`, the meteor may be buried
inside the report. That is backwards. The meteor is the primary object.

Better flow:

```text
Now -> Meteor Moment
```

The Moment Detail should then answer:

- what happened;
- when;
- confidence;
- evidence frames;
- source lineage;
- related outputs;
- whether source is preserved;
- whether generation/share is available.

Sky Cycle is context:

```text
Meteor Moment -> Full cycle context
```

Not the required doorway.

## Scenario 4: Share Timelapse

The user wants to share a timelapse.

Natural user thought:

> Where is the finished timelapse, and is it safe/good enough to share?

Expected path:

```text
Now -> Generated Outputs -> Timelapse
```

or:

```text
Library -> Outputs -> Timelapse
```

Current flow issue:

If outputs are subordinated to Sky Cycle and Moment, a user who only wants a
timelapse may have too many clicks:

1. Now
2. Sky Cycle
3. outputs section
4. timelapse item
5. share/export state

That is too many for a common desire.

Better flow:

Outputs deserve top-level discoverability through a `Highlights` or `Outputs`
surface, especially for generated media.

But Output alone is not enough. It must expose:

- Look applied;
- source lineage;
- source preserved;
- generation status;
- share readiness.

Do not make Output a dumb media card.

## Scenario 5: Three Years Later, "That Night With The Aurora"

The user wants to find an old aurora night.

Natural user thought:

> I remember the phenomenon, not the date.

Current flow issue:

`Sky Cycle` is date/cycle-oriented. That is useful for archive browsing but
weak for memory retrieval.

The user's memory is event-first:

- aurora;
- storm;
- meteor;
- unusually clear;
- moon halo;
- best timelapse;
- camera problem.

Better flow:

```text
Library -> Search by Moment Type -> Aurora -> Moment Detail -> Outputs/Sources
```

or:

```text
Moments -> Aurora -> Time filter -> Moment Detail
```

Sky Cycle should be searchable context, not the only archive unit.

Implication:

The future Library is not optional. It is how the product becomes useful over
years.

## Scenario 6: Two Cameras

The user has two cameras.

Natural user thought:

> Which camera saw what, and which result should I trust?

Current flow issue:

The linear model hides a key dimension: camera/profile identity.

Moment, Output, Source, and Observatory all need camera context. Sky Cycle also
needs it, but not always as the top-level filter.

Potential failure:

If Sky Cycle is global by default, multi-camera users may not know whether a
moment came from Camera A, Camera B, or a combined observation.

Better model:

Every primary object needs a camera/profile facet:

- Now: active camera summary and per-camera health;
- Highlights: grouped by camera when relevant;
- Moment: camera/source identity is first-class;
- Output: generated from which camera/source range;
- Observatory: per-camera operational health;
- Sky Cycle: global plus per-camera views.

Do not bolt multi-camera onto the side. It is part of trust.

## Scenario 7: Observatory Problem

The observatory had a problem.

Natural user thought:

> Did I lose data? What is affected? What should I do?

Current flow issue:

Observatory as a separate section may be too late if the problem affects the
validity of moments or outputs.

Health should be everywhere as trust metadata:

- Now should surface urgent warnings;
- Sky Cycle should say what period is affected;
- Moment should say whether evidence is compromised;
- Output should say whether generation/source lineage is reliable;
- Observatory should explain root cause and operational detail.

Better flow:

```text
Now warning -> Affected cycle/moments/outputs -> Observatory diagnosis
```

Observatory is not just a destination. It is the trust layer behind every
object.

## Cross-Page Analysis

### Now

Now should not try to be the whole product.

Its job:

- answer current state;
- show the most important recent highlights;
- show trust warnings;
- route the user to the right object.

Risk:

Now can become overloaded if it tries to summarize Sky Cycle, Moments, Outputs,
Source Confidence, and Observatory Health in too much detail.

Principle:

Now is a triage surface, not a report.

### Sky Cycle

Sky Cycle is valuable, but it is not always the second step.

Its job:

- explain a complete observation period;
- show phase structure;
- aggregate moments, outputs, sources, and health;
- provide historical context.

Risk:

Sky Cycle can become a mandatory hallway. That would slow the user's path to
the actual object they care about.

Principle:

Sky Cycle is a context/report object, not the universal navigation hub.

### Moment

Moment is likely the strongest product object.

Its job:

- explain what happened;
- show evidence;
- connect source and output;
- support review/confidence;
- become searchable over years.

Risk:

If Moment is treated as secondary to Sky Cycle, the product will feel like an
archive rather than an intelligent all-sky console.

Principle:

Moment should be a first-class destination from Now, Library, notifications, and
Sky Cycle.

### Output

Output is the user's most shareable result.

Its job:

- present generated media;
- explain Look/recipe;
- prove source lineage;
- expose share/export/regeneration readiness in the future.

Risk:

Output can become detached from evidence and source truth if treated as a
gallery item.

Principle:

Output must be beautiful, but never source-blind.

### Observatory

Observatory is trust infrastructure.

Its job:

- explain operational health;
- expose camera/profile/storage/integration state;
- show what data or outputs may be affected;
- support diagnosis.

Risk:

Observatory can regress into an admin panel if isolated from product objects.

Principle:

Observatory is both a section and a status layer embedded across the product.

## The Current Model Under Stress

The current model:

```text
Now -> Sky Cycle -> Moment -> Output -> Observatory
```

What works:

- it is domain-first;
- it avoids settings-first thinking;
- it preserves source/output distinction;
- it gives reports a coherent place;
- it supports 24/7 day/night cycles.

What breaks:

- users often want Moment or Output before Sky Cycle;
- long-term retrieval is Library-first, not Sky-Cycle-first;
- Observatory must be ambient trust, not only a destination;
- multi-camera is a facet across objects, not a later filter;
- boring nights need an "all clear" path, not an empty report path.

The flow is too linear for the actual user journeys.

## Better Navigation

I would build this navigation:

1. Now
2. Highlights
3. Moments
4. Outputs
5. Library
6. Observatory
7. Insights
8. Looks
9. Automation
10. Engine Room

### Now

Triage and current state.

Primary question:

What deserves attention right now?

### Highlights

The best recent things Hybrid found or generated.

This is the missing bridge between Now and the rest of the product.

Highlights can include:

- best image;
- best timelapse;
- likely meteor;
- aurora candidate;
- storm/lightning;
- unusually clear window;
- observatory warning;
- source preservation warning.

Highlights should link directly to Moment or Output.

### Moments

Event/condition archive and review queue.

Primary question:

What happened?

### Outputs

Generated media and shareable products.

Primary question:

What can I view, keep, regenerate, or share?

### Library

Long-term retrieval across cycles, moments, outputs, cameras, Looks, and source
availability.

Primary question:

How do I find something I remember?

### Observatory

Operational trust and diagnosis.

Primary question:

Can I trust this system and the data it produced?

### Insights

Scientific and trend views: sky quality, ADU/SQM, clarity, clouds, source
coverage, anomaly trends.

Primary question:

What patterns are emerging over time?

### Looks

Non-destructive rendering presets and future custom Looks.

Primary question:

How should derived outputs look?

### Automation

Policies for capture, generation, retention, uploads, and future safe actions.

Primary question:

What should Hybrid do automatically?

### Engine Room

Developer/admin internals.

Primary question:

What is happening under the hood?

## New Ideal Flow

The improved product flow is not a line. It is a hub-and-object graph.

```text
Now
  -> Highlights
      -> Moment Detail
      -> Output Detail
      -> Observatory Warning
  -> Current Observatory Health
  -> Current Source Confidence

Moment Detail
  -> Evidence
  -> Source Lineage
  -> Related Outputs
  -> Parent Sky Cycle
  -> Camera/Profile

Output Detail
  -> Look/Recipe
  -> Source Lineage
  -> Related Moments
  -> Parent Sky Cycle
  -> Share/Export readiness

Sky Cycle Report
  -> Phases
  -> Moments
  -> Outputs
  -> Source Confidence
  -> Observatory Health

Library
  -> Search Moments
  -> Search Outputs
  -> Search Sky Cycles
  -> Filter by Camera/Profile/Look/Source Availability

Observatory
  -> Health
  -> Affected Cycles
  -> Affected Moments
  -> Affected Outputs
```

This preserves the domain model but changes the navigation priority.

## Ten Most Important Criticisms

1. Sky Cycle should not be the mandatory second step. It is a report/context
   object, not always the user's next intent.

2. The current flow underweights Highlights. Users often want "what is worth
   seeing?" before they want a full report.

3. Moment is probably the true center of the product. It should be reachable
   directly from Now, Highlights, Library, notifications, and Sky Cycle.

4. Output needs top-level discoverability. Generated media is a core product
   result, not just a subsection of a cycle.

5. Long-term memory is not cycle-first. Users remember phenomena and results,
   not always dates.

6. Observatory health should be embedded as trust metadata across objects, not
   only placed in an Observatory section.

7. Multi-camera is not a filter to add later. It changes trust, source lineage,
   moment identity, and output identity.

8. Boring nights need positive value. "Nothing happened, everything worked, and
   sources are safe" is a product result.

9. Now risks becoming overloaded. It should route and summarize, not become a
   giant report.

10. The current architecture is safe, but it risks becoming contract-complete
    before it is journey-complete.

## Ten Things That Work Best

1. The product is no longer settings-first.

2. Source preservation is correctly treated as sacred.

3. Non-destructive rendering gives the product a strong long-term foundation.

4. Now is the right entry point.

5. Sky Cycle is the right reporting unit for complete observation periods.

6. Moment is correctly defined broadly: not only meteors, not only night.

7. Output is correctly separated from Source.

8. Observatory Health is correctly framed as product trust, not only system
   diagnostics.

9. RPi5-first constraints are appropriate and necessary.

10. Backend-owned sanitized view models are the right implementation boundary
    for this product.

## Navigation I Would Build

Top-level navigation:

- Now
- Highlights
- Moments
- Outputs
- Library
- Observatory
- Insights
- Looks
- Automation
- Engine Room

Secondary object links:

- every Moment links to Source Lineage, Outputs, Sky Cycle, Camera/Profile;
- every Output links to Source Lineage, Look/Recipe, Moments, Sky Cycle;
- every Sky Cycle links to Moments, Outputs, Phases, Source Confidence, Health;
- every Observatory warning links to affected cycles, moments, and outputs.

Mode behavior:

- Basic shows Now, Highlights, Moments, Outputs, Library, Observatory summaries.
- Advanced adds Insights, Looks, Automation, source/lineage detail.
- Developer adds Engine Room, raw diagnostics, audit, safe-action internals.

Basic should not hide Moments, Outputs, Library, or Observatory. It should hide
noise, not capability.

## New Ideal Flow

The product should answer user intent before it exposes domain hierarchy.

For an exceptional cycle:

```text
Now -> Highlights -> Moment or Output -> Source/Lineage -> Share/Export state
```

For a boring but successful cycle:

```text
Now -> All Clear summary -> optional Sky Cycle Report
```

For a meteor:

```text
Now/Notification/Highlights -> Meteor Moment -> Evidence -> Related Outputs
```

For a timelapse:

```text
Now/Highlights/Outputs -> Timelapse Output -> Look/Source/Share readiness
```

For a memory three years later:

```text
Library -> Moment Type/Phenomenon -> Moment -> Output/Sky Cycle/Source
```

For two cameras:

```text
Now -> Camera facet -> Highlights/Moments/Outputs with source identity visible
```

For an observatory issue:

```text
Now Warning -> Affected Objects -> Observatory Diagnosis
```

## Overall Score

Current product flow score: 8.0/10.

Why not lower:

- the domain model is strong;
- the safety model is strong;
- Now and Sky Cycle are good first prototypes;
- the product has escaped admin/settings-first thinking.

Why not higher:

- the navigation is too linear;
- Highlights is missing as a first-class surface;
- Moment and Output are not prominent enough;
- Library is undervalued for long-term retrieval;
- Observatory is not yet fully treated as an ambient trust layer.

## Final Recommendation

Do not abandon the domain model.

Do change the navigation priority.

Keep:

```text
Now, Sky Cycle, Phase, Moment, Source, Output, Look, Observatory
```

But stop presenting the product as:

```text
Now -> Sky Cycle -> Moment -> Output -> Observatory
```

Use:

```text
Now -> Highlights -> Moment/Output -> Source Trust -> Sky Cycle Context
```

and:

```text
Library -> remembered phenomenon/result -> Moment/Output/Sky Cycle
```

The next surface should probably not be generic Moment Detail yet. It should be
either:

1. `Highlights v1`, because it validates the real morning flow; or
2. `Moment Detail v1`, but only if designed as the object behind a Highlight.

If the goal is to build the best product, `Highlights v1` should come first.
It is the missing connective tissue between Now, Moment, Output, and Sky Cycle.

## The One Question

If this were truly the best AllSky software in the world, what would still be
its biggest defect?

Answer:

It might still make the user choose where to go before it has told them what is
worth their attention.

The next direction should be to make Hybrid excellent at attention selection:

- what mattered;
- why it mattered;
- whether it is trustworthy;
- what output/source proves it;
- what the user can do next.

That is the product's real differentiator.
