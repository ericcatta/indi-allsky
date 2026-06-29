# HYBRID NOW CURRENT PHASE SOURCE REVIEW

## Purpose

Mission 015 investigates whether `NowView` can receive a real
`current_phase_summary` using only light, already-available runtime context.

This is analysis-only. It does not implement the provider, modify runtime code,
add queries, read files, call APIs, or change Classic behavior.

## Desired Product Field

`current_phase_summary` should eventually answer:

- is the current sky phase day, twilight, night, or unknown?
- is capture expected to be day/night behavior?
- is the answer bounded and trustworthy?

For NowView, the product value is high: the top of Now should immediately tell
the operator what kind of sky state they are looking at.

## Candidate Sources Found

| Candidate | Location | Available now? | Pros | Cons | Recommendation |
| --- | --- | --- | --- | --- | --- |
| `context['night']` from `TemplateView.get_context()` | `indi_allsky/flask/base_views.py` | yes, after `super().get_context()` | already computed during normal template context build; no new query; no filesystem; no extra astronomy call | only binary day/night; no twilight; name is "night" not product language | Best first runtime source if scoped to day/night/unknown |
| `self.night` on the view instance | `BaseView.get_astrometric_info()` sets it | yes, after `get_astrometric_info()` has run | already in memory after `TemplateView.get_context()`; no extra query | default starts as `True`; unsafe before astrometric info runs; no twilight | Usable only after `super().get_context()` |
| `get_astrometric_info()` return dict | `indi_allsky/flask/base_views.py` | computed during `TemplateView.get_context()` but not retained directly | contains `mode`, `sun_alt`, moon phase, next rise/set, twilight times | local `status_data` is not exposed; calling again would duplicate ephem work in request | Do not call again in Mission 016 |
| `sun_alt` from astrometric info | `get_astrometric_info()` | computed but not stored for Now | could support twilight classification | not available after `super().get_context()` unless refactored; extra call would add duplicate calculations | Future contract candidate, not first step |
| camera `nightSunAlt` | `self.camera.nightSunAlt` | yes | explains threshold for night | not enough without current sun altitude; raw camera setting should not be product truth alone | Do not use alone |
| capture flags | `self.daytime_capture`, `self.daytime_capture_save`, `self.capture_pause` | yes after `cameraSetup()` | useful for capture behavior notes | not sky phase; tells policy, not astronomy | Use later as supporting context, not phase source |
| latest image `night` field | `IndiAllSkyDbImageTable.night` | available only via DB row | real frame context | would add/extend DB dependency and may describe latest frame, not current sky | Do not use for current phase now |
| Modern dashboard metadata | `FrameMetadataAnalytics` and dashboard helpers | available via filesystem metadata reads | rich operational context | file-backed, heavier, not needed for phase | Do not use |

## Relevant Code Paths

### `BaseView.cameraSetup()`

`cameraSetup()` initializes:

- `self.camera`
- `self.daytime_capture`
- `self.daytime_capture_save`
- `self.capture_pause`
- `self.camera_now`
- sun-set date helper state

This happens during `TemplateView.__init__()`.

### `TemplateView.__init__()`

`TemplateView` calls:

```text
setupSession()
cameraSetup()
check_config(...)
self.night = True
latest image query
```

Important caveat: `self.night` is initialized to `True` before astrometric
calculation. It is not reliable until `get_astrometric_info()` runs.

### `TemplateView.get_context()`

`TemplateView.get_context()` calls:

```text
get_indi_allsky_status()
get_camera_info()
get_astrometric_info()
get_smoke_info()
get_aurora_info()
get_image_data()
```

Then it sets:

```python
context['night'] = int(self.night)
```

Therefore `context['night']` is the safest already-available current phase
input for Now, but only as a binary day/night flag.

### `BaseView.get_astrometric_info()`

This method computes:

- latitude/longitude/elevation;
- `sun_alt`;
- moon altitude/phase;
- `mode`: `Day` or `Night`;
- `self.night`;
- next mode change;
- rise/set and astronomical twilight times.

It uses `ephem`, but it is already part of normal template context generation.
The risk is not that one call exists; the risk would be calling it again just
for Now.

## Safety Evaluation

### RPi5 Risk

Low if Mission 016 uses only `context['night']` after `super().get_context()`.

Medium if Mission 016 calls `get_astrometric_info()` again. The calculation is
not enormous, but repeating it per Now request is unnecessary and violates the
"already available" constraint.

High if Mission 016 reads metadata files, queries DB, or performs new
astronomy calculations outside the existing context flow.

### Coupling Risk

Low for a context-only provider:

```text
Flask view extracts context['night'] -> provider maps to product summary ->
build_now_view(...)
```

Medium if provider reads `self.camera`, `self.indi_allsky_config`, or calls
`get_astrometric_info()` directly.

High if `product_view_models.py` imports Flask, ephem, models, or config.

### Wrong Data Risk

Main risk: overclaiming.

`context['night']` can safely support:

- `day`
- `night`
- `unknown`

It cannot safely support:

- civil twilight;
- nautical twilight;
- astronomical twilight;
- dawn/dusk nuance;
- sun altitude display.

Do not label twilight until a real `sun_alt` or phase classification is
available in a sanitized context.

### Product Language Risk

The UI should not say "night mode" as the whole product concept. It should use:

- "Current phase: Day"
- "Current phase: Night"
- "Phase not evaluated"

and avoid raw variables like `night=1`.

## Recommendation

Recommendation: implement a context-provider lightweight step, but only for
binary day/night/unknown.

Do not implement full `day / twilight / night` classification yet.

The safest Mission 016 should:

1. add a framework-free `CurrentPhaseSummaryProvider` or equivalent contract;
2. accept only sanitized input such as `night_flag`;
3. map `0 -> day`, `1 -> night`, anything else -> unknown;
4. keep `twilight` unavailable/not evaluated;
5. inject it from `ModernAdminNowView` using `context.get('night')` after
   `super().get_context()`;
6. avoid calling `get_astrometric_info()` again;
7. avoid reading raw config or camera settings;
8. avoid DB/filesystem/network/media access.

This improves Now honestly without pretending the project has a complete phase
engine yet.

## What Not To Implement Yet

Do not:

- call `get_astrometric_info()` a second time;
- add new ephem calculations in request;
- expose latitude/longitude;
- expose raw sun altitude unless a product contract is reviewed;
- compute twilight from scratch;
- use latest image `night` as current sky truth;
- read frame metadata files;
- query DB;
- add polling or frontend logic.

## Proposed Mission 016

Mission 016 should be:

```text
Add bounded current phase summary contract to NowView
```

Scope:

- add `current_phase_summary` to NowView contract;
- add tests for day/night/unknown mapping;
- add a context-only provider/factory;
- wire `context['night']` from `ModernAdminNowView` after `super().get_context()`;
- leave twilight as `not_evaluated`;
- update Now template to render the new product summary;
- no new DB query;
- no filesystem;
- no new astronomy calculations;
- no config dump;
- no route/API changes.

If the implementation discovers `context['night']` is not reliable in a real
view path, Mission 016 should stop and keep the phase as unknown.

## Final Verdict

There is a safe source, but it is narrower than the ideal product field.

Use it for a truthful, bounded first step:

```text
day / night / unknown
```

Do not claim twilight until the backend exposes a sanitized phase classifier or
retains `sun_alt` from the existing astrometric calculation in a product-safe
view model.

## Mission 016 Update

`current_phase_summary` has been added to the NowView contract using only the
existing `context['night']` value after `TemplateView.get_context()`.

The implementation intentionally supports only:

- `night == 0` -> `day`
- `night == 1` -> `night`
- missing or unexpected values -> `unknown`

Twilight remains explicitly unsupported and `not_evaluated`. No additional
astronomical calculation, database query, filesystem access, network call, media
generation, or runtime camera check was introduced.
