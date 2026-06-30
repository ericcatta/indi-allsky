# Targeted Performance Audit: Media, Loop, Dark Library, Long Term Keogram

## Scope

This pass reviews the operational pages that still feel slower than the Product
UI after the broad performance cleanup:

- Media / Gallery / Images;
- Loop;
- Dark Library;
- Long Term Keogram;
- directly related media list/detail pages.

The goal is to apply only low-risk fixes that preserve behavior.

## Summary

The Product UI remains faster because it asks bounded Product questions and
builds small allowlisted payloads. The targeted operational pages are slower
because they are still operational viewers: they prepare media URLs, previews,
download links, loop frame data, filesystem-backed calibration metadata, or
cached generated images.

Safe fixes were found in the media serialization path. Loop, Dark Library, and
Long Term Keogram need dedicated post-Alpha work if they must become as fast as
Product pages.

## Pages Analyzed

### Media / Gallery / Images

Relevant classes:

- `ModernAdminMediaListView`;
- `ModernAdminMediaGalleryView`;
- `ModernAdminMediaGalleryPageView`;
- `ModernAdminMediaImagesView`;
- `ModernAdminMediaFitsView`;
- media subclasses for timelapses, panorama loop, FITS viewer.

Observed costs:

- bounded DB list query per page;
- per-row serialization;
- per-row media URL generation;
- per-row preview URL generation;
- gallery thumbnail lookup when `thumbnail_uuid` exists;
- gallery camera filter construction from DB rows and multi-camera config.

Classification:

- duplicate URL generation: `SAFE FIX NOW`;
- repeated gallery filter construction in one request: `SAFE FIX NOW`;
- thumbnail lookup strategy: `SAFE AFTER ALPHA`;
- broader media adapter refactor: `SAFE AFTER ALPHA`.

Fixes applied:

- `serialize_media_entry()` now computes `media_url` once and passes it to
  `get_media_preview_url()`.
- Default preview behavior now reuses the already computed media URL instead of
  calling `getUrl()` again.
- Gallery fallback paths also reuse the already computed media URL when thumbnail
  preview is unavailable.
- Gallery camera filters are cached on the view instance for the duration of the
  request, avoiding repeated DB/config matching work.

Expected benefit:

- Images/timelapses/panorama-loop/FITS viewer list pages avoid duplicate URL
  work for each row.
- Gallery avoids repeated camera filter query/config work during the same
  request.
- Pagination and output remain unchanged.

Risk:

- low. URLs and preview URLs remain identical; only duplicate work is removed.

### Gallery Pagination

Existing safety:

- initial load is bounded;
- AJAX page endpoint has a hard cap;
- cursor pagination avoids unbounded page loads.

No change applied.

Reason:

- It is already bounded and changing pagination behavior would affect UX.

Classification: `KEEP`.

### Loop

Relevant class/template:

- `ModernAdminLoopView`;
- `ImageLoopImgView`;
- `modern_admin/loop.html`.

Observed costs:

- inherits legacy loop context;
- client periodically requests loop data;
- image list is built by the existing loop endpoint;
- behavior depends on existing image URL/path normalization.

Fix applied:

- none.

Reason:

- Loop behavior is user-visible and refresh-driven.
- Optimizing it safely requires a dedicated Loop data contract or endpoint audit.

Classification: `RISKY`.

Post-Alpha proposal:

- create a bounded loop metadata adapter;
- preserve current endpoint behavior;
- consider smaller default loop history on Raspberry only if configurable.

### Dark Library

Relevant class/template:

- `ModernAdminDarkLibraryView`;
- `modern_admin/dark_library.html`.

Observed costs:

- loads dark frame and bad pixel map rows;
- calls `getFilesystemPath().stat()` per row to display file size;
- calls URL helpers for download links.

Fix applied:

- none.

Reason:

- file size and download link are visible output today.
- Removing filesystem stat would change displayed values.

Classification: `RISKY`.

Post-Alpha proposal:

- add metadata-backed file size where available;
- make filesystem stat optional/fallback;
- bound calibration rows if real-world installations accumulate many records.

### Long Term Keogram

Relevant class/template:

- `ModernAdminLongTermKeogramView`;
- `modern_admin/longterm_keogram.html`.

Observed costs:

- checks a generated image path;
- stats the cached long-term keogram when present;
- loads eight recent DB samples.

Fix applied:

- none.

Reason:

- filesystem check/stat controls visible output: cached image availability and
  generated age.
- Replacing it with metadata-only behavior requires a new source contract.

Classification: `RISKY`.

Post-Alpha proposal:

- persist generated long-term keogram metadata;
- use metadata first and filesystem as an explicit fallback;
- keep image route behavior unchanged.

## Query / Work Estimate

Static inspection only; no runtime profiler was added.

- Media list: one bounded list query plus per-row serialization. Before this
  pass, many rows also performed duplicate `getUrl()` work for URL and preview.
- Gallery: bounded list query, camera filter query/config matching, optional
  thumbnail lookup per image with thumbnail metadata.
- Gallery page endpoint: bounded cursor query; serializes returned rows.
- Loop: existing loop data endpoint work plus client refresh.
- Dark Library: two calibration queries plus per-row filesystem stat and URL
  helper calls.
- Long Term Keogram: one filesystem image check/stat plus one bounded sample
  query.

## Fixes Not Applied

### Thumbnail Lookup Deferral

Not applied before Alpha.

Reason:

- would change when thumbnails are resolved and may affect visible media cards.

### Loop Endpoint Refactor

Not applied.

Reason:

- user-visible behavior and refresh semantics need dedicated audit.

### Dark Library Metadata-Only Mode

Not applied.

Reason:

- current table displays filesystem-derived size and download links.

### Long Term Keogram Metadata Source

Not applied.

Reason:

- no safe metadata-only source was introduced in this pass.

## Raspberry Manual Test Plan

Recommended manual checks:

- `/modern-admin/media/gallery`
- `/modern-admin/media/images`
- `/modern-admin/media/timelapses`
- `/modern-admin/loop`
- `/modern-admin/cameras/dark-library`
- `/modern-admin/observatory/long-term-keogram`

For each page:

- verify the page renders;
- verify image/media links still open;
- verify gallery camera filters still work;
- verify pagination/load-more behavior still works;
- verify Loop continues cycling frames;
- verify Dark Library still displays size and download links;
- verify Long Term Keogram still displays cached image/age when present.

## Recommendation

Keep the applied media URL reuse and gallery request-cache fixes. They are small,
RPi5-friendly, and preserve output.

Defer Loop, Dark Library, and Long Term Keogram optimization until after Alpha.
Those pages need page-specific contracts rather than broad performance surgery.
