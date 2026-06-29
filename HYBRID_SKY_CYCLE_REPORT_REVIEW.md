# HYBRID SKY CYCLE REPORT REVIEW

## Purpose

This review evaluates the first `/modern-admin/sky-cycle` product prototype.

Sky Cycle Report is the second domain-first Product UI surface after Now v1. It
is intentionally read-only, fake/static, contract-first, and Raspberry Pi 5
first.

## What It Does

Sky Cycle Report v1 introduces a dedicated product surface for the question:

```text
What happened during the sky cycle?
```

It presents a sanitized placeholder contract with these sections:

- cycle summary;
- phase timeline;
- moments summary;
- generated outputs summary;
- source confidence summary;
- observatory health summary;
- attention items;
- metadata.

The page links back to Now and keeps the product navigation moving from:

```text
Now -> Sky Cycle -> Phase -> Moment -> Source -> Output -> Look -> Observatory
```

## What Is Fake / Static

Everything in Sky Cycle Report v1 is fake/static.

Specifically:

- cycle boundaries are not evaluated;
- day/night/twilight ranges are not calculated;
- twilight is explicitly `not_evaluated`;
- moment detection is not connected;
- generated output status is not connected;
- source coverage is not calculated;
- observatory health is not evaluated;
- attention items are placeholders.

This is deliberate. The goal is contract shape and product language, not live
truth.

## What Is Safe

The prototype does not:

- query the database;
- scan the filesystem;
- call `open()`;
- read RAW/FITS/source data;
- generate media;
- create preview URLs;
- call Classic AJAX endpoints;
- expose actions;
- POST/fetch from the browser;
- modify Classic behavior.

The view model is built in the backend product contract layer and validated
before template rendering.

## What Is Missing

Sky Cycle Report cannot yet be considered useful product truth because it lacks:

- a real SkyCycle object;
- a real phase boundary model;
- source coverage calculation;
- source lineage;
- MomentSummary backend data;
- OutputSummary/backend readiness;
- observatory health summary;
- Flask integration tests for the new route.

## Product Score

Initial Sky Cycle Report score: 6.8/10.

Why it scores above a pure mockup:

- it is domain-first;
- it follows Product Architecture;
- it has a backend-owned contract;
- it has validation;
- it has a product route and template;
- it is safe and RPi5-first;
- it avoids Classic copy behavior.

Why it is not higher:

- no real cycle data;
- no real moments;
- no real outputs;
- no real source coverage;
- no real observatory health;
- still mounted under `modern-admin`;
- no integration tests.

## Risks

### Placeholder Drift

Risk: medium.

If more placeholder sections are added without real backend contracts, the page
could become another aspirational dashboard.

### Premature Runtime Data

Risk: medium-high.

The first real Sky Cycle data source must be chosen carefully. Cycle boundaries
and source coverage can become expensive or incorrect if implemented casually.

### RPi5 Load

Risk: medium.

Future cycle reports must avoid unbounded image/source scans, large joins, and
runtime media inspection.

### Product Language

Risk: low-medium.

The prototype is more product-oriented than admin-oriented, but some copy still
mentions backend contracts. That is acceptable for v1 but should fade as real
contracts arrive.

## Next Mission Recommended

Do not connect real DB/runtime data yet.

Mission 021 should be a technical review to identify the safest first bounded
Sky Cycle data source.

Recommended focus:

- cycle identity / time range candidate;
- latest/current day-night context reuse;
- existing image metadata timestamps;
- whether a single bounded query can establish "latest cycle candidate" without
  full cycle computation;
- what must remain fake until a real SkyCycle backend object exists.

The safest likely next step is not implementation. It is a source review similar
to the latest-frame and current-phase reviews.

## Final Verdict

Sky Cycle Report v1 is a good second product surface prototype.

It should now pause until a bounded source review identifies one safe real field
to connect. The first real data should be small, cached or bounded, and should
not require filesystem inspection, RAW/FITS reads, media generation, or full
cycle computation.

## Mission 021 Update

The phase timeline contract has been strengthened.

Each phase now carries explicit product fields:

- observation value;
- source expectation;
- output expectation;
- science note;
- astrophoto note;
- supported flag;
- unsupported reason.

The timeline remains static/fake. Day and night are supported as placeholder
product concepts. Sunset and sunrise twilight remain unsupported and
`future_backend_contract` because no phase engine or astronomical boundary
contract is connected.

Validation now enforces:

- non-empty phase timeline;
- required phase fields;
- phase allowlist;
- allowed data statuses;
- boolean `supported`;
- no secrets, paths, or callables through recursive payload validation.

Updated Sky Cycle Report score: 7.1/10.

The score improves because the timeline is now a clearer product contract
instead of a thin list of labels. It remains below 8/10 because no real cycle
boundary, source coverage, moment evidence, output readiness, or observatory
health data is connected.

Next gap: perform a bounded source review for the first real Sky Cycle field,
preferably cycle identity/time range or a single non-heavy metadata-derived
candidate. Do not implement real cycle computation yet.

## Mission 022 Update

The moments summary contract has been strengthened.

`moments_summary` now describes the product question "what deserves attention?"
with explicit fields:

- count label;
- primary moment;
- moment categories;
- review queue status;
- detection status;
- item list.

Each moment item now carries:

- moment type;
- phase;
- confidence label;
- evidence list;
- source lineage status;
- related outputs status;
- science note;
- astrophoto note;
- review status.

The allowed moment types are:

- meteor;
- aurora;
- lightning;
- storm;
- clouds;
- clear window;
- sunrise;
- sunset;
- moon;
- sky quality;
- camera anomaly;
- generation issue;
- unknown.

The contract remains fake/static. No detector, source lineage, filesystem,
RAW/FITS, media generation, database query, or review queue is connected.

Validation now enforces required summary fields, required item fields, moment
type allowlist, compatible phase allowlist, evidence as a list, allowed
`data_status`, and recursive no-secret/no-path/no-callable checks.

Updated Sky Cycle Report score: 7.4/10.

The score improves because "moments" now has a real product shape instead of a
single placeholder card. It remains below 8/10 because no real detection
evidence, source lineage, output relation, or review queue exists yet.

Next gap: harden the generated outputs summary contract, or review the safest
first bounded runtime source for cycle identity/time range. Do not connect
detector data yet.

## Mission 023 Update

The generated outputs summary contract has been strengthened.

`outputs_summary` now represents generated cycle results as product objects,
not as a single placeholder card.

The summary includes:

- count label;
- generation status;
- Look policy status;
- share readiness status;
- item list.

Each output item now carries:

- output type;
- phase;
- generation status;
- Look applied;
- source lineage status;
- related moments status;
- share status;
- quality note;
- astrophoto note;
- science note;
- safe actions metadata list.

The allowed output types are:

- best image;
- latest image;
- timelapse;
- day timelapse;
- night timelapse;
- keogram;
- startrail;
- startrail video;
- storm highlight;
- aurora highlight;
- meteor highlight;
- cycle summary video;
- unknown.

The contract remains fake/static. No generated media, preview URL, download,
share, filesystem read, source lineage, rendering job, or safe action is
connected.

Validation now enforces required summary fields, required item fields, output
type allowlist, compatible phase allowlist, allowed `data_status`, metadata-only
`safe_actions_available`, and recursive no-secret/no-path/no-callable checks.

Updated Sky Cycle Report score: 7.6/10.

The score improves because Sky Cycle now has product-shaped contracts for
phases, moments, and outputs. It remains below 8/10 because all three are still
static and none has real cycle/source/output truth.

Next gap: harden observatory health summary, or perform a bounded source review
for the first real Sky Cycle field. Do not connect rendering, download, share,
or generation actions yet.
