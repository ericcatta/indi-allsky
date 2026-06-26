# HYBRID PORTING PROTOCOL

This document is the operational protocol for the remaining Classic UI to Modern
UI migration in Hybrid AllSky.

It reflects the current repository state after:

- UI audit and evidence baseline.
- Feature ownership mapping.
- Porting guardrails.
- Dynamic porting backlog.
- Modern Task Queue read-only list, usability and detail pages.
- Modern User Management read-only list page.

This protocol is the workflow for future implementation work. It is not another
planning layer and it should not be treated as optional guidance.

## 1. Purpose

Hybrid AllSky is now Modern-first, profile-first, multicamera-first,
scientific-first and explainability-first. Classic UI still exists and still
hosts active functionality, but it is no longer the target operating model.

This protocol exists to:

- migrate Classic functionality into Modern Admin without regressions;
- preserve all protected Modern work already completed;
- avoid accidental removal of shared, public or external surfaces;
- advance one feature by one phase at a time;
- keep every commit small, reversible and verifiable;
- eliminate Classic UI only when the code, inventory and backlog prove that it
  is safe.

The goal is not to remove Classic quickly. The goal is to make Classic
unnecessary, then deprecate it, then remove it safely.

## 2. Source of Truth

Future porting work must use the current repository state as the primary source
of truth. Documentation supports the decision, but code wins when there is a
conflict.

### Source Priority

1. **Current code**
   - Flask routes in `indi_allsky/flask/views.py`.
   - Existing templates under `indi_allsky/flask/templates`.
   - Static assets under `indi_allsky/flask/static`.
   - Current models, queries and backend behavior.

2. **Inventory**
   - `tools/hybrid_ui_inventory.py`
   - `HYBRID_UI_INVENTORY_REPORT.md`
   - These define what currently exists and what is statically linked.

3. **Ownership**
   - `tools/hybrid_ui_ownership_map.json`
   - This defines the feature owner, status, protected state, routes,
     templates, assets, APIs and known gaps.

4. **Backlog**
   - `HYBRID_PORTING_BACKLOG.md`
   - This defines current phase, priority, effort, risk and recommended next
     feature based on the latest completed work.

5. **Guardrails**
   - `HYBRID_PORTING_GUARDRAILS.md`
   - These define invariants and stop conditions. Guardrails override speed.

6. **Feature map and evidence matrix**
   - `HYBRID_FEATURE_MAP.md`
   - `HYBRID_UI_EVIDENCE_MATRIX.md`
   - These explain semantic ownership and repository evidence.

7. **Historical plans**
   - `HYBRID_UI_SIMPLIFICATION_PLAN.md`
   - This remains useful context, but it is not authoritative when the current
     backlog and code disagree.

### Conflict Rule

If backlog, ownership or documentation disagrees with current code:

1. trust the code;
2. update the backlog and ownership map;
3. regenerate the inventory report;
4. continue only after the mismatch is resolved.

## 3. Porting Lifecycle

Every feature must move through the same lifecycle. Phases must not be skipped.

| Phase | Name | Required meaning |
| --- | --- | --- |
| A | Analysis | Feature is understood from current code, Classic behavior, templates, routes, models and risks. |
| B | Read-only | Modern page or surface displays safe data only. No mutation. Classic fallback remains. |
| C | Read-only usability | Modern read-only surface adds filters, search, sorting, status badges or clearer layout. |
| D | Read-only detail | Modern detail/inspection exists for individual records or objects. No mutation. |
| E | Safe actions | Mutative actions exist only when backend contract, permissions, rollback and tests are clear. |
| F | Feature parity | Modern covers all required Classic behavior or explicitly replaces it with accepted behavior. |
| G | Classic deprecated | Classic route/template remains but points users toward Modern, with compatibility preserved. |
| H | Classic removable | Classic route/template/assets can be removed after parity, deprecation and verification. |

### Phase Rules

- A feature in Phase A may only receive analysis or read-only Modern work.
- A feature in Phase B may receive usability work, not actions.
- A feature in Phase C may receive detail/inspection work, not actions.
- A feature in Phase D may receive safe actions only after an explicit backend
  contract review.
- A feature cannot enter Phase E because a Classic mutation exists. The mutation
  must be safe for Modern users, permissioned, reversible where appropriate and
  tested.
- A feature cannot enter Phase F if Classic is still required for expected user
  workflows.
- A feature cannot enter Phase H if it is public, external, shared, bookmarked
  or has unknown external usage.

## 4. Rules

These rules are absolute for future porting work:

- Port one feature and one phase at a time.
- Do not remove Classic before Modern parity exists for the target feature.
- Do not skip read-only phases.
- Do not mix porting and cleanup/removal in the same commit.
- Do not perform broad refactors during porting.
- Do not modify backend behavior unless the current phase explicitly requires
  it.
- Do not add mutative actions without a reviewed backend contract.
- Do not treat a Classic endpoint as dead because static inventory has no
  consumer.
- Do not remove public/latest routes, Sync API, Action API or shared AJAX
  endpoints as part of UI cleanup.
- Do not degrade protected Modern work.
- Do not flatten profile-first or multicamera behavior into global/single-camera
  assumptions.
- Do not bypass Camera Profiles.
- Do not lose metadata, quality, analytics, environmental, event, detector,
  meteor or scientific-source context.
- Do not promote display images, overlays or stretched JPEGs as scientific
  source data.
- Keep Classic fallback available until Phase G or later.
- Keep commits small, scoped and reversible.

## 5. Protected Modern Work

The current ownership map identifies 92 tracked features. The following are
protected or sensitive and must not be degraded by porting:

- Multi-camera
- Camera Profiles
- Profile-first configuration
- Auto Exposure
- Auto Gain
- Hybrid AWB
- Metadata
- Analytics
- Quality
- Environmental Awareness
- Event Foundation
- Scientific Source Layer
- Detector / Meteor foundations
- Modern Admin shell
- Modern safe controls
- Image Capture
- Camera Settings
- Exposure
- Gain
- White Balance / AWB
- FITS Save
- RAW / Source Files
- Mask
- ADU
- SQM
- FITS Image Viewer
- Raw Viewer
- Timelapse
- Latest Raw
- Star Detection
- Event Candidate Triggers
- Event Review
- Scientific Sources
- Quality Scoring
- Metadata Review
- Config Editor
- Logs
- Safe Controls

Protection does not mean all of these are complete. It means they are sensitive
to regressions and must be preserved while porting nearby Classic functionality.

## 6. Feature Selection Algorithm

Future work should not be chosen manually from memory. Selection must be dynamic
and code-state driven.

For every new porting step:

1. Run or inspect the current inventory:

   ```bash
   python3 tools/hybrid_ui_inventory.py
   ```

2. Open `HYBRID_PORTING_BACKLOG.md`.

3. Select the first incomplete feature that:
   - is not blocked;
   - is not public/external/shared-preserve only;
   - has the highest risk/value ratio for read-only progress;
   - can advance exactly one phase;
   - does not require broad backend redesign.

4. Verify the feature against current code:
   - current Classic route/template;
   - current Modern route/template;
   - model/query/API availability;
   - ownership map entries;
   - safe fallback route;
   - protected feature overlap.

5. If code and backlog disagree:
   - update `HYBRID_PORTING_BACKLOG.md`;
   - update `tools/hybrid_ui_ownership_map.json` if ownership changed;
   - regenerate `HYBRID_UI_INVENTORY_REPORT.md`;
   - do not implement app changes until the state is clear.

6. Implement only the next phase for that feature.

7. If the feature hits a local blocker:
   - mark that feature as blocked in `HYBRID_PORTING_BACKLOG.md`;
   - document the blocking condition and the smallest safe unblocker;
   - update `tools/hybrid_ui_ownership_map.json` if ownership/status notes
     changed;
   - regenerate `HYBRID_UI_INVENTORY_REPORT.md` if inventory surfaces changed;
   - continue with the next available feature instead of stopping the whole
     porting effort.

8. Stop only for global blockers:
   - new architecture;
   - new backend contract;
   - database migration;
   - settings redesign;
   - Classic removal/deprecation;
   - Detector, RMS or AI changes;
   - Scientific Source Layer changes;
   - Event Foundation changes;
   - protected-feature regression risk;
   - unresolved auth, permission, secret or destructive-action uncertainty.

9. Update:
   - `HYBRID_PORTING_BACKLOG.md`;
   - `tools/hybrid_ui_ownership_map.json`, if routes/templates/assets/APIs or
     owner/status changed;
   - `HYBRID_UI_INVENTORY_REPORT.md`, if inventory surfaces changed.

10. Verify.

11. Commit.

12. Report the next recommended feature and phase.

### Blocked Feature Policy

A local blocker belongs to one feature. It should not stop the overall porting
program.

When a local blocker is found:

- do not force the implementation;
- do not broaden scope to work around it;
- mark the feature as `BLOCKED` or document the blocked phase in
  `HYBRID_PORTING_BACKLOG.md`;
- record the reason, risk and smallest safe unblocker;
- update ownership notes when useful;
- move to the next incomplete, non-blocked feature.

Examples of local blockers:

- Task Queue retry/cancel/delete lacks a safe user-facing contract;
- Config Restore mutation lacks rollback UX;
- FITS preview/download would require conversion or filesystem policy;
- Notification acknowledge/delete lacks a safe Modern action contract;
- User detail/mutation requires auth field review.

A global blocker stops autonomous porting. Global blockers include new
architecture, backend contracts, database migrations, settings redesign,
Classic deprecation/removal, Detector/RMS/AI work, Scientific Source Layer work,
Event Foundation work, or uncertainty around protected Modern behavior.

## 7. Commit Policy

### Codex May Commit Automatically When

Codex may commit automatically when all of these are true:

- the task scope is clear;
- only the target feature and required inventory/ownership/backlog files are
  touched;
- no protected feature is degraded;
- Classic fallback remains;
- required checks pass;
- no unexpected files appear;
- no test failure occurs;
- no security/privacy/auth uncertainty exists;
- no broad refactor is needed;
- no removal is being performed unless explicitly requested and Phase H
  criteria are met.

### Codex Must Stop When

Codex must stop and ask for instructions when any of these global conditions
occur:

- current code contradicts backlog and the correct update is ambiguous;
- a protected feature may be affected;
- auth, permissions, password, token, API key or secrets handling is unclear;
- tests or required checks fail;
- unexpected files are modified;
- runtime/capture behavior would change outside scope;
- public/external/shared route usage is uncertain and removal is implied;
- implementation requires broad refactor;
- a rollback path is unclear.

If a mutative action or detail phase lacks a safe backend contract for only the
current feature, treat it as a local blocker: mark the feature blocked, document
the reason and continue with the next available feature.

### Commit Shape

Each porting commit should contain:

- one feature;
- one phase;
- the smallest needed code/template changes;
- inventory/ownership/backlog updates when required;
- no unrelated cleanup.

## 8. Backlog Update Policy

After every completed feature phase, update the backlog.

At minimum:

- feature phase;
- feature percentage;
- backlog progress counts;
- project Modern coverage estimate;
- Classic removal readiness estimate;
- blockers discovered or cleared;
- next recommended feature;
- next recommended phase.

Also update:

- `tools/hybrid_ui_ownership_map.json` when ownership, status, routes,
  templates, assets, APIs or notes change;
- `HYBRID_UI_INVENTORY_REPORT.md` whenever route/template/API/asset surfaces
  change;
- `HYBRID_FEATURE_MAP.md` only when semantic ownership changes materially;
- `HYBRID_PORTING_GUARDRAILS.md` only when a new invariant or stop condition is
  learned.

Backlog updates should reflect current code, not desired future state.

## 9. Metrics

These are the official porting metrics.

### Feature Phase

The current phase of a feature: A, B, C, D, E, F, G, H, Preserve or Protect.

### Feature Completion

Estimated completion percentage for a feature. It measures Modern parity and
Classic removal readiness, not line count.

Recommended defaults:

| State | Default percentage |
| --- | ---: |
| Classic-only / Phase A | 0% |
| Unknown / needs verification | 10% |
| Read-only / Phase B | 35% |
| Usability / Phase C | 55% |
| Detail / Phase D | 65% |
| Safe actions / Phase E | 80% |
| Parity / Phase F | 90% |
| Deprecated / Phase G | 95% |
| Removable / Phase H | 100% |
| Preserve/public/external/shared | Count separately |
| Protect/protected Modern work | Count separately |

### Project Modern Coverage

Percentage of tracked features with a Modern or shared active surface. The
current estimate from the dynamic backlog is about **57%**.

### Classic Removal Readiness

Percentage of tracked features that are realistically safe from a Classic
removal perspective. The current estimate is about **35-40%**.

### Backlog Progress

Backlog Progress is a work-progress metric that should increase as micro-steps
complete, even when Project Modern Coverage changes only slightly.

Track at least:

- completed or protected/canonical features;
- in-progress features;
- blocked features;
- preserve/public/shared features;
- phases completed versus phases planned, when this can be estimated cleanly.

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

This metric is intentionally operational. It should be updated from the current
ownership map and backlog, not from the original planning documents.

### Outstanding Blockers

Count and list of blockers that prevent a feature from advancing. Current major
blockers include:

- no safe user-facing Task Queue mutation contract;
- no Modern auth/user mutation policy;
- no external route usage telemetry;
- settings ownership and Basic/Advanced/Developer redesign still incomplete;
- wrapper-only pages still depend on Classic logic;
- detector work blocked pending real outdoor FITS validation.

## 10. Completion Criteria

### Phase F - Feature Parity

A feature can be marked Phase F only when:

- Modern covers all required user workflows;
- Classic is not required for ordinary operation of that feature;
- public/external/shared contracts are explicitly preserved or replaced;
- ownership map marks Modern or shared canonical ownership;
- inventory reflects the current routes/templates/assets;
- tests or manual checks have passed;
- no protected feature regressed.

Phase F cannot be assigned merely because a Modern page exists.

### Phase G - Classic Deprecated

A feature can be marked Phase G only when:

- Phase F criteria are met;
- Classic route/template remains only as compatibility fallback;
- users have a visible path to the Modern replacement;
- removal risks and rollback are documented;
- public/bookmark/external usage has been considered.

### Phase H - Classic Removable

A feature can be marked Phase H only when:

- Phase G criteria are met;
- no required workflow depends on Classic;
- no public/external/shared contract is being removed accidentally;
- ownership and inventory are up to date;
- deprecation window has passed where appropriate;
- rollback or restoration path is clear;
- removal can be made in a small commit.

## 11. Standard Output

Every future feature implementation must report:

- Feature:
- Previous phase:
- New phase:
- Feature completion percentage:
- Project Modern coverage:
- Classic removal readiness:
- Backlog progress:
- Files changed:
- Protected work touched: yes/no
- Classic fallback: kept/changed/removed with reason
- Verification commands:
- Tests run or missing:
- Commit hash:
- Repository status:
- Next feature:
- Next phase:

For blocked work, report:

- blocking condition;
- local or global blocker;
- why it blocks the current phase;
- smallest safe unblocker;
- whether backlog was updated;
- next available feature if the blocker is local.

## 12. Continuous Improvement

The backlog is dynamic. If current code changes the real state, update the
backlog. Do not follow an old plan because it is written down.

Examples:

- If a Modern page already exists but the backlog says Classic-only, update the
  backlog before porting.
- If a Classic mutation is unsafe, stop at read-only/detail and mark the action
  blocked.
- If a route is public/shared/external, mark it Preserve instead of removal
  candidate.
- If a feature turns out to be wrapper-only, do not remove Classic dependencies
  until a native replacement exists.
- If tests are missing, document that and prefer read-only micro-steps.

The protocol should evolve only when actual work reveals a new invariant, stop
condition or metric. Otherwise, future work should be implementation guided by
this protocol and `HYBRID_PORTING_BACKLOG.md`, not more process documents.
