# Hybrid Library v1 Review

## Purpose

Library v1 is the first read-only product surface for long-term retrieval.

It follows the frozen product flow:

Now -> Highlights -> Moment -> Output -> Sky Cycle -> Library -> Observatory -> Settings -> Developer / Engine Room

Library is where a user should eventually rediscover meaningful sky observations
over time: Highlights, Moments, Outputs, Sky Cycles, future Favorites,
phenomena, source-backed records, and generated results.

It is not a gallery, search engine, file browser, media viewer, or admin index.

## What Works

- The page frames Library as an archive of meaning rather than a list of files.
- The UX uplift makes the page feel more like product memory: find notable sky observations over time, organized by Highlights, Moments, Outputs, Sky Cycles, and future Favorites.
- Collections separate Highlights, Moments, Outputs, Sky Cycles, Favorites, and
  phenomena without introducing a new product domain.
- Search and filters are represented as future bounded contracts, not live UI.
- Recent items are static examples that show how archive entries should carry
  kind, date, phase, Highlight status, source trust, output status, and notes.
- The memory model explicitly states that retrieval should work by meaning, not
  raw implementation paths.
- The builder is framework-free and the template is render-only.
- Validation covers collection type allowlists, item kind allowlists, list
  requirements, unsafe paths, sensitive keys, callables, and JSON safety.

## Static/Fake Scope

Everything in v1 is static/fake:

- no database;
- no query;
- no filesystem access;
- no media read;
- no preview;
- no real search;
- no real indexing;
- no pagination;
- no Favorites;
- no saved searches;
- no tags.

## Limits

- It cannot yet retrieve real items.
- It cannot prove whether the collection model is enough for long-term use.
- It may still feel abstract because no real archive entries are connected.
- The search and filter language is intentionally present but disabled, which
  makes the page useful for contract shaping but not yet useful as a daily tool.

## Safety Boundary

Library v1 does not perform database queries, filesystem scans, RAW/FITS reads,
media reads, preview lookup, real search, indexing, download/share behavior,
safe actions, or mutations.

Future real Library data must be bounded, paginated, sanitized, and RPi5-first.

## Product Score

Initial score: 7.0/10.

Post-uplift score: 7.4/10.

The product direction is clearer after the uplift: Library should help users find remembered sky observations by meaning, not by file paths or thumbnails. The score remains limited because the page has no real archive data and cannot yet demonstrate retrieval speed or usefulness.

## Risks

- It could become a generic gallery if media thumbnails dominate too early.
- It could become a file browser if source paths leak into product language.
- It could become too expensive on Raspberry Pi 5 if search is implemented as
  unbounded database or filesystem scanning.
- It could duplicate Highlights if Library starts ranking attention instead of
  retrieving memory.

## Recommended Next Step

Do not connect real search or filesystem data yet.

Recommended next step: keep Library static until bounded, paginated metadata retrieval is designed. Do not add filesystem indexing, preview thumbnails, or broad search scans.
