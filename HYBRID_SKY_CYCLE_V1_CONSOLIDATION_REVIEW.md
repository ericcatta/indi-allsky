# Hybrid Sky Cycle Report v1 Consolidation Review

## Purpose

This review decides whether Sky Cycle Report v1 is consolidated enough to pause
and move to the next product surface.

It does not introduce implementation work. It evaluates the read-only,
fake/static contract created for:

- `cycle_summary`
- `phase_timeline`
- `moments_summary`
- `outputs_summary`
- `source_confidence_summary`
- `observatory_health_summary`
- `attention_items`
- `metadata`

## Product Assessment

Sky Cycle Report v1 now has the right product shape.

It answers the correct questions:

- what cycle is being reviewed;
- which phases matter;
- what moments may deserve attention;
- which outputs should exist;
- whether sources can be trusted;
- whether the observatory appears healthy;
- what still needs backend truth.

This is materially better than an admin/status page. It is organized around the
user's mental model of a complete sky cycle, not around implementation details,
tables, config keys, or Classic UI parity.

For astrophotographers, it introduces the expected chain from phase to output:
day/night context, generated media readiness, Look policy, share readiness, and
quality notes.

For science-oriented users, it introduces the expected chain from observation to
evidence: moment candidates, confidence, detector status, source lineage, source
coverage, preservation, retention, gaps, and observatory health.

The tone is mostly correct: scientific, operational, and accessible. It avoids
consumer-photo language and avoids poetic language. It still reads like a
prototype in places because most panels must honestly say that data is not
connected yet.

## What Still Feels Too Placeholder

The report is not yet useful as a daily product report because no cycle truth is
connected.

The most visible placeholder gaps are:

- no real cycle identity or time range;
- no real phase boundaries;
- no real moment detection;
- no real output inventory;
- no real source coverage;
- no real source lineage;
- no real observatory health summary;
- no real confidence calculation;
- no preview or media context.

These gaps are acceptable for v1 because the goal was contract consolidation,
not runtime truth.

## Architecture Assessment

The architecture is strong enough to pause.

Strengths:

- the Product UI uses a backend-owned view model;
- the Flask view remains thin;
- templates render sanitized payloads;
- validation enforces required sections and nested contracts;
- allowlists exist for phases, moment types, output types, data statuses, risk
  levels, and metadata-only safe actions;
- fake/static payloads make the product shape visible without pretending to have
  real data;
- the pattern remains RPi5-first: no polling, no heavy query, no filesystem
  scan, no media read, no generation.

Residual coupling risks:

- as real data is added, there is a risk of putting query construction directly
  into Flask views;
- source coverage could easily become an unbounded filesystem or database scan;
- moment detection could pull in detector/runtime logic too early;
- output inventory could accidentally expose paths, filenames, preview URLs, or
  download behavior;
- health summaries could drift toward admin-panel service checks instead of
  product-level health.

The current fake/static contract avoids those risks.

## Future Data Candidates

Safe future candidates, only after source review:

- bounded cycle identity and time range;
- bounded latest image count/coverage metadata;
- metadata-only output counts;
- metadata-only source preservation status;
- metadata-only camera/capture health already available in a safe context.

Data not to connect yet:

- RAW/FITS reads;
- filesystem scans;
- media preview URLs;
- generated media reads;
- detector pipelines;
- source lineage traversal;
- download/share actions;
- render/regenerate actions;
- live service health checks;
- unbounded image queries;
- Classic AJAX/action paths.

## Blockers

Before Sky Cycle Report can become a real report, the project needs bounded
backend contracts for:

- cycle boundaries;
- source coverage;
- output inventory;
- moment candidate summaries;
- observatory health summaries.

Each must be reviewed independently before runtime wiring.

## Final Score

Sky Cycle Report v1 score: 7.8/10.

Reasoning:

- product model: strong;
- contract shape: strong;
- safety posture: strong;
- RPi5 posture: strong;
- current user value: limited by fake/static data;
- visual/product confidence: improving but still clearly prototype-level;
- readiness for real data: not yet, requires bounded source reviews.

The score should not be pushed higher until at least one real bounded Sky Cycle
data source is connected safely.

## Recommendation

Pause Sky Cycle Report v1.

Do not keep adding placeholder sections. The report now has enough structure to
serve as a product contract. More fake/static expansion would risk
over-engineering and would not materially improve the user's experience.

The next product surface should be Moment Detail v1.

Why:

- moments are the emotional and scientific center of the product;
- Now and Sky Cycle both point toward moments as the next object;
- Moment Detail can remain fake/static and contract-first;
- it can define source lineage, evidence, related outputs, confidence, and
  review status without connecting detectors or media;
- it prepares the eventual path from "what happened?" to "why should I care?".

Output Detail is also important, but it should follow Moment Detail. Outputs
make more sense once the product can explain the event or condition that made
them worth generating.

Library should come later. It risks becoming a media browser before the domain
objects are mature.

## Mission 026 Proposal

Mission 026 should create a read-only Moment Detail v1 prototype.

Suggested prompt:

```text
Mission 026 - Create Moment Detail v1 prototype

Objective:
Create the third product surface for Hybrid AllSky: Moment Detail v1.

It must be read-only, contract-first, fake/static, and RPi5-first.

Do not connect DB.
Do not connect filesystem.
Do not read RAW/FITS.
Do not connect detectors.
Do not generate media.
Do not add actions.

Tasks:
1. Add build_moment_detail_view() in product_view_models.py.
2. Add validate_moment_detail_payload().
3. Include sections:
   - moment_summary
   - evidence_summary
   - source_lineage_summary
   - related_outputs_summary
   - science_context
   - astrophoto_context
   - review_status
   - attention_items
   - metadata
4. Add a read-only route /modern-admin/moment.
5. Add template modern_admin/moment.html.
6. Register ownership map as Product UI read-only prototype.
7. Add tests for JSON-safety, required fields, allowlists, no path/secret/callable,
   and no mutative controls.
8. Create HYBRID_MOMENT_DETAIL_REVIEW.md with initial score and next gap.

Constraints:
No DB query, no filesystem, no open(), no detector call, no RAW/FITS read,
no media generation, no preview/download/share URL, no form, no POST, no fetch,
no /ajax/, no Classic change, no action.
```

## Decision

Sky Cycle Report v1 is consolidated enough to stop here temporarily.

Proceed to Moment Detail v1 as the next product surface.
