# DATA001 Latest Frame Metadata Discovery

## Scope

This is a discovery document for Phase 2 Data 001.

Goal: identify whether the project already contains a reliable source for Latest Frame Metadata.

This document does not define runtime wiring, adapters, routes, UI, media previews, filesystem access, RAW/FITS reads, or image generation.

Latest Frame Metadata means metadata about the latest captured frame, not the image file itself.

## Candidate 1: Image database metadata row

Source: `IndiAllSkyDbImageTable`

Location:

- `indi_allsky/flask/models.py`
- `class IndiAllSkyDbImageTable`

Used by:

- `indi_allsky/flask/base_views.py` latest image entry for template/status context.
- `indi_allsky/flask/views.py` AJAX status latest image metadata.
- `indi_allsky/flask/views.py` Modern dashboard latest camera image helpers.
- `indi_allsky/flask/views.py` camera runtime/status helpers.
- `indi_allsky/capture.py` capture fallback for exposure/gain/binning defaults.
- Multiple image/media routes and legacy latest image paths.

Pros:

- Canonical database record for captured image frames.
- Contains metadata needed for Product UI discovery: `createDate`, `camera_id`, `exposure`, `gain`, `binmode`, `night`, `adu`, `sqm`, `stars`, `detections`, `temp`, `moonphase`, `width`, `height`, `fileSize`, and JSON `data`.
- Indexed around `camera_id` and `createDate`, including `idx_image_createDate_ix`.
- Already widely used by existing Classic, Modern, status, dashboard, capture, and media paths.
- Can support a metadata-only Product UI contract if a later phase uses a strict allowlist.
- Does not inherently require reading image bytes.

Cons:

- The ORM object also contains `filename`, URL-capable fields, and file-oriented behavior through the file base class.
- Existing callers sometimes move from metadata into URL, filesystem, or image-read behavior.
- Raw ORM objects must not be passed directly to Product UI.
- Existing usage is not specifically designed as a Product UI contract.

Risk: Low to Medium.

Suitable for Product UI? YES.

Reason: This is the strongest source because it is canonical, indexed, already used, and contains the metadata needed without requiring image/media reads. The risk is manageable only if a later phase keeps the Product UI payload metadata-only and allowlist-based.

## Candidate 2: Existing Now latest frame provider wiring

Source: `ModernAdminNowView.get_latest_frame_provider()` plus `LatestFrameImageTableRepository`

Location:

- `indi_allsky/flask/views.py`
- `indi_allsky/product_view_models.py`

Used by:

- `/modern-admin/now`

Pros:

- Already shaped for the Product UI.
- Uses a provider/repository boundary.
- Avoids preview URL, filename/path exposure, and filesystem reads in the Product UI contract.
- Has lightweight tests around provider behavior.

Cons:

- This is a runtime wiring/provider pattern, not the underlying source of truth.
- Depends on Flask view context for camera and query construction.
- It already represents an integration decision from earlier work, while this phase is discovery-only.

Risk: Low as evidence, Medium if treated as the source itself.

Suitable for Product UI? NO.

Reason: It is useful evidence that a bounded metadata path is possible, but the actual source remains `IndiAllSkyDbImageTable`.

## Candidate 3: Base template/status latest image entry

Source: `self.latest_image_entry`

Location:

- `indi_allsky/flask/base_views.py`
- `indi_allsky/flask/views.py`

Used by:

- Shared template context.
- AJAX status update.
- Camera/image status text.
- Astrometric, smoke, aurora, and image status rendering paths.

Pros:

- Already obtains a recent image entry for the active camera.
- Uses recent-frame logic in existing request context.
- Supplies metadata fields such as exposure, gain, binning, ADU, SQM, stars, detections, and sensor metadata.

Cons:

- Coupled to Flask view state, camera setup, status rendering, and mixed context generation.
- It is not a standalone source.
- Existing paths around it combine latest frame metadata with status text, configuration, and presentation concerns.
- The source is already an ORM row from `IndiAllSkyDbImageTable`, so this adds an extra layer rather than a cleaner source.

Risk: Medium.

Suitable for Product UI? NO.

Reason: It confirms the database table is reliable, but it is too coupled to request/view status context to be the Product UI source.

## Candidate 4: Modern dashboard latest camera image helpers

Source:

- `get_latest_dashboard_camera_image(camera_id)`
- `get_latest_camera_image(camera_id)`

Location:

- `indi_allsky/flask/views.py`

Used by:

- Modern dashboard camera cards.
- Modern camera/runtime status surfaces.

Pros:

- Simple latest-image lookup pattern.
- Modern Admin already uses it.
- Bounded to one camera and one latest row.
- Confirms `createDate` ordering is the local convention for latest frame retrieval.

Cons:

- Returns raw ORM rows.
- Adjacent code converts rows into URLs/status/previews.
- Lives inside Flask view classes.
- Not a framework-free Product UI source.

Risk: Medium.

Suitable for Product UI? NO.

Reason: Useful as evidence of existing latest-frame behavior, but not clean enough as the source. It should not be reused directly for Product UI metadata.

## Candidate 5: Public latest image routes/endpoints

Source:

- `/js/latest`
- `/latestimage`
- `/latestimageview`
- related latest image redirect/view logic

Location:

- `indi_allsky/flask/views.py`

Used by:

- Public latest image display.
- Latest image redirects.
- Image and histogram viewing paths.

Pros:

- Proven user-facing latest image behavior.
- Already handles latest image availability, URLs, and display paths.

Cons:

- Image-delivery oriented, not metadata-only.
- Uses URL generation and file-oriented behavior.
- Some paths call filesystem/file methods and image readers.
- Higher risk of leaking file/path/media concerns into Product UI.

Risk: High.

Suitable for Product UI? NO.

Reason: These routes answer "show me the image", not "summarize latest frame metadata". They are explicitly out of scope for this phase.

## Candidate 6: Capture runtime latest image fallback

Source: latest DB image used during capture fallback

Location:

- `indi_allsky/capture.py`

Used by:

- Capture startup/runtime fallback for exposure, gain, binning, temperature, and SQM-like values.

Pros:

- Uses the image table metadata for operational decisions.
- Confirms recent latest-frame metadata is trusted by capture code.
- Reads useful metadata fields from the latest image row.

Cons:

- Belongs to capture runtime, not Product UI.
- Tied to camera operation and fallback behavior.
- Not a safe read-only UI source.
- Should not be coupled to Product UI discovery.

Risk: Medium.

Suitable for Product UI? NO.

Reason: It proves metadata usefulness, but it is the wrong layer.

## Candidate 7: Processing latest image helper

Source: `getLatestImage()`

Location:

- `indi_allsky/processing.py`

Used by:

- Processing and calibration paths.

Pros:

- Represents a latest image in processing memory.

Cons:

- Not database metadata.
- Not Product UI oriented.
- Coupled to processing lists and image pipeline state.
- Could imply image data access rather than metadata access.

Risk: High.

Suitable for Product UI? NO.

Reason: This is not a durable metadata source and is the wrong abstraction for Product UI.

## Candidate 8: Product view model static/fake latest frame contract

Source:

- `LatestFrameSummaryProvider`
- `StaticLatestFrameRepository`
- `build_latest_frame_summary()`

Location:

- `indi_allsky/product_view_models.py`
- `testing/product_view_models_test.py`

Used by:

- Product UI NowView contract and tests.

Pros:

- Framework-free contract shape.
- JSON-safe and sanitized.
- Protects against path, secret, callable, and unsafe preview URL payloads.

Cons:

- Static/fake by design.
- Not a real data source.
- Exists to shape payloads, not to discover captured frame metadata.

Risk: Low.

Suitable for Product UI? NO.

Reason: It is a useful contract and safety boundary, but not a source of real latest frame metadata.

## Best Source

Chosen source: `IndiAllSkyDbImageTable`

Why this source:

- It is the canonical persisted metadata record for captured image frames.
- It is already used broadly by Classic, Modern, status, dashboard, capture, and media code.
- It contains the metadata needed for Latest Frame Metadata without requiring image bytes.
- It has indexes involving `camera_id` and `createDate`, making it the most plausible bounded source for a later audit phase.
- Other candidates either wrap this table, mix it with presentation/runtime concerns, or cross into image/file/media behavior.

Important boundary:

This discovery chooses only the best source. It does not recommend or implement wiring, adapters, routes, queries, previews, filesystem access, or Product UI changes.
