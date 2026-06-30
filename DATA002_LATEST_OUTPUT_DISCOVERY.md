# DATA002 Latest Generated Output Metadata Discovery

## Scope

This is the discovery document for Phase 2 Data 002.

Goal: identify whether the project already contains reliable sources for Latest Generated Output Metadata.

This document does not implement adapters, providers, wiring, routes, UI, preview URLs, media reads, filesystem scans, RAW/FITS reads, download/share behavior, or generation.

Latest Generated Output Metadata means metadata about generated/derived outputs such as timelapse, keogram, startrail, startrail video, mini timelapse, panorama image, and panorama video. It does not mean opening, previewing, downloading, or generating those files.

## Candidate 1: Generated output DB table family

Source:

- `IndiAllSkyDbVideoTable`
- `IndiAllSkyDbMiniVideoTable`
- `IndiAllSkyDbKeogramTable`
- `IndiAllSkyDbStarTrailsTable`
- `IndiAllSkyDbStarTrailsVideoTable`
- `IndiAllSkyDbPanoramaImageTable`
- `IndiAllSkyDbPanoramaVideoTable`

Location:

- `indi_allsky/flask/models.py`

Output types covered:

- Timelapse videos
- Mini timelapse videos
- Keograms
- Startrails
- Startrail videos
- Panorama images
- Panorama videos

Used by:

- Classic latest generated media redirects/watch routes.
- Modern Admin media list/detail pages.
- Modern Admin keogram/startrail/startrail-video/mini-timelapse/panorama pages.
- Generation insertion code through `miscDb`.
- Legacy migration/scanning code that reconstructs DB entries from generated files.

Pros:

- Canonical persisted metadata for generated outputs.
- Covers the main generated/derived media types.
- Contains useful metadata without requiring file reads: `id`, `createDate`, `dayDate`, `night`, `success`, `uploaded`, `camera_id`, `frames`, `framerate`, `fileSize`, `width`, `height`, and selected timing fields for mini timelapse.
- Already used by existing Classic and Modern surfaces.
- Separate table per output type makes type identity explicit.
- Suitable for metadata-only Product UI if a future adapter uses a strict allowlist.

Cons:

- There is no single unified "generated_output" table.
- Every table inherits file/media behavior through `IndiAllSkyDbFileBase`.
- Tables include forbidden fields such as `filename`, `remote_url`, `s3_key`, and `thumbnail_uuid`.
- Existing views often serialize filenames, URLs, preview URLs, or source labels based on storage state.
- A future adapter would need to normalize multiple schemas into one product contract.

Risk:

- Medium.

Suitable for Product UI?

- YES, as a multi-source table family.

Reason:

This is the best source family because it is canonical, persistent, already used, and metadata-rich. It is not safe as raw ORM data. It becomes Product UI suitable only through a future metadata-only adapter that queries one or more specific output tables and exposes only allowlisted fields.

## Candidate 2: `IndiAllSkyDbVideoTable`

Source:

- Timelapse video table.

Location:

- `indi_allsky/flask/models.py`
- `class IndiAllSkyDbVideoTable`

Output types covered:

- Timelapse videos.

Used by:

- `/latesttimelapse`
- `/latesttimelapsewatch`
- Modern Admin Timelapses list.
- Modern Admin Video Detail.
- Timelapse generation insertion via `miscDb.addVideo()`.

Pros:

- Strong metadata source for generated timelapse videos.
- Includes `createDate`, `dayDate`, `night`, `success`, `uploaded`, `framerate`, `frames`, `fileSize`, `width`, `height`, and `camera_id`.
- Already used by latest video routes and Modern media pages.
- Clear output type.

Cons:

- Covers only timelapse.
- Contains forbidden file/storage fields.
- Existing latest routes immediately redirect to URLs or watch pages.
- Modern serializers include filename and media URL fields.

Risk:

- Medium.

Suitable for Product UI?

- YES, but not alone.

Reason:

It is a good source for timelapse metadata, but Latest Generated Output Metadata must cover more than timelapse.

## Candidate 3: `IndiAllSkyDbKeogramTable`

Source:

- Keogram table.

Location:

- `indi_allsky/flask/models.py`
- `class IndiAllSkyDbKeogramTable`

Output types covered:

- Keograms.

Used by:

- `/latestkeogram`
- `/latestkeogramview`
- Modern Admin Keograms page.
- Keogram generation insertion via `miscDb.addKeogram()`.

Pros:

- Canonical metadata table for keograms.
- Includes `createDate`, `dayDate`, `night`, `success`, `uploaded`, `frames`, `fileSize`, `width`, `height`, and `camera_id`.
- Already used by Classic latest and Modern metadata pages.

Cons:

- Covers only keograms.
- Contains forbidden file/storage fields.
- Existing latest routes are media/view oriented.
- Modern Keograms page includes filename/source summaries.

Risk:

- Medium.

Suitable for Product UI?

- YES, but not alone.

Reason:

Good metadata source for keograms, but not a complete latest generated output source by itself.

## Candidate 4: Startrail output tables

Source:

- `IndiAllSkyDbStarTrailsTable`
- `IndiAllSkyDbStarTrailsVideoTable`

Location:

- `indi_allsky/flask/models.py`

Output types covered:

- Startrail images.
- Startrail videos.

Used by:

- `/lateststartrail`
- `/lateststartrailview`
- `/lateststartrailvideo`
- `/lateststartrailvideowatch`
- Modern Admin Startrails page.
- Modern Admin Startrail Videos page.
- Generation insertion through `miscDb.addStarTrail()` and `miscDb.addStarTrailVideo()`.

Pros:

- Canonical metadata for startrail outputs.
- Includes common generated output metadata: dates, night/day, success, uploaded, frames, dimensions, file size, camera id.
- Separates image and video output types.

Cons:

- Two separate tables.
- Both contain forbidden file/storage fields.
- Existing surfaces expose filename/source summaries.
- Latest public routes are redirect/viewer oriented.

Risk:

- Medium.

Suitable for Product UI?

- YES, as part of a multi-source adapter.

Reason:

These are correct sources for startrail output metadata, but they require normalization into a product-level output contract.

## Candidate 5: Panorama output tables

Source:

- `IndiAllSkyDbPanoramaImageTable`
- `IndiAllSkyDbPanoramaVideoTable`

Location:

- `indi_allsky/flask/models.py`

Output types covered:

- Panorama images.
- Panorama videos.

Used by:

- `/latestpanorama`
- `/latestpanoramaview`
- `/latestpanoramavideo`
- `/latestpanoramavideowatch`
- Modern Admin Panorama page.
- Modern Admin Panorama Loop media list.
- Generation/insertion via `image.py`, `video.py`, and `miscDb`.

Pros:

- Canonical metadata for panorama-derived outputs.
- Panorama image table includes capture-like metadata such as exposure, gain, binmode, night, uploaded, exclude, file size, dimensions, and camera id.
- Panorama video table follows the generated video metadata shape.
- Existing Modern pages already treat these as metadata rows.

Cons:

- Not all deployments may enable panorama generation.
- Contains forbidden file/storage fields.
- Existing routes and Modern pages include media URL/filename concepts.

Risk:

- Medium.

Suitable for Product UI?

- YES, as part of a multi-source adapter.

Reason:

Useful source for panorama generated output metadata, but optional and not sufficient as the single source.

## Candidate 6: Mini timelapse table

Source:

- `IndiAllSkyDbMiniVideoTable`

Location:

- `indi_allsky/flask/models.py`

Output types covered:

- Mini timelapse videos.

Used by:

- Modern Admin Mini-Timelapses page.
- Mini timelapse generation insertion via `miscDb.addMiniVideo()`.

Pros:

- Rich metadata for short generated clips.
- Includes `targetDate`, `startDate`, `endDate`, `framerate`, `frames`, `note`, dimensions, file size, success, uploaded, and camera id.
- Good product relevance for highlight-style outputs.

Cons:

- Specialized output type.
- Contains forbidden file/storage fields.
- Existing page includes filename/source summaries.

Risk:

- Medium.

Suitable for Product UI?

- YES, as part of a multi-source adapter.

Reason:

Useful generated output source, especially later for Highlights/Output Detail, but not the primary single source.

## Candidate 7: Modern Admin media list/detail serializers

Source:

- `ModernAdminMediaListView`
- output-specific Modern Admin pages such as Timelapses, Keograms, Startrails, Startrail Videos, Mini-Timelapses, Panorama.

Location:

- `indi_allsky/flask/views.py`

Output types covered:

- Timelapse
- Keogram
- Startrail
- Startrail video
- Mini timelapse
- Panorama image/video through specific pages

Used by:

- Modern Admin media pages.

Pros:

- Existing Modern read-only code already lists generated media metadata.
- Query patterns are bounded by display limits.
- Serializers show which fields users currently see.
- Useful evidence for field naming and product copy.

Cons:

- Not a clean Product UI source.
- Serializers include `filename`, `url`, `preview_url`, and source values derived from `remote_url` / `s3_key`.
- Uses joins and list queries.
- Designed for media browsing, not a single latest generated output contract.

Risk:

- Medium to High.

Suitable for Product UI?

- NO as a source.

Reason:

Good reference implementation for existing metadata surfaces, but too UI/media-oriented for Product UI Data 002. A future adapter should use the underlying DB tables, not these serializers.

## Candidate 8: Classic/public latest generated routes

Source:

- `/latesttimelapse`
- `/latesttimelapsewatch`
- `/latestkeogram`
- `/latestkeogramview`
- `/lateststartrail`
- `/lateststartrailview`
- `/lateststartrailvideo`
- `/lateststartrailvideowatch`
- `/latestpanorama`
- `/latestpanoramaview`
- `/latestpanoramavideo`
- `/latestpanoramavideowatch`

Location:

- `indi_allsky/flask/views.py`
- classes such as `LatestTimelapseVideoRedirect`, `LatestImageViewRedirect`, and their subclasses.

Output types covered:

- Timelapse
- Keogram
- Startrail
- Startrail video
- Panorama image
- Panorama video

Used by:

- Public/latest generated output endpoints.
- Classic latest media navigation.

Pros:

- Proves that latest generated media retrieval already exists.
- Encodes current convention for latest video/image output lookup.
- Uses DB models rather than filesystem scanning for the route lookup.

Cons:

- Oriented to redirect/watch/view behavior.
- Calls URL helpers or redirects to media viewers.
- Uses joins to camera.
- Does not provide a metadata-only contract.
- Does not cover all output types uniformly.

Risk:

- High for Product UI.

Suitable for Product UI?

- NO.

Reason:

These routes answer "open latest media", not "summarize latest generated output metadata". They should not be reused for Data 002 Product UI integration.

## Candidate 9: Task queue records

Source:

- `IndiAllSkyDbTaskQueueTable`

Location:

- `indi_allsky/flask/models.py`
- generation enqueue code in `indi_allsky/capture.py`

Output types covered:

- Generation jobs for timelapse, keogram/startrails, panorama video, and related tasks.

Used by:

- Capture scheduling.
- Task queue/admin surfaces.
- Video/processing workers.

Pros:

- Captures generation intent and job state.
- Contains queue, state, priority, create date, job data, and result.
- Useful later for generation status/readiness.

Cons:

- It is not generated output metadata.
- `data` and `result` can contain action internals or paths.
- A successful task does not necessarily provide the latest product output row.
- Requires interpretation of job payloads.

Risk:

- Medium.

Suitable for Product UI?

- NO for Latest Generated Output Metadata.

Reason:

Task queue is useful for future generation status, but the output metadata source should be the generated output DB table family.

## Candidate 10: Legacy filesystem migration/scanning code

Source:

- file scanning and bulk insertion paths in `indi_allsky/allsky.py`

Location:

- `indi_allsky/allsky.py`

Output types covered:

- Timelapse
- Keogram
- Startrail
- Startrail video
- Panorama video
- Panorama image

Used by:

- Migration/reconstruction of database rows from existing files.

Pros:

- Confirms the DB table family maps to real generated media artifacts.
- Shows historical filename patterns and output type distinctions.
- Demonstrates which tables receive generated output records.

Cons:

- Filesystem-scanning oriented.
- Uses filenames and file mtimes.
- Not appropriate for request-time Product UI.
- Not metadata-only from DB.

Risk:

- High.

Suitable for Product UI?

- NO.

Reason:

Useful discovery evidence only. It must not be used for Product UI runtime data.

## Best Source Decision

There is no single source table for Latest Generated Output Metadata.

Recommended future source: multi-source generated output DB table family.

Tables:

- `IndiAllSkyDbVideoTable`
- `IndiAllSkyDbMiniVideoTable`
- `IndiAllSkyDbKeogramTable`
- `IndiAllSkyDbStarTrailsTable`
- `IndiAllSkyDbStarTrailsVideoTable`
- `IndiAllSkyDbPanoramaImageTable`
- `IndiAllSkyDbPanoramaVideoTable`

Why not a single source:

- Output types are persisted in separate tables.
- No unified product-level generated output table exists.
- Public latest routes and Modern Media pages wrap these tables but mix in URL/filename/preview behavior.
- Task queue records describe generation jobs, not output records.

Why the multi-source table family is best:

- It is canonical and persistent.
- It covers the output types Product UI cares about.
- It contains useful metadata without reading files.
- It is already used by Classic and Modern surfaces.
- It can support a future metadata-only adapter with strict field allowlists.

Important boundary:

This discovery does not propose wiring or adapter implementation. The next phase should audit which subset of output types and fields can be safely normalized into one latest generated output metadata contract.
