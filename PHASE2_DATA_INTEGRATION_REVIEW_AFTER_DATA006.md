# Phase 2 Data Integration Review after DATA006

This review evaluates the Product UI after DATA001 through DATA006.

It is a product and safety decision point, not an implementation plan.

## 1. Current Product State

Phase 2 has moved the Product UI from a strong read-only skeleton into a partially real, bounded product surface.

Real bounded data now exists for:

- latest frame metadata;
- latest generated output metadata;
- current capture status;
- source trust summary;
- Highlights metadata;
- Sky Cycle summary.

The strongest improvement is that Now, Highlights, and Sky Cycle no longer depend only on placeholders. They can now answer concrete product questions with allowlisted metadata:

- What is the latest known frame?
- What generated output exists most recently?
- Is capture plausibly active, idle, stale, or unknown?
- Is there source metadata that supports trust?
- What deserves attention based on explainable metadata?
- Which Sky Cycle context does the available metadata belong to?

What is still static/fake:

- Moment Detail remains a case-analysis prototype without identifier-specific moment data.
- Output Detail remains a generated-result prototype without identifier-specific output data.
- Library remains product memory without real archive/search/index data.
- Observatory remains readiness-shaped but not connected to real readiness metadata.
- Sky Cycle still has static phase, moment, output, source, and health sections below the real summary.
- Highlights metadata is explainable but intentionally primitive; it is not a detector and not ranking intelligence.

Surfaces that gained the most value:

- Now: now behaves like a real daily console, not a static prototype.
- Highlights: now has explainable attention candidates, which validates the product direction.
- Sky Cycle: now provides real cycle context instead of being purely mock data.

Surfaces that remain weakest:

- Observatory: useful shape, but still no real readiness contract.
- Library: good conceptual model, but no retrieval value yet.
- Moment Detail and Output Detail: product language is good, but they need identifier-specific data before they feel real.

## 2. Updated Scores

| Surface | Updated score | Reason |
| --- | ---: | --- |
| Now | 8.7/10 | Strongest surface. It now combines real latest frame, generated output, capture status, source trust, and product-first briefing without preview/file access. Still not 9+ because it lacks visual proof and can only summarize bounded metadata. |
| Highlights | 8.2/10 | DATA005 made it genuinely useful as an attention layer. It is still rule/metadata-based, not detector-backed, so recommendation quality is limited. |
| Sky Cycle | 8.1/10 | DATA006 added real cycle context safely. It remains limited because only the top summary is real; phase timeline, moments, outputs, and health are still static. |
| Moment | 7.7/10 | Good explanatory structure, but still disconnected from real Highlights or frame/output identifiers. |
| Output | 7.8/10 | Good non-destructive result language, but no identifier-specific generated output metadata yet. DATA002 correctly stayed in Now. |
| Library | 7.8/10 | Strong product memory concept, but no real retrieval/indexing. |
| Observatory | 7.7/10 | Clear readiness shape, but still fake/static. Correctly avoids live checks. |
| Product UI overall | 8.4/10 | The product now has a real heartbeat in Now/Highlights/Sky Cycle. It is close to internal Alpha, but not ready for a Raspberry pull without cleanup and readiness checks. |

These scores are intentionally conservative. The UI is no longer just a skeleton, but the lower half of the product flow is still mostly static.

## 3. Alpha Readiness

Hybrid is close to an internal Alpha, but not quite ready for a Raspberry pull.

The project is ready for Alpha preparation because:

- the architecture is stable;
- Product UI v1 surfaces exist;
- data integrations followed a repeatable safe pattern;
- adapters are bounded and allowlisted;
- Product builders remain framework-free;
- Now/Highlights/Sky Cycle provide real daily value;
- no preview/media/filesystem/RAW/FITS boundary has been crossed.

Missing before Raspberry pull:

- Release Candidate cleanup audit;
- confirmation that Product UI routes render without local developer assumptions;
- RPi5 performance sanity review for Now and Sky Cycle query counts;
- review of generated documentation noise and temporary Phase 2 documents;
- explicit stop list for disabled/future actions in Alpha;
- one pass over navigation/accessibility/basic mobile behavior;
- a clear rollback/fallback posture if DB metadata is missing.

Can wait until after Alpha:

- detector runtime;
- AI/ranking;
- previews/media display;
- Output Detail identifier-specific wiring;
- Library indexing/search;
- Observatory readiness;
- mutative safe actions;
- full Sky Cycle reconstruction;
- source lineage between individual outputs and source frames.

Decision: not yet pull-to-Raspberry Alpha, but close enough to start Release Candidate preparation.

## 4. Detector Decision

Do not build the detector before the Raspberry pull.

Detector value is high:

- it would make Highlights substantially more meaningful;
- it would help answer "what happened?";
- it would provide the first real Moment candidates;
- it would validate the attention-first product model.

Detector risk is also high:

- it may require media access or image-derived features;
- it can become CPU-heavy on RPi5;
- it can blur the boundary between metadata-only Product UI and analysis pipeline;
- it can introduce false confidence if the first detector is weak;
- it can pull the project toward ranking/AI before the system is operationally stable.

The detector should be designed before implementation, but not implemented before cleanup.

Recommended detector posture:

- do a Detector Discovery/Design mission after Release Candidate cleanup audit;
- treat detector output as a backend-owned domain object, not UI logic;
- require bounded jobs, cached/persisted results, and no request-path media scanning;
- require explainability metadata before anything appears in Highlights;
- keep detector off the request path on RPi5.

Decision: detector after cleanup audit, before public Alpha expansion, but not before the first Raspberry readiness pass.

## 5. Cleanup Decision

Do cleanup before detector.

Reason:

- Phase 2 produced many documents, adapters, tests, and Product UI surfaces quickly.
- The safety model is strong, but the codebase now needs consolidation before adding analysis complexity.
- Detector work will increase architectural pressure; starting it on a cluttered surface raises risk.
- Raspberry pull should validate a controlled product, not a moving implementation target.

Cleanup should not mean deleting Classic or doing broad refactors.

Cleanup before detector should focus on:

- Release Candidate audit of touched Product UI files;
- route/template inventory sanity;
- duplicate or temporary documentation classification;
- grep-based safety checks made repeatable;
- Alpha stop list;
- RPi5 query-count and fallback review;
- confirming no Phase 2 adapter exposes forbidden fields;
- making sure Product UI surfaces remain read-only and explainable.

What should not be cleaned up yet:

- Classic routes;
- legacy templates;
- migration-heavy areas;
- storage/media helpers;
- anything that changes runtime behavior outside Product UI.

Decision: cleanup first, detector second.

## 6. Raspberry Pull Checklist

Minimum checklist before Raspberry pull:

- Repository clean.
- All Product UI tests pass.
- `tools/hybrid_ui_inventory.py` passes and report is reviewed.
- `py_compile` passes for `views.py`, `product_view_models.py`, tests, and tooling.
- JSON ownership maps validate.
- Grep confirms no Product UI request-path filesystem/media/preview/fetch/AJAX mutations.
- Now renders with all providers falling back safely when data is absent.
- Sky Cycle renders when no image metadata exists.
- Highlights renders when no candidate metadata exists.
- No Product UI page requires media files or RAW/FITS to exist.
- No Product UI page performs detector/AI/ranking work in request path.
- Bounded query count is documented for Now and Sky Cycle.
- Alpha known limitations are documented in one concise release note.
- Disabled/future actions are clearly non-mutative.
- Product Architecture freeze remains active.

Pull should not happen until this checklist has been reviewed as a specific Raspberry readiness mission.

## 7. Next Mission Recommendation

Recommended next mission: Release Candidate cleanup audit.

Why this, not another DATA:

- DATA001-DATA006 already provide enough real product value to test the architecture.
- Additional DATA would increase complexity before validating RPi5 behavior.
- Detector is strategically important but too risky before cleanup.
- UX polish is useful, but less important than proving the current data integrations are clean, bounded, and deployable.
- Raspberry readiness audit is valuable, but it should come after cleanup identifies what must be checked.

The next mission should produce:

- a Release Candidate cleanup audit document;
- a list of must-fix items before Raspberry pull;
- a list of safe-to-defer items;
- confirmation that no cleanup should change Product Architecture;
- recommendation on whether the next step is cleanup implementation or Raspberry readiness audit.

Suggested mission title:

`Phase 2 — Release Candidate Cleanup Audit before Raspberry Pull`

Suggested objective:

Audit Product UI v1 plus DATA001-DATA006 for Alpha readiness, without adding features or data, and identify the minimal cleanup required before the first Raspberry pull.

## Final Decision

Product UI after DATA006 is close to internal Alpha, but the correct next move is not more data and not detector implementation.

The product has enough real metadata to be meaningful. Now the project needs a Release Candidate cleanup audit to protect the quality bar before testing on Raspberry Pi.
