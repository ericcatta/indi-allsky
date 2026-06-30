# Hybrid Product UI v1 Final Review

## Purpose

This is the final review of the Product UI v1 skeleton before entering the
real-data phase, updated after the UX hierarchy uplift and final static polish
passes.

No code, routes, templates, builders, contracts, runtime behavior, or Product
Architecture were changed for this review.

The frozen Product Architecture v1 remains:

Now -> Highlights -> Moment -> Output -> Sky Cycle -> Library -> Observatory -> Settings -> Developer / Engine Room

## 1. General Status

The Product UI v1 skeleton is complete.

It includes the primary product surfaces needed to test the end-to-end mental
model:

- Now v1
- Highlights v1
- Moment Detail v1
- Output Detail v1
- Sky Cycle Report v1
- Library v1
- Observatory v1

It is coherent enough to move forward. The major navigation gaps found during
consolidation have been fixed: Sky Cycle now links into Highlights, Moment,
Output, and Library; Library now links to Observatory; Observatory already
links to Now and Library.

What still matters before real data:

- keep the real-data phase bounded and incremental;
- avoid turning fake/static contracts into claims;
- continue reducing contract-heavy microcopy as real evidence appears;
- protect the separation between Highlight, Moment, Output, Library, and
  Observatory;
- keep every runtime provider reviewed before wiring it into a request path.

## 2. Surface Scores

| Surface | Score | Product role | Main limit | Next improvement |
| --- | --- | --- | --- | --- |
| Now | 8.3/10 | First operational product view; answers what is happening now and points the user toward Highlights. | Still partly briefing-by-contract; only two bounded real data points are connected. | Add one more cheap, bounded product signal only after review. |
| Highlights | 7.8/10 | Curated attention layer; tells the user where to start. | Concept is strong and hierarchy is better, but recommendations are still static. | Do not add AI/detectors yet; first connect only explainable, low-risk metadata after source trust is stronger. |
| Moment Detail | 7.7/10 | Explains a single case: what happened, why Hybrid surfaced it, and what evidence exists. | No real evidence, detector summary, or lineage yet. | Add bounded evidence metadata later; keep it analytical, not gallery-like. |
| Output Detail | 7.8/10 | Explains a generated result, its recipe, lineage, readiness, and limitations. | No real output metadata or preview; share/readiness remains placeholder. | Add metadata-only generated output summary before any preview URL or media read. |
| Sky Cycle Report | 7.8/10 | Gives cycle context across phase, moments, outputs, source trust, and health. | It is well-structured but entirely fake/static. | Add bounded Sky Cycle metadata only after phase/source contracts are reviewed. |
| Library | 7.8/10 | Product memory for Highlights, Moments, Outputs, Sky Cycles, and future Favorites. | No real index/search; could become generic gallery if previews dominate too early. | Start later with paginated metadata only, not filesystem indexing. |
| Observatory | 7.7/10 | Readiness console for camera, capture, source preservation, storage, generation, and integrations. | No real health evidence; risk of drifting toward admin panel. | Add cached/cheap health summaries only; avoid live probes in request paths. |

## 3. Flow End-to-End

The v1 flow is clear enough for a skeleton:

Now -> Highlights -> Moment -> Output -> Sky Cycle -> Library -> Observatory

What works:

- Now gives a safe starting point.
- Now now points more clearly toward Highlights as the next natural step.
- Highlights gives the product a stronger attention-first direction and now
  separates primary recommendation from secondary review items.
- Moment and Output are distinct enough in contract, intent, and page hierarchy.
- Sky Cycle provides context without becoming the primary home.
- Library gives long-term retrieval a clearer product-memory role.
- Observatory now asks the right operator question: can the observatory capture
  reliably?
- Observatory keeps health separate from Developer and Settings.
- Navigation is now minimally connected across the main v1 surfaces.

Where it remains weak:

- Highlights is closer to the experiential center, but still needs real
  attention data to prove the flow.
- Now still carries some of the burden of explaining the product.
- Sky Cycle is contextually rich but could become a second dashboard if not
  disciplined.
- Library has no real retrieval behavior yet.
- Observatory still has placeholder health language that can feel admin-like.

The flow is acceptable for v1. It is not yet a final product experience.

## 4. Safety / RPi5 Review

Confirmed:

- surfaces are read-only;
- no mutative product actions are exposed;
- no execute endpoints are added;
- no media generation is connected;
- no RAW/FITS/source reads are connected;
- no real preview URLs are exposed by Product UI v1 surfaces;
- product view models are backend-owned;
- templates render sanitized payloads;
- validation exists for the product payload contracts;
- most surfaces remain fake/static by design;
- Now uses bounded runtime data only where previously reviewed;
- the skeleton remains server-rendered and RPi5-first.

The main safety risk in the next phase is not the current skeleton. It is the
temptation to connect useful-looking data without a bounded provider review.

## 5. Real Data Readiness

The Product UI v1 skeleton is ready for a cautious real-data phase.

Recommended order:

1. Keep latest frame metadata and current day/night phase as the baseline real
   data in Now. DATA001 latest frame metadata is now integrated as a bounded,
   metadata-only `latest_frame_summary.frame_metadata` block.
2. Add bounded latest generated output metadata, metadata-only, with no preview
   URL and no filesystem/media read.
3. Add bounded source preservation summary from existing metadata only, with no
   RAW/FITS read and no path exposure.
4. Add bounded Observatory health summaries from cached or cheap existing
   state, with no live hardware/network/filesystem probes.
5. Add bounded Highlights from existing DB metadata only after selection
   reasons can be explained.
6. Add preview/media only after a dedicated media safety review.

The next real-data step should be small enough that failure falls back to a
static/not-evaluated state without breaking the product surface.

## 6. Stop List

Do not do next:

- no AI ranking;
- no real detector integration;
- no media generation;
- no preview URL unless it has a dedicated safety review;
- no editing;
- no output regeneration;
- no download/share behavior;
- no mutative safe actions;
- no filesystem scans;
- no RAW/FITS reads;
- no broad Library indexing;
- no live Observatory hardware checks in request paths;
- no Product Architecture changes during the first real-data pass.

## 7. Decision

Decision: ready for real data phase.

This does not mean the Product UI is final. It means the skeleton is complete,
safe, coherent, and connected enough to begin replacing carefully selected
placeholder fields with bounded real metadata.

Overall Product UI v1 skeleton score: 8.3/10.

Reasoning:

- architecture and safety are strong;
- Now and Sky Cycle are solid anchors;
- navigation gaps are closed;
- Highlights, Moment, Output, and Library now have clearer product hierarchy;
- Observatory now feels more like readiness than a technical checklist;
- Product UI remains partly contract-driven, but less so than before;
- Highlights is strategically correct and now reads more like an attention
  briefing;
- real data is now needed to prove whether the product flow works.

## DATA002 Integration Note

The real-data phase has now connected latest generated output metadata into Now
as a bounded, metadata-only summary. This advances item 3 in the readiness list
without adding preview URLs, media reads, filesystem access, downloads, sharing,
generation jobs, or mutative actions.

Output Detail remains static/fake because the current route is not
identifier-specific. A future Output Detail data step should define that runtime
contract before connecting generated-output metadata there.

## DATA003 Integration Note

Current Capture Status is now integrated into Now as a bounded metadata summary.
It uses persisted capture status/watchdog metadata and camera policy flags to
answer whether capture appears running, idle, paused, error, or unknown.

Observatory remains disconnected by design. A future Observatory readiness step
must define a broader readiness contract without live hardware, process, service,
filesystem, or network probes in request paths.

## DATA004 Integration Note

Source Trust Summary is now integrated into Now as a bounded metadata summary.
It checks latest RAW/FITS source metadata rows for the current camera and reports
source trust cautiously: metadata can support partial confidence, but it does not
prove file existence or output-to-source lineage.

Moment Detail and Output Detail remain disconnected by design. They need
identifier-specific lineage before source trust can be shown honestly.

## 8. Next Mission Proposal

The next mission should be the first cautious real-data step after the static UX
uplift.

Recommended mission:

Mission 040 - Review safe latest generated output metadata source

Goal:

Identify the safest bounded source for an Output/Now generated-output metadata
summary, without implementing runtime wiring yet.

Scope:

- analyze existing image/video/media output models and routes;
- identify metadata-only fields that can describe the latest generated output;
- require a bounded query plan;
- forbid preview URLs, filenames, filesystem paths, media reads, downloads, and
  generation;
- produce a review document with candidate sources, risks, recommended adapter
  shape, and blocker list.

Why this mission:

- it advances real product value;
- it supports Now and Output without changing architecture;
- it is safer than Highlights real ranking;
- it avoids media preview/read complexity;
- it follows the successful latest-frame review-before-wiring pattern.
