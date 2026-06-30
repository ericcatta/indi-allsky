# Performance Audit: Legacy vs Product UI

## Verdict

The Product UI is faster because it follows a bounded, contract-first request
model:

- small backend-owned builders;
- one purpose per request;
- allowlisted metadata payloads;
- bounded queries;
- no filesystem/media reads in the normal Product request path;
- no broad dashboard context created implicitly.

Many legacy/operational `/modern-admin` pages are slower because they still
inherit older view patterns:

- shared context builders do work even when the template no longer renders it;
- media pages often serialize URLs/previews per row;
- some operational pages inherit Classic views that touch filesystem, logs,
  support scripts, or legacy media helpers;
- list pages commonly load 24-100 rows and format each row in Python;
- some pages issue multiple count queries for summary cards;
- some detail pages intentionally read logs or inspect local system files.

## Product UI Request Model

Fast Product surfaces:

- Now;
- Highlights;
- Sky Cycle;
- Moment;
- Output;
- Library;
- Observatory.

The Product surfaces use `indi_allsky/product_view_models.py` builders and
small injected repositories. The request path is intentionally narrow.

Examples:

- Latest frame metadata: one bounded image metadata query for the active camera.
- Latest generated output metadata: one bounded query per descriptor, then select
  latest in memory from a tiny candidate set.
- Current phase: already available `context['night']`; no new astronomy
  calculation.
- Source trust / highlights / sky cycle summaries: metadata-only and fallback
  safe.

This pattern keeps latency predictable on Raspberry Pi 5.

## Legacy / Operational Request Model

Operational pages are not uniformly slow for one reason; they are slower because
several costs stack together.

### Shared Context Work

Before this audit, multiple operational pages inheriting `ModernAdminView` or
`ModernAdminContextMixin` still computed old shell/topbar/dashboard context even
though the Hybrid shell no longer rendered it.

That included:

- runtime status calculation;
- capture service status via `systemctl --user is-active`;
- recent camera status DB queries;
- storage summary;
- latest image URL preparation;
- dashboard analytics from frame metadata files;
- event candidate/timeline summary reads;
- per-camera latest image lookup.

Classification: `SAFE FIX NOW`.

Fix applied:

- `ModernAdminView.get_context()` now builds only lightweight common context.
- `ModernAdminContextMixin.get_context()` no longer builds unused topbar context.
- `ModernAdminStorageView` now explicitly asks for storage context because its
  template uses it.

Expected benefit:

- removes invisible subprocess/status work from operational pages;
- removes invisible recent-camera DB checks from operational pages;
- removes invisible dashboard/event metadata reads from pages like Cameras,
  Storage, Uploads, YouTube, System, and placeholder-derived pages.

Risk:

- low. The hidden `_shell_header.html` no longer renders topbar/nav/action data
  inside the Hybrid shell, and templates do not reference those context fields
  outside that partial.

### Media List Pages

Examples:

- Images;
- Gallery;
- Timelapses;
- Keograms;
- Startrails;
- Panorama;
- RAW;
- FITS.

Observed pattern:

- bounded row load, usually 24-100 rows;
- per-row serialization;
- per-row URL or preview URL preparation;
- thumbnail lookup fallback on gallery entries when `thumbnail_uuid` exists;
- possible remote/local URL decision logic.

Classification: `SAFE AFTER ALPHA`.

Reason:

- These pages are functional operational viewers.
- More optimization requires page-specific adapter design or lazy pagination
  review.
- Avoid changing media behavior immediately before Alpha.

Possible future fixes:

- Product-style list repositories that return metadata-only rows first;
- optional lazy preview loading;
- lower default row limits on Raspberry;
- avoid thumbnail lookup until visible;
- cache camera filter rows for one request.

### Gallery

The gallery is already more bounded than older all-at-once patterns:

- initial limit is bounded;
- pagination endpoint caps limit;
- cursor pagination is present.

Remaining cost:

- camera filters can perform camera matching work;
- preview URL fallback can add thumbnail DB lookups;
- serializing many image URLs is still more expensive than Product metadata
  summaries.

Classification: `KEEP` for now.

Reason:

- It already has bounded pagination and is user-facing media functionality.
- Further changes are UX/data-contract work, not a safe global fix.

### Cameras

Before this audit, Cameras was paying for the old Modern dashboard context via
inheritance even though it only needed camera/profile rows.

Fix applied through shared context cleanup.

Remaining cost:

- camera/profile inventory queries;
- config-derived multi-camera profile analysis;
- optional POST workflows already present.

Classification:

- shared context cleanup: `SAFE FIX NOW`;
- deeper camera page optimization: `SAFE AFTER ALPHA`.

### Loop

Loop inherits Classic loop behavior through `ImageLoopImgView` and wraps it in
the Hybrid shell.

Likely cost:

- legacy loop context and media URL generation;
- possible image path/URL normalization inherited from Classic.

Classification: `RISKY`.

Reason:

- Loop behavior is externally visible and likely bookmark/usage sensitive.
- Optimizing it safely requires a dedicated Loop audit.

### System / Logs / Support

Examples:

- Logs;
- Log detail;
- System Info;
- Support Info.

Costs:

- log detail intentionally reads bounded log tails;
- support info can run a support script;
- system info may inspect Raspberry/system state.

Classification:

- `KEEP` for current behavior;
- `SAFE AFTER ALPHA` for page-specific caching or stricter lazy loading.

Reason:

- These pages are operational diagnostics. Their cost is expected and should not
  be hidden by broad refactors.

### Storage / Uploads

Storage:

- disk usage via `psutil`;
- several count queries by media table.

Uploads:

- task queue counts by state;
- latest upload notifications;
- config summary.

Classification:

- inherited hidden context cleanup: `SAFE FIX NOW`;
- summary count optimization: `SAFE AFTER ALPHA`.

Future option:

- collapse multiple count queries into a single grouped query where practical.

### Dark Library / Calibration

Dark library currently reads calibration rows and calls filesystem helpers for
file size.

Classification: `RISKY`.

Reason:

- It uses filesystem metadata as part of the page result.
- Optimizing it without changing output requires a dedicated calibration/source
  audit.

### Long Term Keogram

Long-term keogram checks for a generated image on disk and stats it when present.

Classification: `RISKY`.

Reason:

- This is explicit page behavior today.
- A metadata-only replacement would require a new contract or DB-backed source.

## Query Count Notes

Measured precisely only by static inspection, not runtime profiling.

Approximate request work:

- Product Now: bounded single-purpose metadata providers; no broad dashboard
  rollup.
- Highlights/Sky Cycle: bounded metadata summaries and mostly Product builders.
- Cameras before fix: camera work plus inherited dashboard/topbar work.
- Cameras after fix: camera/profile work only.
- Media lists: one bounded row query plus per-row URL serialization; gallery can
  add camera filter queries and thumbnail lookups.
- Storage before fix: storage counts plus inherited dashboard/topbar work.
- Storage after fix: disk usage plus storage counts only.

## Root Causes

1. Product UI avoids implicit shared context.
   Classification: `KEEP`.

2. Legacy/operational pages historically inherited context that was convenient
   but too broad.
   Classification: fixed where safe.

3. Media pages still prepare display URLs/previews during the request.
   Classification: `SAFE AFTER ALPHA`.

4. Some diagnostic pages intentionally read local system/log state.
   Classification: `KEEP`.

5. Some calibration/generated-media pages still touch filesystem helpers.
   Classification: `RISKY`.

## Fixes Applied

### Lightweight Modern Admin Context

Applied in `indi_allsky/flask/views.py`.

Changed:

- `ModernAdminView.get_context()` no longer creates dashboard/topbar/latest-image
  context by default.
- `ModernAdminContextMixin.get_context()` no longer creates topbar context by
  default.
- `ModernAdminStorageView.get_context()` explicitly adds storage context because
  the storage page uses it.

Functional behavior:

- visible Hybrid page output should remain the same;
- old nested topbar data was already not rendered inside the Hybrid shell;
- no routes, DATA integrations, providers, media behavior, or Classic behavior
  were changed.

Estimated benefit:

- high on Raspberry for operational pages that inherited `ModernAdminView`;
- moderate for pages that inherited `ModernAdminContextMixin`;
- none for pages that already used pure Product builders.

Risk:

- low.

## Fixes Proposed But Not Applied

### Product-style Media Metadata Adapters

Replace row serialization with bounded metadata adapters, and load previews only
when explicitly needed.

Classification: `SAFE AFTER ALPHA`.

### Dedicated Loop Product Contract

Create a metadata-first loop summary instead of relying on Classic loop context.

Classification: `RISKY` before Alpha.

### Calibration Metadata Contract

Avoid `getFilesystemPath().stat()` in dark library by storing file size metadata
or making filesystem data optional.

Classification: `RISKY`.

### Grouped Storage Counts

Replace several count queries with grouped or cached summaries.

Classification: `SAFE AFTER ALPHA`.

### Runtime Profiling Middleware

Add opt-in request timing/query count instrumentation for Raspberry tests.

Classification: `SAFE AFTER ALPHA`.

Reason:

- useful, but not needed to ship the current audit;
- should be opt-in and never add request overhead by default.

## Stop List

Do not do before Alpha:

- broad media refactor;
- Classic removal;
- Loop behavior rewrite;
- filesystem-backed calibration rewrite;
- new preview/media fetch architecture;
- new polling;
- hidden background profiling.

## Recommendation

The Product UI speed advantage is real and architectural. Keep the Product model:

- domain-specific builders;
- injected bounded repositories;
- metadata-only first;
- no implicit shared dashboard context;
- no filesystem/media access in the default Product request path.

For Alpha, the safe win is the lightweight context cleanup already applied here.
After Alpha, optimize media/loop/calibration pages one at a time with the same
DATA-style discovery, audit, adapter, integration, review process.
