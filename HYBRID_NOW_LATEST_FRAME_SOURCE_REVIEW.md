# HYBRID NOW LATEST FRAME SOURCE REVIEW

## Purpose

Mission 009 investigates the safest future source for real
`latest_frame_summary` data in `NowView`.

This is an analysis-only document. It does not implement a provider, add a
query, expose a route, read image files, scan the filesystem, or change runtime
behavior.

## Current NowView State

`latest_frame_summary` exists in `indi_allsky/product_view_models.py` as a
fake/static, backend-owned contract field.

Current status:

- `safe_preview_url` is `None`.
- `data_status` is `future_backend_contract`.
- no Flask import;
- no database access;
- no filesystem access;
- no RAW/FITS read;
- no media generation;
- no action exposure.

The next real step must preserve those safety properties while adding one
bounded metadata source.

## Candidate Sources

| Candidate | Files / routes | What it provides | Pros | Cons / risks | Suitability |
| --- | --- | --- | --- | --- | --- |
| `IndiAllSkyDbImageTable` bounded latest image query | `indi_allsky/flask/models.py`, `indi_allsky/flask/views.py` helpers such as `get_latest_camera_image()` | image id, `createDate`, dimensions, exposure/gain/binning, night/day, source metadata, camera id | DB-backed, indexed by camera/date, can be limited to one row, no filesystem required for metadata | model methods can expose filename/path if used carelessly; direct use from product builder would couple to Flask/SQLAlchemy | Best future source if wrapped behind a small service/provider |
| Existing `/js/latest` JSON route | `JsonLatestImageView`, `/js/latest` | latest image URL, width, height, message | production-proven latest image behavior | tied to request args, Classic/public AJAX semantics, day/night config branching, filesystem `exists()`/`stat()` in some paths, HTML messages, not product-domain clean | Do not call from NowView; use only as behavior reference |
| Public latest redirects | `/latestimage`, `/latestthumbnail`, `/latestimageview`, related `Latest*Redirect` classes | redirects to latest media URL/view | production-proven public compatibility | redirects/download-like behavior, no product metadata, can expose public URL semantics, not bounded for Now summary | Do not use for NowView provider |
| Modern Admin dashboard latest image context | `ModernAdminView.get_context()`, `get_latest_dashboard_camera_image()`, `get_dashboard_image_url()` | latest image URL, age/status for Modern dashboard | already Modern Admin-oriented; single latest image helper exists | full dashboard context also reads metadata directories, analytics, event files, and up to 500 metadata frames; too broad for Now latest frame | Reuse concepts, not the full dashboard path |
| `TemplateView.latest_image_entry` | `indi_allsky/flask/base_views.py` | last image within 15 minutes for current camera | already runs for many templates; bounded by age | happens inside generic Flask template construction; not product-domain isolated; query is implicit in view lifecycle | Useful reference, not a future contract boundary |
| Thumbnail join | `LatestThumbnailRedirect`, `IndiAllSkyDbThumbnailTable` | possible small preview asset | smaller media target than full image | join complexity; redirect semantics; still URL/download policy; may require thumbnail availability checks | Later preview candidate, not first real metadata step |
| Frame metadata analytics files | Modern dashboard `FrameMetadataAnalytics` path | profile id, exposure/gain, quality metrics, decision reason | rich product-level metadata | reads filesystem-backed metadata directories; current path can load recent frames and latest frames; RPi5/performance concerns | Not for first latest frame provider |

## Models And Fields Found

Primary image model:

- `IndiAllSkyDbImageTable`
- table: `image`
- useful metadata fields:
  - `id`
  - `createDate`
  - `camera_id`
  - `width`
  - `height`
  - `exposure`
  - `gain`
  - `binmode`
  - `night`
  - `adu`
  - `sqm`
  - `stars`
  - `detections`
  - `uploaded`
  - `fileSize`
  - `data`

URL/path-related fields:

- `filename`
- `remote_url`
- `s3_key`
- `thumbnail_uuid`

Relevant model helper:

- `IndiAllSkyDbFileBase.getUrl(s3_prefix='', local=True)`

Important caution: `getUrl()` can produce a relative `images/...` path from
`filename`, or return remote/S3 data. It should only be used behind a sanitizing
provider and URL policy. `getFilesystemPath()`, `validateFile()`, and any file
existence checks should not be used for the first Now provider.

## Existing Latest Image Behavior

### `/js/latest`

`JsonLatestImageView` supports the public/latest image surface. It can query a
latest DB image and return URL, width, and height.

However, the full route also:

- depends on request args;
- performs camera setup;
- includes day/night/capture pause messaging;
- may check local `latest.*` files with `exists()` and `stat()` for focus mode
  or daytime-unsaved images;
- returns UI-facing HTML snippets in messages.

This is useful as a compatibility reference, but not appropriate as the
NowView backend contract.

### Public latest redirects

`LatestImageRedirect` and related classes query latest media and redirect to its
URL.

These routes are externally visible compatibility surfaces. They should not be
called by NowView because they are route-oriented, not product-domain-oriented,
and they do not provide a sanitized metadata summary.

### Modern Admin dashboard

Modern Admin already uses latest image metadata in several places:

- latest image status on the Modern Admin landing context;
- camera cards with latest image age;
- camera runtime pages with latest image age/status.

The useful narrow pattern is:

```text
filter by camera_id
order by image.createDate desc
first row only
format age/status safely
```

The broad dashboard path should not be reused directly because it also reads
metadata/event directories and builds larger chart/card datasets.

## Proposed Bounded Query

The safest future query is a single-row DB lookup on `IndiAllSkyDbImageTable`,
wrapped behind a provider/service that is injected into `build_now_view()` or a
future `build_now_view(provider=...)` boundary.

Conceptual query:

```text
SELECT id, createDate, camera_id, width, height, exposure, gain, binmode,
       night, uploaded, fileSize
FROM image
WHERE camera_id = :active_camera_id
ORDER BY createDate DESC
LIMIT 1
```

Optional bounded freshness:

```text
AND createDate > :now_minus_max_age
```

Recommended initial age window:

- 15 minutes for "current frame" status, matching existing latest behavior; or
- configurable provider parameter with a conservative default.

Recommended output mapping to `latest_frame_summary`:

- `status`: "Latest frame found" / "No recent frame"
- `data_status`: `not_evaluated` or future `available` only after contract
  expansion
- `camera_label`: sanitized current camera label from existing active camera
  context, not from raw config
- `profile_label`: placeholder until profile mapping is explicitly available
- `timestamp`: formatted `createDate`
- `age_label`: formatted from bounded server-side clock
- `image_available`: true only when DB row exists
- `safe_preview_url`: keep `None` in first real metadata provider
- `source_status`: "Metadata row available" / "No recent metadata row"
- `note`: explicit freshness/contract note
- `evidence`: "image.id=<id>, createDate=<timestamp>" style metadata without
  filename/path

## Preview URL Recommendation

Do not add preview URL in the first real provider.

If preview is later added, use a separate review with these requirements:

- no filesystem existence checks;
- no `getFilesystemPath()`;
- no RAW/FITS URLs;
- no absolute path exposure;
- only relative app URLs or already-policy-approved remote URLs;
- validate with the existing `latest_frame_summary.safe_preview_url` guard;
- reject `file:`, `..`, absolute paths, and direct local filesystem strings;
- consider thumbnail-only preview before full image preview.

## Main Risks

### Path exposure

The `filename` column may contain absolute paths. Model helpers can convert
those to relative paths, but this must not leak into the Now payload. The first
real provider should not include `filename` at all.

### Filesystem access

Several existing latest-image paths use `exists()`, `stat()`, `Image.open()`,
`cv2.imread()`, or FITS reads in other contexts. NowView must avoid all of
these for the initial real provider.

### Public/download semantics

`/latestimage`, `/latestthumbnail`, and related routes are compatibility/public
surfaces. Reusing them would mix product summary with redirect/download-style
behavior.

### Query size

Modern dashboard analytics can load many metadata records and read runtime
files. That is not appropriate for the first Now connection on Raspberry Pi 5.

### Flask coupling

The product builder should remain framework-free. A future provider may live at
the Flask/service boundary, but it should return a sanitized plain dict or small
domain object into `build_now_view()`.

### Secrets

Image metadata does not appear to include secrets by default, but the JSON
`data` field is flexible. The initial provider should not dump `data`; it should
whitelist only specific safe fields if any are needed later.

## What Not To Use

Do not use:

- `/js/latest` as a dependency;
- `/latestimage` or redirect routes;
- `/latestthumbnail` until preview policy exists;
- `getFilesystemPath()`;
- `validateFile()`;
- file `exists()` / `stat()` checks;
- RAW/FITS readers;
- `FrameMetadataAnalytics` for the first latest frame connection;
- full Modern Admin dashboard context;
- raw `image.data` dumps;
- raw `filename`;
- absolute paths;
- direct Classic AJAX endpoints.

## Recommended Future Provider Shape

Create a small, testable provider in a future mission:

```text
LatestFrameSummaryProvider
  input:
    active camera id
    optional sanitized camera label
    current time
    max age seconds
    repository callback / query adapter

  output:
    latest_frame_summary dict matching NowView contract
```

The provider should:

- perform at most one bounded query;
- select or map only whitelisted fields;
- never open files;
- never call public latest redirects;
- never return raw filename/path;
- keep `safe_preview_url` as `None` for the first real version;
- return `not_evaluated` / "No recent frame" if no row exists;
- return structured errors as safe notes, not stack traces;
- be unit-testable with fake repository rows.

## Recommendation

Use `IndiAllSkyDbImageTable` via a narrow DB adapter/provider as the first real
latest frame metadata source.

Do not connect the provider directly inside `product_view_models.py`. Keep the
product model framework-free and pass in a sanitized provider result from the
Flask/service boundary.

The first real provider should be metadata-only and should leave
`safe_preview_url` as `None`. Preview routing can come later after a dedicated
URL/thumbnail policy review.

## Next Micro-step Recommended

Mission 010 should add a fake-repository-backed
`LatestFrameSummaryProvider` contract/test, still without Flask runtime or real
DB access.

The provider tests should cover:

- no latest row;
- valid latest row;
- stale latest row;
- repository exception;
- no filename/path leakage;
- no raw `data` dump;
- JSON-safe output;
- `safe_preview_url` remains `None`.

Only after that should a DB-backed adapter be considered.
