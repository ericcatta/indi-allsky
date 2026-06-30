# Release Candidate Cleanup Audit

This audit reviews the repository after Product UI v1 and DATA001-DATA006.

It is intentionally non-destructive. No code, templates, routes, assets, runtime behavior, or Product Architecture should be changed based only on this report. Every removal candidate still requires a separate cleanup mission with verification.

## Executive Verdict

The repository is close to an internal Alpha, but it is not ready for cleanup-by-deletion.

The highest-value cleanup before a Raspberry pull is:

1. remove or ignore local bytecode/cache artifacts from release packaging;
2. archive temporary Product UI/DATA process documents into a structured docs area;
3. tighten ownership/inventory classifications;
4. verify Classic/public/external routes before considering any deletion;
5. keep Product builders, DATA adapters, Product UI templates, and Classic runtime intact.

The main risk is not dead code. The main risk is deleting dynamically used Classic/public/external behavior because static analysis cannot prove consumers.

## Audit Sources

Static inputs used:

- `HYBRID_UI_INVENTORY_REPORT.md`
- `HYBRID_PRODUCT_UI_V1_SURFACE_INVENTORY.md`
- `tools/hybrid_ui_ownership_map.json`
- repository file inventory via `rg --files`
- markdown inventory
- cache/temp file scan
- Product builder/provider definitions in `indi_allsky/product_view_models.py`
- Flask route/template inventory from `indi_allsky/flask/views.py`

Important inventory metrics:

| Area | Count |
| --- | ---: |
| Routes found | 240 |
| Templates found by inventory | 120 |
| Template files under Flask templates | 120 |
| JavaScript files found by inventory | 24 |
| CSS files found by inventory | 9 |
| JS/CSS files under Flask static | 33 |
| Routes/API without static consumers | 107 |
| Possible template orphan candidates | 0 |
| Possible JS orphan candidates | 13 |
| Possible CSS orphan candidates | 3 |
| Ownership mismatches | 71 |
| Undeclared inventory items | 272 |
| Markdown files at depth <= 2 | 83 |
| Python test files under `testing/` | 97 |
| Files under `misc/` and `examples/` | 125 |
| Local `__pycache__` / `.pyc` files found | 351 |
| Tracked `.pyc` files | 0 |

## Priority Summary

| Priority | Area | Classification | Benefit | Risk | Recommendation |
| --- | --- | --- | --- | --- | --- |
| P0 | Product UI builders/adapters/routes/templates | KEEP | Preserve Alpha behavior | High if touched | Do not clean before Raspberry pull. |
| P0 | Classic/public/external API routes | KEEP UNTIL ALPHA | Preserve compatibility | Critical if removed | No deletion until runtime usage is known. |
| P1 | `__pycache__` / `.pyc` local artifacts | SAFE TO DELETE locally | Cleaner release packaging | Low | Delete only in a cleanup mission; ensure ignored. |
| P1 | DATA discovery/audit/integration process docs | SAFE TO ARCHIVE | Reduces repo root noise | Low | Move to `docs/archive/phase2-data/` later. |
| P1 | Product design/review process docs | SAFE TO ARCHIVE | Reduces repo root noise | Low-medium | Keep canonical docs; archive process history. |
| P1 | Inventory ownership mismatches | KEEP UNTIL ALPHA | Better audit signal | Medium | Fix maps/reports, not runtime. |
| P2 | Static JS/CSS orphan candidates | UNKNOWN | Potential asset reduction | Medium-high | Verify dynamic usage first. |
| P2 | `testing/benchmark`, `testing/image`, `testing/net`, `testing/gpio`, `testing/astrometrics` | SAFE TO ARCHIVE after Alpha | Smaller dev tree | Medium | Keep for Alpha; later move to experiments. |
| P2 | `examples/DENOISE PR TEST ENVIRONMENT` | SAFE TO ARCHIVE | Removes large experimental assets | Medium | Archive after detector/denoise direction is decided. |
| P3 | Modern settings preview/final docs/pages | KEEP UNTIL ALPHA | Reference safety | Medium | Do not delete before Product UI Alpha proves replacement. |

## 1. Dead Code Audit

### Product view model builders and adapters

| Element | Classification | Reason | Benefit if removed | Risk |
| --- | --- | --- | --- | --- |
| `build_now_view()` and validation | KEEP | Active Product UI route uses it; DATA001-DATA004 are wired through it. | None | Critical. |
| `build_highlights_view()` and validation | KEEP | Active Product UI route uses it; DATA005 is wired through it. | None | Critical. |
| `build_sky_cycle_report_view()` and validation | KEEP | Active Product UI route uses it; DATA006 is wired through it. | None | Critical. |
| `build_moment_detail_view()` | KEEP | Active v1 skeleton surface; static by design. | Low | High: breaks frozen architecture. |
| `build_output_detail_view()` | KEEP | Active v1 skeleton surface; static by design. | Low | High: breaks frozen architecture. |
| `build_library_view()` | KEEP | Active v1 skeleton surface; static by design. | Low | High: breaks frozen architecture. |
| `build_observatory_view()` | KEEP | Active v1 skeleton surface; static by design. | Low | High: breaks frozen architecture. |
| `LatestFrameImageTableRepository` | KEEP | DATA001 runtime adapter. | None | Critical for Now. |
| `LatestGeneratedOutputRepository` / `GeneratedOutputDescriptor` | KEEP | DATA002 runtime adapter. | None | Critical for Now generated output metadata. |
| `CurrentCaptureStatusRepository` | KEEP | DATA003 runtime adapter. | None | Critical for Now capture status. |
| `SourceTrustRepository` / `SourceTrustDescriptor` | KEEP | DATA004 runtime adapter. | None | Critical for Now source trust. |
| `HighlightsMetadataRepository` | KEEP | DATA005 runtime adapter. | None | Critical for Highlights metadata. |
| `SkyCycleSummaryRepository` | KEEP | DATA006 runtime adapter. | None | Critical for Sky Cycle summary. |
| Static fallback repositories/helpers | KEEP | They are safety fallback paths when DB/context is absent. | Low | High: Alpha would fail less gracefully. |

Verdict: no Product builder/provider/adapter is safe to delete before Alpha.

### General Python modules

The repository contains many domain modules that may appear unused by static grep but are part of capture, upload, media generation, device support, or Classic behavior. Examples include camera backends, device drivers, file transfer providers, overlay modules, stretch modules, and media generators.

Classification: KEEP or UNKNOWN.

Reason: static analysis alone is not sufficient for runtime/import/plugin-style code. Many modules are selected dynamically by configuration.

### Local bytecode/cache

| Element | Count | Classification | Reason | Benefit | Risk |
| --- | ---: | --- | --- | --- | --- |
| `__pycache__` / `.pyc` files | 351 found, 0 tracked | SAFE TO DELETE locally | Build artifacts, not source. | Cleaner working tree/package; avoids accidental release noise. | Low if not tracked and tests can regenerate. |

Recommendation: cleanup mission may delete local bytecode/cache and confirm `.gitignore` coverage. Do not include deletion in this audit commit.

## 2. Route Audit

Route inventory found 240 routes.

### Keep categories

| Category | Classification | Reason |
| --- | --- | --- |
| Product UI v1 routes: `/modern-admin/now`, `/modern-admin/highlights`, `/modern-admin/moment`, `/modern-admin/output`, `/modern-admin/sky-cycle`, `/modern-admin/library`, `/modern-admin/observatory` | KEEP | Frozen Product Architecture and Alpha target. |
| Modern Admin operational routes | KEEP UNTIL ALPHA | Still provide system, media, storage, settings, users, tasks, logs, wrappers. |
| Modern safe-control wrappers | KEEP UNTIL ALPHA | Some are the current bridge to legacy tools; removal would reduce operator coverage. |
| Public/latest routes | KEEP | External/bookmark/API compatibility cannot be inferred statically. |
| Sync API routes | KEEP | External integration surface. |
| Action API routes | KEEP | Existing external/control surface; not part of Product UI cleanup. |
| Classic routes | KEEP UNTIL ALPHA | Still provide fallback and compatibility. |

### Candidate-only route findings

The inventory reports 107 routes/API without static consumers. These are not dead routes. They include:

- public landing/latest routes;
- `/sync/v1/*` external API;
- `/action/*` external API;
- Classic direct pages;
- Modern detail pages;
- Modern wrapper pages;
- routes commonly visited directly or via dynamic `url_for`.

Classification: UNKNOWN unless explicitly documented as active/protected. For Release Candidate, treat them as KEEP UNTIL ALPHA.

### Routes that deserve later verification

| Route family | Classification | Why verify | Do not remove before |
| --- | --- | --- | --- |
| `/modern-admin/classic/<classic_page>` | UNKNOWN | Placeholder bridge may become unnecessary once navigation is complete. | Alpha browser navigation audit. |
| `/modern-admin/tools/*` wrappers | KEEP UNTIL ALPHA | Safe-control wrappers over legacy tools may still be needed. | Safe-action replacement exists. |
| Legacy `/ajax/*` Classic endpoints | KEEP UNTIL ALPHA | Some are still shared APIs or Classic dependencies. | Classic separation plan. |
| `/youtube/*` | KEEP | OAuth/external flow; static consumers are unreliable. | Dedicated OAuth audit. |
| `/latest*`, `/view_*`, `/watch_*`, `/images/<path>` | KEEP | Public/bookmark/media compatibility. | Public route compatibility audit. |

## 3. Template Audit

Inventory found 120 templates and 0 template orphan candidates.

### Keep categories

| Template group | Classification | Reason |
| --- | --- | --- |
| Product UI v1 templates | KEEP | Active v1 skeleton and DATA integrations. |
| Modern Admin shell/templates | KEEP | Current operator surface. |
| Modern settings read-only/final pages | KEEP UNTIL ALPHA | Useful governance/reference during transition; do not delete until Product UI replacement is validated. |
| Classic templates | KEEP UNTIL ALPHA | Direct Classic routes remain registered. |
| Public templates | KEEP | Public web surface. |
| Auth/user/task/log/system templates | KEEP | Operational/admin behavior. |

### Template cleanup candidates

No template is currently SAFE TO DELETE based on static analysis.

Potential future archive/delete candidates are conceptual, not proven:

- Modern settings preview pages may become archivable after Product UI Alpha and after settings-first direction is explicitly retired.
- `modern_admin/placeholder.html` may be removable only if the classic placeholder bridge is removed.
- Some Classic templates may be removable only after Classic separation, not before.

Classification: KEEP UNTIL ALPHA or UNKNOWN.

## 4. JavaScript Audit

Inventory found 24 JS files and 13 possible orphan candidates.

### JS orphan candidates

| File | Classification | Reason | Benefit | Risk |
| --- | --- | --- | --- | --- |
| `DataTables/datatables.js` | UNKNOWN | Unminified counterpart; `datatables.min.js` is referenced. Could be development copy. | Small asset reduction. | Could be used dynamically or for debugging. |
| `photoswipe/dist/photoswipe-lightbox.esm.js` | UNKNOWN | No static reference. | Asset reduction. | PhotoSwipe may be dynamically imported. |
| `photoswipe/dist/photoswipe-lightbox.esm.min.js` | UNKNOWN | No static reference. | Asset reduction. | Classic/media may rely dynamically. |
| `photoswipe/dist/photoswipe.esm.js` | UNKNOWN | No static reference. | Asset reduction. | Same. |
| `photoswipe/dist/photoswipe.esm.min.js` | UNKNOWN | No static reference. | Asset reduction. | Same. |
| `virtualsky/excanvas.min.js` | UNKNOWN | No static reference. | Asset reduction. | Compatibility fallback for VirtualSky. |
| `virtualsky/extra/highlight.pack.js` | SAFE TO ARCHIVE after verification | Looks like demo/docs support, not core runtime. | Reduce shipped demo assets. | Low-medium if VirtualSky examples use it. |
| `virtualsky/extra/qunit-1.12.0.js` | SAFE TO ARCHIVE after verification | Test/demo asset. | Reduce shipped demo assets. | Low if not served. |
| `virtualsky/formatexamples.js` | SAFE TO ARCHIVE after verification | Example/demo asset. | Reduce shipped demo assets. | Low-medium. |
| `virtualsky/lang/translate.js` | UNKNOWN | May support language loading. | Small. | Could break i18n. |
| `virtualsky/stuquery.js` | UNKNOWN | VirtualSky dependency variant. | Small. | Could break VirtualSky. |
| `virtualsky/virtualsky-planets.js` | UNKNOWN | May be optional planets feature. | Small. | Could break VirtualSky. |
| `virtualsky/virtualsky.js` | UNKNOWN | Unminified counterpart; `virtualsky.min.js` may be used. | Asset reduction. | Could be used dynamically. |

Recommendation: do not delete JS before Alpha. Create a static asset verification mission later.

## 5. CSS Audit

Inventory found 9 CSS files and 3 possible orphan candidates.

| File | Classification | Reason |
| --- | --- | --- |
| `DataTables/datatables.css` | UNKNOWN | Unminified counterpart; minified CSS is referenced. Verify before deletion. |
| `virtualsky/extra/highlight.css` | SAFE TO ARCHIVE after verification | Demo/docs support likely. |
| `virtualsky/extra/qunit-1.12.0.css` | SAFE TO ARCHIVE after verification | Test/demo support likely. |
| `modern_admin/modern-admin.css` | KEEP | Product UI and Modern Admin depend on it. |
| `css/style.css`, Bootstrap CSS | KEEP | Classic/shared shell depends on them. |

Recommendation: no CSS deletion before Alpha.

## 6. Builder / Provider / Adapter Audit

Product builders are now the core of the new architecture.

| Group | Classification | Notes |
| --- | --- | --- |
| Product UI builders | KEEP | Active route dependency and test coverage. |
| Product validators | KEEP | Safety boundary before templates. |
| DATA repositories/adapters | KEEP | Runtime integrations for DATA001-DATA006. |
| Static fallback builders | KEEP | Required for missing DB/context safety. |
| Fake test repositories | KEEP | Unit coverage for safety behavior. |
| `tools/hybrid_ui_inventory.py` | KEEP | Release Candidate audit baseline. |
| `tools/hybrid_settings_inventory.py` | KEEP UNTIL ALPHA | Settings governance still references it. |
| Ownership JSON maps | KEEP | Governance/source of truth for audit. |

No builder/provider/adapter is currently a removal candidate.

## 7. Documentation Audit

There are 83 markdown files at depth <= 2, many created during Product UI and Phase 2.

### Permanent documents

| Document/group | Classification | Reason |
| --- | --- | --- |
| `README.md` | KEEP | Project entry point. |
| `HYBRID_PRODUCT_PRINCIPLES.md` | KEEP | Governance manifesto. |
| `HYBRID_PRODUCT_ARCHITECTURE_V1.md` | KEEP | Official architecture. |
| `HYBRID_PRODUCT_DOMAIN_CONTRACT_V1.md` | KEEP | Frontend/backend contract direction. |
| `HYBRID_HIGHLIGHT_DOMAIN_V1.md` | KEEP | Highlights domain definition. |
| `HYBRID_SAFE_ACTIONS_POLICY.md` | KEEP | Safety model. |
| `HYBRID_PORTING_GUARDRAILS.md` / `HYBRID_PORTING_PROTOCOL.md` | KEEP UNTIL ALPHA | Still useful for Classic/Modern separation. |
| `HYBRID_PRODUCT_UI_V1_FINAL_REVIEW.md` | KEEP | Baseline pre-real-data review. |
| `PHASE2_DATA_INTEGRATION_REVIEW_AFTER_DATA006.md` | KEEP | Current decision point. |
| `RELEASE_CANDIDATE_CLEANUP_AUDIT.md` | KEEP | This audit. |

### Temporary/process documents

| Document group | Count | Classification | Recommendation |
| --- | ---: | --- | --- |
| `DATA001_*` through `DATA006_*` discovery/audit/adapter/integration/review docs | 23 | SAFE TO ARCHIVE after Alpha | Valuable history, too noisy at repo root. Move to `docs/archive/phase2-data/`. |
| `HYBRID_NOW_*_REVIEW`, source/wiring/current phase reviews | 7+ | SAFE TO ARCHIVE after Alpha | Keep final/current review in root or docs; archive step reviews. |
| Individual v1 surface review docs | 7 | SAFE TO ARCHIVE after Alpha | Keep summary inventory/final review; archive detailed step reviews. |
| Product flow stress/critique docs | 3 | SAFE TO ARCHIVE after Alpha | Historically valuable, not daily RC material. |
| Settings inventory/redesign docs | several | KEEP UNTIL ALPHA | Still help explain settings-first transition; archive later. |

### Historical documents

| Document group | Classification | Reason |
| --- | --- | --- |
| `HYBRID_ROADMAP.md`, `HYBRID_UX_ROADMAP.md`, `HYBRID_ARCHITECTURE_V2.md`, older porting plans | SAFE TO ARCHIVE | Useful project history but may conflict with current frozen architecture if left at root. |
| `docs/modern-admin-*` plans/audits | SAFE TO ARCHIVE after Alpha | Historical Modern porting context. |

### Eliminable documents

No markdown file is currently SAFE TO DELETE without a documentation owner decision.

Recommendation: archive rather than delete. The documents encode important reasoning and safety boundaries.

## 8. Repository / Experiments / Tests Audit

### `testing/`

There are 97 Python files under `testing/`.

| Group | Classification | Reason |
| --- | --- | --- |
| `testing/product_view_models_test.py` | KEEP | Core Product UI safety test. |
| `testing/modern_safe_action_test.py` | KEEP | Safe-action governance. |
| Domain/unit tests for scientific frames, metadata, detector, event, quality, capture profiles | KEEP | Protects current/future domain work. |
| `testing/benchmark/*` | SAFE TO ARCHIVE after Alpha | Useful experiments, not release tests. |
| `testing/image/*` | SAFE TO ARCHIVE after Alpha | Mostly exploratory media/image scripts. |
| `testing/net/*` | SAFE TO ARCHIVE after Alpha | External network experiments; not RC path. |
| `testing/gpio/*` | SAFE TO ARCHIVE after Alpha | Hardware experiments; not generic RC path. |
| `testing/astrometrics/*` | SAFE TO ARCHIVE after Alpha | Research/diagnostic scripts; not Product UI RC. |
| `testing/blob_detection/*` | KEEP UNTIL DETECTOR DESIGN | Useful if detector work is next, but should not run in Alpha request path. |

### `misc/`

| Group | Classification | Reason |
| --- | --- | --- |
| setup/support scripts | KEEP | Operational install/support value. |
| example hooks | KEEP | User customization examples. |
| upload/sensor/camera experiments | UNKNOWN | Some may be documented support tools. Verify before archive. |
| generated bytecode under `misc/__pycache__` | SAFE TO DELETE locally | Not source. |

### `examples/`

| Group | Classification | Reason |
| --- | --- | --- |
| `examples/properties/*` | KEEP | Camera property reference corpus. |
| `examples/telegraf/*` | KEEP | Integration examples. |
| `examples/DENOISE PR TEST ENVIRONMENT/*` | SAFE TO ARCHIVE after Alpha | Large experimental denoise assets/scripts; not RC runtime. |
| `examples/example.php` | UNKNOWN | Legacy integration example; verify before delete/archive. |

### JSON files

| File | Classification | Reason |
| --- | --- | --- |
| `tools/hybrid_ui_ownership_map.json` | KEEP | Product/Classic/Modern ownership governance. |
| `tools/hybrid_settings_ownership_map.json` | KEEP UNTIL ALPHA | Settings coverage governance. |
| VirtualSky data JSON | KEEP | Static astronomy visualization dependency. |
| `examples/telegraf/*.json` | KEEP | Integration examples. |

## 9. Classic Audit

Classic must not be deleted before Alpha.

### Still dependent on Classic

- Direct Classic page routes remain registered.
- Classic templates have no orphan candidates because routes still map to them.
- Public routes and redirects depend on legacy media/view behavior.
- `/ajax/*` endpoints include shared APIs and Classic behavior.
- Modern wrappers still subclass Classic/backend views for tools such as config, drives, network, focus, generation, camera simulator, GPIO, image processing.
- Auth/user/task/log/system areas still contain Classic or shared behavior.
- External APIs and sync routes are not replaced by Product UI.

### Already independent

- Product UI v1 pages: Now, Highlights, Moment, Output, Sky Cycle, Library, Observatory.
- Product builders in `indi_allsky/product_view_models.py`.
- DATA001-DATA006 adapters are framework-free in the product model layer and wired from Flask only at the edge.
- Product UI templates are read-only and server-rendered.

### Future separation candidates

| Area | Classification | Recommendation |
| --- | --- | --- |
| Modern safe-control wrappers over Classic views | KEEP UNTIL ALPHA | Replace only with safe actions and tests. |
| Classic settings routes | KEEP UNTIL ALPHA | Product UI settings direction is not editor-complete. |
| Classic media viewers/generators | KEEP UNTIL ALPHA | Product UI has no preview/media generation replacement. |
| Classic AJAX endpoints | UNKNOWN | Need per-endpoint consumer audit. |

## 10. Performance Audit

### Current known bounded Product UI runtime queries

| Surface | Source | Risk | Recommendation |
| --- | --- | --- | --- |
| Now | latest frame metadata | Low | Single bounded query with fallback. |
| Now | latest generated output metadata | Medium | Multi-source bounded queries; acceptable but review on RPi5. |
| Now | current capture status | Low-medium | Composite metadata; keep fallback. |
| Now | source trust summary | Medium | Metadata-only, but multiple source descriptors; review query count. |
| Highlights | image metadata candidates | Medium | Bounded, explainable, but should not expand into ranking. |
| Sky Cycle | latest + cycle-start image metadata | Low-medium | Two bounded queries; acceptable. |

### Performance risks before Raspberry pull

| Risk | Classification | Reason | Mitigation |
| --- | --- | --- | --- |
| Now query count grows quietly | KEEP WATCH | Several DATA providers now run in Now. | Add query-count documentation and RPi5 render timing check. |
| Multi-source generated output descriptors | KEEP WATCH | Seven bounded queries are okay, but still several DB hits. | Benchmark on Raspberry before adding more DATA. |
| Flask `views.py` size/coupling | KEEP UNTIL ALPHA | Large file; risky to refactor now. | Defer refactor; only audit. |
| Template payload density | KEEP WATCH | Product UI pages can become verbose. | UX pass after Alpha, not before cleanup. |
| Static assets | UNKNOWN | VirtualSky/PhotoSwipe/DataTables include unused-looking variants. | Asset audit after Alpha. |

## Classification Table

| Item | Classification | Priority | Benefit | Risk | Dependency |
| --- | --- | --- | --- | --- | --- |
| Local `__pycache__` / `.pyc` | SAFE TO DELETE locally | P1 | Clean release packaging | Low | None; confirm ignored. |
| DATA001-DATA006 step docs | SAFE TO ARCHIVE | P1 | Root cleanup | Low | Preserve in docs archive. |
| Product critique/process docs | SAFE TO ARCHIVE | P1 | Root cleanup | Low-medium | Keep canonical architecture docs. |
| `examples/DENOISE PR TEST ENVIRONMENT` | SAFE TO ARCHIVE | P2 | Remove experimental assets | Medium | Detector/denoise planning. |
| VirtualSky extra QUnit/highlight assets | SAFE TO ARCHIVE after verification | P2 | Reduce static assets | Low-medium | Confirm not served by templates. |
| Product UI builders/adapters | KEEP | P0 | Preserve Alpha | Critical if removed | Active routes/tests. |
| Product UI templates | KEEP | P0 | Preserve Alpha | Critical if removed | Active routes. |
| Classic templates/routes | KEEP UNTIL ALPHA | P0 | Compatibility | Critical if removed | Classic fallback/public use. |
| Public/latest/media routes | KEEP | P0 | External compatibility | Critical if removed | Bookmarks/integrations. |
| Sync/action APIs | KEEP | P0 | External/control compatibility | Critical if removed | Remote clients. |
| Modern settings pages | KEEP UNTIL ALPHA | P2 | Reference/governance | Medium | Settings replacement incomplete. |
| JS/CSS orphan candidates | UNKNOWN | P2 | Asset reduction | Medium-high | Dynamic usage possible. |
| `testing/benchmark`, `testing/image`, `testing/net`, `testing/gpio`, `testing/astrometrics` | SAFE TO ARCHIVE after Alpha | P2 | Dev tree cleanup | Medium | Experimental diagnostics. |
| Ownership mismatches | KEEP UNTIL ALPHA | P1 | Better audit signal | Low-medium | Update maps/reports only. |

## Areas Not To Touch Before Alpha

- Product Architecture.
- Product UI route names.
- Product view model contracts.
- DATA001-DATA006 adapters/providers.
- Classic routes/templates.
- Public latest/view/watch/image routes.
- Sync/action APIs.
- Media generation code.
- Storage/filesystem helpers.
- Camera backend modules.
- Device/sensor/focuser/dew-heater/fan modules.
- Filetransfer providers.
- Migrations.
- Install/service files.

## Recommended Cleanup Sequence

### Cleanup Mission 1: Repository Hygiene

Scope:

- delete local ignored `__pycache__` / `.pyc`;
- verify `.gitignore`;
- no source changes.

Expected benefit: low-medium.
Risk: low.

### Cleanup Mission 2: Documentation Archive Plan

Scope:

- define `docs/archive/phase2-data/`;
- move DATA step docs and older process reviews;
- keep canonical architecture/principles/final reviews easy to find.

Expected benefit: high for readability.
Risk: low if links are updated or archive index is added.

### Cleanup Mission 3: Ownership Map Reconciliation

Scope:

- reduce 71 ownership mismatches and 272 undeclared inventory items;
- no route/template behavior changes.

Expected benefit: high for future safe deletion.
Risk: low-medium.

### Cleanup Mission 4: Raspberry Readiness Audit

Scope:

- run tests/inventory/compile;
- measure Product UI render/query behavior on Raspberry target;
- validate fallback without DB data where possible.

Expected benefit: high.
Risk: low.

### Cleanup Mission 5: Static Asset Verification

Scope:

- verify JS/CSS orphan candidates;
- archive demo/test assets only after dynamic route/template verification.

Expected benefit: medium.
Risk: medium.

## Final Recommendation

Do not delete application code before Alpha.

The first Release Candidate cleanup should be conservative:

1. local bytecode/cache cleanup;
2. documentation archiving;
3. ownership/inventory reconciliation;
4. Raspberry readiness audit.

Only after Alpha proves Product UI behavior on Raspberry should the project consider removing Classic surfaces, media viewers, legacy AJAX routes, or static asset variants.
