# Hybrid AllSky Roadmap

Questo e' il documento operativo principale del progetto Hybrid AllSky.
Ogni task futuro deve leggere questo file prima di iniziare e aggiornarlo quando introduce decisioni, modifiche o nuove evidenze.

## 1. Obiettivo del progetto

- Costruire un sistema AllSky multicamera stabile e realmente per-camera.
- Usare ZWO ASI678MC come camera principale zenitale.
- Usare Raspberry Camera Module 3 Wide IMX708 come seconda camera, orientata piu' verso sud.
- Offrire una interfaccia web moderna, chiara e piu' professionale.
- Rendere la configurazione comprensibile distinguendo chiaramente:
  - Basic: parametri operativi quotidiani.
  - Advanced: impostazioni utili ma non necessarie nella gestione normale.
  - Developer: diagnostica, esperimenti, compatibilita' legacy e parametri rischiosi.

## 2. Priorita' 1 - Stabilizzazione auto exposure multicamera

- [ ] ASI678MC sovraesposta di giorno.
- [ ] White balance ASI678MC errato.
- [ ] Possibile reset periodico exposure a 8s.
- [ ] Verificare separazione dello stato exposure/gain per camera/profilo.
- [ ] Verificare che `AUTO_EXPOSURE_ENABLED` applichi solo al profilo/camera corrente.
- [ ] Giorno: preferire gain 0, o il valore piu' vicino possibile, aumentando exposure.
- [ ] Notte: usare gain minimo 100 o superiore per ASI678MC, salvo evidenza contraria.
- [ ] Confermare che IMX708 e ASI678MC non condividano storico ADU, metering, gain o exposure state.
- [ ] Validare i log:
  - `[AUTO_METER]`
  - `[AUTO_METER_STATE]`
  - `[AUTO_EXPOSURE_DECISION]`
  - `[AUTO_EXPOSURE_APPLY]`

## 3. Priorita' 2 - Audit configurazione

- [ ] Esportare la config completa corrente dal Raspberry.
- [ ] Classificare ogni impostazione come Basic / Advanced / Developer.
- [ ] Identificare parametri ridondanti, inutili o pericolosi.
- [ ] Ripristinare default sensati senza cancellare opzioni esistenti.
- [ ] Nascondere impostazioni avanzate nella UI normale.
- [ ] Separare in modo netto:
  - valori globali legacy/fallback;
  - valori operativi per-camera/profilo;
  - diagnostica developer.
- [ ] Documentare i campi legacy ancora necessari per compatibilita'.

## 4. Priorita' 3 - UI/UX

- [ ] Aggiungere descrizioni/didascalie per i parametri principali.
- [ ] Distinguere chiaramente parametri globali e parametri per-camera.
- [ ] Migliorare la gallery multicamera.
- [ ] Rendere piu' evidente quale camera/profilo si sta configurando.
- [ ] Migliorare il layout web generale con una struttura piu' professionale.
- [ ] Organizzare Modern Admin secondo Basic / Advanced / Developer.

## 5. Decisioni tecniche

- Codex lavora sul repository locale, non ha accesso diretto al Raspberry.
- Il Raspberry riceve le modifiche tramite `git pull`.
- I test runtime reali devono essere eseguiti sul Raspberry dopo pull/restart.
- Ogni prompt Codex deve leggere `HYBRID_ROADMAP.md` e aggiornarlo se cambia roadmap, stato operativo o decisioni tecniche.
- Le modifiche runtime devono restare conservative: niente refactor ampi se non richiesti.
- Le impostazioni operative multicamera devono vivere nei Camera Profiles; i global settings restano fallback legacy/single-camera/advanced.
- Default di sicurezza: nuove funzioni attive solo dietro toggle esplicito.

## 6. Audit configurazione - 2026-06-19

### File analizzati

- `indi_allsky/capture_profiles.py`
- `indi_allsky/allsky.py`
- `indi_allsky/capture.py`
- `indi_allsky/image.py`
- `indi_allsky/camera/libcamera.py`
- `indi_allsky/camera/indi.py`
- `indi_allsky/flask/views.py`

### Mappa esposizione / gain / white balance

- UI operativa: Modern Camera Settings, sezione Acquisition, salva nei profili camera.
- UI legacy/fallback: Full Settings / Global Capture Defaults, deve restare compatibilita' e fallback, non sorgente operativa primaria.
- Database config: contiene ancora i globali legacy `CCD_CONFIG`, `CCD_EXPOSURE_*`, `TARGET_ADU*`, `LIBCAMERA.*`, `HYBRID.AWB.*`, `AUTO_EXPOSURE_*`.
- Capture profile: `capture_profiles.py` risolve profilo + globali in una config runtime piatta per ogni camera.
- Runtime CaptureWorker: usa `exposure_av`, `gain_av`, `binning_av` per camera/profilo.
- Runtime ImageWorker: seleziona config/shared-state tramite `profile_id`/`camera_id` e mantiene ADU, metering, Hybrid AWB e Auto Exposure state per camera/profilo.
- Driver libcamera: usa `--gain`, `--shutter`, `--awb`/`--awbgains`; in Hybrid AWB `postprocess_rgb` non deve applicare AWB lato capture.
- Driver INDI/ASI: usa `CCD_EXPOSURE` e, per ASI, `CCD_CONTROLS.Gain`; il white balance operativo e' postprocess RGB, non driver-side.

### Ordine di priorita' osservato

- `gain`: profilo `gain.*` / legacy `ccd_config.*` -> default noti per profilo/camera -> globale `CCD_CONFIG` -> clamp ai limiti driver.
- `exposure`: profilo `exposure.*` -> alias top-level profilo -> globali `CCD_EXPOSURE_*` / `EXPOSURE_PERIOD*`.
- `target ADU`: profilo `target_adu.*` / alias top-level -> globali `TARGET_ADU*`.
- `processing_mode`: profilo -> default `classic`.
- `hybrid.awb.apply_mode`: profilo `hybrid.awb.apply_mode` -> global/config fallback -> default `auto`.
- `AUTO_EXPOSURE_ENABLED`: profilo `auto_exposure.enabled` / alias -> globale -> default `False`.

### Problemi trovati

- Possibile reset periodico exposure a 8s: `capture.py` inizializza `EXPOSURE_CURRENT`/`EXPOSURE_NEXT` da `CCD_EXPOSURE_DEF` quando lo shared state torna a `-1.0`. Se il profilo risolve `CCD_EXPOSURE_DEF=8`, un restart del CaptureWorker o una ricreazione dello stato puo' riportare la camera a 8s. Questa e' la sorgente piu' probabile del reset periodico.
- ASI678MC sovraesposta di giorno: il gain day puo' essere correttamente 0, ma l'exposure puo' ripartire da `CCD_EXPOSURE_DEF` e la logica legacy ADU usa ancora criteri non sempre day-aware. In `image.py`, la scelta fra `TARGET_ADU_DEV_DAY` e `TARGET_ADU_DEV` dipende da `exposure < 0.001`, non dallo stato day/night/moonmode reale; questo puo' applicare tolleranze notturne a frame diurni.
- IMX708 usa gain 1.13 di giorno invece di 0: e' coerente con il clamp al minimo driver libcamera. Se il driver dichiara minimo 1.13, `capture.py` cambia un gain day inferiore al minimo in 1.13. Per IMX708 il default sensato resta 1.13, non 0.
- Partial profile fallback: se un profilo contiene un blocco `gain` o `ccd_config` parziale, i valori mancanti possono ancora cadere sui globali. I default noti IMX708/ASI vanno applicati per campo mancante, non solo quando il blocco e' assente.
- White balance ASI678MC: non esiste un backend capture-driver sicuro per INDI/ASI; il percorso operativo e' Hybrid AWB `postprocess_rgb`. Se il bilanciamento resta errato, il fix va fatto su metering/ROI/smoothing/color calibration postprocess, non su `LIBCAMERA.AWB`.
- ImageWorker fallback: `_select_runtime_context()` avvisa se manca `profile_id`/`camera_id` e cade sullo stato globale. In multicamera questo va considerato un segnale diagnostico importante per contaminazione di stato.

### Prossimi fix consigliati

1. Rendere l'inizializzazione exposure restart-safe: se esiste una last stable exposure recente o uno stato per-camera valido, non rientrare automaticamente da `CCD_EXPOSURE_DEF=8`.
2. Correggere la logica day/night/moonmode in `image.py` per target ADU deviation e auto exposure: usare lo stato runtime giorno/notte/moonmode, non `exposure < 0.001`.
3. Rafforzare `capture_profiles.py`: per profili noti IMX708/ASI, completare ogni campo gain/exposure mancante con default per-camera prima dei globali legacy.
4. Esporre in UI i limiti driver effettivi: IMX708 day gain minimo 1.13, ASI day gain atteso 0.
5. Verificare sul Raspberry i log `[MULTI_CAMERA_RESOLVED_CONFIG]`, `[AUTO_METER_STATE]`, `[AUTO_EXPOSURE_DECISION]`, `[AUTO_EXPOSURE_APPLY]`, `[HYBRID_AWB]` per confermare che payload e runtime context includano sempre `profile_id` e `camera_id`.

### Separazione UI Basic / Advanced / Developer

- Basic: profilo camera, enabled/primary, interfaccia, exposure day/night min/max/default, gain day/night/moon, Auto Exposure Enabled, metering mode, target ADU day/night, Hybrid AWB apply mode.
- Advanced: binning day/night/moon, exposure timeout, exposure period, auto gain day/night/moon/levels, libcamera AWB fixed/manual gains, ROI/mask, camera-specific options.
- Developer: Full Settings globali legacy, raw `CCD_CONFIG`, raw `CCD_EXPOSURE_*`, diagnostica timing, metering internals, upload internals, compatibilita' driver e feature sperimentali.

## 7. Log operativo

- 2026-06-19: Consolidata roadmap Hybrid AllSky come documento operativo principale.
- 2026-06-19: Stabilizzato runtime multicamera con gain/exposure/profile resolver per IMX708 e ASI678MC.
- 2026-06-19: Introdotto metering per-camera selezionabile in shadow mode.
- 2026-06-19: Introdotto Auto Exposure Controller con decisioni shadow, smoothing e deadband trend-aware.
- 2026-06-19: Aggiunto toggle per-camera `AUTO_EXPOSURE_ENABLED`, default OFF, per applicazione runtime controllata.
- 2026-06-19: Eseguito audit configurazione Hybrid AllSky e documentati conflitti fra profili, global fallback e runtime.
