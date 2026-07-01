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
- Classic remains required as fallback/reference for many operational surfaces.
- Settings are the highest-risk consolidation area.
- Settings ownership is the next ambiguity to reduce.

## P0

### Settings Contract Review

- Motivation: settings are the largest complexity and regression risk area.
- Benefit: prepares Basic / Advanced / Developer organization without renaming keys or changing behavior.
- Risk: low if documentation-only.
- Impact: high.
- Dependencies: `tools/hybrid_settings_ownership_map.json`, `HYBRID_SETTINGS_INVENTORY_REPORT.md`.
- Verification: every settings group has owner, user level, risk, fallback, and migration stance.

### Product Spine Regression Checklist

- Motivation: protect the stable Product spine while consolidation work touches surrounding operational pages.
- Benefit: makes Now, Highlights, Moment, Output, Sky Cycle, Library, and Observatory harder to regress.
- Risk: low.
- Impact: medium-high.
- Dependencies: Product view model tests and ownership map.
- Verification: checklist confirms routes, templates, builders, validation, read-only behavior, and no new POST/fetch/AJAX.

### Route Role Matrix Follow-up In Ownership Map

- Motivation: `HYBRID_ROUTE_ROLE_MATRIX.md` now classifies route families by product role, but `tools/hybrid_ui_ownership_map.json` still uses broader `modern` ownership for many routes.
- Benefit: gives inventory reports more useful signal without changing runtime behavior.
- Risk: medium if route classifications are over-applied to dynamic or wrapper routes.
- Impact: medium-high.
- Dependencies: Route Role Matrix.
- Verification: update only evidence-backed ownership metadata; regenerate inventory; do not change routes/templates.

## P1

### Ownership Map Correction Pass

- Motivation: inventory signals are only useful if expected wrappers and intentional exceptions are marked clearly.
- Benefit: lowers false positives in future audits.
- Risk: medium if classifications are guessed.
- Impact: medium-high.
- Dependencies: Route Role Matrix.
- Verification: inventory mismatch count decreases only where ownership evidence exists.

### Safe Action Registry Discovery

- Motivation: mutative Classic/operational actions need explicit ownership before any Product replacement.
- Benefit: prepares future safe actions without adding mutations now.
- Risk: low if discovery-only.
- Impact: high.
- Dependencies: Route Role Matrix and Settings Contract Review.
- Verification: each mutative route/action has owner, risk, required audit trail, and rollback expectation.

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
