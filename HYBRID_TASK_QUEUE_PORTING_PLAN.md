# HYBRID TASK QUEUE PORTING PLAN

## 1. Current State

The Task Queue now exists in two UI surfaces:

| Surface | Route | Template | Status |
| --- | --- | --- | --- |
| Classic Task Queue | `/tasks` | `indi_allsky/flask/templates/taskqueue.html` | Legacy read-only table with DataTables search/export |
| Modern Task Queue | `/modern-admin/tasks` | `indi_allsky/flask/templates/modern_admin/tasks.html` | Modern read-only diagnostics with client-side filters |

The Classic page remains active and must remain the fallback until Modern parity is complete. The Modern page is intentionally diagnostic-only. It does not mutate task state, does not call task action endpoints, and does not replace the Classic route.

## 2. Existing Classic Behavior

Classic `/tasks` is implemented by `TaskQueueView` in `indi_allsky/flask/views.py`.

Current behavior:

- requires `login_required`;
- queries `IndiAllSkyDbTaskQueueTable`;
- limits visible rows to tasks created within the last three days;
- includes states `MANUAL`, `QUEUED`, `RUNNING`, `SUCCESS`, and `FAILED`;
- excludes queues `IMAGE` and `UPLOAD`;
- orders by `createDate` descending;
- normalizes each row to `id`, `createDate`, `queue`, `state`, `action`, and `result`;
- renders `taskqueue.html`;
- uses DataTables for browser-side search, ordering, length selection, copy, CSV, and Excel export.

Classic `/tasks` does not currently expose retry, cancel, delete, requeue, clear completed, or task detail actions.

## 3. Existing Modern Behavior

Modern `/modern-admin/tasks` is implemented by `ModernAdminTaskQueueView` in `indi_allsky/flask/views.py`.

Current behavior:

- inherits the same read-only query scope from `TaskQueueView`;
- uses the Modern Admin shell and navigation;
- displays up to 200 newest rows for readability;
- shows `id`, created timestamp, relative age, update timestamp if available, queue, action, state, camera, profile, and message/result;
- provides client-side search and filters for state, queue, and action;
- shows visual state badges;
- shows a Classic fallback link to `/tasks`;
- performs no POST, no fetch, no AJAX mutation, no delete, no retry, no cancel, and no edit action.

## 4. Backend Model and Data

Task queue persistence is defined by `IndiAllSkyDbTaskQueueTable` in `indi_allsky/flask/models.py`.

Fields:

| Field | Type / meaning | Notes |
| --- | --- | --- |
| `id` | integer primary key | Stable row identifier |
| `createDate` | datetime | Creation timestamp; indexed |
| `state` | enum `TaskQueueState` | Indexed |
| `queue` | enum `TaskQueueQueue` | Indexed |
| `priority` | integer nullable | Lower value is higher priority |
| `data` | JSON | Action payload; structure varies by producer |
| `result` | string nullable | Final or failure message |

States from `TaskQueueState`:

- `MANUAL`
- `QUEUED`
- `RUNNING`
- `SUCCESS`
- `FAILED`
- `EXPIRED`

Queues from `TaskQueueQueue`:

- `IMAGE`
- `VIDEO`
- `UPLOAD`
- `MAIN`

State mutation helpers exist on the model:

- `setQueued()`
- `setRunning()`
- `setSuccess(result)`
- `setFailed(result)`
- `setExpired()`

These helpers commit immediately. They are used by runtime workers and controllers, not exposed as user-facing task management APIs.

Known task producers include:

- `indi_allsky/capture.py`: timelapse, keogram, startrail, upload, expire-data, set-location tasks;
- `indi_allsky/flask/views.py`: config reload, system backup, expire data, manual generation, upload actions;
- `indi_allsky/flask/actionapi_views.py`: pause/unpause tasks;
- `indi_allsky/image.py`, `indi_allsky/miscUpload.py`, `indi_allsky/uploader.py`, `indi_allsky/video.py`: upload and media processing tasks;
- `indi_allsky/allsky.py`: manual task promotion, orphan expiration, old task flushing, periodic system tasks.

## 5. Existing Mutations

| Action | Exists in Classic? | Endpoint | Method | Backend function | Permissions | Risk | Portable now? | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Inspect details | Partial | `/tasks` | GET | `TaskQueueView.get_context()` | `login_required` | Low | Yes, read-only | Current table only shows a subset of `data`; a Modern detail page could show sanitized JSON. |
| Filter/search | Yes | `/tasks` | GET + client-side DataTables | DataTables only | `login_required` | Low | Done | Modern already has client-side search/filter. |
| Export visible rows | Yes | `/tasks` | Browser-side DataTables buttons | DataTables copy/CSV/Excel | `login_required` | Low | Safe later | Browser-only export is read-only, but should be implemented as a Modern export pattern shared with other tables. |
| Retry failed task | No | None found | N/A | None found | N/A | High | No | Would require cloning or requeueing payload safely. Existing backend does not distinguish retryable actions. |
| Cancel queued task | No | None found | N/A | None found | N/A | Medium/High | No | Could race with `allsky.py` promoting `MANUAL` to `QUEUED` or workers selecting `QUEUED`. Needs atomic state transition. |
| Cancel running task | No | None found | N/A | None found | N/A | High | No | Workers do not expose cooperative cancellation. Marking DB state would not stop subprocesses or uploads. |
| Delete task row | No | None found | N/A | `_flushOldTasks()` deletes old rows internally | Runtime/internal | Medium | No | Manual deletion could hide active diagnostics and race with workers. |
| Clear completed | No | None found | N/A | `_flushOldTasks()` deletes rows older than three days | Runtime/internal | Medium | No | Existing cleanup is age-based, not user-triggered. |
| Requeue task | No | None found | N/A | `setQueued()` exists as low-level helper | Runtime/internal | High | No | Directly setting `QUEUED` bypasses validation and may duplicate side effects. |
| Expire task | Internal only | None for user task management | N/A | `setExpired()`, `_expireOrphanedTasks()` | Runtime/internal | Medium | No | Used for orphan/duplicate task handling, not user cancel. |
| Download/export logs | Not task-specific | Log routes exist separately | GET | `LogDownloadView` and related log views | `login_required` | Low | Safe later as link only | Not attached to a specific task ID today. |

## 6. Missing Backend Support

The backend does not currently provide safe task-management APIs for:

- retrying failed tasks;
- canceling queued tasks atomically;
- canceling running tasks cooperatively;
- deleting a single task row from the UI;
- clearing completed rows from the UI;
- requeueing a task with validation;
- marking a task as user-canceled;
- viewing full task details through a dedicated route;
- exporting a task-specific log bundle.

The model has state mutation helpers, but those helpers are too low-level to expose directly. They do not validate task ownership, queue compatibility, action retryability, current worker state, or side effects.

## 7. Safe Modern Actions Candidate

### Safe Now

These are read-only and can be implemented without task mutation:

- dedicated task detail page;
- sanitized JSON view of `task.data`;
- explicit task scope notes;
- copy/export of currently visible table rows;
- links to relevant logs or Classic fallback;
- server-side detail lookup by `id` with `login_required`.

### Safe Later

These need more validation and tests before implementation:

- browser-side CSV export in Modern style;
- task-specific log correlation links;
- read-only task payload diff/inspection;
- refresh control that reloads the page only;
- safe action availability indicators, without executing actions.

### Dangerous / Not Now

These should not be ported until dedicated backend semantics exist:

- retry;
- requeue;
- cancel queued;
- cancel running;
- delete task;
- clear completed;
- expire task from UI;
- edit task payload;
- mutate queue, priority, state, or `data` directly.

## 8. Recommended Task Queue Roadmap

| Phase | Status | Goal |
| --- | --- | --- |
| Phase A | Done | Add read-only Modern Task Queue page. |
| Phase B | Done | Add read-only usability parity: search, filters, badges, limits, fallback. |
| Phase C | Next | Add safe task detail/inspection, read-only only. |
| Phase D | Later | Add safe mutations only if backend supports validated, atomic task transitions. |
| Phase E | Later | Reach full Modern parity where appropriate. |
| Phase F | Later | Deprecate Classic `/tasks` after Modern parity and field validation. |
| Phase G | Later | Remove Classic task queue only after deprecation, rollback plan, and no external usage concerns. |

## 9. Guardrails

Task Queue porting must not break:

- Classic `/tasks`;
- `IndiAllSkyDbTaskQueueTable`;
- task producers in capture, upload, video, action API, and system views;
- `allsky.py` manual task promotion;
- worker selection of `QUEUED` tasks;
- upload queue processing;
- video queue processing;
- capture pipeline;
- scheduler and periodic tasks;
- external/internal producers that create task rows directly;
- Modern Admin shell;
- Modern safe controls;
- public/latest endpoints;
- Sync API;
- Action API;
- profile-first and multi-camera behavior.

Any future mutation must be:

- explicit;
- authenticated;
- ideally admin-restricted where appropriate;
- atomic against expected current state;
- queue-aware;
- action-aware;
- logged;
- reversible or recoverable;
- tested against worker race conditions.

## 10. Recommended Next Micro-Step

The safest next step is:

**Add a read-only Modern task detail page.**

Suggested route:

- `/modern-admin/tasks/<task_id>`

Suggested behavior:

- GET only;
- `login_required`;
- reuse `ModernAdminContextMixin`;
- load one `IndiAllSkyDbTaskQueueTable` row by ID;
- show fields and sanitized `data` JSON;
- do not expose buttons or POST actions;
- show fallback link to `/tasks`;
- show back link to `/modern-admin/tasks`;
- handle missing task ID with a non-destructive message or standard 404;
- update ownership/inventory.

Why this comes next:

- it improves operator understanding without mutating state;
- it reveals real payload structures before any retry/requeue design;
- it is reversible and small;
- it creates the inspection surface needed to decide whether future mutations are safe.

Do not implement retry, cancel, delete, clear completed, or requeue until the detail page has been validated on real Raspberry task data and a backend-safe transition contract exists.
