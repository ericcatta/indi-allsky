# Registro delle evidenze per route Hybrid

Route rilevate dalla `url_map` Flask del candidato `0e6f445c`, avviato in ambiente isolato con Classic disabilitato: **107 ingressi Hybrid e 151 route con altri percorsi (autenticazione, API, asset e compatibilita')**. Il JSON include anche queste ultime. La registrazione di una route non prova il suo funzionamento.

Gli esiti sono riferimenti puntuali alle prove originali, che specificano revisione, ambiente, ruolo, camera/profilo e limiti quando verificati. I record storici restano storici. Il numero di record non e' una percentuale di copertura e non certifica tutti i controlli della pagina.

[Registro completo con riferimenti ai singoli controlli](hybrid-acceptance-route-register.json).
Censimento aggiornato del commit installato `f6975d5f`: 99 ingressi GET, 505 contesti, 376 rendering riusciti, 129 contesti bloccati e nessun errore di rendering. Il report contiene 43.978 occorrenze di controlli, comprese ripetizioni fra ruoli e camere; nessun click viene certificato dal solo censimento. Percorso, hash e limiti sono nel campo `current_control_discovery` del JSON.


| Route Hybrid attuale | Record associati | Fonti |
| --- | ---: | --- |
| `/modern-admin` | 0 | Da associare o collaudare |
| `/modern-admin/account` | 17 | [hybrid-account-native-20260914](../testing/evidence/hybrid-account-native-20260914.json), [hybrid-browser-2026-09-06](../testing/evidence/hybrid-browser-2026-09-06.json), [hybrid-native-users-2026-09-08](../testing/evidence/hybrid-native-users-2026-09-08.json) |
| `/modern-admin/cameras` | 0 | Da associare o collaudare |
| `/modern-admin/cameras/add` | 0 | Da associare o collaudare |
| `/modern-admin/cameras/adu-history` | 0 | Da associare o collaudare |
| `/modern-admin/cameras/dark-library` | 0 | Da associare o collaudare |
| `/modern-admin/cameras/detect-indi` | 0 | Da associare o collaudare |
| `/modern-admin/cameras/image-lag` | 12 | [hybrid-image-lag-native-20260920](../testing/evidence/hybrid-image-lag-native-20260920.json) |
| `/modern-admin/cameras/info` | 2 | [hybrid-camera-info-navigation-20260920](../testing/evidence/hybrid-camera-info-navigation-20260920.json) |
| `/modern-admin/cameras/mask-base` | 0 | Da associare o collaudare |
| `/modern-admin/cameras/start-indi` | 0 | Da associare o collaudare |
| `/modern-admin/capture/abort-exposure` | 0 | Da associare o collaudare |
| `/modern-admin/capture/service` | 0 | Da associare o collaudare |
| `/modern-admin/classic/<classic_page>` | 0 | Da associare o collaudare |
| `/modern-admin/config-history` | 3 | [hybrid-browser-2026-09-06](../testing/evidence/hybrid-browser-2026-09-06.json) |
| `/modern-admin/config-restore` | 3 | [hybrid-browser-2026-09-06](../testing/evidence/hybrid-browser-2026-09-06.json) |
| `/modern-admin/config-restore/<int:config_id>` | 2 | [hybrid-browser-2026-09-06](../testing/evidence/hybrid-browser-2026-09-06.json) |
| `/modern-admin/config-restore/<int:config_id>/apply` | 0 | Da associare o collaudare |
| `/modern-admin/fits` | 2 | [hybrid-source-media-2026-09-06](../testing/evidence/hybrid-source-media-2026-09-06.json) |
| `/modern-admin/fits/<int:fits_id>` | 4 | [hybrid-fits-dimensions-live-20260914](../testing/evidence/hybrid-fits-dimensions-live-20260914.json), [hybrid-source-media-2026-09-06](../testing/evidence/hybrid-source-media-2026-09-06.json) |
| `/modern-admin/highlights` | 0 | Da associare o collaudare |
| `/modern-admin/library` | 32 | [hybrid-browser-media-2026-09-08](../testing/evidence/hybrid-browser-media-2026-09-08.json), [hybrid-library-live-20260914](../testing/evidence/hybrid-library-live-20260914.json), [hybrid-mini-generation-live-20260914](../testing/evidence/hybrid-mini-generation-live-20260914.json), [hybrid-sky-cycle-navigation-native-20260920](../testing/evidence/hybrid-sky-cycle-navigation-native-20260920.json) |
| `/modern-admin/loop` | 0 | Da associare o collaudare |
| `/modern-admin/media/<kind>/<int:camera_id>/<int:media_id>/download` | 0 | Da associare o collaudare |
| `/modern-admin/media/archive` | 15 | [hybrid-archive-2026-09-06](../testing/evidence/hybrid-archive-2026-09-06.json) |
| `/modern-admin/media/fits` | 6 | [hybrid-fits-dimensions-live-20260914](../testing/evidence/hybrid-fits-dimensions-live-20260914.json), [hybrid-source-media-2026-09-06](../testing/evidence/hybrid-source-media-2026-09-06.json) |
| `/modern-admin/media/gallery` | 0 | Da associare o collaudare |
| `/modern-admin/media/gallery/page` | 0 | Da associare o collaudare |
| `/modern-admin/media/images` | 0 | Da associare o collaudare |
| `/modern-admin/media/images/<int:image_id>` | 1 | [hybrid-sky-cycle-navigation-native-20260920](../testing/evidence/hybrid-sky-cycle-navigation-native-20260920.json) |
| `/modern-admin/media/keograms` | 9 | [hybrid-generated-media-2026-09-06](../testing/evidence/hybrid-generated-media-2026-09-06.json) |
| `/modern-admin/media/mini-timelapses` | 9 | [hybrid-generated-media-2026-09-06](../testing/evidence/hybrid-generated-media-2026-09-06.json) |
| `/modern-admin/media/panorama` | 9 | [hybrid-generated-media-2026-09-06](../testing/evidence/hybrid-generated-media-2026-09-06.json) |
| `/modern-admin/media/panorama-loop` | 13 | [hybrid-native-panorama-2026-09-08](../testing/evidence/hybrid-native-panorama-2026-09-08.json) |
| `/modern-admin/media/public-endpoints` | 0 | Da associare o collaudare |
| `/modern-admin/media/raw` | 3 | [hybrid-source-media-2026-09-06](../testing/evidence/hybrid-source-media-2026-09-06.json) |
| `/modern-admin/media/raw-loop` | 0 | Da associare o collaudare |
| `/modern-admin/media/startrail-videos` | 9 | [hybrid-generated-media-2026-09-06](../testing/evidence/hybrid-generated-media-2026-09-06.json) |
| `/modern-admin/media/startrails` | 9 | [hybrid-generated-media-2026-09-06](../testing/evidence/hybrid-generated-media-2026-09-06.json) |
| `/modern-admin/media/timelapses` | 0 | Da associare o collaudare |
| `/modern-admin/media/timelapses/<int:video_id>` | 0 | Da associare o collaudare |
| `/modern-admin/mode/<mode>` | 0 | Da associare o collaudare |
| `/modern-admin/moment` | 0 | Da associare o collaudare |
| `/modern-admin/notifications` | 5 | [hybrid-operations-2026-09-06](../testing/evidence/hybrid-operations-2026-09-06.json), [hybrid-operations-live-20260914](../testing/evidence/hybrid-operations-live-20260914.json) |
| `/modern-admin/notifications/<int:notification_id>` | 5 | [hybrid-operations-2026-09-06](../testing/evidence/hybrid-operations-2026-09-06.json), [hybrid-operations-live-20260914](../testing/evidence/hybrid-operations-live-20260914.json) |
| `/modern-admin/notifications/<int:notification_id>/acknowledge` | 0 | Da associare o collaudare |
| `/modern-admin/now` | 5 | [hybrid-browser-media-2026-09-08](../testing/evidence/hybrid-browser-media-2026-09-08.json), [hybrid-native-panorama-2026-09-08](../testing/evidence/hybrid-native-panorama-2026-09-08.json) |
| `/modern-admin/observatory` | 0 | Da associare o collaudare |
| `/modern-admin/observatory/astropanel` | 0 | Da associare o collaudare |
| `/modern-admin/observatory/charts` | 3 | [hybrid-observatory-native-controls](../testing/evidence/hybrid-observatory-native-controls.json) |
| `/modern-admin/observatory/long-term-keogram` | 3 | [hybrid-observatory-live-20260914](../testing/evidence/hybrid-observatory-live-20260914.json) |
| `/modern-admin/observatory/realtime-keogram` | 1 | [hybrid-observatory-live-20260914](../testing/evidence/hybrid-observatory-live-20260914.json) |
| `/modern-admin/observatory/sensor-panel` | 4 | [hybrid-observatory-native-controls](../testing/evidence/hybrid-observatory-native-controls.json) |
| `/modern-admin/observatory/sqm` | 3 | [hybrid-observatory-live-20260914](../testing/evidence/hybrid-observatory-live-20260914.json), [hybrid-observatory-native-controls](../testing/evidence/hybrid-observatory-native-controls.json) |
| `/modern-admin/observatory/virtualsky` | 2 | [hybrid-observatory-live-20260914](../testing/evidence/hybrid-observatory-live-20260914.json) |
| `/modern-admin/operations/export` | 0 | Da associare o collaudare |
| `/modern-admin/output` | 5 | [hybrid-mini-generation-live-20260914](../testing/evidence/hybrid-mini-generation-live-20260914.json), [hybrid-mini-generation-post-classic-20260921](../testing/evidence/hybrid-mini-generation-post-classic-20260921.json), [hybrid-native-panorama-2026-09-08](../testing/evidence/hybrid-native-panorama-2026-09-08.json) |
| `/modern-admin/safe-action/dry-run` | 0 | Da associare o collaudare |
| `/modern-admin/settings` | 1 | [hybrid-settings-usability-20260920](../testing/evidence/hybrid-settings-usability-20260920.json) |
| `/modern-admin/settings/acquisition-save` | 0 | Da associare o collaudare |
| `/modern-admin/settings/advanced` | 0 | Da associare o collaudare |
| `/modern-admin/settings/analytics` | 0 | Da associare o collaudare |
| `/modern-admin/settings/auto-exposure-gain` | 0 | Da associare o collaudare |
| `/modern-admin/settings/basic` | 0 | Da associare o collaudare |
| `/modern-admin/settings/camera-connection` | 0 | Da associare o collaudare |
| `/modern-admin/settings/camera-profile` | 0 | Da associare o collaudare |
| `/modern-admin/settings/cameras` | 0 | Da associare o collaudare |
| `/modern-admin/settings/capture` | 0 | Da associare o collaudare |
| `/modern-admin/settings/developer` | 0 | Da associare o collaudare |
| `/modern-admin/settings/exposure-gain` | 0 | Da associare o collaudare |
| `/modern-admin/settings/fits-source` | 0 | Da associare o collaudare |
| `/modern-admin/settings/full` | 15 | [hybrid-browser-2026-09-06](../testing/evidence/hybrid-browser-2026-09-06.json), [hybrid-settings-privacy-native-20260920](../testing/evidence/hybrid-settings-privacy-native-20260920.json), [hybrid-settings-usability-20260920](../testing/evidence/hybrid-settings-usability-20260920.json) |
| `/modern-admin/settings/hybrid-awb` | 0 | Da associare o collaudare |
| `/modern-admin/settings/notifications` | 0 | Da associare o collaudare |
| `/modern-admin/settings/ready` | 0 | Da associare o collaudare |
| `/modern-admin/settings/storage` | 0 | Da associare o collaudare |
| `/modern-admin/settings/storage-protection` | 0 | Da associare o collaudare |
| `/modern-admin/settings/timelapse` | 0 | Da associare o collaudare |
| `/modern-admin/sky-cycle` | 2 | [hybrid-sky-cycle-navigation-native-20260920](../testing/evidence/hybrid-sky-cycle-navigation-native-20260920.json) |
| `/modern-admin/storage` | 0 | Da associare o collaudare |
| `/modern-admin/storage/drives` | 0 | Da associare o collaudare |
| `/modern-admin/storage/file-space-usage` | 0 | Da associare o collaudare |
| `/modern-admin/system` | 0 | Da associare o collaudare |
| `/modern-admin/system/config` | 0 | Da associare o collaudare |
| `/modern-admin/system/gpio-control` | 0 | Da associare o collaudare |
| `/modern-admin/system/info` | 0 | Da associare o collaudare |
| `/modern-admin/system/log` | 0 | Da associare o collaudare |
| `/modern-admin/system/log/<log_name>` | 0 | Da associare o collaudare |
| `/modern-admin/system/network` | 0 | Da associare o collaudare |
| `/modern-admin/system/support` | 0 | Da associare o collaudare |
| `/modern-admin/tasks` | 15 | [hybrid-operations-2026-09-06](../testing/evidence/hybrid-operations-2026-09-06.json), [hybrid-operations-live-20260914](../testing/evidence/hybrid-operations-live-20260914.json) |
| `/modern-admin/tasks/<int:task_id>` | 3 | [hybrid-mini-generation-post-classic-20260921](../testing/evidence/hybrid-mini-generation-post-classic-20260921.json), [hybrid-operations-2026-09-06](../testing/evidence/hybrid-operations-2026-09-06.json) |
| `/modern-admin/tools/camera-simulator` | 7 | [hybrid-simulator-2026-09-06](../testing/evidence/hybrid-simulator-2026-09-06.json) |
| `/modern-admin/tools/focus` | 0 | Da associare o collaudare |
| `/modern-admin/tools/focus/preview` | 0 | Da associare o collaudare |
| `/modern-admin/tools/generate` | 22 | [hybrid-end-of-night-pipeline-2026-09-08](../testing/evidence/hybrid-end-of-night-pipeline-2026-09-08.json), [hybrid-generation-2026-09-06](../testing/evidence/hybrid-generation-2026-09-06.json), [hybrid-keogram-encoding-2026-09-08](../testing/evidence/hybrid-keogram-encoding-2026-09-08.json), [hybrid-real-encoding-2026-09-08](../testing/evidence/hybrid-real-encoding-2026-09-08.json), [hybrid-startrail-empty-2026-09-08](../testing/evidence/hybrid-startrail-empty-2026-09-08.json) |
| `/modern-admin/tools/image-circle-helper` | 13 | [hybrid-geometry-2026-09-06](../testing/evidence/hybrid-geometry-2026-09-06.json) |
| `/modern-admin/tools/mini-generate` | 16 | [hybrid-generated-media-2026-09-06](../testing/evidence/hybrid-generated-media-2026-09-06.json), [hybrid-mini-generation-live-20260914](../testing/evidence/hybrid-mini-generation-live-20260914.json), [hybrid-mini-generation-post-classic-20260921](../testing/evidence/hybrid-mini-generation-post-classic-20260921.json), [hybrid-real-encoding-2026-09-08](../testing/evidence/hybrid-real-encoding-2026-09-08.json) |
| `/modern-admin/tools/mini-preview` | 0 | Da associare o collaudare |
| `/modern-admin/tools/process-fits` | 10 | [hybrid-fits-processing-2026-09-06](../testing/evidence/hybrid-fits-processing-2026-09-06.json) |
| `/modern-admin/updates` | 0 | Da associare o collaudare |
| `/modern-admin/updates/start` | 0 | Da associare o collaudare |
| `/modern-admin/uploads` | 0 | Da associare o collaudare |
| `/modern-admin/uploads/<provider_slug>` | 0 | Da associare o collaudare |
| `/modern-admin/users` | 17 | [hybrid-native-users-2026-09-08](../testing/evidence/hybrid-native-users-2026-09-08.json) |
| `/modern-admin/users/<int:user_id>` | 0 | Da associare o collaudare |
| `/modern-admin/youtube` | 7 | [hybrid-youtube-2026-09-06](../testing/evidence/hybrid-youtube-2026-09-06.json) |

## Passaggi ancora necessari

- Completare le associazioni delle evidenze con schemi annidati e dei contratti pubblici; la presenza nel registro non sostituisce una prova funzionale.
- Censire i controlli generati nel DOM, modalita' mobili, ruoli, prerequisiti, richieste ed effetti osservabili ancora mancanti.
- Ricontrollare le prove invalidate da modifiche successive; mantenere separati test automatici, browser isolato e produzione.
- I controlli bloccati restano aperti. Completare il collaudo senza Classic prima della rimozione fisica; le 24 ore restano rinviate.
