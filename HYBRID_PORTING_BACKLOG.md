# HYBRID PORTING BACKLOG

Generated from the current repository state after the completed Modern Task Queue
and Modern User Management read-only micro-steps.

This backlog is intentionally code-state driven. It uses the current Flask routes,
templates, Modern Admin pages, `tools/hybrid_ui_ownership_map.json`,
`HYBRID_UI_INVENTORY_REPORT.md`, `HYBRID_FEATURE_MAP.md`, and
`HYBRID_UI_EVIDENCE_MATRIX.md` as evidence. It does not treat the initial porting
plan as the source of truth.

## 1. Current Porting State

Modern Admin is now the operational center of the project, but Classic UI is
still active and cannot be removed. The real state is mixed:

- Protected Hybrid work is already Modern-first or shared-framework-first.
- Several media, system, observatory and storage surfaces have Modern pages.
- Task Queue has reached read-only list, usability, and detail coverage.
- User Management has reached read-only list and usability coverage.
- Notifications has reached read-only list and usability coverage.
- Multiple system tools are still Modern wrappers over Classic/back-end logic.
- Some important operational pages remain Classic-only.
- Public/latest routes, Sync API, Action API and shared AJAX endpoints are not
  Classic UI cleanup targets.

### Phase Definitions

| Phase | Meaning |
| --- | --- |
| A | No meaningful Modern UI parity; Classic-only or unknown. |
| B | Modern read-only surface exists. |
| C | Modern usability surface exists, but parity/actions/details are incomplete. |
| D | Modern read-only detail/inspection exists. |
| E | Safe Modern actions exist with explicit backend contract. |
| F | Modern parity/canonical behavior exists. |
| G | Classic deprecated but still present. |
| H | Classic removable after verification. |
| Preserve | Public/external/shared surface; not a Classic-removal target. |
| Protect | Protected Modern work; preserve during all porting. |

The percentage is a pragmatic parity estimate for Classic removal readiness, not
a measure of lines of code.

## 2. Executive Summary

### Real Porting Estimate

- Feature map total: 92 tracked features.
- Features with a Modern or shared active surface: about 58%.
- Features that are truly safe from a Classic-removal perspective: about 36-41%.
- Features that are Classic-only or legacy-active: about 12%.
- Features that are wrapper-only: about 7%.
- Features that must be preserved as public/external/shared contracts: about 17%.
- Current Classic UI removability: 0%.

The project is Modern-first, but not yet Modern-only.

### Backlog Progress

Backlog Progress tracks execution progress separately from Modern Coverage. It
should be updated after each micro-step and after each feature is marked blocked
or unblocked.

Current ownership snapshot:

| Category | Count |
| --- | ---: |
| Total tracked features | 92 |
| Protected Modern Work | 21 |
| Modern Canonical | 2 |
| Partial Modern / in progress | 29 |
| Wrapper Only | 8 |
| Public Active | 7 |
| Shared Active | 5 |
| External API | 3 |
| Shared Legacy | 2 |
| Legacy Active | 4 |
| Classic Only | 2 |
| Needs Verification | 9 |

Operational backlog snapshot:

| State | Current examples |
| --- | --- |
| Completed/protected | Multi-camera, Camera Profiles, Metadata, Analytics, Event Foundation, Scientific Source Layer |
| In progress | Task Queue, User Management, Notifications, Config History, Config Restore, FITS Image Viewer, Logs |
| Locally blocked | Task Queue mutations, Config Restore mutation, User Management mutation/detail safety, FITS preview/download/conversion |
| Global blockers | Detector/RMS/AI work, Event Foundation changes, Scientific Source Layer changes, settings redesign, Classic removal |

Local blockers should not stop the overall porting effort. Mark the feature
blocked, document the smallest safe unblocker, and continue with the next
available feature. Stop only for global blockers or protected-feature risk.

### Main Finding

The highest-value remaining work is not raw UI cleanup. It is completing native
Modern parity for the few Classic-only operational pages, while preserving
public/shared endpoints and protected Hybrid features.

## 3. Grouped Backlog

### Already Modern / Protected

These features are ahead of the original simplification plan. Future work should
clarify UX, not replace the underlying architecture.

| Feature | Phase | Real state | Removal rule |
| --- | --- | --- | --- |
| Multi-camera | Protect | Modern/profile-first foundation exists. | Never flatten into single-camera UI. |
| Camera Profiles | Protect | Modern camera/profile settings are canonical. | Do not move profile-owned fields back to global config. |
| Profile-first configuration | Protect | Resolver and Modern settings are active. | Every ported setting must declare ownership. |
| Auto Exposure / Exposure | Protect | Modern/profile-aware runtime exists. | Preserve explainability and profile scope. |
| Auto Gain / Gain | Protect | Modern/profile-aware runtime exists. | Preserve runtime diagnostics and fallback behavior. |
| Hybrid AWB / White Balance | Protect | Modern/profile-aware logic exists. | Preserve camera-specific behavior. |
| Metadata / Analytics / Quality | Protect | Modern dashboard and JSONL analytics exist. | Preserve schema and malformed-row tolerance. |
| Environmental Awareness | Protect | Modern diagnostic context exists. | Keep shadow/read-only semantics. |
| Event Foundation | Protect | Candidate/timeline/classification foundations exist. | Do not add detector behavior during UI porting. |
| Scientific Source Layer | Protect | Raw-first metadata/provider sequence foundations exist. | Do not promote display JPEGs as scientific source. |
| Detector / Meteor foundations | Protect | Domain contracts and offline bridges exist. | Detector work remains blocked pending outdoor FITS validation. |
| Modern Admin shell | Protect | Main operational shell exists. | Keep it as canonical admin surface. |
| Modern safe controls | Protect | Transitional wrappers exist. | Do not remove until native parity exists. |

### Ready for Porting

These have clear value, limited scope, and low-to-medium risk if implemented
read-only first.

| Rank | Feature | Current phase | Next phase | Effort | Risk | Why now |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Notifications | C | D only after notification action review | S | Medium | Read-only usability exists; detail/actions need explicit non-mutative scope. |
| 2 | User Management | C | D only after auth field review | S | High | Read-only usability exists; detail requires careful field/security review. |
| 3 | Logs | D | stop/E only after contract | S | Medium | Modern read-only log detail exists; no new download/action work without contract review. |
| 4 | Task Queue | D | stop/E only after contract | S | High | Detail exists; mutative actions remain blocked. |
| 5 | Image Viewer | C | D | M | Medium | Modern media exists; detail/exclude parity needs careful split. |
| 6 | Video Viewer | C | D | M | Medium | Modern media exists; upload/share parity must be separated. |
| 7 | Timelapse | B-wrapper | C | M | High | Native multicamera generation UX is valuable but riskier. |

### Blocked

The entries below are local blockers unless explicitly marked global. A local
blocker blocks that feature or phase only; it should not stop porting work on
the next available feature.

| Feature | Blocker | Allowed next work |
| --- | --- | --- |
| Meteor Detection (global for detector work) | Real outdoor FITS validation is missing. | Offline reports, validation tooling, documentation. |
| Event Review (global for event UI/action work) | Event review workflow has no UI contract yet. | Architecture/design/read-only evidence browser. |
| Task Queue mutations | No safe user-facing backend contract for retry/cancel/delete/requeue. | No mutation; only diagnostics/detail. |
| Config Restore mutation | Restore is risky without rollback UX. | Read-only restore history/details first. |
| FITS preview/download/conversion | Preview/download requires conversion, filesystem and path policy review. | Metadata-only inspection/detail only. |
| YouTube / OAuth | External auth and upload behavior need safety review. | Read-only provider/status inventory first. |

### Needs Backend First

| Feature | Reason |
| --- | --- |
| Task Queue safe actions | Backend contract is not user-facing safe yet. |
| User role/password management | Auth/security policy must be designed before Modern mutation. |
| Event Review | Needs review/validation domain workflow before UI actions. |
| Detector/Meteor runtime UI | Detector implementation is intentionally not started. |
| Scientific source storage policy | Needs UX/config model for Never/Periodic/Every frame/Event-window buffered. |

### Wrapper Only

These should not be removed. They are transitional.

| Feature | Current wrapper role | Next useful step |
| --- | --- | --- |
| Focus | Modern safe wrapper over Classic tool. | Read-only/native status page before controls. |
| Network | Modern safe wrapper over network manager. | Keep wrapper; high system risk. |
| GPIO | Modern safe wrapper over manual GPIO. | Keep wrapper; hardware action risk. |
| Lens / Image Circle | Modern safe wrapper/reference. | Native read-only helper later. |
| Camera Simulator | Modern safe wrapper. | Low priority. |
| Admin Tools / Safe Controls | Compatibility layer. | Maintain until native pages exist. |

### Public / External / Shared - Not Removal Targets

| Feature | Rule |
| --- | --- |
| Public media endpoints | Preserve; external/bookmark usage is unknowable statically. |
| Latest image/timelapse/raw/startrail | Preserve; not replaced by Modern Admin. |
| Sync API | Preserve as external API. |
| Action API | Preserve as external API. |
| Shared AJAX endpoints | Audit before splitting; some are used by Modern. |
| Authentication | Preserve; not a Classic cleanup target. |
| Vendor JS/CSS | Remove only after templates and runtime loading are verified. |

## 4. Feature Backlog Matrix

| Feature | Owner | Real state | Phase | % | Dependencies | Risk | Effort | Priority | Motivation |
| --- | --- | --- | --- | ---: | --- | --- | --- | --- | --- |
| Multi-camera | modern | PROTECTED MODERN WORK | Protect | 90% | Camera Profiles, profile resolver | Critical | L | Protect | Core architecture; porting must preserve it. |
| Camera Profiles | modern | PROTECTED MODERN WORK | Protect | 90% | Profile-first config | Critical | L | Protect | Canonical configuration model. |
| Profile-first configuration | modern | PROTECTED MODERN WORK | Protect | 90% | Camera Profiles | Critical | L | Protect | Prevents global config regressions. |
| Auto Exposure | modern | PROTECTED MODERN WORK | Protect | 90% | Metadata, profile config | Critical | L | Protect | Runtime behavior must not regress. |
| Auto Gain | modern | PROTECTED MODERN WORK | Protect | 90% | Metadata, profile config | Critical | L | Protect | Runtime behavior must not regress. |
| Hybrid AWB | modern | PROTECTED MODERN WORK | Protect | 90% | Camera-specific settings | Critical | L | Protect | Hardware-specific behavior. |
| Metadata | modern | PROTECTED MODERN WORK | Protect | 90% | Frame metadata JSONL | Critical | L | Protect | Evidence foundation. |
| Analytics | modern | PROTECTED MODERN WORK | Protect | 90% | Metadata | Critical | L | Protect | Modern dashboard core. |
| Quality | modern | PROTECTED MODERN WORK | Protect | 90% | Metadata | Critical | L | Protect | Used by environment/events. |
| Environmental Awareness | modern | PROTECTED MODERN WORK | Protect | 90% | Quality, metadata | Critical | L | Protect | Diagnostic evidence layer. |
| Event Foundation | modern | PROTECTED MODERN WORK | Protect | 90% | Metadata, environment | Critical | L | Protect | Shadow-only event evidence. |
| Scientific Source Layer | shared_api | PROTECTED MODERN WORK | Protect | 90% | FITS/RAW metadata | Critical | L | Protect | Detector-grade input foundation. |
| Detector / Meteor foundations | shared_api | PROTECTED MODERN WORK | Protect | 90% | Scientific sources | Critical | L | Protect | Domain contracts exist; detectors blocked. |
| Modern Admin shell | modern | PROTECTED MODERN WORK | Protect | 90% | Base template, Modern CSS | Critical | L | Protect | Future admin shell. |
| Modern safe controls | modern_wrapper | PROTECTED MODERN WORK | Protect | 90% | Classic tools | Critical | L | Protect | Transitional safety layer. |
| Image Capture | shared_api | MODERN CANONICAL | F | 90% | Capture service | Critical | M | High | Modern owns service controls; runtime shared. |
| Camera Settings | modern | MODERN CANONICAL | F | 90% | Profiles | Critical | L | Protect | Canonical profile settings UI. |
| Exposure | modern | PROTECTED MODERN WORK | Protect | 90% | Auto Exposure | Critical | L | Protect | Same guarded path as auto exposure. |
| Gain | modern | PROTECTED MODERN WORK | Protect | 90% | Auto Gain | Critical | L | Protect | Same guarded path as auto gain. |
| White Balance / AWB | modern | PROTECTED MODERN WORK | Protect | 90% | Hybrid AWB | Critical | L | Protect | Needs explanation, not replacement. |
| Image Save | shared_api | PARTIAL MODERN | C | 55% | Config redesign | Medium | M | Medium | Needs clearer source/display/storage UX. |
| FITS Save | shared_api | PARTIAL MODERN | C | 55% | Scientific source UX | Critical | M | High | Detector-grade persistence needs clear UI. |
| RAW / Source Files | shared_api | PARTIAL MODERN | C | 55% | Scientific source UX | Critical | M | High | Needs source review workflow. |
| Darks | modern | PARTIAL MODERN | C | 55% | Camera/storage pages | Medium | M | Medium | Modern dark library exists; parity needs validation. |
| Bad Pixel Maps | shared_api | NEEDS VERIFICATION | A | 10% | Code/config audit | Medium | M | Medium | Exact UI ownership unclear. |
| Defect Maps | shared_api | NEEDS VERIFICATION | A | 10% | Code/config audit | Medium | M | Medium | Exact UI ownership unclear. |
| Lens / Image Circle | modern_wrapper | WRAPPER ONLY | B | 35% | Safe controls | Medium | M | Medium | Native helper missing. |
| Mask | modern | PARTIAL MODERN | C | 55% | Multicamera mask safety | Critical | M | High | Processing-sensitive; port carefully. |
| ADU | modern | PARTIAL MODERN | C | 55% | Auto exposure/gain | Critical | M | High | Modern history exists; needs clearer UX. |
| SQM | modern | PARTIAL MODERN | C | 55% | Observatory | Critical | M | Medium | Native status limited. |
| Focus | modern_wrapper | WRAPPER ONLY | B | 35% | Safe controls | Medium | M | Medium | Native Modern focus tool missing. |
| Camera Simulator | modern_wrapper | WRAPPER ONLY | B | 35% | Safe controls | Low | L | Low | Low-risk but low-value. |
| Image Lag | modern | PARTIAL MODERN | C | 55% | Camera pages | Medium | M | Medium | Modern page exists; semantics need validation. |
| Image Viewer | modern | PARTIAL MODERN | C | 55% | Media list | Medium | M | Medium | Advanced actions/exclude remain unclear. |
| FITS Image Viewer | modern | PARTIAL MODERN | D | 65% | Scientific source layer | High | M | High | Read-only Modern FITS metadata detail exists; conversion/viewer parity remains Classic-only and locally blocked. |
| Gallery | modern | PARTIAL MODERN | C | 55% | Media list | Medium | M | Medium | Modern gallery exists; PhotoSwipe parity unknown. |
| Panorama | public | SHARED LEGACY | Preserve | 70% | Public endpoints | Medium | M | Medium | Preserve public/latest behavior. |
| Raw Viewer | public | SHARED LEGACY | Preserve | 70% | Raw/source files | Critical | M | Medium | Needs source review, but public routes preserved. |
| Video Viewer | modern | PARTIAL MODERN | C | 55% | Media list | Medium | M | Medium | Upload/share parity unclear. |
| Mini Video Viewer | modern | PARTIAL MODERN | C | 55% | Media list | Low | L | Low | Lower-value parity. |
| Timelapse | modern_wrapper | WRAPPER ONLY | B | 35% | Video queue, media products | Critical | M | High | Native multicamera generation UX missing. |
| Mini Timelapse | classic | CLASSIC ONLY | A | 0% | Timelapse | Low | L | Low | Lower-value legacy product. |
| Keogram | modern | PARTIAL MODERN | C | 55% | Media products | Medium | M | Medium | Generation/status parity needs validation. |
| Startrail | public | PARTIAL MODERN | C | 55% | Media products | Medium | M | Medium | Generation/status parity unclear. |
| Startrail Video | public | PUBLIC ACTIVE | Preserve | 70% | Public endpoints | Critical | XS | Preserve | Not a removal target. |
| Latest Image | public | PUBLIC ACTIVE | Preserve | 70% | Public endpoints | Critical | XS | Preserve | Not a removal target. |
| Latest Timelapse | public | PUBLIC ACTIVE | Preserve | 70% | Public endpoints | Critical | XS | Preserve | Not a removal target. |
| Latest Raw | public | PUBLIC ACTIVE | Preserve | 70% | Public endpoints | Critical | XS | Preserve | Not a removal target. |
| Latest Startrail | public | PUBLIC ACTIVE | Preserve | 70% | Public endpoints | Critical | XS | Preserve | Not a removal target. |
| Public media endpoints | public | PUBLIC ACTIVE | Preserve | 70% | External/bookmarks | Critical | XS | Preserve | Preserve compatibility. |
| Meteor Detection | shared_api | NEEDS VERIFICATION | A | 10% | Outdoor FITS validation | High | L | Blocked | Architecture ready; detector not allowed yet. |
| Star Detection | shared_api | SHARED ACTIVE | Preserve | 70% | Image processing | Critical | XS | Preserve | Shared runtime, not UI cleanup. |
| Event Candidate Triggers | modern | PROTECTED MODERN WORK | Protect | 90% | Event Foundation | Critical | L | Protect | Runtime diagnostics exist. |
| Event Review | modern | NEEDS VERIFICATION | A | 10% | Event review contract | Critical | L | Later | UI workflow not implemented. |
| Scientific Sources | shared_api | PROTECTED MODERN WORK | Protect | 90% | FITS/RAW metadata | Critical | L | Protect | Needs UX/storage policy. |
| Quality Scoring | modern | PROTECTED MODERN WORK | Protect | 90% | Quality | Critical | L | Protect | Protected evidence layer. |
| Metadata Review | modern | PARTIAL MODERN | C | 55% | Metadata analytics | Critical | M | Medium | No row-level browser yet. |
| Config Editor | modern | PARTIAL MODERN | C | 55% | Ajax config, settings redesign | Critical | M | High | Needs Basic/Advanced/Developer redesign. |
| Config History | modern | PARTIAL MODERN | C | 45% | Config DB | High | S | High | Read-only listing and usability filters are now available in Modern. |
| Config Restore | modern | PARTIAL MODERN | D | 65% | Config history, rollback design | High | S | High | Read-only metadata detail exists in Modern; restore action still Classic-only and locally blocked. |
| System Info | modern | PARTIAL MODERN | C | 55% | System pages | Medium | M | Medium | Some actions remain legacy-backed. |
| Logs | shared_api | PARTIAL MODERN | D | 65% | Log APIs | Critical | M | Medium | Read-only detail exists; download parity still uses Classic endpoints. |
| Charts | shared_api | PARTIAL MODERN | C | 55% | Chart APIs | Medium | M | Medium | Legacy chart options may differ. |
| Task Queue | modern | PARTIAL MODERN | D | 65% | Task model | High | S | High | List/usability/detail done; mutations blocked. |
| User Management | modern | PARTIAL MODERN | C | 45% | Auth model | High | S | High | Read-only list usability done; no mutations. |
| Authentication | shared_api | SHARED ACTIVE | Preserve | 70% | Flask login | High | XS | Preserve | Security-critical shared surface. |
| Notifications | modern | PARTIAL MODERN | C | 45% | Notification model/forms | High | S | High | Read-only list usability done; acknowledgement remains Classic/shared. |
| Admin Tools | modern_wrapper | WRAPPER ONLY | B | 35% | Safe controls | Medium | M | Medium | Native pages later. |
| Safe Controls | modern_wrapper | WRAPPER ONLY | B | 35% | Classic tools | Critical | L | Protect | Do not remove. |
| Network | modern_wrapper | WRAPPER ONLY | B | 35% | System/network backend | Medium | M | Medium | High operational risk. |
| Storage / Drives | modern | PARTIAL MODERN | C | 55% | Storage/drive backend | Medium | M | Medium | File space native, drive actions wrapper. |
| GPIO | modern_wrapper | WRAPPER ONLY | B | 35% | Hardware backend | Medium | M | Medium | Hardware risk; keep wrapper. |
| GPS | shared_api | NEEDS VERIFICATION | A | 10% | Sensor/config audit | Low | L | Low | Verify before porting. |
| Sensors | modern | PARTIAL MODERN | C | 55% | Observatory | Medium | M | Medium | Config ownership unclear. |
| Environmental sensors | modern | PARTIAL MODERN | C | 55% | Sensors/weather | Medium | M | Medium | Operational weather awareness incomplete. |
| Power / UPS | shared_api | NEEDS VERIFICATION | A | 10% | Sensor/config audit | Low | L | Low | Verify presence and ownership. |
| Upload | modern | PARTIAL MODERN | C | 55% | Filetransfer providers | Medium | M | Medium | Provider parity unclear. |
| YouTube / OAuth | classic | CLASSIC ONLY | A | 0% | External OAuth | Medium | M | Medium | Modern OAuth missing; risky. |
| Sync API | external_api | EXTERNAL API | Preserve | 70% | External clients | Critical | XS | Preserve | Not UI cleanup. |
| Action API | external_api | EXTERNAL API | Preserve | 70% | External clients | Critical | XS | Preserve | Not UI cleanup. |
| External API clients | external_api | EXTERNAL API | Preserve | 70% | External clients | Critical | XS | Preserve | Not UI cleanup. |
| Classic UI shell | classic | LEGACY ACTIVE | A | 0% | Remaining Classic pages | Low | L | Later | Remove only after parity. |
| Legacy AJAX endpoints | classic | LEGACY ACTIVE | A | 0% | Classic/shared templates | Low | L | Map | Split shared vs legacy later. |
| Shared AJAX endpoints | shared_api | SHARED ACTIVE | Preserve | 70% | Modern/Classic consumers | High | XS | Preserve | Do not remove by static absence. |
| Vendor JS/CSS | shared_api | SHARED ACTIVE | Preserve | 70% | Templates/runtime loading | Medium | XS | Verify | Verify before removal. |
| DataTables | classic | LEGACY ACTIVE | A | 0% | Classic table pages | Low | L | Later | Remove after table parity. |
| PhotoSwipe | classic | LEGACY ACTIVE | A | 0% | Classic gallery | Low | L | Later | Remove after gallery parity. |
| VirtualSky | shared_api | SHARED ACTIVE | Preserve | 70% | Observatory wrapper | Medium | XS | Verify | Modern wraps it. |
| Dynamically loaded assets | known_dynamic | NEEDS VERIFICATION | A | 10% | Runtime loading | Medium | L | Verify | Static analysis limit. |
| Direct navigation routes | known_dynamic | NEEDS VERIFICATION | A | 10% | Bookmarks/users/scripts | High | L | Preserve | Do not remove without telemetry. |
| Bookmark/public routes | public | PUBLIC ACTIVE | Preserve | 70% | External users | Critical | XS | Preserve | Not UI cleanup. |
| Unknown / Needs Verification | known_dynamic | NEEDS VERIFICATION | A | 10% | Static analysis | Medium | L | Verify | Catch-all remains empty/low-use by design. |

## 5. Dynamic Roadmap

This roadmap replaces the initial porting order. It is based on the current code
and the completed Task Queue/User Management work.

### Phase 1 - Finish Safe Read-only Admin Gaps

1. Notifications read-only detail only after notification action review.
2. User Management read-only detail only after auth field review.
3. Config History restore/download parity only after explicit safety review.
4. Config Restore safe actions only after rollback and restore contract review.
5. FITS viewer/conversion/download only after filesystem and path policy review.

### Phase 2 - Complete Read-only Details for Existing Modern Pages

1. Image Viewer media detail.
2. Video Viewer media detail.
3. FITS/source detail.
4. Upload provider status read-only.

### Phase 3 - Native Replacements for Wrappers

1. Focus read-only/native status.
2. Lens/Image Circle native read-only helper.
3. Network status read-only before actions.
4. Drive status read-only before actions.
5. GPIO status read-only before actions.

### Phase 4 - Settings Redesign

1. Define Basic/Advanced/Developer groups.
2. Define profile/global/camera-profile ownership per setting.
3. Add scientific source persistence UX.
4. Keep full settings as Developer fallback.

### Phase 5 - Safe Actions Only Where Backend Contract Exists

1. Do not add Task Queue retry/cancel/delete until backend contract exists.
2. Do not add User Management password/role actions until auth policy exists.
3. Add only actions with rollback, permissions, and Classic fallback.

### Phase 6 - Deprecation and Removal

1. Add Classic-to-Modern links/warnings.
2. Preserve public/latest/external APIs.
3. Remove Classic table pages only after Modern parity and a release window.
4. Remove vendor assets only after runtime loading verification.

## 6. Top 10 Porting Candidates

| Rank | Feature | Next micro-step | Why |
| --- | --- | --- | --- |
| 1 | Notifications | Modern read-only detail/action-safety review | Usability exists; acknowledgement remains out of scope. |
| 2 | User Management | Modern read-only detail field/security review | Usability exists; detail must remain auth-safe. |
| 3 | Logs | Safe action/download contract review only | Detail exists; further work needs explicit backend/download policy. |
| 4 | Image Viewer | Modern read-only media detail | Moves media parity forward without actions. |
| 5 | Video Viewer | Modern read-only media/video detail | Useful before upload/share actions. |
| 6 | Upload | Modern provider status read-only | Avoids touching OAuth/actions first. |
| 7 | Focus | Native read-only focus status | Replaces wrapper slowly, no hardware action. |
| 8 | Config History | Restore/download safety review only | Usability exists; restore/download remain Classic-only. |
| 9 | Config Restore | Restore action contract review only | Metadata-only detail exists; active restore remains blocked. |
| 10 | FITS Image Viewer | Viewer/conversion/download contract review only | Metadata-only detail exists; preview/download/conversion remain blocked. |

## 7. Parallelizable Work

These can proceed in parallel because they touch different surfaces and can stay
read-only:

- Config Restore read-only inspection only.
- Notifications read-only detail/action-safety review.
- FITS/source read-only detail.
- Logs download/detail parity audit.
- Upload provider status read-only.
- Documentation/inventory updates.

Do not parallelize work that touches:

- `AjaxConfigView` save semantics.
- Auth/password/roles.
- Task Queue mutation.
- Capture/runtime controls.
- Public/latest route compatibility.

## 8. True Blockers

1. No safe user-facing Task Queue mutation contract.
2. No Modern auth/user mutation policy.
3. No telemetry proving Classic/public route usage is absent.
4. Settings are still too broad for safe Basic/Advanced/Developer removal.
5. Several Modern pages are wrappers, not native parity.
6. Public/latest routes are externally visible and cannot be inferred dead.
7. Detector work is blocked by real outdoor FITS validation, not UI.

## 9. Answers

### 1. What is the true state of porting today?

Hybrid AllSky is Modern-first, not Modern-only. The Modern Admin shell is broad
and operational, protected Hybrid features are already Modern/shared canonical,
and several Classic-only gaps have started to close. Classic remains required
for notifications, config history/restore, some viewers, OAuth/upload flows,
and several legacy table/action pages.

### 2. Which features are further ahead than expected?

- Task Queue: now at Phase D read-only detail.
- User Management: now at Phase C read-only usability.
- Media lists: broader Modern coverage than the first plan implied.
- Camera/profile/settings work: already canonical Modern/protected.
- Scientific source and detector foundations: architecture is ahead of UI.

### 3. Which features were underestimated?

- Config Restore: it is not just a page; safe restore requires rollback policy.
- FITS Image Viewer: important because it intersects scientific source review.
- Timelapse/media generation: tied to multicamera queue and product semantics.
- Upload/YouTube: external provider/OAuth behavior makes it riskier.
- Public/latest routes: cannot be removed as ordinary Classic pages.

### 4. What are the real blockers?

Safe mutation contracts, auth policy, route-usage uncertainty, settings
ownership clarity, wrapper replacement, and public/external compatibility.

### 5. What is the next feature to port?

Notifications read-only detail/action-safety review.

### 6. Why that feature?

Notifications read-only usability exists, but any detail work must remain
non-mutative and must not acknowledge, delete, create, edit, send or test
notifications.

### 7. Which features can be ported in parallel?

Upload provider status
read-only, and supporting
documentation/inventory updates.

### 8. What percentage is really Modern?

By feature count, roughly 58% has a Modern or shared active surface. By Classic
removal readiness, the safer estimate is 36-41%. By operational center of
gravity, the project is already Modern-first.

### 9. How much remains before Classic UI can be removed?

Substantial work remains. The high-risk remainder is not huge in count, but it
is important: notifications, config history/restore, FITS/source review,
viewer/action parity, upload/OAuth, wrapper replacement, settings redesign, and
public/shared route preservation. Classic UI should not be removed until those
are complete and a deprecation window exists.

## 10. Recommended Next Micro-step

Review whether **Notifications Phase C to D** has a read-only detail step that
can be implemented without acknowledge/delete/edit/create/send/test behavior.
Mark the feature locally blocked if that cannot be guaranteed.

Scope:

- Analyze Classic notification route, `/ajax/notification`, and the existing Modern notifications page.
- Add only read-only detail if it can remain non-mutative.
- Do not add acknowledge, delete, edit, create, send/test, or any notification mutation.
- Preserve Classic fallback.
- Update ownership/inventory.

This is the next smallest useful porting step with the best risk/value ratio.
