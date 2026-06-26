# HYBRID PORTING GUARDRAILS

Created: 2026-06-26

Scope: mandatory operational checklist for future Classic UI to Modern UI
porting and eventual legacy removal. This document is documentation-only and
does not change runtime behavior.

Related baseline documents:

- `HYBRID_UI_SIMPLIFICATION_PLAN.md`
- `HYBRID_UI_EVIDENCE_MATRIX.md`
- `HYBRID_UI_INVENTORY_REPORT.md`
- `HYBRID_FEATURE_MAP.md`
- `tools/hybrid_ui_ownership_map.json`

## 1. Purpose

This document defines the invariants that must be protected before, during and
after every future UI porting micro-step.

Hybrid AllSky is now modern-first, profile-first, multicamera-first,
scientific-first and explainability-first. Classic UI can only be reduced after
Modern parity is proven. Porting work must not break the Hybrid-specific
systems already built on top of the indi-allsky fork.

Every future porting or removal task must answer:

- Which feature is being touched?
- Is the feature protected, shared, public, external, wrapper-only or
  Classic-only?
- What Modern parity exists?
- What fallback remains?
- What verification proves that protected work still behaves correctly?

## 2. Non-Negotiable Rules

- Do not remove Classic UI before Modern parity exists for the target feature.
- Do not remove public routes or external APIs only because they have no static
  consumer.
- Do not flatten multicamera logic into single-camera assumptions.
- Do not move profile-first configuration back into global-only config.
- Do not bypass Camera Profiles.
- Do not lose metadata, quality, analytics, environmental, event, detector,
  meteor, or scientific-source context.
- Do not replace Modern safe controls with unprotected direct legacy actions.
- Do not remove legacy fallback paths without a rollback plan.
- Do not perform broad refactors during porting.
- Do not mix porting and cleanup/removal in the same commit.
- Do not treat shadow-only Event/Detector/Meteor records as validated events.
- Do not treat JPEG/display/overlay output as detector-grade scientific source.
- Do not sync hardware-specific camera settings across cameras unless explicitly
  proven safe.

## 3. Protected Modern Work Checklist

| Feature | What to verify | Sensitive files/routes/API/config | Possible regression | Recommended check |
| --- | --- | --- | --- | --- |
| Multi-camera | Active cameras remain isolated by `camera_id` and profile. | `MULTI_CAMERA`, `MULTI_CAMERA_CAPTURE_ENABLE`, `capture_profiles.py`, `/modern-admin/cameras`, `/modern-admin/settings/cameras` | Single-camera assumptions, mixed frames, wrong profile save. | Regenerate UI inventory; inspect camera/profile routes; Raspberry smoke if runtime touched. |
| Camera Profiles | Profile fields save to the intended profile. | `MULTI_CAMERA.profiles`, `ModernAdminCameraSettingsView`, `settings_cameras.html` | UI writes global config or wrong profile. | Verify profile_id/camera_id remains visible in changed paths. |
| Profile-first configuration | Profile-owned values override global fallback correctly. | `capture_profiles.py`, `/modern-admin/settings/*`, `/ajax/config` | Runtime returns to global defaults. | Run focused resolver/config tests if touched; inspect ownership map. |
| Auto Exposure | Exposure-first behavior and target ADU remain profile-first. | `auto_exposure_controller.py`, `image.py`, `TARGET_ADU_*`, `AUTO_EXPOSURE_*` | Exposure decisions regress or target ADU becomes global. | Do not touch runtime during UI porting; if config touched, verify resolver tests. |
| Auto Gain | Apply gate, runtime state, mode gates and min/max remain intact. | `auto_gain_controller.py`, `image.py`, `AUTO_GAIN_*`, `GAIN_*`, runtime state | Real gain changes unexpectedly or restore breaks. | Confirm no runtime gain code changed; preserve profile UI fields. |
| Hybrid AWB | Hardware-specific color/debayer fields remain per-camera. | Camera Settings Lens/Optics fields, AWB/CFA/debayer config | Wrong CFA/AWB copied between different sensors. | Verify Save & Sync excludes hardware-specific fields. |
| Metadata | Daily metadata schema remains backward-compatible. | `frame_metadata.py`, `frame_metadata_analytics.py`, `frame_metadata/YYYY-MM-DD.jsonl` | Dashboard/analytics crash or old rows unreadable. | Run frame metadata/analytics tests if touched. |
| Analytics | Dashboard summaries still tolerate one camera/offline/malformed rows. | `/modern-admin`, `modern_admin/index.html`, `frame_metadata_analytics.py` | Modern dashboard 500 or missing camera fallback. | Verify dashboard context tests or manual load when analytics changes. |
| Quality | `quality_score` and `quality_flags` remain optional and metadata-only. | `frame_quality.py`, metadata JSONL, dashboard | Old rows fail or quality becomes image-destructive. | Run quality/metadata tests if touched. |
| Environmental Awareness | Sky/cloud/trend/condensation stay read-only diagnostics. | `sky_condition.py`, `cloud_detection.py`, `sky_trend.py`, `condensation_detection.py` | Runtime decisions are introduced accidentally. | Confirm no capture/exposure/gain code changed. |
| Event Foundation | Candidate/timeline/classification stay shadow-only unless explicitly promoted. | `event_candidate.py`, `detector_result.py`, Event JSONL, dashboard diagnostics | Event candidates become claims or notifications. | Run event tests if touched; confirm no runtime side effects outside configured shadow paths. |
| Scientific Source Layer | Detector/source paths remain raw-first and display images are not promoted. | `frame_metadata.py`, `scientific_frame*.py`, `timeline_frame_set.py`, FITS/RAW config | JPEG/overlay used as scientific source. | Run scientific frame/provider/sequence tests if touched. |
| Detector / Meteor foundations | DetectorResult and MeteorObservation remain contracts, not validated claims. | `detector_result.py`, `meteor_observation.py`, offline bridges/reports | Meteor counts produced without validation state. | Run detector/meteor tests if touched. |
| Modern Admin shell | Modern shell navigation and service controls remain usable. | `/modern-admin`, `_shell_header.html`, `modern-admin.css`, `/modern-admin/capture/service` | Admin entry point or capture controls break. | Load Modern Admin manually if shell/template changes. |
| Modern safe controls | Safe wrappers remain until native Modern parity exists. | `ModernAdminSafeControlsMixin`, `modern_admin/safe_controls.html`, `/modern-admin/tools/*`, `/modern-admin/system/*` | Operational tools disappear before replacement. | Do not remove wrappers in porting commits. |

## 4. Public / External API Guardrails

The following surfaces are not Classic UI dead code:

- Latest endpoints: `/latestimage`, `/latesttimelapse`, `/latestraw`,
  `/lateststartrail*`, `/latestpanorama*`, related watch/view routes.
- Public media routes: `/`, `/index_img`, `/index_canvas`, `/raw*`,
  `/panorama*`, `/images/<path:path>`, `/view_*`, `/watch_*`.
- Sync API: `/sync/v1/*`.
- Action API: `/action/*`.
- Shared AJAX/JSON endpoints: `/ajax/config`, `/ajax/generate`,
  `/ajax/network`, `/ajax/drives`, `/ajax/manual_gpio`,
  `/ajax/status_update`, `/js/charts`, `/js/log`, `/js/focus`,
  `/js/latest`, `/js/loop`, `/js/support`.
- Direct navigation and bookmark routes: any page that users may type,
  bookmark, link externally, or access through reverse proxies.

Rule: absence of a static consumer in `HYBRID_UI_INVENTORY_REPORT.md` is not
evidence that a route is unused.

## 5. Porting Commit Checklist

Before each porting commit:

- Feature target is declared.
- Feature status in `tools/hybrid_ui_ownership_map.json` is checked.
- Ownership map is updated if ownership changes.
- `HYBRID_UI_INVENTORY_REPORT.md` is regenerated if route/template/API/asset
  surfaces change.
- No protected feature has degraded.
- Classic fallback remains in place.
- Modern parity has been verified for the target feature.
- Public/external/shared APIs are not removed.
- Tests or checks relevant to the touched area have been run.
- Rollback path is clear.
- Commit scope is small and limited to one feature/micro-step.

## 6. Removal Commit Checklist

Future removal commits require stricter evidence:

- Modern parity is complete for the target feature.
- Ownership map reflects the new canonical owner.
- Evidence Matrix or inventory report is updated when needed.
- Deprecation/release window has happened when user-facing routes may be used
  externally.
- Public routes and external APIs are excluded unless a compatibility plan
  exists.
- Fallbacks or redirects exist where appropriate.
- Tests pass.
- Manual Raspberry validation is documented when runtime/admin behavior is
  affected.
- Rollback is possible.
- Removal commit does not include unrelated refactor or new features.

## 7. Required Verification Commands

Baseline UI consolidation checks:

```bash
python3 tools/hybrid_ui_inventory.py
python3 -m json.tool tools/hybrid_ui_ownership_map.json >/dev/null
git diff --check
git status --short --untracked-files=all
```

If a Python tooling file changes:

```bash
python3 -m py_compile tools/hybrid_ui_inventory.py
```

If application code is touched, run focused tests that already exist for the
touched area. Examples, if available and relevant:

```bash
python3 testing/frame_metadata_test.py
python3 testing/frame_metadata_analytics_test.py
python3 testing/scientific_frame_test.py
python3 testing/scientific_frame_provider_test.py
python3 testing/scientific_frame_sequence_test.py
python3 testing/timeline_frame_set_test.py
python3 testing/event_candidate_test.py
python3 testing/detector_result_test.py
python3 testing/meteor_observation_test.py
python3 testing/capture_profiles_test.py
```

Do not invent mandatory tests for areas that have no test coverage yet. Mark
those checks as manual or `NEEDS VERIFICATION`.

## 8. When Codex May Commit Automatically

Codex may commit automatically when all are true:

- Scope is documentation, tooling, tests, inventory/report, or a clearly
  bounded requested micro-step.
- Requested verification commands pass.
- No critical warnings are present.
- No unexpected application files are changed.
- No conflict exists.
- No protected feature ownership or runtime behavior is ambiguous.
- The commit includes only files requested by the task.

## 9. When Codex Must Stop

Codex must stop and ask for instructions if any of these occur:

- Unexpected application code changes appear.
- Real route/template/API/UI files are touched outside scope.
- A test or required verification fails.
- A protected feature may be affected and the impact is unclear.
- Runtime behavior cannot be verified but would be changed.
- A removal is needed or implied.
- A broad refactor becomes necessary.
- The change conflicts with profile-first or multicamera principles.
- Public/external/shared API ownership is unclear.
- The worktree contains unrelated files that cannot be confidently ignored.

## 10. First Porting Candidate Recommendation

Recommended first candidate: **Task Queue read-only Modern page**.

Why:

- It is currently `CLASSIC ONLY`.
- It is operationally useful for validating timelapse, background jobs, uploads,
  event tasks and system health work.
- A read-only Modern view is lower risk than config editing or hardware
  controls.
- It does not need to modify capture, camera drivers, exposure/gain, event
  logic, metadata persistence, or external APIs.
- Classic fallback can remain untouched during the first port.

Suggested micro-step:

- Add a Modern read-only Task Queue page or safe diagnostic surface.
- Preserve the Classic `/tasks` page.
- Do not remove DataTables, Classic template, AJAX helpers, or task backend.
- Update ownership map and regenerate inventory report.
- Verify Modern navigation, Classic fallback, and no protected feature
  regression.
