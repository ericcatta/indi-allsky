# Hybrid acceptance and maintenance workflow

This is the current workflow for Hybrid after Classic frontend removal. Historical
porting documents explain earlier decisions; their counts, dependency maps and
commands do not certify the current application.

## Authoritative inputs

- Inspect the actual Flask `url_map`, templates, JavaScript, forms and rendered
  DOM of the exact revision being tested. Include redirects, public media/API
  handlers, dynamic controls, dialogs and camera/profile context.
- `testing/hybrid_ui_acceptance_test.py` collects isolated GET-route and rendered
  control discovery. It reports blocked controls by default; rendering never
  proves an interaction or effect. Native DOM discovery is still necessary.
- `docs/hybrid-acceptance-route-register.json` links historical evidence to route
  entries. Read its recorded baseline and individual evidence before reuse.
- `HYBRID_ACCEPTANCE_STATUS.md` records bounded acceptance results and open work.
  `HYBRID_DEPLOYMENT.md` identifies the installed revision and rollback procedure.
- `tools/hybrid_settings_ownership_map.json` remains a runtime input. Retain it
  and its Settings contracts; it is separate from the retired static UI map.

## Discovery and verification

Run the discovery entrypoint with the project Python environment that includes
its Linux dependencies. The source runtime config is read to construct an
isolated application with synthetic users, cameras and database; it is not a
production browser/effect test. Use an explicit new output path outside the repo:

```bash
python testing/hybrid_ui_acceptance_test.py --output /tmp/hybrid-controls-review.json
python testing/run_hybrid_regression.py --list
```

Run the listed regression using the appropriate project and OAuth interpreters;
use a new output directory outside the source checkout. Retain source hashes,
commands, outcomes and errors. Preserve parser/form fingerprints. For each
control record its page, stable identifier, role, camera/profile, prerequisites,
expected request/effect, observed result and evidence revision/environment.
Statuses are `superato`, `difetto`, `bloccato`, or `non applicabile` with a reason.
Unavailable hardware, blocked downloads and unobserved effects are not passes.

Test complete paths, not only HTTP status: authentication/CSRF/permissions,
save/history/download/restore, media creation and playback, task result links,
failed providers/effects, duplicates, expired sessions and camera isolation.
Include keyboard/narrow-screen checks and data present, absent and stale.

## Changes and retirement

Make a complete responsibility or concrete user-flow correction per mission.
Preserve useful backend libraries, public URLs/APIs, data and configuration.
Remove frontend-only files only after independent Hybrid paths are verified.
Inspect dynamic references and installer/script/template/asset dependencies;
absence from a static text search alone is not deletion evidence. Keep physical
Classic removal separate from functional migrations for simple rollback.

Old static UI inventory output, its hand-maintained map and generator were
removed because they classify current shared/public handlers
and deleted templates using historical Classic assumptions. They have no
runtime consumers; current discovery and evidence replace that workflow.
Historical source is available with `git show 8f5c954b:<path>`.

## Live maintenance and delivery

Before deployment verify installed version, services, free space, coherent
backup and rollback. Keep backups private and public assets web-readable.
Scope destructive operations to authorized test data and identified targets;
coordinate network/disks/hardware recovery with the user when physical access
is required. Never infer approval for newly acquired data from an older cleanup.
Observe actual frames, output files, tasks and effects after deployment. The
24-hour test is deferred by the user and must not be reported as passed.

Finish with the appropriate regression, `git diff --check`, one logical commit
and push, clean/synchronized repository, updated operating instructions and
explicit open acceptance limits. Full retirement/acceptance remains incomplete
until the recorded requirements are actually satisfied.
