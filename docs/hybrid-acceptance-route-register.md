# Registro delle evidenze per route Hybrid

Baseline del codice: `4122b122`. Questo registro collega prove storiche con pagina e controllo espliciti alle route letterali di `register_hybrid_routes`. Non certifica il prodotto attuale e non sostituisce il censimento completo del DOM.

Gli esiti dei singoli controlli, con il riferimento preciso al record originale, sono conservati in [hybrid-acceptance-route-register.json](hybrid-acceptance-route-register.json). Le evidenze con schemi diversi restano da associare; nessuna assenza di corrispondenza equivale a una funzione mancante.

| Route nel codice attuale | Record storici associati | Fonti |
| --- | ---: | --- |
| `/modern-admin` | 0 | Da associare o collaudare |
| `/modern-admin/account` | 7 | [hybrid-browser-2026-09-06](../testing/evidence/hybrid-browser-2026-09-06.json), [hybrid-native-users-2026-09-08](../testing/evidence/hybrid-native-users-2026-09-08.json) |
| `/modern-admin/cameras` | 0 | Da associare o collaudare |
| `/modern-admin/cameras/add` | 0 | Da associare o collaudare |
| `/modern-admin/cameras/adu-history` | 0 | Da associare o collaudare |
| `/modern-admin/cameras/dark-library` | 0 | Da associare o collaudare |
| `/modern-admin/cameras/detect-indi` | 0 | Da associare o collaudare |
| `/modern-admin/cameras/image-lag` | 0 | Da associare o collaudare |
| `/modern-admin/cameras/info` | 0 | Da associare o collaudare |
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
| `/modern-admin/fits/<int:fits_id>` | 2 | [hybrid-source-media-2026-09-06](../testing/evidence/hybrid-source-media-2026-09-06.json) |
| `/modern-admin/highlights` | 0 | Da associare o collaudare |
| `/modern-admin/library` | 3 | [hybrid-browser-media-2026-09-08](../testing/evidence/hybrid-browser-media-2026-09-08.json) |
| `/modern-admin/loop` | 0 | Da associare o collaudare |
| `/modern-admin/media/<kind>/<int:camera_id>/<int:media_id>/download` | 0 | Da associare o collaudare |
| `/modern-admin/media/archive` | 15 | [hybrid-archive-2026-09-06](../testing/evidence/hybrid-archive-2026-09-06.json) |
| `/modern-admin/media/fits` | 4 | [hybrid-source-media-2026-09-06](../testing/evidence/hybrid-source-media-2026-09-06.json) |
| `/modern-admin/media/gallery` | 0 | Da associare o collaudare |
| `/modern-admin/media/gallery/page` | 0 | Da associare o collaudare |
| `/modern-admin/media/images` | 0 | Da associare o collaudare |
| `/modern-admin/media/images/<int:image_id>` | 0 | Da associare o collaudare |
| `/modern-admin/media/keograms` | 9 | [hybrid-generated-media-2026-09-06](../testing/evidence/hybrid-generated-media-2026-09-06.json) |
| `/modern-admin/media/mini-timelapses` | 9 | [hybrid-generated-media-2026-09-06](../testing/evidence/hybrid-generated-media-2026-09-06.json) |
| `/modern-admin/media/panorama` | 9 | [hybrid-generated-media-2026-09-06](../testing/evidence/hybrid-generated-media-2026-09-06.json) |
| `/modern-admin/media/panorama-loop` | 0 | Da associare o collaudare |
| `/modern-admin/media/public-endpoints` | 0 | Da associare o collaudare |
| `/modern-admin/media/raw` | 3 | [hybrid-source-media-2026-09-06](../testing/evidence/hybrid-source-media-2026-09-06.json) |
| `/modern-admin/media/raw-loop` | 0 | Da associare o collaudare |
| `/modern-admin/media/startrail-videos` | 9 | [hybrid-generated-media-2026-09-06](../testing/evidence/hybrid-generated-media-2026-09-06.json) |
| `/modern-admin/media/startrails` | 9 | [hybrid-generated-media-2026-09-06](../testing/evidence/hybrid-generated-media-2026-09-06.json) |
| `/modern-admin/media/timelapses` | 0 | Da associare o collaudare |
| `/modern-admin/media/timelapses/<int:video_id>` | 0 | Da associare o collaudare |
| `/modern-admin/mode/<mode>` | 0 | Da associare o collaudare |
| `/modern-admin/moment` | 0 | Da associare o collaudare |
| `/modern-admin/notifications` | 4 | [hybrid-operations-2026-09-06](../testing/evidence/hybrid-operations-2026-09-06.json) |
| `/modern-admin/notifications/<int:notification_id>` | 3 | [hybrid-operations-2026-09-06](../testing/evidence/hybrid-operations-2026-09-06.json) |
| `/modern-admin/notifications/<int:notification_id>/acknowledge` | 0 | Da associare o collaudare |
| `/modern-admin/now` | 2 | [hybrid-browser-media-2026-09-08](../testing/evidence/hybrid-browser-media-2026-09-08.json) |
| `/modern-admin/observatory` | 0 | Da associare o collaudare |
| `/modern-admin/observatory/astropanel` | 0 | Da associare o collaudare |
| `/modern-admin/observatory/charts` | 0 | Da associare o collaudare |
| `/modern-admin/observatory/long-term-keogram` | 0 | Da associare o collaudare |
| `/modern-admin/observatory/realtime-keogram` | 0 | Da associare o collaudare |
| `/modern-admin/observatory/sensor-panel` | 0 | Da associare o collaudare |
| `/modern-admin/observatory/sqm` | 0 | Da associare o collaudare |
| `/modern-admin/observatory/virtualsky` | 0 | Da associare o collaudare |
| `/modern-admin/operations/export` | 0 | Da associare o collaudare |
| `/modern-admin/output` | 0 | Da associare o collaudare |
| `/modern-admin/safe-action/dry-run` | 0 | Da associare o collaudare |
| `/modern-admin/settings` | 0 | Da associare o collaudare |
| `/modern-admin/settings/acquisition-save` | 0 | Da associare o collaudare |
| `/modern-admin/settings/advanced` | 0 | Da associare o collaudare |
| `/modern-admin/settings/analytics` | 0 | Da associare o collaudare |
| `/modern-admin/settings/basic` | 0 | Da associare o collaudare |
| `/modern-admin/settings/cameras` | 0 | Da associare o collaudare |
| `/modern-admin/settings/capture` | 0 | Da associare o collaudare |
| `/modern-admin/settings/developer` | 0 | Da associare o collaudare |
| `/modern-admin/settings/fits-source` | 0 | Da associare o collaudare |
| `/modern-admin/settings/full` | 4 | [hybrid-browser-2026-09-06](../testing/evidence/hybrid-browser-2026-09-06.json) |
| `/modern-admin/settings/notifications` | 0 | Da associare o collaudare |
| `/modern-admin/settings/ready` | 0 | Da associare o collaudare |
| `/modern-admin/settings/storage` | 0 | Da associare o collaudare |
| `/modern-admin/settings/timelapse` | 0 | Da associare o collaudare |
| `/modern-admin/sky-cycle` | 0 | Da associare o collaudare |
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
| `/modern-admin/tasks` | 11 | [hybrid-operations-2026-09-06](../testing/evidence/hybrid-operations-2026-09-06.json) |
| `/modern-admin/tasks/<int:task_id>` | 1 | [hybrid-operations-2026-09-06](../testing/evidence/hybrid-operations-2026-09-06.json) |
| `/modern-admin/tools/camera-simulator` | 7 | [hybrid-simulator-2026-09-06](../testing/evidence/hybrid-simulator-2026-09-06.json) |
| `/modern-admin/tools/focus` | 0 | Da associare o collaudare |
| `/modern-admin/tools/focus/preview` | 0 | Da associare o collaudare |
| `/modern-admin/tools/generate` | 22 | [hybrid-end-of-night-pipeline-2026-09-08](../testing/evidence/hybrid-end-of-night-pipeline-2026-09-08.json), [hybrid-generation-2026-09-06](../testing/evidence/hybrid-generation-2026-09-06.json), [hybrid-keogram-encoding-2026-09-08](../testing/evidence/hybrid-keogram-encoding-2026-09-08.json), [hybrid-real-encoding-2026-09-08](../testing/evidence/hybrid-real-encoding-2026-09-08.json), [hybrid-startrail-empty-2026-09-08](../testing/evidence/hybrid-startrail-empty-2026-09-08.json) |
| `/modern-admin/tools/image-circle-helper` | 13 | [hybrid-geometry-2026-09-06](../testing/evidence/hybrid-geometry-2026-09-06.json) |
| `/modern-admin/tools/mini-generate` | 11 | [hybrid-generated-media-2026-09-06](../testing/evidence/hybrid-generated-media-2026-09-06.json), [hybrid-real-encoding-2026-09-08](../testing/evidence/hybrid-real-encoding-2026-09-08.json) |
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

- Rigenerare il censimento sul codice corrente nella prossima finestra: gli inventari locali disponibili riportano 90–91 pagine di revisioni precedenti.
- Includere le route registrate negli altri moduli, i contratti pubblici e i controlli creati dinamicamente.
- Per ogni controllo, collegare ruolo, camera/profilo, prerequisiti, richiesta ed effetto osservato; ricontrollare le prove invalidate da modifiche successive.
- Mantenere separati esito storico, prova automatica, browser sintetico e produzione. I casi bloccati restano aperti.
- Completare il collaudo con Classic disabilitato prima della rimozione fisica. Il test di 24 ore resta rinviato.
