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

## 7. Audit exposure flow - 2026-06-19

### File analizzati

- `indi_allsky/config.py`
- `indi_allsky/constants.py`
- `indi_allsky/flask/views.py`
- `indi_allsky/capture_profiles.py`
- `indi_allsky/allsky.py`
- `indi_allsky/capture.py`
- `indi_allsky/image.py`
- `indi_allsky/camera/libcamera.py`
- `indi_allsky/camera/indi.py`
- Driver alternativi con stesso pattern: `pycurl_camera.py`, `libcamera_mqtt.py`, `indi_accumulator.py`, `indi_passive.py`, `test_cameras.py`.

### Mappa config -> profile -> runtime -> driver

1. UI / DB config:
   - Legacy global config puo' salvare `CCD_EXPOSURE_DEF` da Full Settings / config API.
   - Modern Camera Settings salva il default operativo del profilo in `MULTI_CAMERA.profiles[n].exposure.default`.
   - Il default statico in `config.py` e' `CCD_EXPOSURE_DEF = 0.0`, quindi 8.0 non nasce dal codice base ma da DB/config/profilo salvato.
2. Capture profile:
   - `capture_profiles.py` risolve `exposure.default` / `exposure_default` / global `CCD_EXPOSURE_DEF`.
   - `build_profile_config()` scrive il valore risolto nella config runtime piatta come `CCD_EXPOSURE_DEF`.
3. Shared state:
   - `constants.py` definisce `EXPOSURE_CURRENT = 0` e `EXPOSURE_NEXT = 1`.
   - `allsky.py` crea gli array shared exposure con `[-1.0, -1.0, ...]`; `-1.0` significa non inizializzato.
   - In multicamera, il profilo primary usa lo shared state principale; i profili secondari ricevono uno shared state separato creato da `_new_profile_shared_state()`.
4. CaptureWorker:
   - `capture.py` legge `CCD_EXPOSURE_DEF` durante `_initialize()`.
   - Se `CCD_EXPOSURE_DEF` e' truthy, usa quel valore come `ccd_exposure_default` e non riusa la last stable exposure dal DB.
   - Se `EXPOSURE_CURRENT == -1.0`, scrive sia `EXPOSURE_CURRENT` sia `EXPOSURE_NEXT` a `ccd_exposure_default`.
   - Se `EXPOSURE_CURRENT` e' gia' valorizzato, non lo resetta durante il semplice restart del worker dentro lo stesso processo padre.
5. Runtime controller:
   - `image.py` puo' aggiornare `EXPOSURE_NEXT` in due punti:
     - legacy ADU `recalculate_exposure()`;
     - Auto Exposure Controller quando `AUTO_EXPOSURE_ENABLED=True`.
   - Entrambi aggiornano `EXPOSURE_DELTA`; nessuno scrive `CCD_EXPOSURE_DEF`.
6. Camera driver:
   - `capture.py` passa `EXPOSURE_NEXT` a `shoot()`.
   - `libcamera.py` e `indi.py` impostano il driver rispettivamente con `--shutter` / `CCD_EXPOSURE`.
   - All'avvio dello scatto il driver aggiorna `EXPOSURE_CURRENT` al valore richiesto. Il driver non decide il valore 8.0.

### Risposte operative

- Chi imposta 8.0 secondi: un valore salvato in DB/config/profilo come `CCD_EXPOSURE_DEF` o `MULTI_CAMERA.profiles[n].exposure.default`. Il codice base non contiene default 8.0.
- Quando viene reimpostato: quando uno shared state exposure nuovo o resettato ha `EXPOSURE_CURRENT == -1.0` e la config runtime del profilo ha `CCD_EXPOSURE_DEF=8.0`.
- Startup: si', startup del servizio crea shared arrays a `-1.0`; se il profilo risolve default 8.0, `capture.py` inizializza current/next a 8.0.
- Profile switch: non esiste un vero trasferimento di stato fra profili. Se il profilo mantiene lo stesso handle/shared state, non resetta. Se il profilo cambia id, viene ricreato, o il servizio ricarica la config creando nuovi handle, torna al default risolto.
- Camera reconnect: se reconnect avviene dentro lo stesso CaptureWorker/shared state, non dovrebbe resettare. Se il worker o il processo padre ricrea lo shared state, puo' rientrare da `CCD_EXPOSURE_DEF`.
- Multicamera handoff: il primary usa lo shared state principale, i secondari hanno shared state separato. Non c'e' handoff di `EXPOSURE_CURRENT/NEXT` tra camere. Se ImageWorker non trova `profile_id` e usa fallback default, puo' leggere/scrivere lo shared state sbagliato; i warning `[MULTI_CAMERA_CONFIG] ... fallback` sono quindi critici.

### Punti critici

- `CCD_EXPOSURE_DEF` truthy disabilita il riuso della last stable exposure recente dal DB.
- Il reset a 8s non e' un timer: e' una reinizializzazione da default quando lo stato torna a non inizializzato.
- Il fix futuro piu' sicuro e' rendere l'inizializzazione restart-safe: preferire last stable exposure per camera/profilo oppure stato persistente recente prima di applicare `CCD_EXPOSURE_DEF`.
- Aggiungere diagnostica esplicita alla sorgente iniziale di exposure: `source=profile_default|global_default|last_image|fallback_min`.

## 8. Audit pipeline diurna IMX708 vs ASI678MC - 2026-06-19

### File analizzati

- `indi_allsky/capture_profiles.py`
- `indi_allsky/capture.py`
- `indi_allsky/image.py`
- `indi_allsky/processing.py`
- `indi_allsky/camera/libcamera.py`
- `indi_allsky/camera/indi.py`
- `indi_allsky/config.py`
- `indi_allsky/flask/views.py`
- `indi_allsky/flask/templates/modern_admin/settings_cameras.html`

### Conclusione

- La pipeline non usa davvero gli stessi parametri completi per le due camere.
- Capture/gain/exposure/target ADU sono per-profilo tramite `capture_profiles.py`.
- Parte del processing resta invece globale o solo parzialmente profile-aware: `CFA_PATTERN`, `CCD_BIT_DEPTH`, `AUTO_WB*`, `WBR/WBG/WBB*`, `GAMMA_CORRECTION*`, `IMAGE_STRETCH`, `DAYTIME_CONTRAST_ENHANCE`, `CLAHE_*`, `SCNR_*`, grayscale e calibrazione.
- IMX708 via libcamera/JPEG arriva spesso gia' demosaicizzata e con un percorso capture-side libcamera piu' deterministico; ASI678MC via INDI dipende molto di piu' da CFA/debayer e white balance postprocess. Quindi una config globale che "va bene" per IMX708 puo' produrre immagini ASI diurne sbagliate.
- Causa piu' probabile per ASI678MC diurna errata: combinazione di exposure/gain day non ancora controllati bene + debayer/CFA/WB/stretch globali non per-camera. Il primo controllo da fare sul Raspberry e' verificare CFA effettivo ASI e log `HYBRID_AWB` con `backend=postprocess_rgb applied`.

### Tabella parametri

| Parametro | IMX708 | ASI678MC | Sorgente config/profile/runtime |
| --- | --- | --- | --- |
| Camera interface | `libcamera_imx708` | INDI/ZWO ASI | `MULTI_CAMERA.profiles[n].camera_interface` -> `build_profile_config()` |
| Capture driver | `rpicam-still` via `libcamera.py` | INDI `CCD_EXPOSURE` / `CCD_CONTROLS.Gain` via `indi.py` | Runtime CaptureWorker |
| Camera ID | atteso `1` DB / libcamera camera id profilo | atteso `2` DB / INDI camera name | DB camera + profilo |
| Day gain | 1.13, clamp minimo libcamera | 0.0 atteso | Profilo `gain.day`; fallback known defaults; clamp driver in `capture.py` |
| Night gain | 16 | 220 | Profilo `gain.night`; fallback known defaults |
| Moon gain | 16 | 75 | Profilo `gain.moonmode`; fallback known defaults |
| Day exposure | profilo/fallback `exposure.*` | profilo/fallback `exposure.*` | Profilo -> `CCD_EXPOSURE_*` runtime; rischio reset da `exposure.default` |
| Auto Exposure Enabled | per profilo, default OFF | per profilo, default OFF | `auto_exposure.enabled` -> `AUTO_EXPOSURE_ENABLED` |
| Auto Metering | per profilo | per profilo | `auto_exposure.metering_mode` -> `AUTO_EXPOSURE_METERING_MODE` |
| Target ADU day/night | per profilo | per profilo | `target_adu.*` -> `TARGET_ADU*` |
| Auto gain day/night/moon | per profilo | per profilo | `gain.auto_*` -> `CCD_CONFIG.AUTO_GAIN_ENABLE_*` |
| Capture AWB | libcamera command may use `--awb`/`--awbgains`; Hybrid `postprocess_rgb` suppresses Hybrid capture gains | no safe INDI capture AWB backend | `LIBCAMERA.*` only applies to libcamera; ASI uses postprocess |
| Hybrid AWB apply | expected `postprocess_rgb` | expected `postprocess_rgb` | `hybrid.awb.apply_mode` -> `HYBRID.AWB.APPLY_MODE`; shared `hybrid_av` per profile |
| Hybrid AWB measurement | after stack, before stretch | after stack, before stretch | `image.py update_hybrid_awb()` using current BGR image |
| Hybrid AWB apply point | before measurement, before stretch | before measurement, before stretch | `image.py apply_hybrid_awb()` |
| Debayer | often no CFA effect for JPEG/libcamera path; raw DNG/FITS would use CFA | critical for ASI raw/FITS frames | `processing.py debayer()`; `CFA_PATTERN` can override detected Bayer globally/profile |
| CFA_PATTERN | profile can override, else global | profile can override, else global | `capture_profiles.py` only supports `cfa_pattern`; must verify ASI-specific value |
| CCD bit depth | profile can override, else global | profile can override, else global | `ccd_bit_depth` -> `CCD_BIT_DEPTH`; affects scaling |
| Dark/calibration | currently global/profile fallback only if profile sets keys not fully mapped in resolver | same | `IMAGE_CALIBRATE_*`; mostly global processing |
| Stretch | same global config unless profile map/fallback carries override | same global config unless profile map/fallback carries override | `IMAGE_STRETCH.*`; not currently a first-class per-camera profile field |
| Daytime stretch enable | same global `IMAGE_STRETCH.DAYTIME` | same global `IMAGE_STRETCH.DAYTIME` | Global unless explicit profile extension added |
| Gamma day | same global `GAMMA_CORRECTION_DAY` | same global `GAMMA_CORRECTION_DAY` | Global processing |
| Manual WB day | same global `WBR/WBG/WBB_FACTOR_DAY` unless config copied into profile manually | same global | Global processing |
| Legacy Auto WB day | same global `AUTO_WB_DAY` | same global | Global processing; separate from Hybrid AWB |
| SCNR day | same global `SCNR_ALGORITHM_DAY` | same global | Global processing |
| CLAHE/contrast day | same global `DAYTIME_CONTRAST_ENHANCE`, `CLAHE_*` | same global | Global processing |
| Grayscale day | same global `DAYTIME_GRAYSCALE` | same global | Global processing |

### Differenze trovate

- IMX708 e ASI678MC hanno capture profile separati per gain/exposure/AWB apply mode, ma molte impostazioni di rendering finale sono ancora condivise.
- IMX708 e' meno sensibile a `CFA_PATTERN` quando acquisisce JPEG da libcamera; ASI678MC e' molto sensibile perche' il debayer avviene nel processing.
- `processing.py` applica WB legacy, gamma, SCNR, stretch e contrast dopo Hybrid AWB. Questi valori sono globali e possono correggere IMX708 ma peggiorare ASI.
- `ImageProcessor` e' cacheato per `profile_id:camera_id`, ma viene creato con la config selezionata in quel momento. Se ImageWorker cade su fallback globale per profilo mancante, anche processing e maschere possono contaminarsi.

### Verifiche runtime consigliate sul Raspberry

- Controllare `IMAGE_PAYLOAD_START` e `IMAGE_PROCESSOR_CONTEXT` per `asi678mc` e `imx708-wide`.
- Controllare assenza di warning `[MULTI_CAMERA_CONFIG] ... fallback` per entrambi i profili.
- Controllare `HYBRID_AWB`:
  - IMX708: `backend=postprocess_rgb applied_red=... applied_blue=...`
  - ASI678MC: `backend=postprocess_rgb applied_red=... applied_blue=...`
- Verificare `CFA_PATTERN` effettivo ASI678MC: se errato o globale adatto a IMX708, il colore diurno ASI sara' sbagliato anche con AWB.
- Verificare esposizione/gain diurna ASI nei log `[MULTI_CAMERA_RESOLVED_CONFIG]` e `[AUTO_EXPOSURE_APPLY]`.

### Prossimi fix consigliati

1. Rendere per-camera i parametri processing minimi per ASI: `CFA_PATTERN`, `CCD_BIT_DEPTH`, `WBR/WBG/WBB_FACTOR_DAY`, `AUTO_WB_DAY`, `GAMMA_CORRECTION_DAY`, `IMAGE_STRETCH.DAYTIME`, `SCNR_ALGORITHM_DAY`, `DAYTIME_CONTRAST_ENHANCE`.
2. Aggiungere log diagnostico processing per frame: profile, camera_id, CFA pattern usato, bit depth, stretch daytime on/off, gamma day, WB legacy on/off, Hybrid AWB applied/skipped.
3. Verificare e correggere il CFA ASI678MC prima di modificare algoritmi AWB: un Bayer pattern errato rende ogni WB successivo inaffidabile.
4. Separare i preset Basic per camera:
   - ASI678MC day: gain 0, auto exposure enabled, Hybrid AWB postprocess, CFA corretto, no stretch aggressivo.
   - IMX708 day: gain minimo driver 1.13, Hybrid AWB postprocess o libcamera fixed deterministico, processing dedicato.
5. Solo dopo CFA/WB/exposure day corretti, valutare color calibration per-camera.

## 9. Log operativo

- 2026-06-19: Profile-first Settings/UI coherence patch.
  - Camera Profile Settings / Acquisition ora include anche i campi processing critici per camera:
    - `processing.cfa_pattern`
    - `processing.ccd_bit_depth`
    - `processing.auto_wb`
    - `processing.auto_wb_day`
    - `processing.wbr_factor*`
    - `processing.wbg_factor*`
    - `processing.wbb_factor*`
    - `processing.gamma_correction*`
    - `processing.image_stretch_daytime`
    - `processing.daytime_contrast_enhance`
    - `processing.daytime_grayscale`
    - `processing.scnr_algorithm_day`
  - Full Settings nasconde questi campi dalla normale UI operativa insieme a gain/exposure/target/AWB, trattandoli come legacy fallback.
  - I campi Acquisition mostrano badge `Per-camera`, `Profile override`, `Legacy fallback`, `Runtime reuse` e `ASI audit` dove utile.
  - Il resolver profili non copia piu' automaticamente `CCD_EXPOSURE_DEF` globale dentro un profilo multicamera reale se il profilo non ha un default esposizione esplicito. Questo riduce il rischio che `CCD_EXPOSURE_DEF=8` resetti IMX708/ASI dopo restart/reinit.
  - Runtime logging esteso:
    - `[MULTI_CAMERA_RESOLVED_CONFIG]` include CFA, bit depth, legacy auto WB, gamma day, stretch day, contrast day.
    - `[MULTI_CAMERA_PROCESSING_CONFIG]` logga una volta per profilo/camera i parametri CFA/debayer/WB/gamma/stretch effettivamente risolti.
  - Mancante/verifica Raspberry:
    - impostare o confermare il CFA corretto per ASI678MC;
    - controllare che `exposure_default` vuoto sui profili non torni a 8s dopo restart;
    - controllare se ASI678MC resta a `smoothed_value ~239/255` anche con CFA/WB/stretch profilo corretti;
    - se resta sovraesposta a gain 0/exposure 0.05s, investigare driver/bit depth/debayer o saturazione reale del sensore.

- 2026-06-19: Consolidata roadmap Hybrid AllSky come documento operativo principale.
- 2026-06-19: Stabilizzato runtime multicamera con gain/exposure/profile resolver per IMX708 e ASI678MC.
- 2026-06-19: Introdotto metering per-camera selezionabile in shadow mode.
- 2026-06-19: Introdotto Auto Exposure Controller con decisioni shadow, smoothing e deadband trend-aware.
- 2026-06-19: Aggiunto toggle per-camera `AUTO_EXPOSURE_ENABLED`, default OFF, per applicazione runtime controllata.
- 2026-06-19: Eseguito audit configurazione Hybrid AllSky e documentati conflitti fra profili, global fallback e runtime.
- 2026-06-19: Mappato flusso `CCD_EXPOSURE_DEF` -> `EXPOSURE_CURRENT/NEXT` e identificata la reinizializzazione da shared state `-1.0` come causa probabile dei ritorni a 8s.
- 2026-06-19: Auditata pipeline diurna IMX708 vs ASI678MC; identificati CFA/debayer/WB/stretch globali come causa probabile delle immagini ASI diurne errate.
