# Hybrid acceptance status

Updated 29 September 2026. **Classic removal is deployed; whole-product acceptance remains open.**
The separate 24-hour day/night observation is deferred by the user. Detector and AI implementation are outside this release.

## Installed product

The Raspberry runs `3577fa82aa53808195687635f71e8197e7faf82f`.
Settings device identity and index navigation now preserve the selected camera/profile; both native round trips passed.
Classic frontend classes, templates and exclusive assets are physically removed.
Hybrid is the only UI and requires login. Shared workers, drivers, public media/API handlers and navigation redirects remain supported components.
Later main commits document acceptance; they do not change the installed runtime.

The 824-file installed source/asset manifest matches the tested candidate:
`c658eed40a313af6994862d3817da74ada29cbb5a714b4a046c7059c5e350388`.
The backend retains the 166-entrypoint image-publication regression. This
JS/template-only release reran all 34 JavaScript tests and both affected Python
Charts/Sensor Panel flows. It is not a new full
Python suite run. [Current evidence](testing/evidence/hybrid-observatory-timeout-20260929.json).
This does not certify every native control or hardware effect.

Configuration revision 118 and capture PID 1447332 remain unchanged; web was
reloaded. Code/config backup and rollback are prepared. Native Charts and Sensor Panel load
real data for both cameras; range selection and manual Refresh pass. Newly saved frames were observed at
13:08:41 and 13:08:42; this is not the deferred 24-hour acceptance.
Use [current deployment and rollback instructions](HYBRID_DEPLOYMENT.md).

## Cold-start defect corrected and deployed

Capture restart exposed a backend moon bitmap removed during Classic retirement.
The bitmap now belongs to `indi_allsky/overlay/assets/`; the temporary old-path
copy is removed. The installed cold/cached overlay test passes for four phases,
and the release manifest now includes raster images, SVG, icons and fonts.
The image algorithms and original bitmap bytes are unchanged.

After the 22:09:58 restart both cameras saved new frames: IMX708 at 22:10:12 and
ASI678MC at 22:10:21. Both decoded in the production browser. A bounded log sample
contains no image-worker exception after restart. See [recovery evidence](testing/evidence/hybrid-moon-asset-recovery-20260921.json).
No Classic frontend was restored. This closes the specific cold-start defect,
not the remaining whole-product acceptance gates below.

## Media identifier correction deployed

Oversized media identifiers could reach SQLite and raise OverflowError in FITS
preview, Hybrid downloads and public originals. Bounds are now validated before
querying. The original FITS class fingerprint is retained around the exact added
guard. All 165 Python entrypoints passed after a test-only guardrail correction;
the unchanged JavaScript results remain applicable. Native production checks now
return controlled 400/404 errors on all three corrected routes. Both Now images
decoded (22:56:47 IMX708 and 22:56:58 ASI678MC). See [identifier validation evidence](testing/evidence/hybrid-media-id-boundary-20260921.json).

## Storage estimate correction deployed

Failed Startrail attempts without an output file were suppressing the capacity
estimate. The corrected query excludes unsuccessful generated-output rows with
no recorded size, retaining all known bytes and the checks for genuinely unknown
sizes. All 165 Python entrypoints pass. A read-only production-data comparison
restores the estimate (8.51 GiB/day, approximately six days capacity at observation).
The installed page now shows the estimate. A native same-value save persisted revision 118,
with the original 5 GiB / 8 GiB / 3-day policy and all other settings unchanged.
Both latest frames decoded after deployment. [Evidence](testing/evidence/hybrid-storage-estimate-fix-20260929.json).

## Post-removal evidence

| Scope | Verified result | Evidence |
| --- | --- | --- |
| Settings, isolated browser | Login, both camera previews, edit/save, value after reload, snapshot restore and original value recovered | [Release acceptance](testing/evidence/hybrid-retirement-final-native-20260921.json) |
| Production UI and capture | Both Now images decoded; Full Settings search works; source manifest matches; configuration and capture process preserved | [Release acceptance](testing/evidence/hybrid-retirement-final-native-20260921.json) |
| Notifications, production administrator | Dedicated expired notice acknowledged and retained; 198 existing acknowledgement values unchanged. Search, filters, paging, seven sort columns, copy and keyboard detail verified. Native export receipt remains open | [Native notifications](testing/evidence/hybrid-notification-live-20260921.json) |
| Notifications, narrow viewport | At 390/320 px, search and keyboard detail navigation pass; at 320 px, acknowledgement filtering, empty state and return to list pass. No page-level horizontal overflow. Export delivery remains open | [Mobile notifications](testing/evidence/hybrid-notifications-mobile-20260929.json) |
| Public media families | All 17 latest-media routes checked for both cameras: 30 ranged responses match on-disk camera/model files, four RAW requests show the correct empty state. Native download receipt remains open | [Live public families](testing/evidence/hybrid-public-families-live-20260921.json) |
| Public image viewer controls | Both camera directory links open decoded images; Copy link verified by actual paste, fullscreen enter/exit and return to correctly filtered Hybrid archive | [Native public viewers](testing/evidence/hybrid-public-viewer-native-20260921.json) |
| Production authentication boundary | All 99 Hybrid GET entries reach login for anonymous GET/HEAD on both camera/profile contexts (396 cases, including alias chains). Public latest-image range bytes match each camera file; 14 invalid API authentication requests rejected | [Live HTTPS boundary](testing/evidence/hybrid-live-auth-boundary-20260921.json) |
| Current-release mini generation | Native submissions 12747/12748 produced five-frame, 2 FPS clips for cameras 1/2; file/DB/probe match and both played to natural end. Capture continued | [Live generation after fixes](testing/evidence/hybrid-generation-guard-live-20260921.json) |
| Real mini timelapses | Tasks 12718/12719 succeeded for cameras 1/2. Each output has 9 frames at 2 fps, verified with ffprobe and complete browser playback | [Live generation](testing/evidence/hybrid-mini-generation-post-classic-20260921.json) |
| Loop | Both cameras, individual filters, history, speed selection, native forward/reverse playback and return to forward playback | [Loop acceptance](testing/evidence/hybrid-loop-post-classic-20260921.json) |
| RAW Loop with absent data | Correct empty state on both cameras and navigation back to processed Loop; the live RAW table is empty | [Loop acceptance](testing/evidence/hybrid-loop-post-classic-20260921.json) |
| Satellite provider | Real requests validated 156 visual, 10,695 Starlink and 20 station entries; production catalog unchanged; real task outcomes visible in Hybrid. Historical 403 not reproduced | [Provider recheck](testing/evidence/hybrid-satellite-recheck-20260921.json) |
| Mobile navigation | At 390 px, drawer focus/Escape/Enter, Settings navigation, profile search and Loop filters verified; Loop also fits 320 px with both images decoded. Profile-tab context defect found in this historical run was corrected and verified in the Settings navigation entry below | [Mobile acceptance](testing/evidence/hybrid-mobile-navigation-20260921.json) |
| Settings camera/profile round trip | Both native profile → Settings → Exposure/Gain paths preserve the correct camera ID and profile; Now images decoded after web-only update | [Settings navigation](testing/evidence/hybrid-settings-navigation-context-20260921.json) |
| Highlights, Moment and Output | 16 image-detail links and previews verified; seven output-type links per camera preserve filters; both completed day keograms display real files. Download delivery remains open | [Product media navigation](testing/evidence/hybrid-product-media-navigation-20260921.json) |
| Static cleanup and VirtualSky | Five unused vendor demo assets removed (78,384 bytes); both camera overlays, fullscreen and preview reset verified; services preserved | [Static cleanup](testing/evidence/hybrid-static-cleanup-20260921.json) |
| Complete day outputs | Four automatic tasks succeeded: both camera timelapses (3,165 frames each) and panoramas (1,581 each). Original files/probes match; all four played to natural end in the browser | [Day output playback](testing/evidence/hybrid-day-output-playback-20260921.json) |
| System tools and Focus | Native network/drive refresh, SD metadata, complete support output and GPIO disabled-state checks; Focus crop/reset/fullscreen and both-camera preview with automatic refresh. Physical device effects remain open | [System and Focus](testing/evidence/hybrid-system-focus-native-20260921.json) |
| Camera detection correction | Real INDI capabilities exclude Telescope Simulator from camera selection; actual driver preserved. Both cameras still acquire and decode after web-only deploy | [Detection release](testing/evidence/hybrid-camera-detection-release-20260921.json) |
| Browser downloads | Video and empty CSV clicks returned, but no matching file was found in Mac Downloads; delivery remains unverified | [Open download checks](testing/evidence/hybrid-download-delivery-post-classic-20260921.json) |

Earlier evidence remains useful for its stated revision, role, camera and environment.
It is not automatically recertified against the current release.
The [route evidence register](docs/hybrid-acceptance-route-register.md) links each recorded control to its source.

## Inventory and coverage limits

The isolated discovery of installed `7d9e49f9` covers all 99 registered Hybrid GET entries in
505 role/camera/detail contexts: 376 rendered and 129 blocked or redirected,
with no rendering defects and no matches for the selected placeholder phrases.
It records 43,978 control occurrences, including repetition across roles,
cameras, aliases and shared navigation. This is not a count of unique features.

The full report is `/home/eric/hybrid-current-controls-20260921.json`, SHA-256
`6bd756f13a3a34a7e139a6372e0372b777ba0daff1ccb2764c162fa43ccf912b`.
Its source manifest and limitations are recorded in `current_control_discovery`
in the [JSON register](docs/hybrid-acceptance-route-register.json).

The static identity index preserves all 43,978 references in 7,351 exact page/control groups.
Six non-page GET families now link to their passing isolated API/redirect tests on this source manifest;
see [current discovery evidence](testing/evidence/hybrid-current-discovery-20260921.json).
This does not certify native download receipt or hardware effects.

Discovery does not mark clicks passed. JavaScript-generated controls, keyboard/mobile behavior,
mutating requests and observable effects require their own evidence.
The full control/effect matrix is not yet certified; blocked cases are not passes.
Absence of selected placeholder phrases is not proof that every function is implemented.

## Astropanel timeout recovery deployed

A stalled request could leave Refresh disabled indefinitely. A 15-second client
deadline now restores the control, distinguishes unavailable data from retained
stale values, and permits retry. Native isolated 20-second delays verified initial
failure and stale-data preservation; retry and camera switching recovered.
Production refresh/camera selection passed without restarting capture.
[Evidence](testing/evidence/hybrid-astropanel-timeout-20260929.json).

## Users table acceptance extended

A native isolated 28-account fixture verifies pagination, all ascending sort
columns, ID reverse sorting, page sizes, combined filters, account details and
self-account navigation. Administrator, ordinary-user and anonymous behavior
were observed. At 320px the table scrolls horizontally without page overflow;
Details opens after its column is made visible. Compared account fields remain
unchanged apart from expected login metadata excluded from that comparison.
Copy still lacks verified clipboard delivery; native CSV/Excel receipt remains
open. [Evidence](testing/evidence/hybrid-users-native-controls-20260929.json).

## Focused Settings controls verified on both profiles

Production administrator paths through Basic/Advanced to Storage, Analytics,
Acquisition/Save and FITS/Source were exercised for both cameras. Search,
keyboard clear, focus checkbox off/on and return navigation produced the expected
visible results and retained camera/profile context. The eight round trips record
56 control occurrences; this is not whole-product coverage. Configuration 118
remained unchanged; save/restore/download are outside this particular check.
[Evidence](testing/evidence/hybrid-settings-domain-controls-20260929.json).

## Capture image publication deployed

Release `07b2098d` preserves the previous latest preview if copying or publication
fails, publishes complete archive files, and removes encoded temporary files on
all exits. The 166 Python entrypoints pass using the full run plus one corrected
focus test harness rerun; all 34 JavaScript tests pass. The 824-file source manifest
matches production. Capture restarted in a bounded 12-second maintenance window;
web PID and configuration 118 remained unchanged. Three new saved files per camera
decoded successfully; both Now previews decoded in the native browser. The last two
intervals per camera were 15 seconds, which does not close the separate latency
finding. [Evidence](testing/evidence/hybrid-image-publication-20260929.json).

## Mobile management-grid correction deployed

Uploads overflowed a 320px screen to 785px because of the intrinsic grid minimum.
The CSS correction and cache version updates are installed. Native isolated and
production checks fit Uploads, YouTube and Sensor Panel at 320px; desktop retains
two columns. All 34 JavaScript tests and three affected Python flow tests pass.
Production provider navigation and empty states were verified against the database.
External transfers remain open. [Evidence](testing/evidence/hybrid-upload-management-layout-20260929.json).

## Encoder failure handling deployed

The worker could overwrite a valid latest PNG preview with an empty file when
the encoder returned false. The installed fix rejects that failure and removes
partial encoder files on exceptions. All 166 Python entrypoints pass; the
823-file tested manifest matched that release. Both cameras saved new frames and
their Now images decoded after the controlled restart. This does not resolve
the separate latency finding. [Evidence](testing/evidence/hybrid-image-encoder-failure-20260929.json).

## Backup space recovery — 29 September

Four historical database snapshots were losslessly archived and verified, reclaiming
approximately 3 GiB without removing media. Free space reached 8.53 GiB. The current
release backup remains directly usable; capture was not restarted. Both cameras
saved 30 frames in the bounded check, with one 19-second IMX708 interval. This is
not a resolution of the latency finding below. [Evidence](testing/evidence/hybrid-backup-archival-20260929.json).

## Capture latency finding — 29 September

A read-only six-hour retrospective sample found transient queue backpressure,
one IMX708 timeout during the backup window, and saved-image gaps up to 67/61
seconds. Both cameras recovered; the last five saved frames for each were again
15 seconds apart. Typical processing times are low, but log boundaries show
23.9-second compression/save and 38.9-second DB/metadata gaps outside the reported
processing metric. The cause is not established and steady cadence is not yet
certified. [Measured evidence](testing/evidence/hybrid-capture-queue-review-20260929.json).
A later 60-second syscall trace measured a 16.483467-second database fdatasync
in the image worker. This identifies a blocking persistence stage, consistent
with checkpoint work; the physical cause and correction remain open. In the
12:18–13:10 sample, IMX708 had one 38-second gap and ASI678MC had no gap over
17 seconds. This is not the deferred 24-hour acceptance. No capture settings
were changed.
The installed SQLite 3.46.1 predates the upstream WAL-reset correction. A private
3.51.3 library passed a synthetic concurrency/integrity and old-library readback
probe; it is not deployed. Full application compatibility and checkpoint lifecycle
verification are prerequisites to the proposed background checkpoint change.

## Remaining acceptance gates


- Resolve the observed transient worker/save stalls and verify end-to-end cadence under the identified load.
- Finish the control/effect matrix, including uncovered role, camera/profile, mobile, empty/stale-data and failure cases. Reuse applicable evidence and preserve its scope.
- Resolve native download delivery: establish whether the browser has a pending Save dialog or another destination, then verify the received file against its source. Do not substitute a successful HTTP request for native delivery.
- Complete remaining live effects, including dedicated-data cleanup/deletion and test-destination uploads. Short mini timelapses and both cameras’ automatic day timelapse/panorama outputs are verified; other automatic/isolated tests remain separately labeled.
- Identify devices and arrange recovery/physical presence before interrupting networking, disks or GPIO. Current user clarification is pending. Do not claim unavailable hardware as tested.
- Complete remaining repository/backend review and operational cleanup. The [47 core dependency review](docs/HYBRID_DEPENDENCIES.md) and installer path/syntax checks are recorded; clean platform builds and optional integration acceptance are not implied. Retain useful shared backend, public contracts, user data, migrations and supported functions.
- Cold power-loss recovery has not been directly tested. The earlier warm reboot/startup evidence is in [reboot acceptance](testing/evidence/hybrid-reboot-autostart-20260914.json).

The 24-hour observation is explicitly excluded from this run and is not passed.
No new detector/AI algorithms or simulated classifications belong to these closure tasks.

## Reproducing checks and reading history

Use [the regression instructions](testing/HYBRID_REGRESSION.md) and
[the acceptance workflow](docs/HYBRID_ACCEPTANCE_WORKFLOW.md).
Run discovery and integration tests in the isolated runtime, never against production data.
[Capture cadence documentation](HYBRID_CAPTURE_CADENCE.md) describes shared intervals and independent exposure/gain behavior.

The former 4,412-line chronological status log is preserved in Git at `ad41d847`:
`git show ad41d847:HYBRID_ACCEPTANCE_STATUS.md`.
All individual evidence JSON files remain in `testing/evidence/`.
Those historical entries include superseded candidates, counts, deadlines and rollback targets;
they must not be read as the current installation state.
