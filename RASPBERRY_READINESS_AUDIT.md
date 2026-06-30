# Raspberry Readiness Audit

This audit evaluates whether the repository is ready for a first controlled pull
and test on Raspberry Pi 5 after Product UI v1, DATA001-DATA006, Release
Candidate cleanup audit, and conservative cleanup.

This is an audit only. It does not change code, runtime behavior, routes,
templates, Product Architecture, or deployment state.

## Verdict

READY WITH WARNINGS

The repository is ready for a first controlled Raspberry Pi 5 pull/test if the
pull is treated as an internal validation run, not as a user-facing release.

It is not yet "ready without warnings" because:

- Product UI render behavior has not been browser-verified on the Raspberry;
- query count has not been timed on the Raspberry database;
- only Product View Model tests have been run locally in this audit;
- Moment, Output, Library, and Observatory remain mostly static/fake;
- Classic/public/external route compatibility still depends on preserving the
  existing runtime.

The important point: there is no known blocker that requires more product data
integration before the first Raspberry pull.

## What Is Ready

### Product UI skeleton

The Product UI v1 surface set exists:

- Now;
- Highlights;
- Moment Detail;
- Output Detail;
- Sky Cycle Report;
- Library;
- Observatory.

The Product Architecture remains frozen:

Now -> Highlights -> Moment -> Output -> Sky Cycle -> Library -> Observatory -> Settings -> Developer / Engine Room

### Real bounded data

Bounded metadata integrations are present:

- DATA001: latest frame metadata;
- DATA002: latest generated output metadata;
- DATA003: current capture status;
- DATA004: source trust summary;
- DATA005: Highlights metadata;
- DATA006: Sky Cycle summary.

The integrations remain metadata-only and use allowlisted payloads.

### Safety posture

The Product UI request path intentionally excludes:

- preview URLs;
- media reads;
- RAW/FITS reads;
- filesystem scans;
- detector runtime;
- AI/ranking;
- media generation;
- polling;
- fetch/AJAX on Product UI prototype pages;
- mutative Product UI actions.

### Fallback posture

The DATA integrations use safe fallback behavior:

- missing camera context falls back to not evaluated / unavailable state;
- missing DB rows do not break Product UI rendering;
- query construction failures are caught at the Flask edge;
- product builders validate sanitized payloads before templates render;
- static/fake contract content remains available where real metadata is absent.

## What Is Not Ready

### Not ready as a full Alpha

This is not yet a polished Alpha for broader users.

Missing before broader Alpha:

- Raspberry browser render verification;
- RPi5 render timing and query-count observation;
- documented known limitations;
- smoke test of Product UI routes behind the actual Raspberry service stack;
- confirmation that fallback states are acceptable on a real empty/stale DB;
- explicit operator instructions for rollback.

### Not ready as a replacement for Classic

Classic must remain intact.

The Product UI does not replace:

- Classic config editing;
- media viewers;
- generators;
- public/latest routes;
- sync/action APIs;
- task/log/system operations;
- auth/user behavior;
- hardware/device utility routes.

### Not ready for detector work in request path

Detector work should not be introduced before this Raspberry validation.

Any future detector must be backend-owned, persisted/cached, explainable, and
off the request path.

## Product UI Route Readiness

| Surface | Route | Raspberry readiness | Notes |
| --- | --- | --- | --- |
| Now | `/modern-admin/now` | READY WITH WARNINGS | Most valuable surface; several bounded metadata queries need RPi5 timing. |
| Highlights | `/modern-admin/highlights` | READY WITH WARNINGS | Uses bounded metadata candidates; no detector/AI. Needs real-world empty/stale DB check. |
| Sky Cycle | `/modern-admin/sky-cycle` | READY WITH WARNINGS | DATA006 adds real summary; lower sections remain static/fake. |
| Moment Detail | `/modern-admin/moment` | READY | Static/read-only; no runtime data risk. |
| Output Detail | `/modern-admin/output` | READY | Static/read-only; no preview/media risk. |
| Library | `/modern-admin/library` | READY | Static/read-only; no search/indexing risk. |
| Observatory | `/modern-admin/observatory` | READY | Static/read-only; no hardware/service checks. |

## DATA001-DATA006 Wiring Review

| DATA | Surface | Runtime source | Query/performance risk | Readiness |
| --- | --- | --- | --- | --- |
| DATA001 latest frame metadata | Now | `IndiAllSkyDbImageTable` | Low: bounded latest image query. | Ready. |
| DATA002 latest generated output metadata | Now | generated-output table descriptors | Medium: multiple bounded table queries. | Ready with RPi5 timing warning. |
| DATA003 current capture status | Now | composite metadata/context | Low-medium. | Ready with stale-data warning. |
| DATA004 source trust summary | Now | source metadata descriptors | Medium: bounded metadata checks, no filesystem verification. | Ready with honesty warning. |
| DATA005 Highlights metadata | Highlights | bounded image metadata | Medium: candidate rules are primitive, not detector-backed. | Ready with explanation-quality warning. |
| DATA006 Sky Cycle summary | Sky Cycle | image metadata `dayDate/createDate/night` | Low-medium: latest + cycle-start bounded queries. | Ready with cycle-boundary warning. |

## Fallback If DB Has No Metadata

Expected behavior:

- Now should render with unavailable/not evaluated summaries.
- Highlights should render without real candidate metadata.
- Sky Cycle should render with placeholder/unknown cycle summary.
- Static surfaces should render normally.

Risk:

- Product value will be low on an empty DB, but the page should not fail.
- Some labels may be conservative or repetitive, but that is preferable to
  overclaiming.

Decision:

- acceptable for first Raspberry pull;
- verify explicitly on the device.

## Query / Performance Notes

Estimated Product UI request-path cost:

- Now: several bounded metadata sources.
  - latest frame: one bounded query;
  - latest generated output: multiple bounded descriptor queries;
  - current capture: bounded/contextual metadata;
  - source trust: bounded source metadata descriptors.
- Highlights: one bounded image metadata candidate query path.
- Sky Cycle: two bounded image metadata query paths.
- Moment/Output/Library/Observatory: static Product View Model construction.

Expected RPi5 risk:

- low for static pages;
- low-medium for Sky Cycle;
- medium for Now because it aggregates multiple DATA providers;
- medium for Highlights if candidate query grows later.

Required Raspberry observation:

- time `/modern-admin/now`;
- time `/modern-admin/highlights`;
- time `/modern-admin/sky-cycle`;
- confirm no visible timeout or heavy CPU spike;
- confirm query count does not grow with total media volume beyond bounded
  expectations.

## Import / Runtime Risk

Known good signs:

- Product builders remain framework-free.
- Flask creates providers/adapters at the edge.
- Product payloads are validated.
- Product View Model tests pass locally.

Residual risks:

- Flask `views.py` is still large and imports many concerns.
- Some DB model imports may be heavier on Raspberry than on the local machine.
- Real DB schema/version on Raspberry must match expected model fields.
- Missing optional dependencies could affect unrelated Classic/Modern pages.

Decision:

- acceptable for controlled pull;
- not acceptable for unattended release without service-level smoke tests.

## Filesystem / Media / RAW/FITS Boundary

The Product UI data integrations are designed not to:

- call filesystem helpers;
- open files;
- call `exists()` / `stat()`;
- call media serializers that expose URLs;
- read images/media;
- read RAW/FITS;
- generate outputs;
- expose preview URLs.

Audit grep during readiness found Product UI prototype templates and
`product_view_models.py` still aligned with this boundary. Mentions of
`safe_preview_url` remain null/validation-only.

## POST / Fetch / AJAX / Mutation Boundary

Product UI prototype surfaces remain read-only.

No new Product UI prototype behavior should:

- submit forms;
- call POST;
- call fetch/AJAX;
- execute safe actions;
- mutate config/runtime/media.

Existing non-Product UI Classic/Modern/system routes may still have POST/action
behavior, but they are outside this Product UI readiness decision and were left
untouched.

## Classic Separation

Classic is intentionally preserved.

For Raspberry pull, this is a strength, not a weakness:

- existing operators keep fallback functionality;
- public/latest/media routes remain compatible;
- config/generation/system tools remain available;
- Product UI can be tested without replacing operational Classic behavior.

Risk:

- Product UI and Classic coexist, so navigation and user expectations must be
  tested carefully.

Decision:

- keep Classic untouched for the first pull.

## Minimal Documentation For Pull

Before the Raspberry pull, prepare a short operator note with:

- target branch/commit;
- expected Product UI routes to test;
- known limitations;
- no detector/AI/media preview claims;
- rollback command plan;
- logs to inspect if pages fail;
- explicit instruction not to remove Classic.

This can be a small release note. It does not need a full user manual.

## Checklist Before Pull

Minimum local checklist:

- repository clean;
- latest commit recorded;
- Product View Model tests pass;
- Hybrid UI inventory runs;
- `py_compile` passes for key files;
- ownership map JSON validates;
- no untracked bytecode/cache;
- no pending generated report diffs;
- Raspberry target branch/commit selected.

Recommended local commands before pull:

```bash
git status --short --untracked-files=all
python3 testing/product_view_models_test.py
python3 tools/hybrid_ui_inventory.py
python3 -m py_compile indi_allsky/flask/views.py indi_allsky/product_view_models.py testing/product_view_models_test.py tools/hybrid_ui_inventory.py
python3 -m json.tool tools/hybrid_ui_ownership_map.json >/dev/null
git diff --check
git diff --cached --check
```

Recommended quick grep before pull:

```bash
rg -n "fetch\\(|/ajax/|<form|method=|POST" indi_allsky/flask/templates/modern_admin/now.html indi_allsky/flask/templates/modern_admin/highlights.html indi_allsky/flask/templates/modern_admin/sky_cycle.html
rg -n "open\\(|getFilesystemPath|getRelativePath|getUrl|exists\\(|stat\\(" indi_allsky/product_view_models.py
```

## Checklist After Pull On Raspberry

Do not start with broad exploration. Validate the smallest safe path first.

Recommended sequence:

1. Record current Raspberry commit before pull.
2. Pull/checkout the target commit.
3. Restart only the expected application service if needed.
4. Open `/modern-admin/now`.
5. Open `/modern-admin/highlights`.
6. Open `/modern-admin/sky-cycle`.
7. Open static surfaces:
   - `/modern-admin/moment`;
   - `/modern-admin/output`;
   - `/modern-admin/library`;
   - `/modern-admin/observatory`.
8. Confirm Classic still opens.
9. Confirm public latest route still opens.
10. Watch application logs for raw exceptions.
11. Note render time and CPU feel for Now/Highlights/Sky Cycle.
12. If any Product UI page fails, do not continue adding data; rollback.

Suggested Raspberry smoke commands, adjusted to the local service setup:

```bash
git rev-parse --short HEAD
git status --short --untracked-files=all
python3 testing/product_view_models_test.py
python3 -m py_compile indi_allsky/flask/views.py indi_allsky/product_view_models.py
```

Use browser validation for actual route rendering because local Flask/service
setup can differ across Raspberry installations.

## Rollback Plan

Before pull:

1. Record the current Raspberry commit:

```bash
git rev-parse --short HEAD
```

2. Record service state and any local modifications:

```bash
git status --short --untracked-files=all
```

3. Do not pull over uncommitted local changes.

If Product UI fails after pull:

1. Capture the failing route, stack trace, and current commit.
2. Stop testing new surfaces.
3. Return to the previous known-good commit/branch.
4. Restart the application service.
5. Re-open Classic and the previous working page.

Rollback should prefer the repository's existing operational practice. If the
deployment uses direct git checkout, the previous commit recorded before pull is
the rollback target.

Do not run destructive cleanup during rollback. The goal is to restore the
previous runtime, not to repair the repo interactively on the Raspberry.

## Stop Conditions

Stop the Raspberry test and rollback if:

- `/modern-admin/now` raises a server error;
- Product UI pages block Classic/public routes;
- application logs show repeated DB/model import failures;
- Now render time is clearly unacceptable on RPi5;
- any Product UI route attempts filesystem/media/RAW/FITS access unexpectedly;
- any Product UI route exposes raw filenames/paths/URLs unexpectedly;
- Classic config/media routes regress;
- public/latest routes regress.

## Final Decision

READY WITH WARNINGS.

Proceed with a first controlled Raspberry Pi 5 pull/test only after recording
the current Raspberry commit and preparing rollback.

Do not add detector, AI, preview, media reads, filesystem checks, or additional
DATA integrations before this device validation.

The purpose of the pull is to answer one question:

Can the Product UI v1 plus DATA001-DATA006 render safely and responsively on the
actual Raspberry Pi 5 environment while Classic remains intact?
