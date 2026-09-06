# Hybrid acceptance status

## Completion gate

The complete product audit is **open**. Detector/AI are deferred; their absence
must be represented honestly. Classic has not been removed and these changes
have not been deployed to the live Raspberry checkout. A 24-hour product
validation has not started.

## Verified mission: authenticated Hybrid navigation and account

Baseline: `6b80191f`. Real Flask reproduction found `BuildError` on successful
login with Classic disabled: the response required `indi_allsky.index_view`.
Authenticated page context also required the Classic `user_view` endpoint.

Corrections:
- Login and logout land on Hybrid Now.
- My Account has a native Hybrid route/form and uses the existing account-save
  endpoint. Navigation exposes sign-in, account and sign-out appropriately.
- Account edits preserve username/email/role restrictions; name and password
  changes still require the current password. Returned user labels are escaped.
- Login fits narrow screens, prevents duplicate submission, and displays
  unexpected/non-JSON failures safely.

Evidence:
- `testing/hybrid_authenticated_flow_test.py`: real login, authenticated page
  rendering, name persistence, password change and subsequent login, rejected
  incorrect passwords, mismatched passwords, missing CSRF, ordinary-user
  privilege isolation and anonymous access. Synthetic users/configuration,
  two cameras, in-memory database, Classic import prohibited.
- `testing/hybrid_account_browser_test.js`: controller request contract,
  duplicate submission, failed/expired/network responses, clearing passwords
  only after success. This is a controller test, **not a browser click test**.
- Existing shell and route fingerprints retained. The new account navigation
  and additional route are explicitly tested separately.

## Initial runtime discovery: gaps remain

`testing/hybrid_ui_acceptance_test.py` derives template routes from registration
and requests them through real authenticated test sessions. Hardware bus and
external process calls are blocked. It never touches production data.

Initial discovery after the authentication fix:
- 89 template routes; 79 parameter-free routes requested in four contexts
  (admin/camera 1, admin/camera 2, ordinary user/camera 1, anonymous/camera 1).
- 316 contexts: 159 render successfully, 63 fail, 94 are blocked or redirect.
- 11,660 control occurrences discovered across rendered contexts. These are
  **not unique features and not successful interactions**.
- 10 parameterized routes need dedicated detail fixtures.
- 21 pages fail: ten Settings contract pages hit a Jinja dictionary/method
  collision; remaining failures include legacy route links in media, task,
  notification, generation and integration surfaces.

Every discovered control starts `bloccato` until its interaction and effect
are explicitly tested. The JSON contains route, stable control identifier,
role, camera, form method/action, link, disabled state and evidence slots.
Input values are excluded. Dynamic browser-created controls and all detail
states must supplement this discovery before a coverage claim is possible.

Run explicitly, outside the production checkout:

```
python testing/hybrid_ui_acceptance_test.py --output /tmp/hybrid-controls.json
python testing/hybrid_authenticated_flow_test.py
node testing/hybrid_account_browser_test.js
```

## Remaining gates

Complete Settings, media, operational tools and all supported effects; replace
static product panels with real data or explicit capability states; execute
actual browser paths and hardware/integration checks. Test destructive actions
only on dedicated new fixtures. Arrange physical presence for connectivity
and device interruption tests. Keep migration and physical Classic removal in
separate commits, then repeat essential tests and the required day/night soak.
