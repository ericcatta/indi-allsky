# YouTube authorization operations

Hybrid → YouTube shows authorization status, upload categories and prerequisites.
Authorization is shared by all cameras. Stored authorization does not prove that
Google is reachable or that uploads are succeeding; inspect the upload task result.

## Setup and use

1. During planned maintenance, install the project's optional Python modules in
   the application virtualenv using the existing setup workflow (see
   `requirements/requirements_optional.txt`). OAuth needs `google_auth_oauthlib`;
   uploading also needs `google-api-python-client`. Restart the web service after
   installation. Back up configuration/database and record the installed package
   versions before changes.
2. In YouTube → YouTube settings, configure the client secrets file and upload
   categories. The file must be readable by the web service. Keep it outside
   public media/static directories. The registered Google redirect URI must equal
   the externally served `/indi-allsky/youtube/oauth2callback` URL exactly,
   including HTTPS, hostname and any installation prefix.
3. As administrator, use Connect account and complete Google's consent screen.
   The request expires after ten minutes. Denied/expired requests can be restarted;
   existing authorization is kept until a new offline grant is saved successfully.
4. Refresh authorization explicitly requests a new access token. Revoke requires
   confirmation, revokes access for all profiles and removes stored authorization
   after Google's success response. Already uploaded videos are kept.
5. Use a dedicated test destination/account for acceptance uploads and verify the
   resulting video and task outcome. The current automated tests simulate Google;
   they do not establish live upload acceptance.

## Failures and rollback

- Missing optional modules, secrets file or refresh token are explicit prerequisites.
  Configure/install the missing prerequisite; reconnect when offline access is absent.
- Transport failures preserve the stored authorization. A timed-out revocation
  may already have taken effect at Google; check the account before retrying.
- A storage failure after Google accepted an action can leave local and Google
  state different. Reconnect to establish a fresh grant. Restoring a database
  backup cannot undo revocation at Google.
- Deployment rollback uses the prior application commit, virtualenv package
  inventory and coherent database/config backup. Credential keys and worker
  payload shape are unchanged. No production deployment or Google account change
  occurred during the isolated acceptance mission.
