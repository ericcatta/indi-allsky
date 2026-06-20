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
- Camera Profile Settings include Save & Sync controllato verso l'altra camera:
  - copia solo blocchi comuni `gain`, `auto_exposure`, `target_adu` ed `exposure`;
  - ogni sezione salvabile puo' salvare il profilo corrente e sincronizzare in un solo config snapshot;
  - preserva identity/hardware (`profile_id`, `camera_id`, driver, `indi`, `libcamera`, lens, processing, binning, AWB);
  - `CFA / Debayer Pattern` resta profile-specific, hardware-specific e non viene copiato;
  - crea una nuova config row e richiede restart/reload manuale per il runtime.
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
- Validazione runtime ASI678MC profile Target ADU del 2026-06-20:
  - Day Target ADU modificato da Camera Profile Settings a `95`;
  - latest config DB contiene `MULTI_CAMERA.profiles[n].profile_id=asi678mc` con `target_adu.day=95`;
  - dopo restart `[MULTI_CAMERA_RESOLVED_CONFIG][asi678mc]` mostra `target_adu_day=95`;
  - `[AUTO_EXPOSURE_DECISION]` e `[AUTO_GAIN_DECISION]` usano `target=95.00`.
- Verifica pipeline Target ADU profile-first del 2026-06-20:
  - `target_adu.day`, `target_adu.night`, `target_adu.dev_day` e `target_adu.dev` seguono la stessa catena UI -> latest config DB -> `capture_profiles.py` resolver -> runtime flat config;
  - il runtime espone rispettivamente `TARGET_ADU_DAY`, `TARGET_ADU`, `TARGET_ADU_DEV_DAY` e `TARGET_ADU_DEV`;
  - il legacy ADU controller legge i target da day/night e le deviazioni da `TARGET_ADU_DEV_DAY` per esposizioni day molto brevi o `TARGET_ADU_DEV` per gli altri casi.

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

Design review e architettura proposta.

Obiettivo:

- Rendere il gain automatico una policy per-camera/profile, non un effetto collaterale della logica legacy globale.
- Evitare due autorita' concorrenti:
  - legacy `recalculate_exposure()` con `auto_gain_step_list`.
  - nuovo Auto Exposure Controller profile-aware.
- Mantenere default sicuro:
  - gain automatico spento se il profilo non lo abilita esplicitamente.
  - giorno con gain fisso/minimo.
  - notte con exposure-first e gain solo quando serve.

Macchina a stati proposta:

- `day`:
  - condizione: stato diurno corrente.
  - policy: gain fisso/minimo, soprattutto ASI gain `0`.
  - exposure e' il controllo primario.
  - gain cambia solo se `AUTO_GAIN_ENABLE_DAY=True` nel profilo.
- `twilight_evening`:
  - transizione day -> night.
  - policy: evitare salti bruschi verso gain notturni.
  - aumentare exposure gradualmente; gain resta bloccato finche' exposure non e' vicina al limite twilight/notte per N frame.
- `night`:
  - policy: prima exposure fino a `exposure.max`, poi gain.
  - gain automatico consentito solo se `AUTO_GAIN_ENABLE_NIGHT=True`.
  - gain minimo notturno puo' essere diverso dal gain day.
- `moonmode`:
  - policy separata da night.
  - proteggere dettagli lunari e alte luci.
  - gain automatico consentito solo se `AUTO_GAIN_ENABLE_MOONMODE=True`.
  - step piu' conservativi rispetto a night se il meter segnala alte luci importanti.
- `twilight_morning`:
  - transizione night -> day.
  - policy: ridurre gain prima che il cielo diventi troppo luminoso.
  - usare cooldown/hysteresis per evitare ping-pong night/day vicino alla soglia.

Priorita' exposure vs gain:

- Sottoesposizione:
  - se exposure < max della modalita': aumentare exposure.
  - se exposure e' al limite o stabilmente vicino al limite per N frame: aumentare gain.
  - se gain automatico e' disabilitato: non cambiare gain e loggare `reason=gain_auto_disabled`.
- Sovraesposizione:
  - se il gain era stato aumentato automaticamente dal controller e gain > min della modalita': ridurre gain prima.
  - se il gain non era stato aumentato automaticamente o e' gia' al minimo: demandare la riduzione a exposure control.
  - in day, ridurre exposure prima perche' il gain dovrebbe gia' essere minimo/fisso.
- `hold`:
  - se il meter e' dentro deadband o cooldown attivo.
  - se il frame e' marcato outlier/non affidabile.

Limiti min/max per camera:

- I limiti devono arrivare dal profilo risolto e dagli array runtime:
  - `GAIN_MIN_DAY`, `GAIN_MAX_DAY`.
  - `GAIN_MIN_NIGHT`, `GAIN_MAX_NIGHT`.
  - `GAIN_MIN_MOONMODE`, `GAIN_MAX_MOONMODE`.
- I globali restano solo fallback iniziale se il profilo non contiene valori.
- ASI678MC:
  - giorno: gain `0` come default operativo; non abilitare auto gain day salvo test specifici.
  - notte: gain minimo consigliato almeno `100` se la policy notturna lo richiede, con massimo profilo corrente `220`.
  - moonmode: default operativo corrente `75`.
  - step gain piccoli per evitare amplificazione improvvisa su raw 16 bit molto sensibile.
- IMX708:
  - giorno: gain minimo effettivo libcamera `1.13`.
  - notte/moonmode: default operativo corrente `16`.
  - range piu' stretto e gia' clampato dal driver; auto gain deve essere piu' conservativo.
  - non reintrodurre AWB/exposure comportamenti libcamera che hanno causato cadence lunga.

Anti-oscillazione:

- Usare sempre baseline runtime:
  - `GAIN_NEXT`, poi `GAIN_CURRENT`, poi fallback profilo.
  - mai usare il default profilo come current se il runtime ha gia' un valore valido.
- Deadband separata per gain, piu' larga della deadband exposure.
- Trend requirement:
  - cambiare gain solo dopo errore persistente con stesso segno per N frame.
  - reset trend se cambia modalita', profilo, camera, segno errore o frame outlier.
- Step bounded:
  - `gain_step_factor`.
  - `gain_min_step`.
  - `gain_max_step`.
  - possibilmente separati day/night/moonmode.
- Saturation guard:
  - frame quasi saturo: ridurre exposure/gain in modo controllato ma prioritario.
  - frame quasi nero: aumentare exposure gradualmente prima del gain.
- Flapping guard:
  - se gain aumenta e poi diminuisce subito, dimezzare step successivo e attivare cooldown.

Cooldown:

- Stato per `profile_id:camera_id`.
- Cooldown breve dopo cambio exposure.
- Cooldown piu' lungo dopo cambio gain, perche' il gain cambia rumore, saturazione e colore.
- Cooldown separato dopo cambio stato day/twilight/night/moonmode.
- Durante cooldown:
  - continuare meter e log.
  - decisione `hold` con `reason=cooldown`.
  - consentire solo emergency down-step se frame e' gravemente saturo.

Integrazione con Auto Exposure esistente:

- Il nuovo Auto Exposure Controller deve diventare il coordinatore unico exposure/gain quando `AUTO_EXPOSURE_ENABLED=True`.
- La logica legacy `recalculate_exposure()`/`auto_gain_step_list` va mantenuta solo per compatibilita' quando il nuovo controller non e' attivo.
- In modalita' controller attivo:
  - decisione exposure e decisione gain devono uscire dallo stesso oggetto decisionale o da due oggetti coordinati.
  - evitare che legacy auto gain riscriva `GAIN_NEXT` dopo il controller.
- Il controller deve sapere:
  - modalita' corrente (`day`, `twilight_evening`, `night`, `moonmode`, `twilight_morning`).
  - current/proposed exposure.
  - current/proposed gain.
  - limiti per modalita'.
  - flag `AUTO_GAIN_ENABLE_*` del profilo.
  - stato cooldown/trend.
- Il primo rollout deve essere shadow-only:
  - loggare decisioni Auto Gain senza applicarle.
  - confrontare con `GAIN_NEXT` reale.
  - poi abilitare apply solo per un profilo alla volta.

Configurazione profile-first proposta:

- Usare e mantenere i campi gia' presenti:
  - `gain.day`.
  - `gain.night`.
  - `gain.moonmode`.
  - `gain.auto_day`.
  - `gain.auto_night`.
  - `gain.auto_moonmode`.
  - `gain.auto_levels`.
- Aggiungere in futuro, solo quando necessario:
  - `gain.day_min`, `gain.day_max`.
  - `gain.night_min`, `gain.night_max`.
  - `gain.moonmode_min`, `gain.moonmode_max`.
  - `gain.step_factor_day`, `gain.step_factor_night`, `gain.step_factor_moonmode`.
  - `gain.min_step_day`, `gain.min_step_night`, `gain.min_step_moonmode`.
  - `gain.max_step_day`, `gain.max_step_night`, `gain.max_step_moonmode`.
  - `gain.cooldown_frames_day`, `gain.cooldown_frames_night`, `gain.cooldown_frames_moonmode`.
  - `gain.twilight_policy`.
- Global `CCD_CONFIG.AUTO_GAIN_*` resta fallback legacy/advanced, non sorgente operativa primaria.

Logging necessario:

- `[AUTO_GAIN_STATE]`
  - `profile`, `camera_id`, `state`, `mode`, `trend_count`, `cooldown_remaining`, `last_action`.
- `[AUTO_GAIN_DECISION]`
  - `profile`, `camera_id`, `mode`, `enabled`, `action`, `reason`.
  - `current_gain`, `proposed_gain`, `source_gain`.
  - `gain_min`, `gain_max`, `step`, `step_strategy`.
  - `current_exposure`, `proposed_exposure`, `exposure_min`, `exposure_max`.
  - `meter_value`, `target`, `error`, `deadband`.
  - `saturation_pct`, `black_pct` se disponibili.
  - `shadow=True|False`.
- `[AUTO_GAIN_APPLY]`
  - `old_gain`, `new_gain`, `old_exposure`, `new_exposure`.
  - `status=applied|skipped`.
  - `reason`.

Fasi consigliate:

- Fase 1: Auto Gain shadow controller, nessun apply runtime.
- Fase 2: disaccoppiare legacy auto gain dal nuovo controller quando `AUTO_EXPOSURE_ENABLED=True`.
- Fase 3: enable controllato per ASI night only.
- Fase 4: twilight state esplicito.
- Fase 5: UI Advanced per step/cooldown, lasciando Basic con soli toggle day/night/moonmode.

Primo micro-step implementato:

- Controller Auto Gain shadow-only separato.
- Stato diagnostico per `profile_id:camera_id`.
- Log `[AUTO_GAIN_STATE]` e `[AUTO_GAIN_DECISION]`.
- Nessun write su `GAIN_NEXT`, `GAIN_CURRENT` o configurazione.
- Day mode rispetta `AUTO_GAIN_ENABLE_DAY=False` e logga `reason=gain_auto_disabled`.
- La policy resta exposure-first: se exposure non e' al limite, il gain resta in `hold` con `reason=exposure_first`.
- La riduzione gain viene proposta solo se lo stato shadow sa che il gain era stato aumentato automaticamente.
- Parametri diagnostici Auto Gain leggibili da `profile.gain.*` tramite resolver, con globali solo fallback.

Validazione runtime Raspberry del 2026-06-20:

- Nessun `ERROR`, `Traceback` o `Exception` dopo restart.
- `[AUTO_GAIN_STATE]` e `[AUTO_GAIN_DECISION]` compaiono per `imx708-wide` e `asi678mc`.
- In `mode=day`, Auto Gain resta `enabled=False`.
- Le decisioni restano `action=hold`, `reason=gain_auto_disabled`, `shadow=True`.
- ASI678MC mantiene `current_gain=0.00` e `proposed_gain=0.00`.
- IMX708 mantiene `current_gain=1.13` e `proposed_gain=1.13`.
- Nessun write reale su gain runtime osservato.

Secondo micro-step implementato:

- Aggiunto gate profile-first `auto_gain.apply_enabled`, esposto runtime come `AUTO_GAIN_APPLY_ENABLED`.
- Default globale/profilo `False`; i profili esistenti restano shadow-only.
- Aggiunto log `[AUTO_GAIN_APPLY]`.
- Quando `apply_enabled=False`, log `status=skipped reason=apply_disabled`.
- Quando `apply_enabled=True`, il solo write consentito e' verso `GAIN_NEXT`.
- Apply consentito solo se mode auto gain e' abilitata, trend e' attivo, cooldown non blocca la decisione, gain resta nei limiti e la decisione rispetta Exposure-first/Gain-last.
- Di giorno `AUTO_GAIN_ENABLE_DAY=False` continua a bloccare sia proposta sia apply.

Terzo micro-step implementato: Night Gain Decision Validation.

- Auto Gain resta diagnostico: nessun write reale su `GAIN_NEXT`.
- Aggiunto log `[AUTO_GAIN_BLOCKER]` per spiegare perche' il gain non aumenta.
- Blocker espliciti:
  - `exposure_not_at_limit`.
  - `mode_disabled`.
  - `cooldown_active`.
  - `trend_not_confirmed`.
  - `gain_already_max`.
  - `gain_already_min`.
  - `deadband_hold`.
- Quando tutte le condizioni sono soddisfatte, `[AUTO_GAIN_DECISION]` mostra `action=increase_gain`, `shadow=True` e `proposed_gain`, ma `[AUTO_GAIN_APPLY]` resta `status=skipped reason=validation_only` anche se `apply_enabled=True`.

Quarto micro-step implementato: Auto Gain Apply reale gated.

- `AUTO_GAIN_APPLY_ENABLED=False` resta il default sicuro e non scrive nulla.
- Quando `AUTO_GAIN_APPLY_ENABLED=True`, il controller applica solo decisioni `increase_gain`/`decrease_gain` con `blocker=none`, mode abilitata, trend confermato, exposure al limite massimo della modalita' e gain entro min/max.
- Il write runtime e' limitato a `GAIN_NEXT`; non scrive camera, config o DB.
- `[AUTO_GAIN_APPLY]` logga `status=applied shadow=False` solo quando il write su `GAIN_NEXT` avviene davvero; tutti gli altri casi restano `status=skipped` con motivo esplicito.
- Test mirati coprono apply disabled, day/mode disabled, exposure sotto max, condizioni valide con trend attivo e clamp al gain massimo.
- Auto Gain convergence improvement:
  - errori grandi `abs_error > 20 ADU` usano `convergence_mode=aggressive` e `step_strategy=aggressive_bounded` con step 2x rispetto al bounded normale;
  - errori normali tra circa `5` e `20 ADU` mantengono il comportamento esistente;
  - errori piccoli persistenti `abs_error < 5 ADU` per 5 frame attivano `fine_convergence`, con step ridotto, fino a `abs_error <= 1.5 ADU`;
  - trend/cooldown/gain min/max/exposure-at-limit/apply gate restano invariati;
  - i log includono `fine_convergence`, `convergence_frames` e `convergence_mode`.
- Gain Max profile-first:
  - Modern Camera Settings > Acquisition espone `Day/Night/Moon Mode Gain Max` per profilo camera;
  - i valori salvati in `gain.max_day`, `gain.max_night`, `gain.max_moonmode` alimentano `GAIN_MAX_DAY`, `GAIN_MAX_NIGHT`, `GAIN_MAX_MOONMODE` runtime;
  - questi limiti sono hardware-specific e non vengono copiati da Save & Sync Acquisition tra camere diverse.

Validazione runtime Raspberry del secondo micro-step del 2026-06-20:

- `[AUTO_GAIN_APPLY]` compare nei log.
- Auto Gain `apply_enabled=false` di default.
- Apply resta `status=skipped`, `reason=apply_disabled`, `shadow=True`.
- ASI678MC day mantiene `old_gain=0.00` e `new_gain=0.00`.
- IMX708 day mantiene `old_gain=1.13` e `new_gain=1.13`.
- Nessun gain reale viene applicato.

Validazione runtime Raspberry del quarto micro-step del 2026-06-20:

- Auto Gain Apply gated validato dopo introduzione del path reale su `GAIN_NEXT`.
- Default `AUTO_GAIN_APPLY_ENABLED=False`.
- Runtime log mostra `[AUTO_GAIN_APPLY] status=skipped reason=apply_disabled`.
- `mode_disabled` blocca correttamente la day mode quando Auto Gain day e' disattivato.
- Nessun `status=applied` osservato.
- Nessun cambio gain runtime osservato.

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
- Dashboard con visione simultanea dell'ultima immagine di entrambe le camere:
  - mostrare affiancate ASI678MC Zenith e IMX708 South Wide.
  - non mostrare solo una camera come nella dashboard attuale.
  - ogni riquadro deve includere timestamp, age, exposure, gain, quality/status e link alla gallery filtrata.
  - se una camera non ha frame recente, mostrare placeholder/stato chiaro senza nascondere l'altra.
  - layout responsive: affiancato su desktop, stacked su mobile.
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
grep -E "AUTO_GAIN_STATE|AUTO_GAIN_DECISION|AUTO_GAIN_APPLY" /var/log/indi-allsky/indi-allsky.log | tail -200
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
- Auto Gain shadow:
  - `AUTO_GAIN_STATE` and `AUTO_GAIN_DECISION` present for both profiles.
  - day mode remains `enabled=False`.
  - `action=hold`, `reason=gain_auto_disabled`, `shadow=True`.
  - ASI proposed gain remains `0.00`; IMX proposed gain remains `1.13`.
- Auto Gain gated apply:
  - `AUTO_GAIN_APPLY` present.
  - default `apply_enabled=False`.
  - `status=skipped`, `reason=apply_disabled`, `shadow=True`.
  - ASI day remains `old_gain=0.00`, `new_gain=0.00`.
  - IMX day remains `old_gain=1.13`, `new_gain=1.13`.
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
- 2026-06-20: Definita architettura Auto Gain profile-first con state machine day/twilight/night/moonmode.
- 2026-06-20: Aggiunto Auto Gain shadow controller diagnostico, senza apply runtime.
- 2026-06-20: Validati log runtime Auto Gain shadow su Raspberry per IMX708 e ASI678MC.
- 2026-06-20: Aggiunto path Auto Gain apply gated, disattivato di default e limitato a `GAIN_NEXT`.
- 2026-06-20: Aggiunto obiettivo UI dashboard per mostrare simultaneamente l'ultima immagine di entrambe le camere.
- 2026-06-20: Validati log runtime Auto Gain apply gated con `apply_enabled=false` e nessun gain reale applicato.
- 2026-06-20: Aggiunti diagnostici Night Gain Decision Validation con `[AUTO_GAIN_BLOCKER]` e apply validation-only.
- 2026-06-20: Validata persistenza profile-first di ASI678MC Day Target ADU a `95` da UI fino a resolver runtime e controller Auto Exposure/Auto Gain.
- 2026-06-20: Verificata simmetria pipeline profile-first per `target_adu.day/night/dev_day/dev` da UI a runtime flat config.
- 2026-06-20: Abilitato Auto Gain apply reale ma gated: default off, mode-specific, exposure-first, write solo su `GAIN_NEXT`.
- 2026-06-20: Validato su Raspberry che Auto Gain Apply gated resta spento di default (`apply_disabled`) e non cambia il gain runtime.
- 2026-06-20: Convertito sync Camera Settings in Save & Sync per sezione, con CFA/Debayer Pattern esplicitamente profile-specific e non sincronizzabile.
- 2026-06-20: Aggiunto sync Modern Admin Acquisition da un profilo all'altro, limitato ai blocchi automatici comuni e senza copiare identity/hardware camera.
