# Reproducible Hybrid regression

Run `run_hybrid_regression.py` from an isolated checkout on a prepared Linux test
runtime. Integration tests require the project dependencies and read the runtime
configuration at `/etc/indi-allsky/flask.json` to build isolated fixtures. This
runner does not install dependencies, deploy code or restart services. Tests of
controllers do not substitute for native browser or live hardware acceptance.

Inspect the complete command plan without running any test:

```sh
python3 testing/run_hybrid_regression.py --list
```

Example for the existing Raspberry test overlay, after synchronizing the exact
candidate source into it (do not run from the production checkout):

```sh
python3 /home/eric/hybrid-acceptance-archive-return/testing/run_hybrid_regression.py \
  --python /home/eric/indi-allsky/virtualenv/indi-allsky/bin/python \
  --oauth-python /home/eric/hybrid-acceptance-oauth-venv/bin/python \
  --node node \
  --output /home/eric/hybrid-regression-candidate-evidence
```

Choose a new output directory for each run. It must be outside the source tree;
existing directories are rejected to preserve previous evidence. Node must be
available in the test environment. `--timeout` is a per-entrypoint timeout in
seconds (default 240), not a deadline for the whole run.

Use `--list` for the current entrypoint count, including the separate Library
entrypoint and compilation. Discovery automatically
includes new `modern_admin_*_test.py`, `hybrid_*_test.py` and `hybrid_*_test.js`
entrypoints. `hybrid_ui_acceptance_test.py` remains a separate HTML discovery
workflow, not native browser acceptance. Additional historical Book 2 entrypoints
are listed in `EXTRA_TESTS`.

Flows using `hybrid_runtime_fixture.isolated_app` run with Classic route imports
blocked and a restrictive Jinja loader. Only `modern_admin/`, `shared/` and the
standalone `login.html` are available. Loading a Classic template, including through
inheritance or a fallback include, fails the test. Static URLs generated with
Flask also pass an explicit asset ownership guard: Hybrid assets, the shared
VirtualSky library and the named shared files in `hybrid_asset_guard.py` are
allowed. Classic tab CSS/JS and unclassified files fail the test. This demonstrates
template and generated-URL independence for executed flows. Hardcoded URLs,
CSS imports and JavaScript network requests still require separate inspection;
these guards do not establish complete browser coverage or permit removal of
unverified functionality.

`results.json` records the exact plan, source hashes and each child exit code,
duration and log path. It is updated atomically after each result. `running` or
`interrupted` is incomplete, never passed. `source_changed` means the run cannot
validate one stable candidate. A missing dependency is a failed execution, not a
successful test or an implicit skip. Inspect logs to distinguish environmental
blocks from product failures. Only a complete `passed` report with unchanged
source hashes proves this automated suite passed; it does not prove deployment
or complete product acceptance.

Self-check (standard-library Python only):

```sh
python3 testing/hybrid_regression_runner_test.py
```
