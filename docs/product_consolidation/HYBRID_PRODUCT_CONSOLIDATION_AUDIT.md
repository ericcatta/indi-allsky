# Hybrid Product Consolidation Audit

## Executive Summary

Hybrid AllSky has moved beyond a Classic-to-Modern port. The repository now contains a distinct product direction built around:

- Product UI and Hybrid shell;
- Product Domain and backend-owned view models;
- Scientific Source Layer;
- metadata and analytics foundations;
- environmental awareness;
- event and detector foundations;
- meteor foundation;
- DATA001-DATA006 real bounded metadata integrations.

The next risk is not missing functionality. The next risk is unmanaged complexity: duplicated surfaces, mixed Classic/Modern ownership, settings sprawl, operational pages that still bridge Classic behavior, and unclear boundaries between Product, Advanced, Developer, and Legacy fallback.

This audit is documentation-only. It does not remove Classic, change routes, change settings keys, alter runtime behavior, add detector logic, add AI, introduce new algorithms, or redesign UI.

### Current Verdict

Hybrid is ready for disciplined consolidation planning, not deletion.

The safest next consolidation work is:

1. tighten ownership maps and route classifications;
2. define the settings architecture as Basic / Advanced / Developer by product domain;
3. document which Modern pages are primary Product surfaces, operational surfaces, Developer surfaces, or legacy fallback wrappers;
4. consolidate concepts before consolidating code;
5. preserve Classic/public/external APIs until runtime consumers are known.

### Key Evidence

- `tools/hybrid_ui_inventory.py` reports 240 routes, 120 templates, 24 JS files, 10 CSS files, 99 mapped features, 45 protected features, 9 wrapper features, and 28 shared/public/external features.
- Product UI v1 routes are active and backed by `indi_allsky/product_view_models.py`.
- DATA001-DATA006 have already established the safe pattern: metadata-only, bounded, allowlisted, fallback-safe.
- `tools/hybrid_settings_ownership_map.json` has 39 settings groups, 33 high-risk groups, 30 `do_not_move_yet` groups, 13 dedicated preview groups, and 13 final read-only groups.
- `RELEASE_CANDIDATE_CLEANUP_AUDIT.md` found no route/template/Product builder safe to delete before Alpha.
- `PERFORMANCE_AUDIT_LEGACY_VS_PRODUCT.md` shows Product pages are faster because they avoid broad Classic context, filesystem/media access, and unbounded work.
- `docs/product_consolidation/HYBRID_ROUTE_ROLE_MATRIX.md` is the current route-role reference for `/modern-admin/*` Product, Advanced, Developer, wrapper, and dynamic compatibility surfaces.
- `docs/product_consolidation/HYBRID_SETTINGS_CONTRACT_REVIEW.md` is the current settings contract reference for Basic, Advanced, Developer, Classic fallback, and hidden/internal settings groups.

## Audit Rules Used

Every recommendation below includes:

- motivation;
- benefits;
- risks;
- impact;
- dependencies;
- priority: P0 / P1 / P2;
- verification method.

Classification labels:

- **Primary Product**: belongs in the main Hybrid product journey.
- **Operational**: useful operator page, not the main product story.
- **Advanced**: user-facing but deeper control/inspection.
- **Developer**: diagnostic, raw, dangerous, low-frequency, or internals-heavy.
- **Legacy Required**: Classic/shared behavior still needed.
- **Legacy Fallback Candidate**: keep until a safe native replacement exists.
- **Unknown / Needs Evidence**: do not remove or move without more runtime proof.

## Current Product Surface Map

### Primary Product Surfaces

| Surface | Route | Owner | Product value | Duplicates | Recommended role | Change risk |
| --- | --- | --- | --- | --- | --- | --- |
| Now | `/modern-admin/now` | Product UI / Product Domain | Home product console; shows current sky/capture/latest frame/latest output/source trust/highlights/sky cycle context. | Partially overlaps legacy dashboard but with product-first model. | Primary Product. | Medium: central surface; changes must preserve DATA001-DATA006. |
| Highlights | `/modern-admin/highlights` | Product UI / Product Intelligence layer | Curated attention object entry point; connects user to what deserves review. | Conceptually overlaps Moments/Events/Gallery if not kept distinct. | Primary Product. | Medium-high: product model still young. |
| Moment Detail | `/modern-admin/moment` | Product UI / Product Domain | Explains what happened and why it was selected. | Overlaps future event detail/detector detail. | Primary Product, currently static/fake. | Medium: future data needs identifiers. |
| Output Detail | `/modern-admin/output` | Product UI / Product Domain | Explains generated result, recipe/look, source lineage, share readiness. | Overlaps Media/Gallery if it becomes visual browsing. | Primary Product, currently static/fake. | Medium: route is not identifier-specific. |
| Sky Cycle | `/modern-admin/sky-cycle` | Product UI / Product Domain | Gives day/night/cycle context and summary. | Overlaps old dashboard and analytics. | Primary Product / Context. | Medium: DATA006 is bounded but not a full report. |
| Library | `/modern-admin/library` | Product UI / Product Domain | Long-term memory model for Highlights/Moments/Outputs/Sky Cycles/Favorites. | Overlaps Gallery if reduced to media browsing. | Primary Product, currently static/fake. | Low-medium: no real search yet. |
| Observatory | `/modern-admin/observatory` | Product UI / Product Domain | Readiness/health summary without becoming Developer. | Overlaps System/Storage/Cameras if not kept high-level. | Primary Product health entry. | Medium: real health data not fully connected. |

Recommendation P0: Freeze these as the product spine.

- Motivation: This spine is the clearest departure from Classic page parity.
- Benefits: future work has a stable mental model.
- Risks: premature changes to the spine would churn documentation, navigation, and contracts.
- Impact: high product clarity.
- Dependencies: `HYBRID_PRODUCT_ARCHITECTURE_V1.md`, Product UI templates, `product_view_models.py`.
- Verification: route inventory continues to list these seven routes; tests in `testing/product_view_models_test.py` continue to pass.

### Operational Modern Surfaces

| Surface family | Routes | Product value | Duplicates | Recommended role | Change risk |
| --- | --- | --- | --- | --- | --- |
| Cameras | `/modern-admin/cameras`, `/modern-admin/cameras/*` | Multi-camera and profile operational control. | Classic `/cameras`, settings camera/profile pages. | Advanced / Operational primary. | High: camera/profile ownership is protected. |
| Media/Gallery/Images | `/modern-admin/media/*`, `/modern-admin/fits*` | Review generated/source media metadata. | Classic image/video/gallery/FITS viewers. | Advanced / Operational. | High: media paths, URLs, previews, filesystem risk. |
| Storage/Uploads | `/modern-admin/storage`, `/modern-admin/storage/*`, `/modern-admin/uploads*` | Operational status for disk and transfer. | Classic storage/system/upload surfaces. | Advanced / Operational. | Medium-high: may touch filesystem or external providers. |
| Observatory tools | `/modern-admin/observatory/*` | SQM, charts, sensor panel, astropanel, virtualsky, keograms. | Classic charts/sensor/virtualsky pages. | Advanced Observatory. | Medium-high: mixed runtime/legacy data sources. |
| System/Tasks/Users/Logs | `/modern-admin/system*`, `/modern-admin/tasks*`, `/modern-admin/users*` | Diagnostics and admin support. | Classic system/log/user/task pages. | Developer / Operational. | High: security/log/system behavior. |
| Notifications/Config history/restore | `/modern-admin/notifications*`, `/modern-admin/config-*` | Audit and safety visibility. | Classic notifications/config routes. | Developer / Advanced. | High: restore/download/mutations are sensitive. |
| Safe-control wrappers | `/modern-admin/tools/*`, `/modern-admin/system/config`, `/modern-admin/system/network`, `/modern-admin/system/gpio-control`, `/modern-admin/storage/drives` | Gives Hybrid access to useful tools while keeping legacy behavior contained. | Classic tool pages. | Developer / Legacy fallback wrapper. | High: actions and OS/hardware mutations. |

Recommendation P1: Keep operational surfaces, but label them by role.

- Motivation: they are useful but not all are Product-first.
- Benefits: user navigation and future cleanup can distinguish Product from Operations and Developer.
- Risks: hiding too aggressively could strand operators who rely on Classic workflows.
- Impact: medium-high maintainability and UX clarity.
- Dependencies: Hybrid shell navigation, ownership map, current templates.
- Verification: manual route walk; `tools/hybrid_ui_inventory.py` shows no new orphan templates/routes.

### Classic, Public, and External Surfaces

| Surface family | Examples | Role | Change risk |
| --- | --- | --- | --- |
| Classic UI | `/config`, `/imageviewer`, `/gallery`, `/fitsimageviewer`, `/generate`, `/tasks`, `/notifications`, etc. | Legacy Required / compatibility / fallback. | Critical if removed without evidence. |
| Public/latest | `/latestimage`, `/latestkeogram`, `/lateststartrail`, `/latesttimelapse`, `/images/<path>`, etc. | Public/external compatibility. | Critical: bookmarks and external consumers. |
| Shared AJAX/JS endpoints | `/ajax/*`, `/js/*` | Shared API, Classic support, dynamic pages. | High: static analysis cannot prove all consumers. |
| Sync API | `/sync/v1/*` | External API. | Critical: contract surface. |
| Action API | `/action/*` | External control API. | Critical: automation surface. |
| Auth/OAuth | `/login`, `/logout`, YouTube OAuth routes. | Auth and external credential flow. | Critical. |

Recommendation P0: Do not remove or rename any Classic/public/external route before Alpha.

- Motivation: static analysis cannot identify every external consumer.
- Benefits: protects installed systems.
- Risks: repository remains larger and more complex.
- Impact: high safety, medium complexity.
- Dependencies: runtime usage telemetry or manual verification.
- Verification: route inventory diffs and Raspberry/manual smoke tests.

## Classic Dependency Map

### Native Modern

| Area | Evidence | Classification | Notes |
| --- | --- | --- | --- |
| Product UI builders/validators | `indi_allsky/product_view_models.py` has `build_now_view`, `build_highlights_view`, `build_sky_cycle_report_view`, `build_moment_detail_view`, `build_output_detail_view`, `build_library_view`, `build_observatory_view` plus validators. | Native Modern | Keep framework-free. |
| DATA repositories/adapters | `LatestFrameImageTableRepository`, `LatestGeneratedOutputRepository`, `CurrentCaptureStatusRepository`, `SourceTrustRepository`, `HighlightsMetadataRepository`, `SkyCycleSummaryRepository`. | Native Modern | Product data integration foundation. |
| Hybrid shell/design system | `modern_admin/base.html`, `hybrid-product-ui.css`, design system freeze docs. | Native Modern | Do not redesign; future pages adapt to it. |
| Ownership maps/inventory tools | `tools/hybrid_ui_ownership_map.json`, `tools/hybrid_ui_inventory.py`, `tools/hybrid_settings_ownership_map.json`, `tools/hybrid_settings_inventory.py`. | Native Modern governance | Strengthen, do not delete. |

### Wrapped Legacy

| Area | Evidence | Classification | Notes |
| --- | --- | --- | --- |
| Modern operational pages inheriting Classic views | Many classes use `ModernAdminContextMixin` with Classic base classes such as `ImageLoopImgView`, `ChartView`, `SensorPanelView`, `VirtualSkyView`, `ImageLagView`, `RollingAduView`, `LogView`. | Wrapped Legacy | Useful bridge; high cleanup caution. |
| Safe controls | `ModernAdminSafeControlsMixin` wraps Config, Network, Drive Manager, GPIO, Focus, Generator, Camera Simulator, Image Processing. | Wrapped Legacy / Legacy Fallback Candidate | Keep until safe-action/native contracts exist. |
| Media list/details | Modern media routes often reuse existing media models and public URL helpers. | Wrapped Legacy / Advanced | Avoid path/URL leaks and filesystem reads. |
| Settings full/capture/cameras | Modern settings pages still expose/read Classic/global config concepts. | Wrapped Legacy / Redesign | Need product-domain grouping before implementation. |

### Legacy Required

| Area | Evidence | Classification | Notes |
| --- | --- | --- | --- |
| Classic UI routes | Inventory lists many active Classic routes and zero template orphan candidates. | Legacy Required | Do not remove. |
| Public/latest routes | `/latest*`, `/images/<path>`, public image/video routes. | Legacy Required / Public | External compatibility surface. |
| Sync API and Action API | `syncapi_views.py`, `actionapi_views.py`. | Legacy Required / External API | Version/contract surface. |
| OAuth/auth routes | auth and YouTube flows. | Legacy Required | Security/credential behavior. |

### Legacy Fallback Candidates

| Area | Why fallback | Future native requirement |
| --- | --- | --- |
| Config restore/import/export | Useful but dangerous. | Diff/preview/rollback safe action. |
| Media generation tools | Mutative and may trigger heavy work. | Queue-backed Product Output actions. |
| Focus/GPIO/Network/Drive tools | Hardware/OS mutation. | Explicit safe-action policy and audit log. |
| FITS conversion/download | File/media access. | Source trust/download policy. |
| YouTube/OAuth upload flows | External credential mutation. | Integration settings and safe credential workflow. |

### Legacy Dead / Possibly Unused

No route, template, Product builder, or Classic module is proven dead by this audit.

Possible static asset candidates from prior cleanup audit remain **UNKNOWN** until runtime/dynamic loading is verified:

- unminified or unused-looking DataTables assets;
- PhotoSwipe ESM variants;
- VirtualSky extra/demo/test files;
- possible CSS counterparts.

Recommendation P2: Do a static asset verification mission after Alpha.

- Motivation: reduce shipped noise only with evidence.
- Benefits: smaller frontend footprint.
- Risks: dynamic imports or old pages may break.
- Impact: low-medium.
- Dependencies: browser/manual checks for Classic and Hybrid media pages.
- Verification: asset request logs or browser network tab on Gallery, FITS, VirtualSky, Classic viewers.

## Settings Architecture Findings

The settings system is the largest consolidation target. It has the highest product value and the highest risk.

Evidence:

- `tools/hybrid_settings_ownership_map.json` has 39 groups.
- 33 groups are high risk.
- 30 groups are marked `do_not_move_yet`.
- 13 groups have dedicated preview pages.
- 13 groups are final read-only groups.
- Existing Classic `/config` remains the complete fallback.

### Proposed Basic / Advanced / Developer Organization

#### Basic

| Domain | User-facing settings | Technical settings to hide | Notes |
| --- | --- | --- | --- |
| Camera | Camera label, active camera/profile, connection summary. | driver-specific internals, low-level INDI/libcamera options. | Preserve multicamera/profile separation. |
| Capture | capture enabled/paused, day/night capture intent, exposure/gain basics. | raw timing internals, service controls, low-level thresholds. | Should answer "is it capturing correctly?". |
| Source Preservation | RAW/FITS/source retention status and enablement. | raw paths, storage internals, sync ids. | Product language: Source preserved, not config key names. |
| Storage | retention, disk risk, source/output retention summaries. | filesystem paths unless Advanced/Developer. | Avoid scans in UI request path. |
| Notifications | important alerts and delivery status. | provider credentials, raw templates. | User-facing warnings, not full integration config. |

#### Advanced

| Domain | User-facing settings | Technical settings to hide | Notes |
| --- | --- | --- | --- |
| Camera Profiles | profile-specific exposure/gain/AWB, sensor metadata. | DB internals, migration flags. | Protected Modern work. |
| Image Processing | stretch/look-like rendering knobs, calibration options, masks. | algorithm class names, raw OpenCV internals. | Do not create full editor. |
| Scientific Metadata | FITS/source metadata, metadata generation, quality fields. | filesystem helper paths, raw JSON internals. | Source truth must remain backend-owned. |
| Environmental | SQM, sensors, astropanel, smoke/sky quality context. | provider internals and polling controls. | Needs ownership clarification. |
| Events | event candidate/timeline settings, review policy. | detector internals. | Event foundation is protected but not detector product yet. |
| Detection / Meteor Foundation | detector readiness, offline validation status. | raw thresholds, legacy Hough toggles, RMS/AI toggles. | Developer until real detector design exists. |
| Generated Outputs | timelapse, keogram, startrail, panorama product settings. | ffmpeg command details, output paths, raw queue internals. | Future Output actions should be safe-action based. |
| Integrations | upload providers, MQTT, YouTube status. | credentials, cert bypass, endpoint secrets. | Credentials are Developer/secured. |

#### Developer

| Domain | Keep here | Why |
| --- | --- | --- |
| Legacy / Full Settings | raw config editor, unmapped settings, compatibility flags. | recovery and parity. |
| System | network, GPIO, drives, OS-level controls. | mutation/hardware risk. |
| Users/Auth | users, admin flags, auth flows. | security risk. |
| Logs/Tasks | raw logs, task internals. | diagnostics. |
| Detector/Meteor Legacy | `DETECT_METEORS`, legacy detector toggles, Hough/line settings. | do not expose as product before detector design. |
| Config Restore/Import/Export | restore/download/import. | rollback and data-loss risk. |

### Settings Groups Requiring Caution

| Group | Finding | Recommendation |
| --- | --- | --- |
| Camera/profile/exposure/gain/AWB | Protected Modern work and high risk. | P0: do not flatten into global settings. |
| Source/FITS/scientific metadata | Critical for non-destructive source model. | P0: keep source truth backend-owned. |
| Media product generation | Useful but action-heavy. | P1: status/settings can be Advanced; generation actions need safe-action design. |
| Upload/OAuth | Credential/external behavior. | P1: keep status separate from credential mutation. |
| GPS/sensors/environmental | Some ownership still uncertain. | P1: audit provider ownership before UI changes. |
| Legacy detector | Exists as toggles, not product-ready detector. | P0: keep Developer/Legacy. |

Recommendation P1: Create a Settings Product Contract before touching active settings UI.

- Motivation: settings are high-risk and duplicated.
- Benefits: reduces user confusion and prevents wrong owner writes.
- Risks: takes time before visible improvement.
- Impact: high maintainability and safety.
- Dependencies: `tools/hybrid_settings_ownership_map.json`, Classic config schema, Modern settings pages.
- Status: completed in `docs/product_consolidation/HYBRID_SETTINGS_CONTRACT_REVIEW.md`.
- Verification: generated settings inventory, manual review of all 39 groups, no runtime changes.

## Duplication Findings

### Duplicate Concepts

| Concept | Duplicate surfaces | Risk | Recommended owner |
| --- | --- | --- | --- |
| Current status / dashboard | Now, old Modern dashboard, Classic public/latest/status pages. | Users may not know where "truth" lives. | Now/Product Domain for product status; operational dashboard becomes Advanced. |
| Latest image/frame | Now latest frames, Gallery, `/latest*`, Classic viewers, media pages. | Path/URL/preview leakage risk. | Product summary uses bounded metadata and safe public URL only; media pages own browsing. |
| Generated outputs | Now latest output, Output Detail, Media pages, Classic generation pages. | Output could collapse into Gallery. | Output domain owns explanation/lineage; Media owns browsing/listing. |
| Source trust / FITS / RAW | Now source trust, FITS pages, RAW pages, settings FITS/source, scientific source modules. | Source truth could split across UI and filesystem helpers. | Scientific Source Layer backend owns truth; UI gets sanitized summaries. |
| Events / Highlights / Moments | Highlights, Moment Detail, event foundation, detector/meteor foundation. | Highlights could become event list or AI ranking prematurely. | Highlights = attention layer; Moment/Event = domain evidence. |
| Observatory health | Observatory, System, Storage, Cameras, Uploads, environmental pages. | Observatory could become admin dashboard. | Observatory owns readiness summary; System/Storage/Cameras own details. |
| Settings | Classic `/config`, Modern settings inventory, Basic/Advanced/Developer previews, dedicated settings pages, full settings. | Too many entry points and raw key exposure. | Settings Product Contract and ownership map. |
| Actions | Classic mutative routes, safe controls, safe-action dry-run, external Action API. | Mutations may bypass safe-action model. | Safe Action service for Product; Classic remains fallback until replaced. |

### Duplicate Code / Endpoint Patterns

| Pattern | Evidence | Recommendation |
| --- | --- | --- |
| Modern pages wrapping Classic views | `ModernAdminContextMixin` + Classic base classes. | Keep now; migrate only when product contract exists. |
| Multiple media list/detail routes | Images, videos, keograms, startrails, panoramas, raw, FITS. | Consider future shared metadata list repository; do not merge before Alpha. |
| Shared AJAX endpoints | `/ajax/*` used by Classic and some Modern pages. | Treat as shared API; no cleanup without consumer evidence. |
| Public latest routes and Product latest summaries | Both are useful but serve different users. | Product uses summaries; public routes remain compatibility. |

Recommendation P1: Consolidate concepts in docs and contracts before code.

- Motivation: code duplication often reflects real compatibility needs.
- Benefits: avoids deleting useful paths.
- Risks: slower cleanup.
- Impact: high correctness.
- Dependencies: domain contracts and route inventory.
- Verification: every proposed code consolidation maps to a documented domain owner and rollback path.

## Ownership Findings

### Intended Domain Owners

| Domain | Frontend owner | Backend/service owner | Config/settings owner | Classic fallback |
| --- | --- | --- | --- | --- |
| Now | Product UI shell/template | Product Domain view model + bounded repositories | none directly | old dashboard/public latest as reference only |
| Highlights | Product UI | Product Intelligence / Highlights metadata repository | event/highlight policy future | none as product; event foundation is evidence |
| Moment/Event | Product UI | Event/Moment domain future | detector/event settings Advanced/Developer | Classic detector toggles only fallback |
| Output | Product UI | Output domain / generated output repository / recipe future | media product settings | Classic media generation |
| Sky Cycle | Product UI | Sky Cycle repository / phase context | capture/day-night settings | analytics/dashboard context |
| Library | Product UI | Library/search/favorites future | tags/favorites future | Gallery as browsing fallback |
| Observatory | Product UI | Observatory health/readiness service future | sensors/storage/system settings | System/Storage/Cameras pages |
| Camera/Profile | Operational UI + settings | Camera/profile services | profile-first settings map | Classic camera/config |
| Scientific Source | Source UI summaries | Scientific Source Layer | FITS/source settings | FITS/RAW viewers |
| Media Browsing | Operational UI | Media metadata repositories | output/storage settings | Classic viewers |
| Actions | Product/operational UI only via safe-action metadata | Safe Action service | action policy | Classic mutative routes |
| Developer/System | Developer UI | system/log/task/auth services | Developer settings | Classic admin tools |

### Unclear or Split Ownership

| Area | Problem | Recommendation |
| --- | --- | --- |
| Settings source of truth | Classic config, Modern preview pages, ownership maps, full settings all coexist. | P1: define settings contract and mark each group active/read-only/fallback. |
| Media output metadata | Product output summary and media pages both read generated output tables. | P1: shared metadata-only adapter pattern for all output types. |
| Environmental awareness | Observational context appears in analytics, observatory, sensor pages, processing metadata. | P1: create Environmental Summary contract before adding more UI. |
| Event foundation vs Highlights | Highlights are attention objects; event foundations are evidence. | P0: do not let Highlights become detector UI. |
| Safe actions vs Classic actions | Safe-action metadata exists, but Classic mutative routes remain. | P1: action registry/audit before replacing Classic actions. |
| Modern shell naming | Some internals still use Modern naming, product uses Hybrid. | P2: code naming cleanup only after Alpha; visible language already converged. |

## Safe Cleanup Candidates

These are candidates only. Do not execute in this audit.

| Candidate | Classification | Motivation | Benefits | Risks | Impact | Dependencies | Priority | Verification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Move process docs into `docs/archive/...` | Safe after Alpha | Root contains many historical docs. | Easier repo navigation. | Broken doc links. | Medium. | Link audit. | P2 | `rg` doc filenames before move. |
| Tighten ownership map undeclared/mismatch entries | Safe docs/tooling | Inventory reports ownership mismatches and undeclared items. | Better future audits. | Misclassification if rushed. | Medium-high. | `HYBRID_UI_INVENTORY_REPORT.md`. | P1 | regenerate inventory and compare diff. |
| Add settings contract document | Safe docs | Settings map exists but active contract is not formalized. | Reduces risky settings work. | None if docs-only. | High. | settings ownership map. | P1 | review all 39 groups. |
| Document Operational/Advanced/Developer route roles | Safe docs | Hybrid shell has many routes with different intent. | Clearer navigation and cleanup. | None if docs-only. | Medium. | route inventory. | P1 | route map review. |
| Remove local cache/bytecode if present | Safe local cleanup | Prior audit found only untracked bytecode/cache safe to delete. | Clean tree/package. | Low if untracked. | Low. | status scan. | P2 | `git status`, tests. |
| Clarify old Modern dashboard role | Safe docs | `/modern-admin` redirects/old dashboard role can confuse. | Product clarity. | Navigation assumptions. | Medium. | shell/route docs. | P1 | manual route check. |
| Consolidate duplicate documentation summaries | Safe docs after Alpha | Many step reviews duplicate current state. | Less cognitive load. | Loss of decision history if deleted. | Medium. | archive plan. | P2 | preserve archive index. |

## High-Risk Cleanup Candidates

Do not start these without a dedicated mission.

| Candidate | Why valuable | Risks | Dependencies | Priority | Verification |
| --- | --- | --- | --- | --- | --- |
| Remove Classic routes/templates | Smaller codebase. | Break installed workflows, bookmarks, public endpoints, fallback actions. | Alpha telemetry/manual route audit. | P0 avoid. | Full Classic smoke test and rollback plan. |
| Rename or remove settings keys | Cleaner product language. | Break runtime config, migrations, user configs. | Settings contract, migrations, compatibility plan. | P0 avoid. | Config migration tests and backup/restore. |
| Merge media viewers and output detail | Better conceptual clarity. | Path/URL/preview leaks, route breakage, user workflow loss. | Output identifiers, media policy. | P1 later. | media route tests and manual browser checks. |
| Replace Classic mutative tools with safe actions | Better safety and product consistency. | Hardware/system/data-loss regressions. | safe-action registry, audit, dry-run, rollback. | P1 later. | action-specific tests on Raspberry. |
| Consolidate shared AJAX endpoints | Cleaner API surface. | Dynamic consumers, Classic breakage. | JS consumer map and browser network audit. | P2 later. | request logs and route compatibility tests. |
| Change background worker behavior | Performance/architecture clarity. | Capture/output regressions. | worker-specific tests. | P0 avoid. | Raspberry soak test. |
| Add real detector/meteor algorithms | Product value. | False positives, performance, source trust issues. | detector discovery/design after consolidation. | P1 later. | offline FITS/source test corpus. |
| Reorganize settings UI live behavior | Better UX. | Wrong owner writes and config corruption. | settings contract and read-only review. | P1 later. | config diff tests, profile/camera tests. |

## Recommended Consolidation Roadmap

### Phase A: Governance Tightening

1. Update UI ownership map classifications.
2. Create a Settings Product Contract from the 39 settings groups.
3. Create a route role matrix: Product / Advanced / Developer / Fallback / Public / External.
4. Define doc archive policy, but do not archive until Alpha unless root noise becomes blocking.

### Phase B: Product Boundary Hardening

1. Keep Product builders framework-free.
2. Ensure every real-data integration has discovery/audit/adapter/integration/review records.
3. Add no new DATA integrations until ownership and settings maps are reconciled.
4. Keep Detector/Meteor foundation in design/discovery mode only.

### Phase C: Operational Surface Stabilization

1. Mark operational pages by role in docs and navigation language.
2. Avoid converting wrapped legacy pages until native contracts exist.
3. Audit Media, System, Logs, Storage, and Tools one at a time if performance or UX demands it.

### Phase D: Post-Alpha Cleanup

1. Archive historical process docs.
2. Verify static assets with runtime evidence.
3. Consider Classic fallback reduction only after Product replacements are safe and tested.
4. Start detector discovery/design, not implementation, once source trust and offline test corpus are ready.

## Proposed Micro-step Sequence

### Micro-step 1: Route Role Matrix

- Motivation: clarify Product vs Operations vs Developer vs Fallback before changing anything.
- Benefits: reduces accidental UI/route churn.
- Risks: low; docs-only.
- Impact: high planning clarity.
- Dependencies: `HYBRID_UI_INVENTORY_REPORT.md`, `tools/hybrid_ui_ownership_map.json`.
- Priority: P0.
- Status: completed in `docs/product_consolidation/HYBRID_ROUTE_ROLE_MATRIX.md`.
- Verification: route families from `HYBRID_UI_INVENTORY_REPORT.md` are classified by product role.

### Micro-step 2: Settings Contract Review

- Motivation: settings are the biggest complexity and risk center.
- Benefits: protects profile-first/multicamera/source settings.
- Risks: low if docs-only.
- Impact: high.
- Dependencies: `tools/hybrid_settings_ownership_map.json`, `HYBRID_SETTINGS_INVENTORY_REPORT.md`.
- Priority: P0.
- Status: completed in `docs/product_consolidation/HYBRID_SETTINGS_CONTRACT_REVIEW.md`.
- Verification: every one of 39 settings groups has Basic/Advanced/Developer, owner, risk, and fallback classification.

### Micro-step 3: Ownership Map Correction Pass

- Motivation: inventory still reports mismatches/undeclared items.
- Benefits: better audit signal.
- Risks: medium if classifications are guessed.
- Impact: medium-high.
- Dependencies: route role matrix.
- Priority: P1.
- Verification: inventory mismatch count decreases for known intentional wrappers; no runtime changes.

### Micro-step 4: Documentation Archive Plan

- Motivation: many historical docs are useful but noisy.
- Benefits: lower cognitive load.
- Risks: broken links.
- Impact: medium.
- Dependencies: doc link audit.
- Priority: P2.
- Verification: `rg` for moved filenames; archive index created.

### Micro-step 5: Safe Action Registry Discovery

- Motivation: mutative Classic tools remain fallback.
- Benefits: prepares safe replacement without touching behavior.
- Risks: low if discovery-only.
- Impact: high future safety.
- Dependencies: route role matrix and settings contract.
- Priority: P1.
- Verification: list each mutative route/action, owner, required dry-run/audit/rollback.

### Micro-step 6: Detector Discovery/Design

- Motivation: Highlights will eventually need real detector evidence.
- Benefits: product value.
- Risks: high if implementation starts too early.
- Impact: high.
- Dependencies: source trust, offline test corpus, event contract, performance budget.
- Priority: P1 after consolidation.
- Verification: design doc only; no runtime detector code.

## Open Questions / Manual Verification Needed

1. Which Classic routes are still used by the current Raspberry installation in daily operation?
2. Which public/latest URLs are bookmarked or consumed externally?
3. Which AJAX endpoints are still used by Classic, Hybrid, or external pages?
4. Which settings groups are actually edited by users vs kept for compatibility?
5. Which source/FITS/RAW metadata fields are trustworthy enough for future source coverage?
6. Which operational pages are essential before Alpha: Media, Loop, Cameras, Storage, Logs, Settings?
7. Which safe-control wrappers are used frequently enough to deserve native Product replacements?
8. Which generated media outputs should become identifier-specific Output Detail pages first?
9. Which environmental/sensor providers are active on the Raspberry target?
10. Which detector/meteor fields are legacy compatibility only vs current foundation?

## Final Recommendation

Do not start detector work and do not delete Classic.

The next best step is a **Route Role Matrix + Settings Contract Review**. It is small, documentation-first, low-risk, and directly reduces complexity before any implementation.

The product has strong foundations. The consolidation priority is now ownership clarity, not more surfaces.
