# Hybrid Product UI v1 Consistency Review

## Purpose

This review evaluates the completed Product UI v1 skeleton as one product
system, not as a set of isolated prototype pages.

The frozen v1 flow is:

Now -> Highlights -> Moment -> Output -> Sky Cycle -> Library -> Observatory -> Settings -> Developer / Engine Room

No runtime behavior, routes, templates, builders, or real data sources were
added for this review.

## Summary Verdict

The v1 skeleton is coherent enough to freeze and review as a product system.
It has the right safety posture: backend-owned view models, validation,
server-rendered templates, read-only surfaces, and RPi5-first constraints.

The main weakness is not architecture. It is product expression. Several
surfaces still read like contract demonstrations instead of final user
experiences. That is acceptable for v1 skeleton consolidation, but it should
not become the final product language.

## Naming Consistency

Strong names:

- Now
- Highlights
- Moment
- Output
- Sky Cycle
- Library
- Observatory

Watchouts:

- `Moment Detail` and `Output Detail` are useful implementation labels, but
  they are not ideal product-facing names forever.
- `Sky Cycle Report` sounds like a report, while the other surfaces are objects
  or places. This is acceptable in v1 because Sky Cycle is context, not the
  primary attention object.
- `Developer / Engine Room` remains the right separation for internals, but it
  should stay out of the primary user journey.

## Microcopy Consistency

What works:

- The surfaces consistently avoid sensational language.
- Placeholder states are honest.
- Source preservation and non-destructive rendering are named repeatedly.
- Real-data gaps are labeled as pending backend contracts.
- Product-language polish now makes Observatory readiness, Library memory,
  Highlight attention, Moment case analysis, and Output generated-result
  lineage more consistent.

What needs work:

- Phrases like "pending backend contract" and "not evaluated yet" still appear
  often enough that the UI can feel like a developer specification in places.
- Basic product surfaces need more user-centered language once real data is
  introduced.
- Placeholder copy should eventually be replaced with useful empty states, not
  simply removed.

## Tone Review

The tone is mostly scientific and astrophotographic. It avoids consumer-photo
language and avoids poetic claims.

Remaining risks:

- Observatory can drift toward admin-panel language if future health data is
  shown as raw subsystem names.
- Library can drift toward a generic gallery if it prioritizes thumbnails over
  retrieval, lineage, and meaning.
- Highlights can drift toward a list of detector outputs if it does not explain
  why each item deserves attention.

## Domain Distinctions

### Highlight vs Moment

Highlight is the curated attention object. It answers: "Start here."

Moment is the analyzable event or condition. It answers: "What happened, when,
and why does the evidence support it?"

Current distinction: conceptually strong, visually still fragile.

### Highlight vs Output

Highlight decides what deserves attention.

Output is a generated or derived result. It answers: "What was produced, from
which sources, with which Look or recipe?"

Current distinction: strong in contracts, needs stronger product hierarchy in
future UI.

### Highlight vs Favorite

Highlight is suggested or curated attention.

Favorite is a user decision.

This distinction is critical and should be protected before real data or user
curation is added.

### Sky Cycle vs Library vs Observatory

Sky Cycle gives temporal context for phases, moments, outputs, source trust,
and health across a cycle.

Library supports long-term retrieval.

Observatory explains readiness and health without becoming Developer or
Settings.

Current distinction: stronger after the final polish. The main remaining risk
is that Sky Cycle and Library both become broad summaries unless Library stays
retrieval-first.

## Flow Review

What works:

- Now -> Highlights is present and conceptually correct.
- Highlights -> Moment is present and matches the frozen flow.
- Moment -> Output is present and natural for analysis.
- Output -> Library is present and supports long-term retrieval.
- Now -> Sky Cycle is present for users who want cycle context.
- Sky Cycle now links to Highlights, Moment, Output, Library, Now, and
  Observatory.
- Library now links to Observatory.
- Observatory is reachable from Now and several product surfaces.

Remaining watchouts:

- Some pages still link back to Now more clearly than they explain the forward
  product journey.
- Link labels are consistent enough for v1, but not yet governed by a shared
  product navigation map.

Recommendation:

Treat future navigation changes as a deliberate product navigation pass. The
known v1 link gaps are closed; remaining work is refinement, labeling, and
hierarchy.

## Dead Ends

There are no total dead ends because the Modern shell remains available and
most product surfaces link back to Now.

Product-specific dead ends have been reduced:

- Sky Cycle is no longer under-connected to the main v1 surfaces.
- Library can now move directly to Observatory.
- Highlights needs a stronger sense of "this is the first thing to review"
  before it becomes the center of the product.

## Risk Review

### Admin Panel Risk

Low to medium. Observatory now reads more like readiness than telemetry, but
future real health data can still pull it toward admin-panel language.

### Generic Gallery Risk

Medium. Output and Library are intentionally not galleries, but future preview
work could weaken that boundary.

### Contract-Driven UI Risk

Medium. The skeleton remains contract-first, but the final polish translates
the lowest-scoring pages into clearer product experiences.

### RPi5-First Risk

Low. The v1 skeleton is server-rendered, bounded, and avoids JavaScript,
polling, scans, media reads, and generation.

### Frontend/Backend Separation Risk

Low to medium. The product view-model pattern is strong. The main watchout is
that Flask wiring for real data should remain thin and should not grow into
domain logic.

## Recommendation

Do not add more primary product surfaces.

Before connecting more real data, complete a small product navigation and
language pass across the existing v1 surfaces. Real data should then be added
only through bounded, reviewed providers that preserve the current safety
boundary.
