# Emergency Product UI Correction

## Summary

This pass corrects the Product UI experience so Hybrid opens as a product-first sky console instead of another Modern/Admin surface.

## Observatory Fix

The likely `/modern-admin/observatory` Internal Server Error was caused by Jinja resolving `attention_items.items` as the Python dictionary method instead of the payload key. The template now uses explicit key access: `attention_items['items']`.

The same safe key-access correction was applied to Product UI templates that iterate payload fields named `items`.

## Now Home

`/modern-admin` now redirects to `/modern-admin/now`, making Now the entry surface for the Hybrid product path.

Now was updated to emphasize:

- current capture and sky status;
- latest frames from up to two available cameras;
- latest generated output metadata;
- source trust;
- Highlights as the next natural step.

## Latest Camera Frames

Now includes a new `latest_camera_frames` view-model section. Runtime wiring is bounded and conservative:

- up to two non-hidden cameras;
- one latest image metadata row per camera;
- existing image URL route only;
- no filesystem scan;
- no `getFilesystemPath()`;
- no RAW/FITS read;
- no media generation;
- fallback frame cards if camera/image/URL metadata is unavailable.

The Product builder remains framework-free. Flask owns URL normalization and injects a sanitized provider.

## Classic / Modern Language

Product UI templates no longer expose "Modern dashboard", "Settings index", "Classic", or "Modern Admin" as primary Product UI language. Classic remains available in backend/runtime; it is not removed.

## Visual Skin

The dedicated Product UI stylesheet now gives the central Product surfaces a stronger Hybrid Sky Console identity:

- compact hero hierarchy;
- latest-camera frame strip;
- darker astro/science console skin;
- clearer status badges;
- less generic Bootstrap/admin card rhythm;
- responsive two-camera layout for desktop and mobile.

## Safety Boundary

This pass does not add:

- POST/fetch/AJAX;
- mutative actions;
- detector/AI/ranking;
- hardware checks;
- filesystem scans;
- RAW/FITS reads;
- media generation;
- new routes.

DATA001-DATA006 integrations remain in place.
