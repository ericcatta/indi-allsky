# Modern Admin Classic Navigation Inventory

This inventory maps the classic admin sidebar and dropdown navigation before modernizing the remaining pages. It is documentation-only and does not propose route or behavior changes by itself.

The classic shell is defined in `indi_allsky/flask/templates/base.html`. The routes below are registered on the `indi_allsky` blueprint, which uses the `/indi-allsky` URL prefix.

## Summary

- Total direct classic navigation pages found: 34
- Top-level links: 2
- Media dropdown pages: 9
- Info dropdown pages: 8
- Tools dropdown pages: 10
- System dropdown pages: 5

Some dropdown items are only visible when `current_user.is_authenticated` or `login_disabled` is true. Those items are still included because they are reachable from the classic admin shell for authenticated admin users.

## Inventory

| Visible menu label | Classic URL | Flask view / route | Template | Category | Recommended modern destination | Risk level | Priority |
|---|---|---|---|---|---|---|---|
| Latest | `/indi-allsky/` | `IndexImgView` / `index_view` | `index_img.html` | Dashboard | merge | read-only | P0 |
| Loop | `/indi-allsky/loop` | `ImageLoopImgView` / `image_loop_view` | `loop_img.html` | Dashboard | merge | read-only | P1 |
| Gallery | `/indi-allsky/gallery` | `GalleryViewerView` / `gallery_view` | `gallery.html` | Media | placeholder | read-only | P1 |
| Images | `/indi-allsky/imageviewer` | `ImageViewerView` / `imageviewer_view` | `imageviewer.html` | Media | placeholder | read-only | P1 |
| Timelapses | `/indi-allsky/videoviewer` | `VideoViewerView` / `videoviewer_view` | `videoviewer.html` | Media | placeholder | read-only | P1 |
| Mini-Timelapses | `/indi-allsky/minivideoviewer` | `MiniVideoViewerView` / `mini_videoviewer_view` | `minivideoviewer.html` | Media | placeholder | read-only | P2 |
| Panorama | `/indi-allsky/panorama` | `LatestPanoramaImgView` / `latest_panorama_view` | `index_img.html` | Media | merge | read-only | P2 |
| Panorama Loop | `/indi-allsky/looppanorama` | `PanoramaLoopImgView` / `panorama_loop_view` | `loop_img.html` | Media | merge | read-only | P2 |
| Realtime Keogram | `/indi-allsky/realtime_keogram` | `RealtimeKeogramView` / `realtime_keogram_view` | `realtime_keogram.html` | Observatory | placeholder | read-only | P2 |
| Long Term Keogram | `/indi-allsky/longtermkeogram` | `LongTermKeogramView` / `longterm_keogram_view` | `longterm_keogram.html` | Observatory | placeholder | read-only | P2 |
| FITS Viewer | `/indi-allsky/fitsimageviewer` | `FitsImageViewerView` / `fitsimageviewer_view` | `fitsimageviewer.html` | Media | classic-only | read-only | Later |
| SQM | `/indi-allsky/sqm` | `SqmView` / `sqm_view` | `sqm.html` | Observatory | merge | read-only | P1 |
| Charts | `/indi-allsky/charts` | `ChartView` / `chart_view` | `chart.html` | Observatory | merge | read-only | P1 |
| Sensor Panel | `/indi-allsky/sensor_panel` | `SensorPanelView` / `sensor_panel_view` | `sensor_panel.html` | Observatory | merge | read-only | P1 |
| Dark Library | `/indi-allsky/darks` | `DarkFramesView` / `darks_view` | `darks.html` | Cameras | placeholder | safe action | P2 |
| ADU History | `/indi-allsky/adu` | `RollingAduView` / `rolling_adu_view` | `adu.html` | Cameras | merge | read-only | P2 |
| Image Lag | `/indi-allsky/lag` | `ImageLagView` / `image_lag_view` | `lag.html` | Cameras | merge | read-only | P1 |
| File Space Usage | `/indi-allsky/filespaceusage` | `FileSpaceUsageView` / `filespaceusage_view` | `filespaceusage.html` | Storage | merge | read-only | P1 |
| Camera Info | `/indi-allsky/camera` | `CameraLensView` / `camera_lens_view` | `cameraLens.html` | Cameras | merge | read-only | P1 |
| VirtualSky | `/indi-allsky/virtualsky` | `VirtualSkyView` / `virtualsky_view` | `virtualsky.html` | Observatory | merge | read-only | P2 |
| Camera Simulator | `/indi-allsky/camerasimulator` | `CameraSimulatorView` / `camera_simulator_view` | `camera_simulator.html` | Tools | classic-only | safe action | Later |
| Astropanel | `/indi-allsky/astropanel` | `AstroPanelView` / `astropanel_view` | `astropanel.html` | Observatory | merge | read-only | P1 |
| Generate | `/indi-allsky/generate` | `TimelapseGeneratorView` / `generate_view` | `generate.html` | Media | classic-only | safe action | Later |
| Focus | `/indi-allsky/focus` | `FocusView` / `focus_view` | `focus.html` | Cameras | classic-only | risky action | Later |
| Process FITS | `/indi-allsky/processing` | `ImageProcessingView` / `image_processing_view` | `imageprocessing.html` | Tools | classic-only | safe action | Later |
| Image Circle Helper | `/indi-allsky/imagecirclehelper` | `ImageCircleHelperView` / `image_circle_helper_view` | `imagecirclehelper.html` | Cameras | classic-only | safe action | Later |
| Mask Base | `/indi-allsky/mask` | `MaskView` / `mask_view` | `mask.html` | Cameras | classic-only | safe action | Later |
| Log | `/indi-allsky/log` | `LogView` / `log_view` | `log.html` | System | merge | read-only | P2 |
| Support Info | `/indi-allsky/support` | `SupportInfoView` / `support_info_view` | `support_info.html` | System | merge | read-only | P2 |
| Config | `/indi-allsky/config` | `ConfigView` / `config_view` | `config.html` | System | classic-only | destructive/admin | Later |
| Network | `/indi-allsky/network` | `NetworkManagerView` / `network_manager_view` | `network.html` | System | classic-only | risky action | Later |
| Drives | `/indi-allsky/drives` | `DriveManagerView` / `drive_manager_view` | `drive_manager.html` | Storage | classic-only | destructive/admin | Later |
| GPIO Control | `/indi-allsky/manual_gpio` | `ManualGpioView` / `manual_gpio_view` | `manual_gpio.html` | System | classic-only | risky action | Later |
| System Info | `/indi-allsky/system` | `SystemInfoView` / `system_view` | `system.html` | System | merge | read-only | P1 |

## Notes By Modern Section

### Dashboard

Dashboard should absorb the daily operational status from `Latest`, parts of `Loop`, active camera freshness, capture status, and key alerts. Keep this read-only until the summary model is stable.

### Cameras

Camera-facing read-only information can merge `Camera Info`, `Image Lag`, `ADU History`, and some dark-library metadata. Camera setup, focus, mask editing, simulator controls, and image-circle calibration should remain classic-only until each action has explicit safety design.

### Storage

Storage should merge `File Space Usage` first because it is naturally read-only and matches the existing Modern Admin storage card. `Drives` should remain classic-only because mount/unmount or drive-management actions are operationally risky.

### Uploads

No direct Uploads item exists in the visible classic sidebar. Upload-related behavior appears to live in configuration and background/task flows, so Modern Admin should start with a placeholder, then a read-only upload/sync health summary later.

### Observatory

Observatory can merge `SQM`, `Charts`, `Sensor Panel`, `Astropanel`, `VirtualSky`, and keogram views over time. These are mostly read-only and map well to a product-facing observatory status section.

### System

System should start with read-only `System Info`, `Log`, and `Support Info`. `Config`, `Network`, `GPIO Control`, and system/drive management must stay classic-only until explicitly approved.

### Media

Media should initially expose placeholders for the gallery/viewer family. Read-only browsing can come before any generation, processing, deletion, exclusion, or download-management actions.

### Advanced

FITS processing, camera simulator, focus, mask base, image circle helper, config, network, drives, GPIO, and other expert workflows should be treated as Advanced/classic-only until each flow is designed independently.

## Recommended Phased Migration Plan

### Phase 1: Placeholder Coverage

Create Modern Admin placeholder destinations for all reachable classic pages and group them under the existing top-level Modern Admin sections. Do not connect actions, forms, mutating endpoints, or configuration writes. Every placeholder should provide a clear path back to Dashboard and Classic Admin.

Recommended first placeholder groups:

- Media: Gallery, Images, Timelapses, Mini-Timelapses, Panorama, Panorama Loop, FITS Viewer.
- Observatory: SQM, Charts, Sensor Panel, Astropanel, VirtualSky, Realtime Keogram, Long Term Keogram.
- System: System Info, Log, Support Info.
- Advanced/classic-only group: Config, Network, Drives, GPIO Control, Focus, Camera Simulator, Process FITS, Image Circle Helper, Mask Base.

### Phase 2: Read-Only Pages With Real Data

Prioritize read-only pages that already have safe data sources and strong dashboard value:

1. `Latest` and active camera freshness into Dashboard.
2. `Camera Info`, `Image Lag`, and `ADU History` into Cameras.
3. `File Space Usage` into Storage.
4. `System Info`, `Log`, and `Support Info` into System.
5. `SQM`, `Charts`, `Sensor Panel`, and `Astropanel` into Observatory.
6. Gallery and media browsing into Media after the information architecture for Media is defined.

### Phase 3: Safe Actions

Only add low-risk actions after the corresponding read-only page is stable. Candidate safe actions may include opening classic equivalents, downloading reports, filtering views, refreshing read-only data, and generating preview-only summaries. Avoid changing capture, hardware, credentials, services, or stored configuration in this phase.

### Phase 4: Risky/Admin Actions Stay Classic

Risky or destructive/admin flows should remain in Classic Admin until explicitly approved. This includes:

- Configuration writes.
- Network changes.
- Drive mount/unmount or cleanup operations.
- GPIO controls.
- Focus/capture hardware controls.
- Camera add/edit/delete or active-camera switching.
- FITS processing or media generation jobs.
- Mask/image-circle calibration changes.
- Any deletion, exclusion, credential, service, reboot, or reload action.

## Recommended First Batch

The first practical Modern Admin migration batch should be read-only and high-value:

1. Dashboard: latest frame, capture freshness, and capture status.
2. Cameras: Camera Info, Image Lag, ADU History summary.
3. Storage: File Space Usage summary.
4. Observatory: SQM, Charts, Sensor Panel, Astropanel summary cards.
5. System: System Info and Support Info read-only summary.

This batch avoids write actions while making the modern UI useful as a daily monitoring surface.

