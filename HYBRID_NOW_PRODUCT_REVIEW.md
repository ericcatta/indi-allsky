# HYBRID NOW PRODUCT REVIEW

## Purpose

This review evaluates the first read-only `/modern-admin/now` prototype as a
Product UI surface, not as a ported admin page.

The prototype is intentionally static and placeholder-driven. That is correct
for this stage: it tests information architecture, product language, and
frontend/backend boundaries before any live NowView contract exists.

## Review Summary

Overall rating: 6.5/10 as a product prototype.

The page is a useful first physical artifact for the new direction, but it is
not yet the real Hybrid AllSky home. It demonstrates the correct domains and
keeps the implementation safe, but it is still too skeletal to deliver the
morning/now experience described by the product principles.

It should be treated as a scaffold, not a destination.

## What Works

- The route is domain-first: `Now` is a product object, not a Classic page copy.
- The page is read-only and honest about missing contracts.
- The view passes a structured view model to the template.
- The template renders the model and does not perform domain logic.
- The sections match the Product Architecture: Current Sky, Sky Cycle, Moments,
  Outputs, Observatory Health, and Attention Items.
- Source preservation and non-destructive outputs appear in the product
  language.
- The page does not query the database, scan files, evaluate RAW/FITS, or start
  media generation.
- The page is server-rendered and RPi5-first.

## What Does Not Work Yet

- It does not yet answer "what is happening now?" because every live status is a
  placeholder.
- It does not yet produce the morning/sky-cycle briefing the product vision
  calls for.
- It does not show a real latest frame, source coverage, output readiness, or
  observatory health.
- It has no visual hierarchy strong enough to make the user understand the
  state in ten seconds.
- It still lives under `/modern-admin`, so it inherits an admin mental model.
- The navigation links still point to legacy Modern Admin concepts such as
  dashboard and settings rather than product-domain surfaces.

## What Is Too Placeholder

- Current phase is `Unknown` instead of a credible `day`, `twilight`, `night`,
  or `unknown with reason`.
- Latest image is not represented visually.
- The Sky Cycle briefing has no date, cycle label, coverage estimate, or
  confidence.
- Moments all have identical placeholder confidence and evidence.
- Generated outputs do not distinguish between missing, queued, generated, or
  blocked.
- Observatory Health does not surface any real safe summary.

The placeholder honesty is correct. The density of placeholders makes the page
feel more like a contract preview than a product screen.

## Admin Panel Risk

Risk: medium.

The card layout and "Read-only product prototype" language are safe, but the
surface still risks feeling like an admin panel because:

- it is mounted under `/modern-admin`;
- the links point back to Modern dashboard, Settings, and Observatory;
- it lacks a strong product headline or operational verdict;
- every card uses similar status-card treatment.

The next iteration should move toward product sections and away from equal
weight admin cards.

## Too Poetic / Consumer Risk

Risk: low to medium.

The page mostly avoids poetic language. The main risk is not consumer tone; the
risk is being too abstract. Phrases like "Future MomentSummary evidence" are
accurate for developers but weak for product UX.

Future copy should be scientific/astrophoto:

- "No cycle summary available yet"
- "Source coverage not evaluated"
- "Output recipe pending"
- "Moment evidence pending backend contract"

Avoid decorative storytelling until the backend can provide real evidence.

## Scientific / Astrophotographic Gaps

The page needs real scientific/astrophoto anchors before it feels like Hybrid
AllSky:

- latest frame thumbnail or safe placeholder with timestamp;
- current phase derived from a future phase contract;
- source coverage percentage or bounded status;
- output status for image, timelapse, keogram, startrail;
- moment evidence fields: time, source frame/range, confidence, reason;
- sky quality metrics when available: SQM/ADU/cloud/quality flags;
- look/output recipe metadata for derived media;
- explicit source preservation status.

These should arrive through sanitized backend view models, not template logic.

## Frontend / Backend Separation

Rating: 8/10.

The implementation respects the boundary:

- backend view creates `modern_admin_now`;
- template renders the model;
- no domain lookup lives in the template;
- no permission, source, lineage, or rendering logic is inferred client-side.

The missing piece is a formal NowView builder/service. That should come later
and should remain backend-owned.

## RPi5-First Review

Rating: 9/10.

The prototype is lightweight:

- server-rendered;
- no JavaScript;
- no polling;
- no DB query in the Now view;
- no filesystem scan;
- no media generation;
- no image processing.

Future live data must preserve this shape by using cached summaries, bounded
queries, and lazy/paginated detail.

## Product Principles Fit

### Product First

Good direction. It starts from Now as a product experience rather than a Classic
route.

### Experience First

Partial. The sections reflect the desired experience, but the page does not yet
create the five-minute morning flow.

### Domain First

Strong. The page maps cleanly to Now, Sky Cycle, Moment, Source, Output, Look,
and Observatory.

### Source Preservation

Present but not yet measurable. The next contract must make source preservation
visible as a real status.

### Non-Destructive Rendering

Present as product language. Needs OutputRecipe/Look data to become real.

### Progressive Disclosure

Incomplete. The page is Basic-facing in intent, but Advanced/Developer exits are
still Modern Admin links rather than product-level drilldowns.

## First Real Data To Connect Later

Connect only through a sanitized NowView backend contract:

1. Current phase label and reason.
2. Latest image metadata: timestamp, camera/profile label, safe thumbnail URL if
   already available through existing safe media URL rules.
3. Source preservation aggregate: source enabled, latest source timestamp,
   bounded coverage status.
4. Output readiness: best image, timelapse, keogram, startrail status.
5. Latest notifications summarized as AttentionItems.
6. Cached observatory health: camera, storage, generation, upload.
7. Existing safe metadata analytics summarized, not raw.

## What Not To Connect Yet

- Raw config values.
- Full source file paths.
- RAW/FITS reads.
- Filesystem scans.
- Live media generation or conversion.
- Safe actions or mutative buttons.
- Task queue mutations.
- OAuth/upload operations.
- Download links.
- Unbounded moments/media/source lists.
- Direct Classic AJAX endpoints.

## Next Mission Recommended

Mission 004 should define and implement a minimal `NowView` backend contract
builder with static/fake-safe data only, or very bounded existing metadata if it
can be obtained without heavy queries.

Recommended shape:

- create a small view-model builder function/class;
- keep it backend-owned and template-independent;
- add unit/helper tests if lightweight;
- keep `/modern-admin/now` read-only;
- replace the current inline placeholder dictionary with a named NowView
  structure;
- do not connect live DB/filesystem yet.

This would improve architecture without pretending the product has real Now
truth before the backend contract exists.

## Final Verdict

The prototype is safe and directionally correct.

It is not yet the product home. It is the first visible contract sketch.

Proceed, but do not spend time polishing the current placeholder UI before the
NowView contract exists. The next value is not prettier cards. The next value is
credible, bounded, sanitized product truth.
