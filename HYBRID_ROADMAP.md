# Hybrid AllSky Roadmap

Questo e' il documento operativo principale del progetto Hybrid AllSky.
Ogni task futuro deve leggere questo file prima di iniziare e aggiornarlo quando introduce decisioni, modifiche, nuove evidenze o nuovi rischi.

## Obiettivo

- Sistema AllSky multicamera stabile e realmente per-camera.
- ZWO ASI678MC come camera principale zenitale.
- Raspberry Camera Module 3 Wide IMX708 come seconda camera orientata piu' verso sud.
- Interfaccia web moderna, chiara e professionale.
- Configurazione organizzata in:
  - Basic: parametri operativi quotidiani.
  - Advanced: opzioni utili ma non necessarie nella gestione normale.
  - Developer: diagnostica, esperimenti, compatibilita' legacy e parametri rischiosi.

## Architettura e Decisioni

- Codex lavora sul repository locale, non ha accesso diretto al Raspberry.
- Il Raspberry riceve modifiche tramite `git pull`.
- I test runtime reali vanno eseguiti sul Raspberry dopo pull/restart.
- Le modifiche runtime devono restare conservative: niente refactor ampi senza motivo.
- Le impostazioni operative multicamera devono vivere nei Camera Profiles.
- I global settings restano fallback legacy/single-camera/advanced, non UI operativa primaria.
- Nuove funzioni attive solo dietro toggle esplicito o in modalita' diagnostica/shadow.
- Ogni camera/profilo deve avere stato runtime separato per exposure, gain, ADU, metering, Hybrid AWB e Auto Exposure.

## Stato Attuale

- Multicamera attiva con profili separati:
  - `asi678mc`: ZWO ASI678MC, camera principale zenitale, INDI.
  - `imx708-wide`: Raspberry Camera Module 3 Wide, camera secondaria verso sud, libcamera.
- ASI678MC:
  - `processing_mode=hybrid`.
  - `hybrid.awb.apply_mode=postprocess_rgb`.
  - gain day atteso `0`.
  - gain night atteso `220`.
  - gain moonmode atteso `75`.
  - CFA/processing runtime verificati: `CFA_PATTERN=RGGB`, `CCD_BIT_DEPTH=16`, `AUTO_WB_DAY=True`.
- IMX708:
  - `processing_mode=hybrid`.
  - `hybrid.awb.apply_mode=postprocess_rgb`.
  - gain day effettivo `1.13` per clamp minimo libcamera.
  - gain night/moonmode `16`.
- La sovraesposizione ASI diurna e' stata confermata come saturazione raw FITS quando l'exposure sale troppo, non come artefatto creato da debayer, stretch, JPEG o Hybrid AWB.

## DONE

### Modern Admin e Configurazione

- Modern Admin e' diventato il centro operativo principale.
- Camera Profile Settings e' il punto operativo per gain, exposure, target ADU, AWB, processing e Auto Exposure.
- Global Capture Defaults / Full Settings sono stati de-enfatizzati come fallback legacy/advanced.
- Aggiunti badge e messaggi per distinguere:
  - Per-camera.
  - Global.
  - Legacy fallback.
  - Read-only.
- Modern Cameras page mostra profili multicamera e link Settings per profilo.
- Gallery Modern supporta filtro camera/profile e mantiene il filtro con infinite scroll.
- Topbar Modern Admin include toggle Start/Stop Capture, Restart indi-allsky e badge stato servizio.

### Multicamera Runtime

- Capture profile resolver usa configurazione per profilo prima dei globali.
- Gain per camera risolti correttamente:
  - IMX708 day/night/moonmode: `1.13 / 16 / 16`.
  - ASI678MC day/night/moonmode: `0 / 220 / 75`.
- Exposure, gain, target ADU, auto gain, processing mode e Hybrid AWB vengono propagati nella config runtime piatta per CaptureWorker/ImageWorker.
- Stato ADU/auto exposure separato per `profile_id:camera_id`.
- `ImageWorker` seleziona runtime context per `profile_id`/`camera_id` e logga warning se cade sul fallback globale.
- Risolto bug INDI BLOB multicamera: un worker non tratta piu' come errore i BLOB legittimi di un altro device.
- Ridotto rumore log libcamera/rpicam e diagnostici normali.

### Libcamera / IMX708

- AWB auto libcamera con shutter lungo diagnosticato come causa cadence 5x.
- Supporto AWB libcamera profile-specific:
  - `auto`.
  - `fixed` con `awbgains`.
  - preset libcamera.
- Hybrid AWB `postprocess_rgb` evita `--awb auto`/`--awbgains` runtime indesiderati quando non serve applicazione capture-driver.
- Rimosso `--immediate` per esposizioni libcamera lunghe, mantenendolo per esposizioni brevi.
- Timeout guard libcamera piu' stretto per evitare blocchi lunghi.
- Exposure period runtime clamp:
  - `effective_exposure_period = max(configured_period, requested_exposure + 5s)`.
  - Il valore salvato in config non viene modificato.

### Hybrid AWB

- `processing_mode = classic | hybrid` per profilo.
- Hybrid AWB separa:
  - measurement/controller.
  - backend applicazione.
- Backend attuali:
  - `libcamera_capture` per libcamera quando selezionato.
  - `postprocess_rgb` per INDI/ASI e opzionalmente libcamera.
  - `disabled`.
  - `unsupported_not_applied`.
- `hybrid.awb.apply_mode` per profilo:
  - `auto`.
  - `capture_driver`.
  - `postprocess_rgb`.
  - `disabled`.
- Per ASI/INDI il backend operativo e' `postprocess_rgb`.
- I log distinguono chiaramente misurazione e applicazione AWB.

### Processing ASI / Diagnostica

- Resolver legge `MULTI_CAMERA.profiles[n].processing` con alias lower-case e uppercase/legacy:
  - `CFA_PATTERN`.
  - `CCD_BIT_DEPTH`.
  - `AUTO_WB_DAY`.
  - `WBR_DAY`, `WBG_DAY`, `WBB_DAY`.
  - equivalenti Modern lower-case.
- Runtime logga:
  - `[MULTI_CAMERA_RESOLVED_CONFIG]`.
  - `[MULTI_CAMERA_PROCESSING_CONFIG]`.
- Patch diagnostica temporanea `[ASI_FRAME_STATS]` aggiunta per ASI/INDI, limitata al primo frame e poi ogni 10 frame.
- Checkpoint `[ASI_FRAME_STATS]`:
  - `raw_fits_after_read_pre_debayer`.
  - `after_calibration_bitdepth_pre_debayer`.
  - `after_debayer_cfa`.
  - `before_hybrid_awb_postprocess`.
  - `after_hybrid_awb_postprocess`.
  - `before_auto_meter`.
- `[ASI_FRAME_STATS]` ha dimostrato che la sovraesposizione ASI diurna appare gia' nel FITS raw quando exposure e' troppo alta.

### Auto Meter e Auto Exposure

- Sistema Auto Meter per-camera/profile introdotto.
- Modalita' metering disponibili:
  - `default`.
  - `average`.
  - `median`.
  - `sigma_clipped`.
  - `background`.
  - `moon_aware`.
  - `stars_only`.
- `default` punta attualmente a `moon_aware`.
- Stato Auto Meter per camera/profilo:
  - `measured_value`.
  - `smoothed_value` con EMA alpha `0.25`.
  - `sample_count`.
  - `excluded_pixels`.
- Auto Exposure Controller introdotto prima in shadow mode.
- Toggle per profilo `auto_exposure.enabled` / `AUTO_EXPOSURE_ENABLED`, default OFF.
- Quando enabled=True, il controller puo' applicare runtime exposure/gain solo al profilo/camera corrente.
- Fix runtime baseline:
  - decisione usa `EXPOSURE_NEXT`, poi `EXPOSURE_CURRENT`, poi fallback profilo.
  - gain usa `GAIN_NEXT`, poi `GAIN_CURRENT`, poi fallback profilo.
  - `AUTO_EXPOSURE_APPLY old_exposure` e' allineato a `decision.current_exposure`.
- Fix oscillazione daytime ASI:
  - daytime usa `step_strategy=day_bounded`.
  - parametri runtime:
    - `AUTO_EXPOSURE_DAY_STEP_FACTOR`, default `0.35`.
    - `AUTO_EXPOSURE_DAY_MIN_STEP`, default `0.00025s`.
    - `AUTO_EXPOSURE_DAY_MAX_STEP`, default `0.005s`.
  - profilo supporta:
    - `auto_exposure.day_step_factor`.
    - `auto_exposure.day_min_step`.
    - `auto_exposure.day_max_step`.
  - gain diurno non viene modificato dal controller se `AUTO_GAIN_ENABLE_DAY` non e' attivo.
- Log estesi:
  - `[AUTO_METER]`.
  - `[AUTO_METER_STATE]`.
  - `[AUTO_EXPOSURE_DECISION]`.
  - `[AUTO_EXPOSURE_APPLY]`.
- Validazione runtime ASI678MC daytime Auto Exposure del 2026-06-20:
  - i log mostrano `step_strategy=day_bounded`;
  - `source_exposure=runtime_next`;
  - `current_exposure` e' allineato con `AUTO_EXPOSURE_APPLY old_exposure`;
  - gain day rimasto `0.00`;
  - nessun salto `0.000032 -> 0.050000`;
  - convergenza stabile attorno al target `85 ADU` con exposure circa `0.021686-0.024186s`.

## IN TEST

### Hybrid AWB / Color ASI

- ASI usa `postprocess_rgb`; verificare se il colore diurno e' stabile dopo risoluzione exposure.
- Se il raw FITS non e' saturo ma il colore resta errato:
  - controllare CFA effettivo.
  - controllare legacy `AUTO_WB_DAY`.
  - controllare manual WB day.
  - valutare color calibration per-camera.

### Processing Profile Completeness

- Verificare se tutti i parametri processing critici sono davvero profile-first:
  - CFA.
  - bit depth.
  - auto/manual WB.
  - gamma.
  - stretch daytime.
  - contrast.
  - SCNR.
  - grayscale.
- Verificare che i globali restino solo fallback e non sovrascrivano le camere.

### UI Profile-First

- Verificare che Camera Profile Settings sia comprensibile come unica UI operativa.
- Verificare che Global Capture Defaults sia chiaramente legacy/fallback.
- Valutare descrizioni per i parametri critici:
  - gain day/night/moon.
  - exposure min/default/max.
  - Auto Exposure Enabled.
  - day bounded step.
  - Hybrid AWB apply mode.
  - CFA/bit depth.

## NEXT

### Auto Gain

- Separare formalmente controllo gain da controllo exposure.
- Policy per modalita':
  - giorno: preferire gain minimo/fisso, soprattutto ASI gain 0.
  - notte: consentire gain automatico dopo exposure ai limiti.
  - twilight: evitare cambi bruschi fra logica day/night.
- Usare `AUTO_GAIN_ENABLE_DAY`, `AUTO_GAIN_ENABLE_NIGHT`, `AUTO_GAIN_ENABLE_MOONMODE` per profilo.
- Garantire limiti min/max gain per profilo.
- Implementare step gain bounded:
  - fattore step.
  - min step.
  - max step.
  - cooldown.
- Evitare oscillazioni exposure/gain:
  - priorita': prima exposure, poi gain solo quando exposure e' al limite.
  - quando si diminuisce luminosita': prima ridurre gain se gain automatico e' attivo, poi exposure.
- Logging decisionale completo per gain:
  - current/proposed gain.
  - source runtime/profile.
  - limits.
  - step.
  - reason/action.

### Auto Exposure Refinement

- Rafforzare anti-oscillazione/hysteresis.
- Rendere il trend piu' robusto:
  - contatori separati per sovra/sottoesposizione.
  - reset su frame outlier.
  - finestre temporali invece di soli frame consecutivi.
- Aggiungere cooldown dopo grandi variazioni o frame saturi/quasi neri.
- Parametri per profilo camera:
  - deadband.
  - inner deadband.
  - trend frames.
  - day min/max step.
  - night min/max step.
  - cooldown.
- Strategie separate ASI e Raspberry camera, senza hardcode fragile.
- Metrica esposimetrica piu' stabile per cielo diurno:
  - usare percentili bassi/medi.
  - ignorare top percentile.
  - gestire Sole/nubi molto luminose.
- Protezione frame saturi/quasi neri:
  - se raw p99 e' saturo, forzare riduzione graduale ma decisa.
  - se raw e' quasi nero, aumentare gradualmente senza salto enorme.
- Valutare se il meter per Auto Exposure debba misurare prima o dopo Hybrid AWB.

### Metadata / Analytics Base

- Salvare per ogni frame:
  - `camera_id`.
  - `profile_id`.
  - exposure corrente.
  - gain corrente.
  - brightness/meter value.
  - smoothed brightness.
  - auto exposure action.
  - quality score futuro.
- Definire se usare:
  - colonne DB esistenti.
  - JSON metadata.
  - tabella SQLite dedicata.
- Aggiungere export/debug semplice per analizzare una giornata.

### Reliability Outdoor

- Watchdog camera per blocchi capture.
- Recovery se una camera si blocca senza fermare l'altra.
- Log health periodico:
  - ultimo frame per camera.
  - eta' ultimo frame.
  - ultimo errore.
  - stato service.
- Monitor:
  - temperatura Raspberry/CPU.
  - spazio disco.
  - memoria.
  - dimensione log.
- Rotazione/cleanup automatica file diagnostici temporanei.

## LATER

### Web UI / Gallery

- Dashboard piu' professionale.
- Stato camere in una vista unica:
  - Running/Stopped.
  - ultimo frame per camera.
  - last image age.
  - current exposure/gain.
  - processing mode.
  - AWB backend.
- Grafici:
  - brightness.
  - exposure.
  - gain.
  - quality score.
  - temperatura.
- Gallery:
  - filtri per camera.
  - filtri giorno/notte.
  - filtri qualita'.
  - badge qualita' immagine.
  - confronto rapido ASI/IMX nello stesso timestamp.
- Pagina pubblica esterna pulita:
  - senza controlli admin.
  - immagine principale.
  - immagine secondaria opzionale.
  - metadati essenziali.

### Multi-camera Hybrid

- Formalizzare ASI678MC come camera principale zenitale.
- Formalizzare IMX708 come camera secondaria orientata verso sud.
- UI con nomi camera chiari:
  - "ASI678MC Zenith".
  - "IMX708 South Wide".
- Profili indipendenti per:
  - capture.
  - processing.
  - AWB.
  - metering.
  - output/publication.
- Pipeline e logging separati per camera.
- Possibilita' di pubblicare:
  - entrambe le camere.
  - solo ASI.
  - solo IMX.
  - una camera admin-only e una pubblica.

### AI / Smart Detection

- Cloud detection.
- Sky clarity score.
- Rain/fog/haze detection.
- Day/night quality score.
- Riconoscimento frame inutilizzabili:
  - saturi.
  - neri.
  - fuori fuoco.
  - coperti.
  - mossi/artefatti.
- Meteor detection futura.
- Aurora/light pollution/event detection futura.
- Output salvabile come metadata persistente, non solo log.
- UI con badge e filtri basati su quality/event score.

### Advanced Processing

- Color calibration per-camera.
- Stretch custom per-camera.
- Auto stretch separato day/night.
- Postprocess AWB piu' robusto:
  - Grey World robusto.
  - percentile clipped.
  - white patch controllato.
  - smoothing per-camera.
- ROI/mask per metering e AWB.

## IDEAS

- Modalita' "science/debug day" che salva campioni raw periodici per analisi.
- Profilo "public-safe" con pubblicazione solo frame validi.
- Timeline diagnostica giornaliera con eventi:
  - camera restart.
  - exposure jump.
  - saturation.
  - missing frame.
  - service restart.
- Alert futuri:
  - Telegram.
  - email.
  - webhook.
- Preset hardware:
  - ASI678MC daytime.
  - ASI678MC night.
  - IMX708 long exposure.
  - IMX708 daylight.

## Deployment / Maintenance

### Update Raspberry

```bash
cd ~/indi-allsky
git pull
systemctl --user restart indi-allsky
```

### Verify Logs After Update

```bash
grep -E "ERROR|Traceback|Exception" /var/log/indi-allsky/indi-allsky.log | tail -100
grep -E "MULTI_CAMERA_RESOLVED_CONFIG|MULTI_CAMERA_PROCESSING_CONFIG" /var/log/indi-allsky/indi-allsky.log | tail -100
grep -E "AUTO_METER_STATE|AUTO_EXPOSURE_DECISION|AUTO_EXPOSURE_APPLY" /var/log/indi-allsky/indi-allsky.log | tail -200
grep -E "ASI_FRAME_STATS|HYBRID_AWB" /var/log/indi-allsky/indi-allsky.log | tail -200
```

### Known Good Checks

- No repeated `Received Blob from unexpected camera device`.
- ASI profile runtime:
  - `cfa_pattern=RGGB`.
  - `ccd_bit_depth=16`.
  - `auto_wb_day=True`.
  - gain day `0`.
- IMX profile runtime:
  - gain day `1.13`.
  - gain night/moonmode `16`.
- ASI daytime Auto Exposure:
  - `source_exposure=runtime_next` or `runtime_current` after initialization.
  - `AUTO_EXPOSURE_DECISION current_exposure` equals `AUTO_EXPOSURE_APPLY old_exposure`.
  - `step_strategy=day_bounded`.
  - no single jump from `0.000032s` to `0.050s`.
- Hybrid AWB:
  - ASI backend `postprocess_rgb`.
  - IMX backend according to profile apply mode.
- Libcamera long exposures:
  - no `--immediate` for exposure >= 1s.
  - no repeated 5x exposure cadence caused by AWB auto.

## Log Operativo Breve

- 2026-06-19: Consolidata roadmap Hybrid AllSky come documento operativo principale.
- 2026-06-19: Stabilizzato runtime multicamera con gain/exposure/profile resolver per IMX708 e ASI678MC.
- 2026-06-19: Modern Admin migrato verso modello profile-first.
- 2026-06-19: Risolto filtering BLOB INDI multicamera.
- 2026-06-19: Ridotto logging rumoroso libcamera/diagnostico.
- 2026-06-19: Implementato Hybrid AWB con backend `postprocess_rgb`.
- 2026-06-19: Introdotto Auto Meter per-camera/profile.
- 2026-06-19: Introdotto Auto Exposure Controller con shadow/apply mode dietro toggle.
- 2026-06-19: Aggiunti log processing profile e `[ASI_FRAME_STATS]`.
- 2026-06-20: Fix Auto Exposure baseline runtime: decisione usa `EXPOSURE_NEXT`/`GAIN_NEXT`.
- 2026-06-20: Fix step daytime bounded per evitare oscillazione ASI dark/saturated.
