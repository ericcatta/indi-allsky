# Hybrid Observatory v1 Review

## Purpose

Observatory v1 is the first read-only product surface for understanding whether
the physical and logical observing system is ready to work.

It follows the frozen product flow:

Now -> Highlights -> Moment -> Output -> Sky Cycle -> Library -> Observatory -> Settings -> Developer / Engine Room

Observatory should answer:

- can the camera system capture reliably?
- is the capture pipeline healthy?
- are source files being preserved?
- is storage safe enough?
- are generated outputs and integrations in a usable state?
- does anything require attention?

It is not Developer, Settings, a raw system dashboard, or a technical admin
panel.

## What Works

- The page is organized around product health rather than implementation
  metrics.
- Camera, capture, source preservation, storage, generation, integrations, and
  attention items are separate contract sections.
- Source preservation is treated as a first-class trust requirement.
- Readiness is expressed as product language rather than raw config or service
  internals.
- The builder is framework-free and fake/static.
- The template is render-only and does not include live refresh behavior.
- Validation covers section presence, allowed statuses, trust/risk levels,
  attention item lists, sensitive keys, absolute paths, callables, and JSON
  safety.

## Static/Fake Scope

Everything in v1 is static/fake:

- no database;
- no queries;
- no storage scan;
- no device probe;
- no camera connection probe;
- no remote request;
- no media read;
- no live health refresh;
- no real source preservation status;
- no real generation or integration status.

## Limits

- It cannot yet reassure the user with real health evidence.
- It cannot distinguish an OK system from a degraded system.
- It cannot explain real capture gaps, storage pressure, or failed generation.
- Existing observatory subpages still exist separately and are not consolidated
  into this v1 product surface.

## Safety Boundary

Observatory v1 does not perform database access, filesystem inspection, device
probing, camera probing, remote service access, RAW/FITS reads, media reads,
preview lookup, live refresh, safe actions, or mutations.

Future real health data must be bounded, cached or cheap, sanitized, and
RPi5-first.

## Product Score

Initial score: 7.2/10.

The page has the right product shape: health as readiness and trust, not admin
telemetry. The score remains limited because no real health evidence is
connected yet.

## Risks

- It could drift back into Developer if raw service internals dominate.
- It could become Settings if remediation controls are added too early.
- It could become noisy if every warning is promoted equally.
- It could become expensive on Raspberry Pi 5 if future checks are not bounded.

## Recommended Next Step

Do not connect real checks yet.

Recommended Mission 036: consolidate the v1 product surface set. Review Now,
Highlights, Moment, Output, Sky Cycle, Library, and Observatory together before
adding Settings/Developer or real data.
