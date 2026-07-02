# Hybrid Product Consolidation Next Microsteps

This is the living backlog for Hybrid Product Consolidation.

The source of truth for the current consolidation baseline is
`docs/product_consolidation/HYBRID_PRODUCT_CONSOLIDATION_AUDIT.md`.

## Working Rules

- One mission, one micro-step, one commit.
- Prefer clarification, ownership, and low-risk simplification before code changes.
- Do not remove Classic, rename settings keys, change routes, or change runtime behavior without explicit approval.
- When evidence is weak, classify as `UNKNOWN` and document the question.
- Keep Product UI, DATA001-DATA006, and the frozen Product Architecture stable.

## Current Baseline

- Product UI v1 exists and is visually converged.
- DATA001-DATA006 are integrated with bounded metadata-only contracts.
- Route roles for `/modern-admin/*` are now classified in `HYBRID_ROUTE_ROLE_MATRIX.md`.
- Settings groups are now classified in `HYBRID_SETTINGS_CONTRACT_REVIEW.md`.
- Classic remains required as fallback/reference for many operational surfaces.
- Settings remain high risk, but their product contract is now explicit.
- Notifications settings are the first read-only settings contract slice moved
  into a Hybrid-owned contract helper; existing keys, defaults, config behavior,
  and Classic fallback remain unchanged.
- Storage settings are the second read-only settings contract slice moved into
  the same Hybrid-owned settings contract helper; storage keys remain descriptive
  only and no path validation, filesystem access, or config writes were added.
- Mutative/safe-action ownership is now discovered in
  `HYBRID_SAFE_ACTION_REGISTRY.md`; the next blocker is a canonical action
  contract schema before any new execution path.
- The Product spine is now protected by
  `testing/product_spine_regression_test.py`.
- Product spine Flask views now share `ModernAdminProductView`, a small Hybrid
  ownership boundary that keeps Product payload wiring out of Classic wrappers.
- Observatory tool wrappers now share `ModernAdminObservatoryToolView`, reducing
  direct Classic-style ownership for read-only observatory context pages.
- Camera diagnostic wrappers now share `ModernAdminCameraToolView`, reducing
  direct Classic-style ownership for read-only camera operational pages. Camera
  Info lens/sensor summary formatting and Image Lag read-only window/limit
  policy now live in a Hybrid-owned diagnostics service.
- System read-only wrappers now share `ModernAdminSystemToolView`, reducing
  direct Classic-style ownership for developer/status pages; the boundary owns
  the read-only login guard for this family.
- Notification read-only wrappers now share `ModernAdminNotificationStatusView`.
  The read-only list/detail formatter, context summaries, acknowledge lookup,
  acknowledge result/audit types, and acknowledge action policy now live in the
  Hybrid-owned Notifications service layer. `modern_safe_action.py` remains the
  safe-action wrapper/orchestrator for permission and execution contracts.
- Task/status wrappers now share `ModernAdminTaskStatusView`, reducing direct
  Classic-style ownership for read-only queue listing/detail pages; the
  boundary also owns the read-only login guard for this family. Task list/detail
  read-only query, visibility policy, and formatting now live in a Hybrid-owned
  service layer.
- Media metadata listing wrappers now share `ModernAdminMediaMetadataView`;
  interactive gallery/download/preview surfaces remain intentionally outside
  this boundary. The boundary owns the read-only login guard for metadata
  listing/detail pages. Startrail video, keogram, startrail, and mini-timelapse
  metadata listings and their read-only summary counts are the first
  media-metadata slices moved into Hybrid-owned services.
- Media browse wrappers now enter through `ModernAdminMediaBrowseView`, but
  preview, URL generation, lightbox and download behavior remain unchanged and
  require a separate safety review before deeper extraction.
- Remaining direct Modern Admin wrappers have been reviewed. No clearly safe
  read-only family remains for simple boundary extraction; the easy extraction
  phase is complete for now.
- Classic Exit Assessment now identifies the real removal blockers: settings
  ownership, media/public filesystem behavior, operational/developer actions,
  system/auth/support surfaces, and external compatibility APIs.

## Remaining Direct Modern Admin Wrapper Review

Decision: Option B. Do not force another boundary class. The next Classic
extraction phase should replace one backend implementation behind an existing
Hybrid boundary, preserving routes, templates, payloads, context keys, and
runtime behavior.

### Safe Next Extraction Candidate

- None found with low enough risk. The obvious read-only families now have
  Hybrid boundaries.

### Intentionally Left Classic-Owned For Now

- `ModernAdminPublicMediaEndpointsView`: read-only compatibility catalog, but
  it describes public media endpoints and should stay near media compatibility
  ownership until public/latest route contracts are reviewed.
- Section landing pages based on `ModernAdminView`
  (`ModernAdminCamerasView`, `ModernAdminStorageView`,
  `ModernAdminUploadsView`, `ModernAdminYoutubeView`,
  `ModernAdminSystemView`, `ModernAdminUpdatesView`): these are shell/section
  pages rather than direct Classic wrapper families. Leave them until a
  dedicated section ownership pass.
- `ModernAdminPlaceholderView` and related mode/placeholder routing remain
  compatibility glue. Changing them would risk navigation/session behavior.

### Risky / Requires Dedicated Review

- `ModernAdminUsersView` and `ModernAdminUserDetailView`: auth/user ownership
  is sensitive and includes account metadata and adjacent mutating user flows.
- `ModernAdminConfigHistoryView`, `ModernAdminConfigRestoreView`, and
  `ModernAdminConfigRestoreDetailView`: config history/restore touches settings
  payloads and restore semantics; keep out of safe boundary extraction.
- `ModernAdminFileSpaceUsageView`: storage/filesystem reporting requires a
  separate filesystem-safety review.
- `ModernAdminLoopView`: loop/media behavior can involve preview, URL
  generation, and client-side media assumptions.
- `ModernAdminSettingsInventoryView` and settings preview descendants:
  settings/config ownership is high risk until a settings implementation
  migration is explicitly approved.

### Mutating / Action-Related, Do Not Touch

- Camera add/detect/server-start flows.
- Safe controls, config save/restore surfaces, generation/focus/process
  controls, network/drives/GPIO controls, and safe-action dry-run/capture
  endpoints.
- Any POST/action endpoint, external API, restore/import/export, restart/stop,
  purge/delete, upload/download, or media-generation path.

## P0

### Settings Contract Implementation Slice

- Motivation: `HYBRID_CLASSIC_EXIT_ASSESSMENT.md` identifies Settings as the
  lowest Hybrid ownership domain and the largest real blocker to making Classic
  removable.
- Benefit: continues moving from settings documentation to native Hybrid
  settings ownership without renaming keys, changing defaults, or removing
  Classic fallback. Notifications and Storage are complete as the first
  read-only contract slices; choose the next low-risk group rather than broad
  settings migration.
- Risk: high if the first slice edits runtime config; keep the first step
  bounded to one low-risk read-only/edit-preview group.
- Impact: high for Classic exit.
- Dependencies: `HYBRID_SETTINGS_CONTRACT_REVIEW.md`, existing settings
  inventory, current Modern settings preview pages, and Classic fallback.
- Verification: preserve settings keys/defaults; add shape/regression tests;
  run settings inventory and route inventory; keep Classic full config working.

### Replace One Backend Implementation Behind Existing Boundary

- Motivation: Hybrid now owns the easy wrapper boundaries, but many boundaries
  still inherit Classic backend implementation details.
- Benefit: reduces actual Classic dependency rather than only moving wrapper
  ownership. Notification, task/status, and four media metadata slices have been
  moved into Hybrid-owned services; continue with one similarly bounded family.
- Risk: medium; choose one bounded read-only implementation and preserve all
  existing routes, templates, payloads, and context keys.
- Impact: high if done behind a mature boundary such as task/status,
  notifications, or media metadata.
- Dependencies: completed boundary regression tests and current wrapper review.
- Verification: add regression tests for unchanged context keys/output shape;
  run relevant boundary tests and py_compile.

### Route Role Matrix Follow-up In Ownership Map

- Motivation: `HYBRID_ROUTE_ROLE_MATRIX.md` now classifies route families by product role, but `tools/hybrid_ui_ownership_map.json` still uses broader `modern` ownership for many routes.
- Benefit: gives inventory reports more useful signal without changing runtime behavior.
- Risk: medium if route classifications are over-applied to dynamic or wrapper routes.
- Impact: medium-high.
- Dependencies: Route Role Matrix.
- Verification: update only evidence-backed ownership metadata; regenerate inventory; do not change routes/templates.

### Safe Action Contract Schema

- Motivation: the action discovery found many live mutative surfaces but no canonical metadata schema for future Product/Operations actions.
- Benefit: gives every future action a consistent review shape before endpoint, UI, audit, or permission work starts.
- Risk: low if documentation-only.
- Impact: high.
- Dependencies: `HYBRID_SAFE_ACTION_REGISTRY.md`, Safe Actions policy, Route Role Matrix, and Settings Contract Review.
- Verification: schema covers action id, endpoint, owner, target, role, destructive/reversible flags, confirmation, auth, CSRF, dry-run, audit, rollback/fallback, runtime risk, and stop conditions.

## P1

### Ownership Map Correction Pass

- Motivation: inventory signals are only useful if expected wrappers and intentional exceptions are marked clearly.
- Benefit: lowers false positives in future audits.
- Risk: medium if classifications are guessed.
- Impact: medium-high.
- Dependencies: Route Role Matrix and Settings Contract Review.
- Verification: inventory mismatch count decreases only where ownership evidence exists.

### Query-Style POST Semantics Audit

- Motivation: the Safe Action Registry found several POST endpoints that are read/list compatibility APIs rather than mutations.
- Benefit: separates true actions from legacy AJAX query endpoints before any route cleanup.
- Risk: low if audit-only.
- Impact: medium.
- Dependencies: Safe Action Registry and browser/network evidence for dynamic callers.
- Verification: each POST endpoint is classified as mutation, query-style read, mixed, or unknown; no route methods change.

### External Action API Compatibility Review

- Motivation: `/action/*` and `/sync/v1/*` contain real mutative external contracts that should not be conflated with Product UI actions.
- Benefit: protects automation/sync consumers during consolidation.
- Risk: low if review-only.
- Impact: high.
- Dependencies: Safe Action Registry and current API route definitions.
- Verification: external endpoints remain unchanged and are classified by owner, auth, destructive behavior, and compatibility risk.

### Environmental Ownership Discovery

- Motivation: environmental awareness is product-critical but can be split across config, sensors, metadata, and legacy pages.
- Benefit: clarifies future source trust, observatory, and science metadata work.
- Risk: low if discovery-only.
- Impact: medium.
- Dependencies: Settings Contract Review.
- Verification: each environmental source is classified as metadata, runtime sensor, config-derived, or legacy fallback.

### Output Detail Identifier Strategy

- Motivation: Output Detail is not identifier-specific yet, limiting real metadata integration.
- Benefit: prepares future output pages without preview/media access.
- Risk: medium if route changes are attempted; keep this design-only.
- Impact: medium-high.
- Dependencies: DATA002 review and Route Role Matrix.
- Verification: design proposes identifier handling, fallback, and no filesystem/media access.

## P2

### Documentation Archive Plan

- Motivation: historical process docs are useful but create cognitive noise.
- Benefit: easier onboarding and lower maintenance overhead.
- Risk: broken links if moved too early.
- Impact: medium.
- Dependencies: doc link audit.
- Verification: archive index exists and `rg` confirms important references still resolve.

### Static Asset Verification

- Motivation: legacy JS/CSS assets may still be dynamically required by operational pages.
- Benefit: prevents unsafe deletion and identifies real cleanup candidates.
- Risk: medium without browser/Raspberry evidence.
- Impact: medium.
- Dependencies: Route Role Matrix and manual operational page walk.
- Verification: each candidate asset has usage evidence or is marked `UNKNOWN`.

### Modern Naming Cleanup Plan

- Motivation: Hybrid still carries Modern/Admin terminology internally.
- Benefit: long-term naming clarity.
- Risk: high if route/API/template names change prematurely.
- Impact: medium.
- Dependencies: Alpha stability and external URL review.
- Verification: plan only; no renames until explicit approval.

### Post-Alpha Historical Doc Archive

- Motivation: many DATA/Product mission documents should remain available but not dominate active planning.
- Benefit: preserves history while reducing working-set size.
- Risk: broken links.
- Impact: medium.
- Dependencies: Alpha branch/tag and documentation archive plan.
- Verification: archive move is link-checked and reversible.

## Completed

- Product Consolidation Audit baseline established in `HYBRID_PRODUCT_CONSOLIDATION_AUDIT.md`.
- Living consolidation backlog created in this file.
- P0 Route Role Matrix completed in `HYBRID_ROUTE_ROLE_MATRIX.md`.
- P0 Settings Contract Review completed in `HYBRID_SETTINGS_CONTRACT_REVIEW.md`.
- P0 Safe Action Registry Discovery completed in `HYBRID_SAFE_ACTION_REGISTRY.md`.
- P0 Product Spine Regression Checklist implemented as `testing/product_spine_regression_test.py`.
- Product spine view ownership boundary added via `ModernAdminProductView`.
- Observatory tool ownership boundary added via `ModernAdminObservatoryToolView`.
- Observatory SQM context summary ownership moved into
  `ModernAdminSqmSummaryService`.
- Long-term Keogram generated-age display formatting moved into
  `ModernAdminLongTermKeogramDisplayService`.
- VirtualSky overlay form-data defaults moved into
  `ModernAdminVirtualSkyContextService`.
- Camera diagnostic ownership boundary added via `ModernAdminCameraToolView`.
- Camera Info lens/sensor summary formatting moved into
  `ModernAdminCameraInfoService`.
- Image Lag read-only window/limit policy moved into
  `ModernAdminImageLagPolicy`.
- System read-only ownership boundary added via `ModernAdminSystemToolView`.
- System read-only login guard ownership moved into `ModernAdminSystemToolView`.
- Log Detail display policy, source rows, redaction, and file-size formatting moved
  into `ModernAdminLogDisplayPolicy`.
- System Info overview card composition moved into
  `ModernAdminSystemInfoSummaryService`.
- Notification read-only ownership boundary added via `ModernAdminNotificationStatusView`.
- Notification read-only list/detail formatting moved into
  `ModernAdminNotificationReadService`.
- Notification read-only context summary ownership moved into
  `ModernAdminNotificationReadService`.
- Task/status ownership boundary added via `ModernAdminTaskStatusView`.
- Task/status login guard ownership moved into `ModernAdminTaskStatusView`.
- Task/status list/detail query and formatting moved into
  `ModernAdminTaskReadService`.
- Media metadata listing ownership boundary added via `ModernAdminMediaMetadataView`.
- Media metadata login guard ownership moved into `ModernAdminMediaMetadataView`.
- Startrail video metadata listing moved into
  `ModernAdminStartrailVideoMetadataService`.
- Keogram metadata listing moved into `ModernAdminKeogramMetadataService`.
- Startrail metadata listing moved into `ModernAdminStartrailMetadataService`.
- Mini-timelapse metadata listing moved into
  `ModernAdminMiniTimelapseMetadataService`.
- Media metadata uploaded/success/source summary ownership moved into the
  Hybrid-owned metadata services for the extracted slices.
- Media browse ownership boundary added via `ModernAdminMediaBrowseView`.
- Remaining direct Modern Admin wrapper review completed; no further easy
  read-only boundary extraction is safe without a dedicated implementation
  replacement review.
