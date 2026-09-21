# Hybrid acceptance status

Updated 21 September 2026. **Classic removal is deployed; whole-product acceptance remains open.**
The separate 24-hour day/night observation is deferred by the user. Detector and AI implementation are outside this release.

## Installed product

The Raspberry runs `9b984cb53ee0ab98aba90e4205e2c13da8399ba0`.
Settings device identity and index navigation now preserve the selected camera/profile; both native round trips passed.
Classic frontend classes, templates and exclusive assets are physically removed.
Hybrid is the only UI and requires login. Shared workers, drivers, public media/API handlers and navigation redirects remain supported components.
Later main commits document acceptance; they do not change the installed runtime.

The 777-file installed code/template manifest matches the tested snapshot:
`a60e9a444fb7bb85ea47a75ba3912037350df8aaf5d801efd6ead264dba53fb9`.
All 164 Python entrypoints passed with unchanged source. The 34 JavaScript passes remain applicable to unchanged JS/templates/CSS. Details: [generation/storage guard](testing/evidence/hybrid-generation-storage-guard-20260921.json).
This automated result does not certify every native control or hardware effect.

The deployment preserved configuration revision 117, Flask configuration and user files.
Web and capture restarted (PIDs 892509 and 892510). The backup passed integrity checking in 32.94 seconds.
Use [current deployment and rollback instructions](HYBRID_DEPLOYMENT.md).

## Cold-start defect recovered; permanent asset correction pending

The restart exposed a backend dependency missed by Classic asset removal:
`moonOverlay.py` still loaded `static/astropanel/img/moon_rot.png`. The previous
worker cached that image; new workers failed before saving frames.
The exact historical bitmap was restored temporarily at its old path. Both cameras
resumed and their 21:58:46 / 21:58:53 frames decoded in the production browser.
No Classic page, class or navigation was restored.

The permanent correction moves the bitmap into backend overlay assets, adds a
four-phase cold/cached rendering test and includes binary assets in the regression
manifest. All 165 isolated Python entrypoints pass with unchanged sources; it is not yet deployed. Do not remove
the temporary production bitmap before the permanent correction is installed.
The earlier 777-file manifest did not include binary assets and does not prove their completeness.

## Post-removal evidence

| Scope | Verified result | Evidence |
| --- | --- | --- |
| Settings, isolated browser | Login, both camera previews, edit/save, value after reload, snapshot restore and original value recovered | [Release acceptance](testing/evidence/hybrid-retirement-final-native-20260921.json) |
| Production UI and capture | Both Now images decoded; Full Settings search works; source manifest matches; configuration and capture process preserved | [Release acceptance](testing/evidence/hybrid-retirement-final-native-20260921.json) |
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

## Remaining acceptance gates


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
