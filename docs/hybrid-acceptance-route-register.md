# Registro delle evidenze per route Hybrid

Route rilevate dalla `url_map` Flask del candidato `0e6f445c`, avviato in ambiente isolato con Classic disabilitato: **107 ingressi Hybrid e 151 route con altri percorsi (autenticazione, API, asset e compatibilita')**. Il JSON include anche queste ultime. La registrazione di una route non prova il suo funzionamento.

Gli esiti sono riferimenti puntuali alle prove originali, che specificano revisione, ambiente, ruolo, camera/profilo e limiti quando verificati. I record storici restano storici. Il numero di record non e' una percentuale di copertura e non certifica tutti i controlli della pagina.

[Registro completo con riferimenti ai singoli controlli](hybrid-acceptance-route-register.json).
Ultimo censimento statico, riferito a `970d1799` (29 settembre): 99 ingressi GET, 505 contesti, 376 rendering riusciti, 129 contesti bloccati e nessun errore di rendering. Il report contiene 43.978 occorrenze di controlli, comprese ripetizioni fra ruoli e camere; nessun click viene certificato dal solo censimento. Percorso, hash e limiti sono nel campo `current_control_discovery` del JSON.

Indice statico: 7.368 identità con tutti i 43.978 riferimenti originali conservati. Non rappresenta un conteggio di funzionalità né certifica automaticamente le interazioni. Sei ingressi API/redirect sono collegati alle [prove isolate già superate sulla versione installata](../testing/evidence/hybrid-current-discovery-20260921.json); download nativi ed effetti hardware restano fuori da queste prove.

[Verifica HTTPS anonima sul Raspberry](../testing/evidence/hybrid-live-auth-boundary-20260921.json): tutti i 99 ingressi GET Hybrid, 396 casi GET/HEAD nelle due camere/profili, arrivano al login. Sono verificati anche i passaggi degli alias Settings. Questo risultato riguarda il confine di autenticazione, non certifica i controlli dopo il login.

| Route Hybrid attuale | Record associati | Fonti |
| --- | ---: | --- |
| `/modern-admin` | 0 | Da associare o collaudare |
| `/modern-admin/account` | 18 | [hybrid-account-native-20260914](../testing/evidence/hybrid-account-native-20260914.json), [hybrid-browser-2026-09-06](../testing/evidence/hybrid-browser-2026-09-06.json), [hybrid-native-users-2026-09-08](../testing/evidence/hybrid-native-users-2026-09-08.json), [Menu amministratore](../testing/evidence/hybrid-navigation-drawer-20260929.json) |
| `/modern-admin/cameras` | 3 | [hybrid-camera-detection-release-20260921](../testing/evidence/hybrid-camera-detection-release-20260921.json), [hybrid-camera-diagnostics-native-20260921](../testing/evidence/hybrid-camera-diagnostics-native-20260921.json), [Menu amministratore](../testing/evidence/hybrid-navigation-drawer-20260929.json) |
| `/modern-admin/cameras/add` | 2 | [hybrid-camera-detection-release-20260921](../testing/evidence/hybrid-camera-detection-release-20260921.json), [hybrid-camera-diagnostics-native-20260921](../testing/evidence/hybrid-camera-diagnostics-native-20260921.json) |
| `/modern-admin/cameras/adu-history` | 5 | [hybrid-camera-diagnostics-native-20260921](../testing/evidence/hybrid-camera-diagnostics-native-20260921.json) |
| `/modern-admin/cameras/dark-library` | 2 | [hybrid-camera-diagnostics-native-20260921](../testing/evidence/hybrid-camera-diagnostics-native-20260921.json) |
| `/modern-admin/cameras/detect-indi` | 0 | Da associare o collaudare |
| `/modern-admin/cameras/image-lag` | 12 | [hybrid-image-lag-native-20260920](../testing/evidence/hybrid-image-lag-native-20260920.json) |
| `/modern-admin/cameras/info` | 2 | [hybrid-camera-info-navigation-20260920](../testing/evidence/hybrid-camera-info-navigation-20260920.json) |
| `/modern-admin/cameras/mask-base` | 1 | [hybrid-camera-diagnostics-native-20260921](../testing/evidence/hybrid-camera-diagnostics-native-20260921.json) |
| `/modern-admin/cameras/start-indi` | 0 | Da associare o collaudare |
| `/modern-admin/capture/abort-exposure` | 0 | Da associare o collaudare |
| `/modern-admin/capture/service` | 1 | [Contratto API/redirect isolato](../testing/evidence/hybrid-current-discovery-20260921.json) |
| `/modern-admin/classic/<classic_page>` | 1 | [Contratto API/redirect isolato](../testing/evidence/hybrid-current-discovery-20260921.json) |
| `/modern-admin/config-history` | 7 | [hybrid-browser-2026-09-06](../testing/evidence/hybrid-browser-2026-09-06.json), [hybrid-settings-chain-20260929](../testing/evidence/hybrid-settings-chain-20260929.json), [hybrid-sqlite-checkpoint-20260929](../testing/evidence/hybrid-sqlite-checkpoint-20260929.json) |
| `/modern-admin/config-restore` | 5 | [hybrid-browser-2026-09-06](../testing/evidence/hybrid-browser-2026-09-06.json), [hybrid-settings-chain-20260929](../testing/evidence/hybrid-settings-chain-20260929.json) |
| `/modern-admin/config-restore/<int:config_id>` | 4 | [hybrid-browser-2026-09-06](../testing/evidence/hybrid-browser-2026-09-06.json), [hybrid-settings-chain-20260929](../testing/evidence/hybrid-settings-chain-20260929.json) |
| `/modern-admin/config-restore/<int:config_id>/apply` | 2 | [hybrid-snapshot-acceptance-20260930](../testing/evidence/hybrid-snapshot-acceptance-20260930.json) |
| `/modern-admin/fits` | 2 | [hybrid-source-media-2026-09-06](../testing/evidence/hybrid-source-media-2026-09-06.json) |
| `/modern-admin/fits/<int:fits_id>` | 4 | [hybrid-fits-dimensions-live-20260914](../testing/evidence/hybrid-fits-dimensions-live-20260914.json), [hybrid-source-media-2026-09-06](../testing/evidence/hybrid-source-media-2026-09-06.json) |
| `/modern-admin/highlights` | 18 | [hybrid-product-media-navigation-20260921](../testing/evidence/hybrid-product-media-navigation-20260921.json), [Menu amministratore](../testing/evidence/hybrid-navigation-drawer-20260929.json) |
| `/modern-admin/library` | 48 | [hybrid-browser-media-2026-09-08](../testing/evidence/hybrid-browser-media-2026-09-08.json), [hybrid-library-live-20260914](../testing/evidence/hybrid-library-live-20260914.json), [hybrid-mini-generation-live-20260914](../testing/evidence/hybrid-mini-generation-live-20260914.json), [hybrid-product-media-navigation-20260921](../testing/evidence/hybrid-product-media-navigation-20260921.json), [hybrid-sky-cycle-navigation-native-20260920](../testing/evidence/hybrid-sky-cycle-navigation-native-20260920.json), [Menu amministratore](../testing/evidence/hybrid-navigation-drawer-20260929.json), [hybrid-sqlite-checkpoint-20260929](../testing/evidence/hybrid-sqlite-checkpoint-20260929.json) |
| `/modern-admin/loop` | 7 | [hybrid-loop-post-classic-20260921](../testing/evidence/hybrid-loop-post-classic-20260921.json), [hybrid-mobile-navigation-20260921](../testing/evidence/hybrid-mobile-navigation-20260921.json), [Menu amministratore](../testing/evidence/hybrid-navigation-drawer-20260929.json) |
| `/modern-admin/media/<kind>/<int:camera_id>/<int:media_id>/download` | 1 | [Contratto API/redirect isolato](../testing/evidence/hybrid-current-discovery-20260921.json) |
| `/modern-admin/media/archive` | 15 | [hybrid-archive-2026-09-06](../testing/evidence/hybrid-archive-2026-09-06.json) |
| `/modern-admin/media/fits` | 7 | [hybrid-fits-dimensions-live-20260914](../testing/evidence/hybrid-fits-dimensions-live-20260914.json), [hybrid-source-media-2026-09-06](../testing/evidence/hybrid-source-media-2026-09-06.json), [Menu amministratore](../testing/evidence/hybrid-navigation-drawer-20260929.json) |
| `/modern-admin/media/gallery` | 2 | [Menu amministratore](../testing/evidence/hybrid-navigation-drawer-20260929.json), [hybrid-gallery-state-20260929](../testing/evidence/hybrid-gallery-state-20260929.json) |
| `/modern-admin/media/gallery/page` | 1 | [hybrid-gallery-state-20260929](../testing/evidence/hybrid-gallery-state-20260929.json) |
| `/modern-admin/media/images` | 2 | [hybrid-navigation-drawer-20260929](../testing/evidence/hybrid-navigation-drawer-20260929.json), [hybrid-media-detail-context-20260930](../testing/evidence/hybrid-media-detail-context-20260930.json) |
| `/modern-admin/media/images/<int:image_id>` | 2 | [hybrid-sky-cycle-navigation-native-20260920](../testing/evidence/hybrid-sky-cycle-navigation-native-20260920.json), [hybrid-media-detail-context-20260930](../testing/evidence/hybrid-media-detail-context-20260930.json) |
| `/modern-admin/media/keograms` | 10 | [hybrid-generated-media-2026-09-06](../testing/evidence/hybrid-generated-media-2026-09-06.json), [Menu amministratore](../testing/evidence/hybrid-navigation-drawer-20260929.json) |
| `/modern-admin/media/mini-timelapses` | 10 | [hybrid-generated-media-2026-09-06](../testing/evidence/hybrid-generated-media-2026-09-06.json), [Menu amministratore](../testing/evidence/hybrid-navigation-drawer-20260929.json) |
| `/modern-admin/media/panorama` | 10 | [hybrid-generated-media-2026-09-06](../testing/evidence/hybrid-generated-media-2026-09-06.json), [Menu amministratore](../testing/evidence/hybrid-navigation-drawer-20260929.json) |
| `/modern-admin/media/panorama-loop` | 14 | [hybrid-native-panorama-2026-09-08](../testing/evidence/hybrid-native-panorama-2026-09-08.json), [Menu amministratore](../testing/evidence/hybrid-navigation-drawer-20260929.json) |
| `/modern-admin/media/public-endpoints` | 2 | [Native public image viewer](../testing/evidence/hybrid-public-viewer-native-20260921.json) |
| `/modern-admin/media/raw` | 4 | [hybrid-source-media-2026-09-06](../testing/evidence/hybrid-source-media-2026-09-06.json), [Menu amministratore](../testing/evidence/hybrid-navigation-drawer-20260929.json) |
| `/modern-admin/media/raw-loop` | 1 | [hybrid-loop-post-classic-20260921](../testing/evidence/hybrid-loop-post-classic-20260921.json) |
| `/modern-admin/media/startrail-videos` | 10 | [hybrid-generated-media-2026-09-06](../testing/evidence/hybrid-generated-media-2026-09-06.json), [Menu amministratore](../testing/evidence/hybrid-navigation-drawer-20260929.json) |
| `/modern-admin/media/startrails` | 10 | [hybrid-generated-media-2026-09-06](../testing/evidence/hybrid-generated-media-2026-09-06.json), [Menu amministratore](../testing/evidence/hybrid-navigation-drawer-20260929.json) |
| `/modern-admin/media/timelapses` | 2 | [hybrid-navigation-drawer-20260929](../testing/evidence/hybrid-navigation-drawer-20260929.json), [hybrid-media-detail-context-20260930](../testing/evidence/hybrid-media-detail-context-20260930.json) |
| `/modern-admin/media/timelapses/<int:video_id>` | 1 | [hybrid-media-detail-context-20260930](../testing/evidence/hybrid-media-detail-context-20260930.json) |
| `/modern-admin/mode/<mode>` | 1 | [Contratto API/redirect isolato](../testing/evidence/hybrid-current-discovery-20260921.json) |
| `/modern-admin/moment` | 19 | [hybrid-product-media-navigation-20260921](../testing/evidence/hybrid-product-media-navigation-20260921.json), [Menu amministratore](../testing/evidence/hybrid-navigation-drawer-20260929.json) |
| `/modern-admin/notifications` | 35 | [hybrid-operations-2026-09-06](../testing/evidence/hybrid-operations-2026-09-06.json), [hybrid-operations-live-20260914](../testing/evidence/hybrid-operations-live-20260914.json), [Menu amministratore](../testing/evidence/hybrid-navigation-drawer-20260929.json), [hybrid-notification-live-20260921](../testing/evidence/hybrid-notification-live-20260921.json), [hybrid-notifications-mobile-20260929](../testing/evidence/hybrid-notifications-mobile-20260929.json) |
| `/modern-admin/notifications/<int:notification_id>` | 9 | [hybrid-operations-2026-09-06](../testing/evidence/hybrid-operations-2026-09-06.json), [hybrid-operations-live-20260914](../testing/evidence/hybrid-operations-live-20260914.json), [hybrid-notification-live-20260921](../testing/evidence/hybrid-notification-live-20260921.json), [hybrid-notifications-mobile-20260929](../testing/evidence/hybrid-notifications-mobile-20260929.json) |
| `/modern-admin/notifications/<int:notification_id>/acknowledge` | 1 | [hybrid-notification-live-20260921](../testing/evidence/hybrid-notification-live-20260921.json) |
| `/modern-admin/now` | 13 | [hybrid-browser-media-2026-09-08](../testing/evidence/hybrid-browser-media-2026-09-08.json), [hybrid-camera-detection-release-20260921](../testing/evidence/hybrid-camera-detection-release-20260921.json), [hybrid-mobile-navigation-20260921](../testing/evidence/hybrid-mobile-navigation-20260921.json), [hybrid-native-panorama-2026-09-08](../testing/evidence/hybrid-native-panorama-2026-09-08.json), [hybrid-settings-navigation-context-20260921](../testing/evidence/hybrid-settings-navigation-context-20260921.json), [Menu amministratore](../testing/evidence/hybrid-navigation-drawer-20260929.json), [hybrid-sqlite-checkpoint-20260929](../testing/evidence/hybrid-sqlite-checkpoint-20260929.json), [hybrid-storage-estimate-fix-20260929](../testing/evidence/hybrid-storage-estimate-fix-20260929.json) |
| `/modern-admin/observatory` | 1 | [Menu amministratore](../testing/evidence/hybrid-navigation-drawer-20260929.json) |
| `/modern-admin/observatory/astropanel` | 9 | [Menu amministratore](../testing/evidence/hybrid-navigation-drawer-20260929.json), [hybrid-astropanel-timeout-20260929](../testing/evidence/hybrid-astropanel-timeout-20260929.json) |
| `/modern-admin/observatory/charts` | 8 | [hybrid-observatory-native-controls](../testing/evidence/hybrid-observatory-native-controls.json), [Menu amministratore](../testing/evidence/hybrid-navigation-drawer-20260929.json), [hybrid-observatory-timeout-20260929](../testing/evidence/hybrid-observatory-timeout-20260929.json) |
| `/modern-admin/observatory/long-term-keogram` | 3 | [hybrid-observatory-live-20260914](../testing/evidence/hybrid-observatory-live-20260914.json) |
| `/modern-admin/observatory/realtime-keogram` | 1 | [hybrid-observatory-live-20260914](../testing/evidence/hybrid-observatory-live-20260914.json) |
| `/modern-admin/observatory/sensor-panel` | 10 | [hybrid-observatory-native-controls](../testing/evidence/hybrid-observatory-native-controls.json), [Menu amministratore](../testing/evidence/hybrid-navigation-drawer-20260929.json), [hybrid-observatory-timeout-20260929](../testing/evidence/hybrid-observatory-timeout-20260929.json) |
| `/modern-admin/observatory/sqm` | 4 | [hybrid-observatory-live-20260914](../testing/evidence/hybrid-observatory-live-20260914.json), [hybrid-observatory-native-controls](../testing/evidence/hybrid-observatory-native-controls.json), [Menu amministratore](../testing/evidence/hybrid-navigation-drawer-20260929.json) |
| `/modern-admin/observatory/virtualsky` | 6 | [hybrid-observatory-live-20260914](../testing/evidence/hybrid-observatory-live-20260914.json), [hybrid-static-cleanup-20260921](../testing/evidence/hybrid-static-cleanup-20260921.json), [Menu amministratore](../testing/evidence/hybrid-navigation-drawer-20260929.json) |
| `/modern-admin/operations/export` | 0 | Da associare o collaudare |
| `/modern-admin/output` | 28 | [hybrid-generation-guard-live-20260921](../testing/evidence/hybrid-generation-guard-live-20260921.json), [hybrid-day-output-playback-20260921](../testing/evidence/hybrid-day-output-playback-20260921.json), [hybrid-download-delivery-post-classic-20260921](../testing/evidence/hybrid-download-delivery-post-classic-20260921.json), [hybrid-mini-generation-live-20260914](../testing/evidence/hybrid-mini-generation-live-20260914.json), [hybrid-mini-generation-post-classic-20260921](../testing/evidence/hybrid-mini-generation-post-classic-20260921.json), [hybrid-native-panorama-2026-09-08](../testing/evidence/hybrid-native-panorama-2026-09-08.json), [hybrid-product-media-navigation-20260921](../testing/evidence/hybrid-product-media-navigation-20260921.json), [Menu amministratore](../testing/evidence/hybrid-navigation-drawer-20260929.json) |
| `/modern-admin/safe-action/dry-run` | 0 | Da associare o collaudare |
| `/modern-admin/settings` | 14 | [hybrid-mobile-navigation-20260921](../testing/evidence/hybrid-mobile-navigation-20260921.json), [hybrid-settings-navigation-context-20260921](../testing/evidence/hybrid-settings-navigation-context-20260921.json), [hybrid-settings-usability-20260920](../testing/evidence/hybrid-settings-usability-20260920.json), [Menu amministratore](../testing/evidence/hybrid-navigation-drawer-20260929.json), [hybrid-settings-domain-controls-20260929](../testing/evidence/hybrid-settings-domain-controls-20260929.json), [hybrid-sqlite-checkpoint-20260929](../testing/evidence/hybrid-sqlite-checkpoint-20260929.json) |
| `/modern-admin/settings/acquisition-save` | 2 | [hybrid-settings-domain-controls-20260929](../testing/evidence/hybrid-settings-domain-controls-20260929.json) |
| `/modern-admin/settings/advanced` | 6 | [hybrid-settings-domain-controls-20260929](../testing/evidence/hybrid-settings-domain-controls-20260929.json) |
| `/modern-admin/settings/analytics` | 2 | [hybrid-settings-domain-controls-20260929](../testing/evidence/hybrid-settings-domain-controls-20260929.json) |
| `/modern-admin/settings/auto-exposure-gain` | 0 | Da associare o collaudare |
| `/modern-admin/settings/basic` | 2 | [hybrid-settings-domain-controls-20260929](../testing/evidence/hybrid-settings-domain-controls-20260929.json) |
| `/modern-admin/settings/camera-connection` | 0 | Da associare o collaudare |
| `/modern-admin/settings/camera-profile` | 0 | Da associare o collaudare |
| `/modern-admin/settings/cameras` | 4 | [hybrid-mobile-navigation-20260921](../testing/evidence/hybrid-mobile-navigation-20260921.json), [hybrid-settings-navigation-context-20260921](../testing/evidence/hybrid-settings-navigation-context-20260921.json) |
| `/modern-admin/settings/capture` | 0 | Da associare o collaudare |
| `/modern-admin/settings/developer` | 0 | Da associare o collaudare |
| `/modern-admin/settings/exposure-gain` | 0 | Da associare o collaudare |
| `/modern-admin/settings/fits-source` | 2 | [hybrid-settings-domain-controls-20260929](../testing/evidence/hybrid-settings-domain-controls-20260929.json) |
| `/modern-admin/settings/full` | 62 | [hybrid-browser-2026-09-06](../testing/evidence/hybrid-browser-2026-09-06.json), [hybrid-settings-privacy-native-20260920](../testing/evidence/hybrid-settings-privacy-native-20260920.json), [hybrid-settings-usability-20260920](../testing/evidence/hybrid-settings-usability-20260920.json), [Ricerca Settings nel browser](../testing/evidence/hybrid-full-settings-filter-native-20260929.json), [hybrid-settings-chain-20260929](../testing/evidence/hybrid-settings-chain-20260929.json), [hybrid-settings-domain-controls-20260929](../testing/evidence/hybrid-settings-domain-controls-20260929.json) |
| `/modern-admin/settings/hybrid-awb` | 0 | Da associare o collaudare |
| `/modern-admin/settings/notifications` | 0 | Da associare o collaudare |
| `/modern-admin/settings/ready` | 0 | Da associare o collaudare |
| `/modern-admin/settings/storage` | 2 | [hybrid-settings-domain-controls-20260929](../testing/evidence/hybrid-settings-domain-controls-20260929.json) |
| `/modern-admin/settings/storage-protection` | 8 | [hybrid-shared-settings-context-20260929](../testing/evidence/hybrid-shared-settings-context-20260929.json), [hybrid-storage-estimate-fix-20260929](../testing/evidence/hybrid-storage-estimate-fix-20260929.json) |
| `/modern-admin/settings/timelapse` | 5 | [Menu amministratore](../testing/evidence/hybrid-navigation-drawer-20260929.json), [hybrid-shared-settings-context-20260929](../testing/evidence/hybrid-shared-settings-context-20260929.json) |
| `/modern-admin/sky-cycle` | 3 | [hybrid-sky-cycle-navigation-native-20260920](../testing/evidence/hybrid-sky-cycle-navigation-native-20260920.json), [Menu amministratore](../testing/evidence/hybrid-navigation-drawer-20260929.json) |
| `/modern-admin/storage` | 1 | [Menu amministratore](../testing/evidence/hybrid-navigation-drawer-20260929.json) |
| `/modern-admin/storage/drives` | 5 | [hybrid-system-focus-native-20260921](../testing/evidence/hybrid-system-focus-native-20260921.json), [Menu amministratore](../testing/evidence/hybrid-navigation-drawer-20260929.json) |
| `/modern-admin/storage/file-space-usage` | 18 | [hybrid-file-space-native-20260929](../testing/evidence/hybrid-file-space-native-20260929.json), [hybrid-table-blur-20260929](../testing/evidence/hybrid-table-blur-20260929.json) |
| `/modern-admin/system` | 16 | [Menu amministratore](../testing/evidence/hybrid-navigation-drawer-20260929.json), [hybrid-system-index-20260929](../testing/evidence/hybrid-system-index-20260929.json) |
| `/modern-admin/system/config` | 0 | Da associare o collaudare |
| `/modern-admin/system/gpio-control` | 2 | [hybrid-system-focus-native-20260921](../testing/evidence/hybrid-system-focus-native-20260921.json) |
| `/modern-admin/system/info` | 1 | [Menu amministratore](../testing/evidence/hybrid-navigation-drawer-20260929.json) |
| `/modern-admin/system/log` | 7 | [Menu amministratore](../testing/evidence/hybrid-navigation-drawer-20260929.json), [hybrid-log-controller-20260929](../testing/evidence/hybrid-log-controller-20260929.json) |
| `/modern-admin/system/log/<log_name>` | 5 | [hybrid-log-controller-20260929](../testing/evidence/hybrid-log-controller-20260929.json) |
| `/modern-admin/system/network` | 2 | [hybrid-system-focus-native-20260921](../testing/evidence/hybrid-system-focus-native-20260921.json) |
| `/modern-admin/system/support` | 2 | [hybrid-system-focus-native-20260921](../testing/evidence/hybrid-system-focus-native-20260921.json), [hybrid-system-index-20260929](../testing/evidence/hybrid-system-index-20260929.json) |
| `/modern-admin/tasks` | 28 | [hybrid-download-delivery-post-classic-20260921](../testing/evidence/hybrid-download-delivery-post-classic-20260921.json), [hybrid-operations-2026-09-06](../testing/evidence/hybrid-operations-2026-09-06.json), [hybrid-operations-live-20260914](../testing/evidence/hybrid-operations-live-20260914.json), [Menu amministratore](../testing/evidence/hybrid-navigation-drawer-20260929.json), [hybrid-task-table-native-20260929](../testing/evidence/hybrid-task-table-native-20260929.json) |
| `/modern-admin/tasks/<int:task_id>` | 12 | [hybrid-generation-guard-live-20260921](../testing/evidence/hybrid-generation-guard-live-20260921.json), [hybrid-day-output-playback-20260921](../testing/evidence/hybrid-day-output-playback-20260921.json), [hybrid-mini-generation-post-classic-20260921](../testing/evidence/hybrid-mini-generation-post-classic-20260921.json), [hybrid-operations-2026-09-06](../testing/evidence/hybrid-operations-2026-09-06.json), [hybrid-satellite-recheck-20260921](../testing/evidence/hybrid-satellite-recheck-20260921.json), [hybrid-task-table-native-20260929](../testing/evidence/hybrid-task-table-native-20260929.json) |
| `/modern-admin/tools/camera-simulator` | 8 | [hybrid-simulator-2026-09-06](../testing/evidence/hybrid-simulator-2026-09-06.json), [Menu amministratore](../testing/evidence/hybrid-navigation-drawer-20260929.json) |
| `/modern-admin/tools/focus` | 8 | [hybrid-system-focus-native-20260921](../testing/evidence/hybrid-system-focus-native-20260921.json), [Menu amministratore](../testing/evidence/hybrid-navigation-drawer-20260929.json) |
| `/modern-admin/tools/focus/preview` | 1 | [Contratto API/redirect isolato](../testing/evidence/hybrid-current-discovery-20260921.json) |
| `/modern-admin/tools/generate` | 22 | [hybrid-end-of-night-pipeline-2026-09-08](../testing/evidence/hybrid-end-of-night-pipeline-2026-09-08.json), [hybrid-generation-2026-09-06](../testing/evidence/hybrid-generation-2026-09-06.json), [hybrid-keogram-encoding-2026-09-08](../testing/evidence/hybrid-keogram-encoding-2026-09-08.json), [hybrid-real-encoding-2026-09-08](../testing/evidence/hybrid-real-encoding-2026-09-08.json), [hybrid-startrail-empty-2026-09-08](../testing/evidence/hybrid-startrail-empty-2026-09-08.json) |
| `/modern-admin/tools/image-circle-helper` | 13 | [hybrid-geometry-2026-09-06](../testing/evidence/hybrid-geometry-2026-09-06.json) |
| `/modern-admin/tools/mini-generate` | 18 | [hybrid-generation-guard-live-20260921](../testing/evidence/hybrid-generation-guard-live-20260921.json), [hybrid-generated-media-2026-09-06](../testing/evidence/hybrid-generated-media-2026-09-06.json), [hybrid-mini-generation-live-20260914](../testing/evidence/hybrid-mini-generation-live-20260914.json), [hybrid-mini-generation-post-classic-20260921](../testing/evidence/hybrid-mini-generation-post-classic-20260921.json), [hybrid-real-encoding-2026-09-08](../testing/evidence/hybrid-real-encoding-2026-09-08.json) |
| `/modern-admin/tools/mini-preview` | 1 | [Contratto API/redirect isolato](../testing/evidence/hybrid-current-discovery-20260921.json) |
| `/modern-admin/tools/process-fits` | 10 | [hybrid-fits-processing-2026-09-06](../testing/evidence/hybrid-fits-processing-2026-09-06.json) |
| `/modern-admin/updates` | 1 | [Menu amministratore](../testing/evidence/hybrid-navigation-drawer-20260929.json) |
| `/modern-admin/updates/start` | 0 | Da associare o collaudare |
| `/modern-admin/uploads` | 8 | [Upload inspection](../testing/evidence/hybrid-upload-management-layout-20260929.json), [Menu amministratore](../testing/evidence/hybrid-navigation-drawer-20260929.json) |
| `/modern-admin/uploads/<provider_slug>` | 4 | [Upload inspection](../testing/evidence/hybrid-upload-management-layout-20260929.json) |
| `/modern-admin/users` | 50 | [hybrid-native-users-2026-09-08](../testing/evidence/hybrid-native-users-2026-09-08.json), [Menu amministratore](../testing/evidence/hybrid-navigation-drawer-20260929.json), [hybrid-settings-chain-20260929](../testing/evidence/hybrid-settings-chain-20260929.json), [hybrid-users-clipboard-live-20260929](../testing/evidence/hybrid-users-clipboard-live-20260929.json), [hybrid-users-native-controls-20260929](../testing/evidence/hybrid-users-native-controls-20260929.json) |
| `/modern-admin/users/<int:user_id>` | 5 | [hybrid-users-native-controls-20260929](../testing/evidence/hybrid-users-native-controls-20260929.json) |
| `/modern-admin/youtube` | 8 | [hybrid-youtube-2026-09-06](../testing/evidence/hybrid-youtube-2026-09-06.json), [Menu amministratore](../testing/evidence/hybrid-navigation-drawer-20260929.json) |

## Passaggi ancora necessari

- Completare le associazioni delle evidenze con schemi annidati e dei contratti pubblici; la presenza nel registro non sostituisce una prova funzionale.
- Censire i controlli generati nel DOM, modalita' mobili, ruoli, prerequisiti, richieste ed effetti osservabili ancora mancanti.
- Ricontrollare le prove invalidate da modifiche successive; mantenere separati test automatici, browser isolato e produzione.
- I controlli bloccati restano aperti. Completare il collaudo senza Classic prima della rimozione fisica; le 24 ore restano rinviate.

## Public media HTTP acceptance, 21 September 2026

[Production evidence](../testing/evidence/hybrid-public-families-live-20260921.json) covers all 17 latest-media routes on both cameras: 30 ranged responses matched recorded files and four RAW requests returned the explicit empty state. Individual cases are linked in the JSON route register. This does not certify full-file or native Mac download delivery, nor delivery of absent RAW data. The verifier corrected its HTML range handling and thumbnail model lookup; the original observations remain on the Pi. No runtime change was necessary.

## Notification acceptance recorded 29 September 2026

[Native production evidence](../testing/evidence/hybrid-notification-live-20260921.json) records the 21 September administrator flow: dedicated expired notice 199 acknowledged, persistence verified, 198 pre-existing acknowledgement states preserved. Filters, search, paging, seven-column sorting, copy and keyboard detail are recorded individually in the JSON register. CSV/Excel receipt remains blocked; ordinary/anonymous role checks are separately identified as isolated tests. The report hash, installed revision and retained acknowledgement were rechecked on 29 September; this is not continuous observation.

## Storage estimate and Settings acceptance, 29 September 2026

[Release evidence](../testing/evidence/hybrid-storage-estimate-fix-20260929.json) records the corrected live capacity estimate, invalid-threshold rejection, Settings navigation, same-value save to revision 118 and Tasks navigation. All persisted values equal revision 117. Both current camera images decoded after web-only deploy. No cleanup was invoked; native field toggling and live deletion are not implied by the same-value save.

## Notifications mobile acceptance — 29 September 2026

[Six scoped records](../testing/evidence/hybrid-notifications-mobile-20260929.json) cover administrator search, acknowledgement filtering, keyboard detail navigation, return navigation and measured layout at 390/320 px. The JSON register links each record to its route. No mutation was submitted; export receipt, touchscreen scrolling and other roles remain outside this check.

Discovery aggiornata il 29 settembre sul runtime `970d1799`: 99 ingressi GET, 505 contesti, 376 rendering riusciti e 129 bloccati/reindirizzati; nessun difetto di rendering o segnale delle frasi placeholder cercate. Il nuovo indice comprende 7.368 identità statiche e conserva tutti i 43.978 riferimenti. Quaranta contesti hanno identità diverse dopo le correzioni ai link. Conteggi e fingerprint aggiornati sono nel JSON; nessuna interazione viene dichiarata superata da questa discovery. Le prove del 29 settembre erano già associate e non sono duplicate.

[Dodici verifiche Task del 29 settembre](../testing/evidence/hybrid-task-table-native-20260929.json) coprono filtri, ricerca, dettaglio da tastiera, collegamento all’output, ritorno, ordinamento ID e paginazione con amministratore. I riferimenti puntuali sono nel JSON; export e altre colonne di ordinamento restano fuori da questa prova.

Il controllo del menu del 29 settembre verifica 41 ingressi tramite click nativi
sul Raspberry, con destinazione e contenuto della pagina osservati. Riguarda
soltanto la navigazione in sessione amministratore; non certifica tutte le azioni
delle pagine o gli altri ruoli. Le voci storiche di Settings sono dentro un
riferimento tecnico chiuso, distinto dai sei editor operativi.
