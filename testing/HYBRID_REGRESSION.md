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

The current plan has 120 Python entries (including the separate Library entrypoint,
compilation, CPU sampling and the runner test) and 31 JavaScript entries. Discovery automatically
includes new `modern_admin_*_test.py`, `hybrid_*_test.py` and `hybrid_*_test.js`
entrypoints. `hybrid_ui_acceptance_test.py` remains a separate native acceptance
workflow. Additional historical Book 2 entrypoints are listed in `EXTRA_TESTS`.

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
