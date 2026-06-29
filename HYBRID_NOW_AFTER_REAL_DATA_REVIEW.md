# HYBRID NOW AFTER REAL DATA REVIEW

## Purpose

This review evaluates `/modern-admin/now` after the first two bounded runtime
signals were added:

- latest frame metadata from a bounded image-table provider with safe fallback;
- current phase summary derived from the existing `context['night']` value.

This is a Product Architecture review, not an implementation plan.

## Current Score

Current Now score: 8.1/10.

Now is no longer only a static contract sketch. It has crossed an important
threshold: it can show two pieces of bounded product truth without breaking the
frontend/backend boundary or the Raspberry Pi 5 constraints.

It is still not the final product home. The screen now knows something real, but
it does not yet explain a sky cycle, prove source confidence, or identify what
is worth reviewing.

## What Improved Since 7.5/10

### 1. Current Sky Is Less Abstract

`current_phase_summary` makes the first card immediately more useful. A user can
now see `day`, `night`, or `unknown` instead of a generic placeholder.

The limitation is handled honestly: twilight is explicitly not evaluated.

### 2. Latest Frame Has a Safe Runtime Anchor

`latest_frame_summary` now has a bounded path toward real metadata:

- single latest image metadata source;
- camera-scoped query;
- no filename;
- no path;
- no preview URL;
- no filesystem access;
- safe fallback.

That makes Now feel connected to the actual observatory without becoming heavy.

### 3. Product Contract Discipline Is Holding

The most important win is architectural. The screen now proves that Hybrid can
connect real data through:

```text
Flask/service context -> provider -> backend-owned NowView -> sanitized template
```

That is the right direction.

### 4. RPi5-First Constraints Still Hold

No polling, no media processing, no source reads, no filesystem scans, no
frontend framework, and no mutative action were introduced.

## What Still Feels Placeholder

### Current Verdict

The headline still says `Observation data not evaluated yet`. That is honest,
but it prevents the page from delivering the product promise in the first ten
seconds.

The current verdict is the emotional and operational center of Now. Until it is
based on a real bounded summary, the page cannot feel finished.

### Sky Cycle Briefing

The briefing section still has no real cycle identity, date range, source
coverage, generated output status, or confidence.

It describes the future product rather than reporting the current one.

### What Happened / Worth Reviewing

The Moments area is still entirely synthetic. That is acceptable for safety, but
it is the biggest product gap because the core user question is:

```text
Is there anything worth looking at?
```

Right now Now cannot answer that.

### Source Confidence

The page can say a latest frame exists, but it cannot yet summarize whether
source capture is continuous, missing, stale, or preserved.

This is the next real product truth users need before they trust the report.

### Observatory Health

Health is still mostly product copy. It does not yet summarize camera, storage,
generation, uploads, or source preservation from bounded backend signals.

The risk is that it reads like an admin dashboard waiting to happen.

## First Ten Seconds Review

Score: 7.8/10.

The user can now understand:

- whether the system thinks it is day or night;
- whether latest frame metadata exists;
- that source and media evaluation are still incomplete.

The user still cannot understand:

- whether the observatory is healthy;
- whether the last sky cycle was successful;
- whether any moment deserves attention;
- whether generated outputs are ready.

The page is much closer, but it still answers "what is connected?" more clearly
than "what happened?"

## User Value By Audience

### Astrophiles

Value: moderate.

They get a clear phase and latest-frame metadata. They do not yet get a reason
to explore media or moments.

### Astrophotographers

Value: moderate.

The source-preservation language is good, but output readiness and look/output
recipe status are not real yet.

### Science Users

Value: moderate-low.

The product is honest and safe, but there is no source coverage, evidence
confidence, or quality metric yet.

## Microcopy Review

Score: 8/10.

The copy is mostly aligned with the desired tone:

- scientific / operational;
- not poetic;
- not consumer-photo;
- honest about missing contracts.

Main weakness: some copy still speaks to implementers more than observers.

Examples that still feel contract-first:

- `pending backend contract`;
- `placeholder answers`;
- `No detector evidence connected yet`.

These are safe, but not final. Future copy should move toward:

- `Not evaluated yet`;
- `No evidence available yet`;
- `Source coverage unavailable`;
- `Output readiness unavailable`.

## Safety Review

Score: 8.8/10.

The current direction is safe:

- no mutative UI;
- no safe action execution;
- no unbounded DB access;
- no filesystem scan;
- no RAW/FITS read;
- no media generation;
- no preview URL;
- product builder remains framework-free.

The main safety gap is still integration testing. The code has strong helper
tests, but not full Flask/app/DB test coverage.

## Risk Of Growing In The Wrong Direction

Risk: medium.

The page is at a fork.

Good path:

```text
Now becomes a concise product briefing backed by small bounded summary signals.
```

Bad path:

```text
Now becomes another dashboard of technical cards.
```

The next step should not add many panels. It should make one existing product
question more truthful.

## What Is Needed For 8.5/10

Now can reach 8.5/10 with one more bounded, meaningful summary:

- source preservation / source coverage summary; or
- output readiness summary; or
- attention summary from existing safe notifications.

The best next candidate is `source_confidence_summary`.

Why:

- it directly supports trust;
- it fits the product mission;
- it does not require media generation;
- it can start fake/provider-contract-only;
- later it can be backed by bounded metadata counts or cached state;
- it improves Latest Frame and Sky Cycle without adding a new page.

## What Is Needed For 10/10

Now needs four mature product truths:

1. Current state
   - phase, latest frame, capture freshness, source recording.

2. Sky Cycle report
   - cycle identity, coverage, generated outputs, notable moments.

3. Evidence and review targets
   - moments with confidence, reason, source lineage, and output links.

4. Observatory health
   - concise health verdict with drilldowns, not admin noise.

It also needs a future route outside the `modern-admin` mental model. The
current path is acceptable during migration, but not final product language.

## Next Direction Decision

Recommendation: consolidate Now with one more bounded contract before starting
Sky Cycle Report or Moment Detail.

Do not start Sky Cycle Report yet. It would be mostly placeholder until Now has
source confidence and output readiness.

Do not start Moment Detail yet. It would be premature without a real moment
source, event confidence model, and source lineage.

Do not add another DB-backed runtime query yet unless reviewed first.

## Recommended Mission 018

Mission 018 should add a `source_confidence_summary` contract to NowView as a
fake/static provider only.

This improves the product model without adding risky runtime access.

It should answer, conservatively:

```text
Can I trust the sources?
```

Initial fields:

- status;
- data_status;
- source_recording_status;
- latest_source_state;
- coverage_label;
- gaps_label;
- preservation_label;
- note;
- evidence;

All values should be placeholder/not evaluated. No DB, filesystem, RAW/FITS, or
media reads.

## Mission 018 Prompt

```text
Mission 018 — Add source confidence summary contract to NowView

Objective:
Add a read-only, fake/static `source_confidence_summary` to NowView.

Do not connect DB, filesystem, RAW/FITS, media generation, camera runtime, or
new routes.

Tasks:
1. Add `source_confidence_summary` to the NowView payload.
2. Create a framework-free helper/provider in `product_view_models.py`.
3. Include fields:
   - status
   - data_status
   - source_recording_status
   - latest_source_state
   - coverage_label
   - gaps_label
   - preservation_label
   - note
   - evidence
4. Render it in `/modern-admin/now` near Source confidence.
5. Validate the new section:
   - required keys;
   - allowed data_status;
   - JSON-safe;
   - no secrets;
   - no paths;
   - no callable;
   - safe_actions_available remains metadata-only.
6. Add tests for contract presence, JSON safety, validation failure, and no
   Flask/db/open/filesystem imports.
7. Update `HYBRID_NOW_PRODUCT_REVIEW.md` with a short note.

Constraints:
- no mutations;
- no actions;
- no unbounded DB;
- no DB at all for this mission;
- no filesystem scan;
- no RAW/FITS read;
- no media generation;
- no route/API changes;
- no fetch/JS/POST;
- frontend/backend separation;
- RPi5-first.
```

## Final Recommendation

Continue with Now, but do not broaden it. Deepen one product question at a time.

The next product question should be:

```text
Can I trust the sources?
```

That is the right bridge from latest frame metadata toward real Sky Cycle
reporting.

## Mission 018 Update

`source_confidence_summary` has been added to NowView as a fake/static contract.

It answers the product question "Can I trust the sources?" only at the contract
level for now. It does not calculate source coverage, read RAW/FITS files,
inspect the filesystem, query the database, generate media, or infer real
preservation state.

Real source coverage remains future work and must be introduced as a bounded
backend summary before it is treated as product truth.
