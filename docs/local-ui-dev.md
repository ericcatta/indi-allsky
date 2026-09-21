# Hybrid UI development and isolated acceptance

Hybrid is the only frontend. Open `/indi-allsky/modern-admin/now` and sign in.
There is no Classic mode, fallback shell or feature flag to enable it. Useful
shared drivers, workers, public media handlers and integration APIs remain.

## Use the existing isolated browser server

Use a Linux environment with the project dependencies, including D-Bus and image
libraries. macOS alone does not supply the full runtime; a Linux host with an SSH
forward to the Mac browser is the established development path.

From the repository root, using that environment's Python:

```sh
python testing/hybrid_browser_sandbox.py --runtime-config /etc/indi-allsky/flask.json --port 18110
```

The fixture reads the source Flask configuration, replaces database/media paths
and security keys, creates synthetic cameras and users, and binds only to
`127.0.0.1`. Database and media are temporary and disappear on exit. External
service, D-Bus and integration effects are blocked; there is no capture worker.
Use only this fixture for disposable browser tests, never a production DB copy
with live effects enabled. Do not expose the sandbox on the network.

For a sandbox running on the Raspberry, forward its loopback port from the Mac:

```sh
ssh -N -L 18110:127.0.0.1:18110 eric@allsky-pi.local
```

Open `http://127.0.0.1:18110/indi-allsky/modern-admin/now`. The synthetic users
are `test-user-1` (administrator) and `test-user-2` (ordinary user); their test-only
password is defined in [the fixture](../testing/hybrid_runtime_fixture.py).
Login and CSRF remain enabled. Do not use fixture credentials in production.

The optional `--maintenance-fixture` seeds disposable cleanup targets. Its
queued tasks have no worker, so this cannot certify actual generation/upload or
hardware effects. Stop the server with Ctrl-C when finished.

## Development and verification

Templates are in `indi_allsky/flask/templates/modern_admin/`, assets in
`indi_allsky/flask/static/modern_admin/`. Template reload is enabled in the
sandbox; restart it after Python changes. Keep current shell, authentication,
camera/profile selection and public contracts intact.

Use [the regression entrypoints](../testing/HYBRID_REGRESSION.md) and
[the acceptance workflow](HYBRID_ACCEPTANCE_WORKFLOW.md). The discovery report
censuses routes/controls; it does not prove clicks or effects. Exercise both
roles and cameras, missing/stale data, failures and narrow layouts. Record the
revision and separate synthetic evidence from direct production checks.

For production deployment, backups and rollback use
[the current runbook](../HYBRID_DEPLOYMENT.md). For unresolved acceptance gates
use [the status document](../HYBRID_ACCEPTANCE_STATUS.md).
