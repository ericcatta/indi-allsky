# Hybrid Product UI v1 Surface Inventory

## Purpose

This inventory consolidates the Product UI v1 skeleton after the first complete
set of read-only product surfaces.

It records what exists, what is real, what is static/fake, and where each
surface sits in the frozen Product Architecture:

Now -> Highlights -> Moment -> Output -> Sky Cycle -> Library -> Observatory -> Settings -> Developer / Engine Room

No surface listed here exposes mutations, media generation, filesystem access,
raw source reads, or real safe actions.

## Surface Inventory

| Surface | Route | Template | Builder | Validation | Ownership key | Review doc | Score | Real data | Fake/static | Main links | Safety boundary |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Now v1 | `/modern-admin/now` | `modern_admin/now.html` | `build_now_view()` | `validate_now_view_payload()` | `now_product_prototype` | `HYBRID_NOW_V1_CONSOLIDATION_REVIEW.md` | 8.2/10 final | Bounded latest frame metadata with fallback; current day/night phase from existing context | Briefing, moments, outputs, source confidence, health, attention items | Out: Highlights, Sky Cycle, Observatory, legacy Modern dashboard/settings. In: most product surfaces link back to Now | Read-only. No preview URL, actions, filesystem, RAW/FITS read, media generation, or unbounded query. |
| Highlights v1 | `/modern-admin/highlights` | `modern_admin/highlights.html` | `build_highlights_view()` | `validate_highlights_payload()` | `highlights_product_prototype` | `HYBRID_HIGHLIGHTS_V1_REVIEW.md`, `HYBRID_HIGHLIGHTS_V1_CRITIQUE.md` | 7.0/10 initial; 5.8/10 critique | None | Highlight summary, items, source trust, review queue, selection policy | Out: Now, Moment Detail, Sky Cycle, Observatory, Settings. In: Now, Moment, Output, Library, Observatory | Read-only. No detector, DB, filesystem, media read, favorite/ignore/archive, or actions. |
| Moment Detail v1 | `/modern-admin/moment` | `modern_admin/moment_detail.html` | `build_moment_detail_view()` | `validate_moment_detail_payload()` | `moment_detail_product_prototype` | `HYBRID_MOMENT_DETAIL_V1_REVIEW.md` | 7.0/10 initial | None | Moment summary, evidence, source trust, related outputs, Sky Cycle context, Observatory context | Out: Highlights, Output Detail, Sky Cycle, Now, Observatory. In: Highlights | Read-only. No detector, source read, DB, preview, media, or actions. |
| Output Detail v1 | `/modern-admin/output` | `modern_admin/output_detail.html` | `build_output_detail_view()` | `validate_output_detail_payload()` | `output_detail_product_prototype` | `HYBRID_OUTPUT_DETAIL_V1_REVIEW.md` | 7.1/10 initial | None | Output summary, disabled preview, recipe, source lineage, related Moments, Sky Cycle context, review readiness | Out: Moment Detail, Sky Cycle, Library, Highlights, Now. In: Moment Detail, Library | Read-only. `safe_preview_url` remains null. No media read, rendering, export, sharing, or actions. |
| Sky Cycle Report v1 | `/modern-admin/sky-cycle` | `modern_admin/sky_cycle.html` | `build_sky_cycle_report_view()` | `validate_sky_cycle_report_payload()` | `sky_cycle_report_prototype` | `HYBRID_SKY_CYCLE_V1_CONSOLIDATION_REVIEW.md` | 7.8/10 final | None | Cycle summary, phase timeline, moments, outputs, source confidence, health, attention items | Out: Now, Highlights, Moment Detail, Output Detail, Library, Observatory. In: Now, Highlights, Moment Detail, Output Detail, Library | Read-only. No phase engine, astronomy calculation, detector, DB, source read, media generation, or actions. |
| Library v1 | `/modern-admin/library` | `modern_admin/library.html` | `build_library_view()` | `validate_library_payload()` | `library_product_prototype` | `HYBRID_LIBRARY_V1_REVIEW.md` | 7.0/10 initial | None | Library summary, collections, search summary, filters, recent items, memory model | Out: Output Detail, Sky Cycle, Observatory, Highlights, Now. In: Output Detail, Observatory, Sky Cycle | Read-only. No search, indexing, DB query, filesystem scan, media read, preview, or actions. |
| Observatory v1 | `/modern-admin/observatory` | `modern_admin/observatory.html` | `build_observatory_view()` | `validate_observatory_payload()` | `observatory_product_prototype` | `HYBRID_OBSERVATORY_V1_REVIEW.md` | 7.2/10 initial | None | Observatory readiness, camera, capture, source preservation, storage, generation, integrations, attention items | Out: Library, Now, Highlights, Settings. In: Now, Highlights, Moment Detail, Sky Cycle, Library | Read-only. No live checks, DB, filesystem, camera probe, network call, media read, polling, or actions. |

## Cross-Surface Status

- All v1 surfaces are backend-owned view-model prototypes.
- All payloads are JSON-safe and validated before template rendering.
- All templates are server-rendered and read-only.
- Now is the only surface with bounded runtime data.
- All other surfaces remain fake/static by design.
- Product UI v1 is complete as a skeleton, not as a real-data product.

## Link Gap Status

- Sky Cycle now links directly to Highlights, Moment Detail, Output Detail,
  Library, Now, Observatory, and Settings index.
- Library now links directly to Observatory as well as Output Detail, Sky Cycle,
  Highlights, and Now.
- Observatory already linked to Now and Library.
- Remaining navigation work is refinement, not a known v1 skeleton gap.
