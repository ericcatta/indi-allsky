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

## Roadmap Per Area

### 1. Camera Control

- DONE:
  - Metering per-camera/profile con modalita' `default`, `average`, `median`, `sigma_clipped`, `background`, `moon_aware`, `stars_only`.
  - Auto Meter state smoother con EMA per `profile_id:camera_id`.
  - Auto Exposure profile-first con runtime baseline da `EXPOSURE_NEXT`/`EXPOSURE_CURRENT`.
  - Auto Exposure daytime ASI con `day_bounded` step e convergenza stabile validata sul Raspberry.
  - Auto Exposure convergence tiers `aggressive/normal/fine/target`.
  - Auto Gain shadow controller, apply gated, profile-specific gain limits e convergence modes.
  - Auto Gain runtime state persistence/restore separata dalla config DB.
  - Hybrid AWB per-camera con `postprocess_rgb` operativo per ASI/INDI.
- IN TEST:
  - Coordinamento continuo Auto Exposure + Auto Gain in condizioni notte/moonmode reali.
  - Auto Exposure blocker/reason diagnostics per tuning senza cambiare comportamento.
- NEXT:
  - Raffinare cooldown/trend profile-first per Auto Exposure.
  - Validare Auto Gain night/moonmode su piu' notti.
  - Ridurre o rimuovere diagnostica temporanea `[ASI_FRAME_STATS]` quando non serve piu'.
- LATER:
  - ROI/mask per metering e AWB.
  - Color calibration per-camera.
  - Stretch custom per-camera.

### 2. Metadata & Analytics

- DONE:
  - `FrameMetadata` JSONL append-only.
  - Daily rotation in `VARLIB_FOLDER/frame_metadata/YYYY-MM-DD.jsonl`.
  - Metadata Analytics Reader con day load, latest frames, recent frames, camera summary e decision statistics.
  - Dashboard MVP read-only con camera cards, latest frame, charts 24h, decision statistics e quick summary.
  - Dashboard Polish v1 con unita' leggibili, reason label, chart Y-axis, tooltip e X-axis temporale.
  - Nightly Summary v1 analytics/UI polish locale: cards responsive per overview, quality, exposure, gain, meter, missing frames, anomaly events, best/worst frame, flags, reasons e trend.
  - Metadata Health & Consolidation locale: report di completezza/validita' metadata, compatibilita' legacy quality e sezione dashboard compatta.
  - Raw-first / Scientific Source Image Architecture micro-step 1:
    - `FrameMetadata` resta backward-compatible mantenendo `image_file_path`;
    - aggiunti campi opzionali per separare immagine display, sorgente scientifica, input detector, FITS/RAW, thumbnail e rendering;
    - per ora `display_image_path=image_file_path`;
    - `source_image_path`, `detector_image_path`, `detector_image_type`, `fits_path`, `raw_path` e `thumbnail_path` restano `None` finche' non vengono collegati in modo sicuro;
    - `rendering_profile=indi-allsky-display-v1`;
    - `overlay_applied` e `stretch_applied` sono popolati con helper conservativi basati su config/capture status;
    - nessun cambio a processing, salvataggio FITS/RAW, detector, dashboard o runtime capture.
- IN TEST:
  - Quality Score v1 metadata-only: usa meter/target, exposure/gain state, capture status e decision state; non usa AI, image analysis o star detection.
  - Nightly Summary v1 sul Raspberry: validare una giornata/notte completa multicamera con gap, anomaly events e trend reali.
  - Metadata Health sul Raspberry: validare coverage/completeness reali sui JSONL giornalieri dopo pull/restart.
- NEXT:
  - Validare Quality Score v1 sul Raspberry con frame buoni, saturi, scuri e capture error.
  - Validare Nightly Summary v1 sul Raspberry con giornata completa e metadata multicamera.
  - Aggiungere filtri dashboard/gallery basati su metadata e quality flags.
  - Grafici storici giornalieri piu' ricchi per brightness/exposure/gain.
  - Raw-first micro-step 2:
    - collegare in modo sicuro `fits_path` e/o `raw_path` ai record DB `IndiAllSkyDbFitsImageTable` / `IndiAllSkyDbRawImageTable` quando esistono;
    - definire `detector_image_path` e `detector_image_type` senza cambiare frequenza o comportamento di salvataggio FITS/RAW;
    - mantenere JPEG/PNG/WebP come display/review rendering, non come source scientifica.
- LATER:
  - Retention policy metadata.
  - Export/debug metadata.
  - Persistenza analytics in SQLite solo se JSONL diventa insufficiente.

### 3. Environmental Awareness

- Scopo della fase:
  - Dopo Metadata / Analytics consolidation, il sistema inizia a interpretare condizioni cielo/ambiente usando segnali affidabili prima di introdurre AI o event detection.
  - Event Detection e AI devono aspettare finche' metadata quality, sky condition e health signals sono abbastanza stabili.
  - Non avviare AI detection prima che il sistema sappia distinguere condizioni cielo buone/scarse.
- Elementi gia' presenti da non duplicare:
  - Dew heater, dew point e sensori ambiente esistono gia' in `sensor.py`, device sensor modules e utility MQTT.
  - Dew heater threshold/control e dew point da sensori/API esistono gia' nella pipeline legacy; Environmental Awareness v1 non deve comandare heater/fan.
  - Weather/API integration esiste in forma legacy/utility, incluso Astrospheric/cloud cover in script di test.
  - Star count e' gia' documentato come misura oggettiva delle condizioni cielo, ma non e' ancora parte della fondazione metadata-only v1.
  - Nightly Summary calcola gia' `night_trend` per quality, meter, exposure e gain; Sky Trend v1 non lo sostituisce, ma aggiunge una classificazione compatta diagnostica.
- IN TEST:
  - Sky Condition foundation v1:
    - modulo isolato metadata-only `sky_condition.py`;
    - valori ammessi: `unknown`, `excellent`, `good`, `usable`, `poor`, `unusable`;
    - input usati: `quality_score`, `quality_flags`, `capture_status`, `meter_value_smoothed`, `target_meter`, `profile_id`, `camera_id`;
    - output profile-aware e multi-camera safe, senza decisioni operative;
    - fallback a `unknown` quando metadata/quality/meter non sono sufficienti;
    - integrato nel Nightly Summary analytics come stato calcolato dall'ultimo frame della camera;
    - nessuna cloud detection, trend, dew/condensation detection, weather fusion, AI o event detection.
  - Cloud Detection v1:
    - modulo isolato metadata-only `cloud_detection.py`;
    - modalita' solo shadow/diagnostica, senza decisioni operative;
    - valori ammessi: `unknown`, `clear`, `mostly_clear`, `partly_cloudy`, `cloudy`, `overcast`;
    - input usati:
      - `sky_condition`;
      - `quality_score`;
      - `quality_flags`;
      - `capture_status`;
      - metadata meter/target quando serve fallback via `sky_condition`;
      - `profile_id` e `camera_id` tramite frame metadata/summary.
    - mapping conservativo:
      - `excellent` -> `clear` se non ci sono flag negativi forti;
      - `good` -> `mostly_clear` se non ci sono flag negativi forti;
      - `usable` -> `partly_cloudy`;
      - `poor` -> `cloudy`;
      - `unusable` con qualita' molto bassa o flag severi -> `overcast`;
      - metadata incompleti o capture fallito -> `unknown`.
    - integrato nel Nightly Summary analytics come `cloud_condition` calcolato dall'ultimo frame della camera.
  - Sky Trend v1:
    - modulo isolato metadata-only `sky_trend.py`;
    - modalita' solo shadow/diagnostica, senza decisioni operative;
    - valori ammessi: `unknown`, `improving`, `stable`, `degrading`;
    - input usati:
      - sequenza temporale metadata della singola camera/profilo;
      - `quality_score`;
      - `sky_condition` come fallback;
      - `cloud_condition` come fallback;
      - `quality_flags` e `capture_status` per penalizzare frame non processati/errori;
      - `timestamp`, `profile_id`, `camera_id` per ordinamento e isolamento.
    - comportamento conservativo:
      - lista vuota, un solo frame o metadata insufficienti -> `unknown`;
      - sequenze con camera/profilo misti -> `unknown`;
      - delta medio iniziale/finale >= 10 punti -> `improving`;
      - delta medio iniziale/finale <= -10 punti -> `degrading`;
      - variazioni piccole -> `stable`.
    - integrato nel Nightly Summary analytics come `sky_trend`, senza rimuovere il dettaglio `night_trend`.
  - Dew / Condensation Detection v1:
    - modulo isolato metadata-only `condensation_detection.py`;
    - modalita' solo shadow/diagnostica, senza decisioni operative;
    - output: `possible_condensation` boolean;
    - input usati:
      - sequenza temporale metadata della singola camera/profilo;
      - `quality_score`;
      - `quality_flags`;
      - `capture_status`;
      - `exposure_us`;
      - `gain`;
      - `sky_trend` tramite classificatore metadata-only.
    - comportamento conservativo:
      - lista vuota, un solo frame, meno di 4 frame o metadata insufficienti -> `False`;
      - sequenze con camera/profilo misti -> `False`;
      - capture fallito o flag critici -> `False`;
      - cloudiness da sola non basta;
      - richiede degrado netto e persistente della qualita', `sky_trend=degrading`, qualita' finale bassa e almeno un segnale coerente tra exposure/gain in aumento o quality flags negativi persistenti.
    - integrato nel Nightly Summary analytics come `possible_condensation`;
    - non usa dew point, sensori ambiente o heater control in questa fase.
  - Environmental Awareness dashboard read-only:
    - card compatta `Sky Awareness` nella Nightly Summary del Modern Admin;
    - mostra per camera `sky_condition`, `cloud_condition`, `sky_trend` e `possible_condensation`;
    - usa solo valori gia' calcolati da `FrameMetadataAnalytics`;
    - nessuna decisione runtime, nessun controllo capture, nessuna AI/ML/event detection.
- NEXT:
  - Raspberry field validation / threshold tuning:
    - verificare su piu' notti/giorni reali che `sky_condition`, `cloud_condition`, `sky_trend` e `possible_condensation` siano coerenti con immagini e meteo osservato;
    - annotare falsi positivi/negativi prima di cambiare soglie;
    - mantenere la visualizzazione read-only finche' i segnali non sono validati.
  - Weather Awareness:
    - Purpose: combinare in futuro metadata interni con meteo esterno o sensori locali.
    - Nessun requisito di API esterna nella prima fase.
- Prossimo micro-step consigliato:
  - Raspberry field validation / threshold tuning degli indicatori Environmental Awareness prima di usare questi segnali in dashboard avanzate o automazioni.
- LATER:
  - Integrare temperatura Raspberry/CPU, spazio disco e health log.
  - Alert futuri Telegram/email/webhook.
  - Analisi ambientale persistita come metadata, non solo log.

### 4. Event Detection

- IN TEST:
  - Event Candidate v0 data contract + persistence/analytics shadow-only:
    - modulo isolato `event_candidate.py`;
    - contratto `EventCandidate` con `schema_version=event_candidate_v0`;
    - `candidate_type` forzato a `unclassified`;
    - `shadow_only=True`;
    - contesto quality/environment salvato come snapshot diagnostico;
    - persistenza append-only JSONL in directory `event_candidates/YYYY-MM-DD.jsonl`;
    - analytics minimi per riepilogo notturno: totale candidate, conteggio per camera, conteggio per reason, score medio e score massimo;
    - builder placeholder disabilitato di default se non vengono fornite reason esplicite;
    - nessuna integrazione nella capture pipeline, nessuna decisione runtime, nessuna classificazione meteor/satellite/aircraft/aurora.
  - Event Timeline v0 shadow-only:
    - contratto `EventTimelineSegment` con `schema_version=event_timeline_segment_v0`;
    - `segment_type` forzato a `unclassified`;
    - `shadow_only=True`;
    - raggruppa solo candidate esistenti e omogenee per `camera_id`, `profile_id`, `night_id`;
    - max gap configurabile tra candidate, default `2s`;
    - persistenza append-only JSONL in directory `event_timelines/YYYY-MM-DD.jsonl`;
    - analytics minimi: totale segmenti, segmenti per camera, durata media/max, candidate medie/max per segmento e conteggi reason;
    - nessuna dashboard UI, nessuna classificazione reale, nessuna integrazione capture.
  - Event Foundation Dashboard Read-only v0:
    - Modern Admin dashboard mostra analytics JSONL esistenti per Event Candidates ed Event Timelines;
    - espone totale, conteggi per camera/reason, score candidate medio/max, durata timeline media/max e candidate per segmento;
    - gestisce file mancanti/vuoti/malformati senza crash;
    - solo diagnostica read-only: nessuna generazione automatica candidate, nessun trigger runtime, nessuna classificazione.
  - Event Foundation manual smoke test:
    - script manuale `testing/event_foundation_smoke_test.py`;
    - genera dati sintetici chiaramente marcati `synthetic-smoke-v0`;
    - default sicuro in `/tmp/indi-allsky-event-foundation-smoke`;
    - per popolare la dashboard Raspberry: `python3 testing/event_foundation_smoke_test.py --varlib /var/lib/indi-allsky`;
    - cleanup mirato: `python3 testing/event_foundation_smoke_test.py --varlib /var/lib/indi-allsky --cleanup`;
    - nessuna generazione automatica, nessun hook runtime.
  - Candidate Trigger Rules v0 shadow-only:
    - funzione pura/test-only `evaluate_candidate_triggers(...)`;
    - valuta solo metadata gia' esistenti e contesto quality/environment;
    - trigger conservativi v0: `brightness_spike`, `quality_drop`, `condensation_onset`, `sky_condition_transition`;
    - `sky_condition_transition` viene soppresso quando `quality_flags` contiene `exposure_adjusting` o `meter_near_edge`, per evitare candidate rumorose durante settling exposure/metering;
    - la soppressione `sky_condition_transition` viene conteggiata in `event_candidate_runtime.json` e nell'offline pipeline report, con breakdown per `exposure_adjusting` e `meter_near_edge`;
    - supporta override opzionali via `profile_config`;
    - puo' essere disabilitata via `event_candidate_triggers.enabled=False`;
    - non persiste e non viene chiamata automaticamente;
    - genera solo `EventCandidate` `unclassified` e `shadow_only=True`;
    - nessuna AI, RMS, meteor detection o classificazione reale.
  - Candidate Trigger Smoke Test v0:
    - script manuale `testing/candidate_trigger_smoke_test.py`;
    - genera metadata sintetici per casi normal, brightness spike, quality drop, condensation onset e sky/cloud transition;
    - default sicuro in `/tmp/indi-allsky-candidate-trigger-smoke`;
    - per popolare la dashboard Raspberry: `python3 testing/candidate_trigger_smoke_test.py --varlib /var/lib/indi-allsky`;
    - cleanup mirato: `python3 testing/candidate_trigger_smoke_test.py --varlib /var/lib/indi-allsky --cleanup`;
    - resta manual-only: nessun hook capture/runtime, nessuna classificazione.
  - Runtime Shadow Integration v0:
    - collega i trigger candidate al path metadata solo dopo la persistenza `FrameMetadata`;
    - gated da `event_candidate_triggers.enabled`, default `False`;
    - quando disabilitato non valuta trigger, non persiste candidate e non aggiorna timeline;
    - quando abilitato valuta metadata + quality + contesto Environmental Awareness corrente e persiste JSONL candidate/timeline;
    - failure isolation: errori trigger/persistenza sono loggati e non bloccano image saving, metadata generation o capture;
    - timeline giornaliera ricostruita dai candidate JSONL per evitare duplicati;
    - ancora nessuna AI, RMS, meteor detection, classificazione, notification o decisione runtime.
  - Controlled Enablement v0:
    - abilita la generazione candidate runtime solo se `event_candidate_triggers.enabled=True`;
    - aggiunge safety limit runtime `max_candidates_per_hour`, default `100`;
    - Web UI config controls aggiunti nella configurazione Full Settings / Modern Settings Inventory:
      - `EVENT_CANDIDATE_TRIGGERS.enabled`, default `False`;
      - `EVENT_CANDIDATE_TRIGGERS.max_candidates_per_hour`, default `100`;
      - sezione `Event Detection Foundation`, con testo esplicito shadow-only.
    - se il limite orario viene raggiunto, non vengono persistiti nuovi candidate e la capture continua invariata;
    - persiste diagnostica runtime in `event_candidate_runtime.json`:
      - trigger evaluations;
      - generated candidates;
      - candidates by reason;
      - trigger evaluation failures;
      - rate-limit hits.
      - `last_status`, incluso `disabled`, `evaluated`, `generated`, `failure`, `rate_limited`.
    - la diagnostica runtime viene scritta anche quando:
      - `enabled=True` ma nessuna regola produce candidate (`status=no_candidates`, `reason=no_trigger_rules_matched`);
      - `enabled=False`, cosi' la dashboard puo' distinguere runtime spento da path non eseguito.
    - Modern Admin mostra card read-only `Event Candidate Runtime`;
    - Nightly Summary espone `event_trigger_evaluations`, `event_trigger_candidates`, `event_trigger_failures`;
    - ancora shadow-only: nessuna AI, RMS, meteor detection, classificazione, notification o decisione runtime.
  - Event Classification v1 foundation:
    - contratto `EventClassification` con `schema_version=event_classification_v1`;
    - writer JSONL append-only in directory `event_classifications/YYYY-MM-DD.jsonl`;
    - classifier `RuleBasedEventClassifierV1` shadow-only;
    - registry regole `ClassificationRuleRegistry` con contratti `ClassificationRule` e `ClassificationRuleResult`;
    - registry vuoto di default, quindi il comportamento resta no-op e produce `unknown_event`;
    - se in futuro piu' regole shadow matchano, il classifier sceglie il label con score piu' alto e tie-break deterministico per ordine registrazione;
    - explainability foundation:
      - `rules_matched` contiene `rule_id`, `target_label`, `score`, `reason`;
      - `features_used` include candidate ids, timestamp inizio/fine, summary quality e summary environment della timeline;
      - rende auditabili regole future senza introdurre regole reali.
    - prima regola shadow-only non registrata di default:
      - `WeatherOrCloudEventRule`;
      - `target_label=weather_or_cloud_event`;
      - matcha solo segnali ambientali forti da timeline summary/reasons;
      - `sky_condition_transition` e `partly_cloudy` da soli non bastano per classificare;
      - `sky_condition_transition` contribuisce solo come segnale di supporto quando e' presente almeno un segnale forte;
      - confidence conservativa `0.35-0.65`;
      - usabile solo in test/manual registry finche' non verra' deciso un path runtime/dashboard dedicato.
    - runner offline/manuale:
      - legge Event Timeline JSONL esistenti;
      - registra esplicitamente `WeatherOrCloudEventRule` solo per la run manuale;
      - scrive Event Classification JSONL append-only;
      - salta righe malformate o incomplete senza fermare l'intera run;
      - nessun hook runtime/capture/dashboard.
    - report offline/read-only Event Pipeline:
      - legge Event Candidate, Event Timeline ed Event Classification JSONL;
      - produce conteggi per camera, profilo, reason, label, quality flags e segnali environmental;
      - tollera file mancanti, vuoti o righe JSONL malformate;
      - non genera nuovi record e non modifica file.
    - semantica:
      - `unclassified` = non processato da classifier;
      - `unknown_event` = processato dal classifier ma nessuna regola ha matchato;
    - con registry vuoto produce `label=unknown_event`; `status=shadow` e `method=rule_based_v1` restano forzati;
    - nessuna AI, RMS, meteor/satellite/aircraft/aurora detection, notification o decisione runtime.
- NEXT:
  - Raspberry validation Controlled Enablement v0:
    - abilitare temporaneamente `event_candidate_triggers.enabled=True` in configurazione controllata;
    - verificare che `/var/lib/indi-allsky/event_candidate_runtime.json` venga creato anche con zero candidate;
    - verificare che `total_evaluations` cresca e `last_status` rifletta `evaluated`/`generated`/`disabled`;
    - verificare che candidate/timeline reali compaiano nei JSONL e nella dashboard;
    - verificare che con `enabled=False` non vengano generati nuovi record;
    - verificare che `max_candidates_per_hour` limiti correttamente il volume candidate;
    - confermare assenza di effetti su capture timing, exposure, gain e image saving.
  - Event Timeline dashboard detail:
    - collegare segmenti a frame/candidate per ispezione manuale;
    - mantenere tutti i segmenti `unclassified`;
    - nessuna azione runtime o pubblicazione automatica.
  - Event Classification analytics/dashboard read-only:
    - contatori per label/status/method quando la classificazione sara' generata da job/manual hook;
    - mantenere label reali future separate da `unknown_event`.
  - Event Timeline frame traceability:
    - aggiungere un reader offline che colleghi `EventTimeline.candidate_ids` ai rispettivi `EventCandidate.frame_id`;
    - collegare poi `frame_id/camera_id/profile_id` ai `FrameMetadata.image_file_path`;
    - restituire una sequenza ordinata di frame prima/durante/dopo la timeline, senza eseguire detection;
    - questo e' prerequisito per qualsiasi detector meteor responsabile, per review manuale e per futuri input RMS/AI;
    - mantenere tutto read-only/offline e profile-first.
- LATER:
  - Meteor detection.
  - Aurora detection.
  - Satellite detection.
  - Aircraft detection, se utile per il sito pubblico o per debug.
  - Light pollution/event detection futura.
  - Timeline diagnostica giornaliera con eventi camera restart, exposure jump, saturation, missing frame, service restart.

### 5. Meteor Intelligence

- Scopo della fase:
  - Aprire il dominio Meteor Intelligence senza implementare detection, RMS, AI o integrazione runtime.
  - Separare il concetto scientifico `MeteorObservation` dai contratti generici `EventCandidate` e `EventTimeline`.
  - Mantenere il paradigma Event Framework: shadow-first, profile-first, multi-camera, explainability e provenance.
- IN TEST:
  - MeteorObservation domain model:
    - modulo isolato `meteor_observation.py`;
    - contratto `MeteorObservation` con `schema_version=meteor_observation_v1`;
    - rappresenta una osservazione meteor indipendente dal detector che l'ha prodotta;
    - collega l'osservazione a `source_event_id` e `source_timeline_id`;
    - include `detector_id`, `detector_version`, `confidence`, `validation_state`, `observation_timestamp`, `camera_id`, `profile_id`, `created_at` e `status`;
    - genera `meteor_id` deterministico dai riferimenti di evidenza, detector, camera/profilo e timestamp;
    - persistenza append-only JSONL tramite `MeteorObservationWriter`;
    - directory default `meteor_observations/`;
    - file giornalieri `YYYY-MM-DD.jsonl` derivati da `observation_timestamp`;
    - stati ammessi iniziali:
      - `status`: `shadow`, `validated`, `reviewed`, `ground_truth`;
      - `validation_state`: `unknown`, `automatic`, `human_reviewed`, `ground_truth`;
    - non include ancora magnitude, shower, radiant, velocity, duration, persistent train, orbit o campi RMS-specifici.
  - MeteorReview domain model:
    - contratto `MeteorReview` con `schema_version=meteor_review_v1`;
    - rappresenta l'assessment corrente di una `MeteorObservation`;
    - non rileva nulla e non valida nulla: review registra valutazione, validation registrera' trust in una fase successiva;
    - include `review_id`, `meteor_id`, `review_actor`, `review_timestamp`, `review_result`, `confidence`, `evidence_sources`, `notes` e `created_at`;
    - `review_id` deterministico da meteor, actor, timestamp, result ed evidence sources;
    - actor ammessi: `automatic_policy`, `human`, `external_detector`, `cross_camera`, `ai_assisted`;
    - result ammessi: `pending`, `accepted`, `rejected`, `needs_more_evidence`, `ground_truth`;
    - persistenza append-only JSONL tramite `MeteorReviewWriter`;
    - directory default `meteor_reviews/`;
    - file giornalieri `YYYY-MM-DD.jsonl` derivati da `review_timestamp`;
    - nessuna UI, RMS, AI, dashboard o integrazione runtime.
  - MeteorValidation domain model:
    - contratto `MeteorValidation` con `schema_version=meteor_validation_v1`;
    - registra la trust decision assegnata a una `MeteorObservation` dopo review/evidence;
    - separa chiaramente trust state da detection e review;
    - include `validation_id`, `meteor_id`, `validation_state`, `validation_actor`, `validation_timestamp`, `confidence`, `evidence_review_ids`, `evidence_sources`, `reason` e `created_at`;
    - `validation_id` deterministico da meteor, stato, actor, timestamp, review ids e evidence sources;
    - puo' referenziare uno o piu' `MeteorReview` tramite `evidence_review_ids`;
    - stati ammessi: `unvalidated`, `automatically_validated`, `human_validated`, `rejected`, `ground_truth`, `benchmark`;
    - actor ammessi: `automatic_policy`, `human`, `cross_camera`, `external_detector`, `ai_assisted`;
    - persistenza append-only JSONL tramite `MeteorValidationWriter`;
    - directory default `meteor_validations/`;
    - file giornalieri `YYYY-MM-DD.jsonl` derivati da `validation_timestamp`;
    - nessuna validation algorithm, RMS, AI, dashboard, UI o integrazione runtime.
  - Meteor Intelligence offline report:
    - funzione read-only `build_meteor_intelligence_offline_report(...)`;
    - legge JSONL di `MeteorObservation`, `MeteorReview` e `MeteorValidation`;
    - tollera file mancanti, vuoti e righe JSONL malformate;
    - produce conteggi per profilo, camera, detector, observation status, review actor/result e validation actor/state;
    - espone conteggi foundation per meteor validati, rejected, ground truth e benchmark;
    - non crea record, non muta file e non introduce dashboard, Telegram, RMS, AI o detection.
  - Meteor Intelligence text summary renderer:
    - funzione read-only `render_meteor_intelligence_text_summary(...)`;
    - converte il report offline in testo breve human-readable;
    - include date opzionale, observation count, validated/rejected/ground truth/benchmark count, detector counts, validation state counts e warning malformed solo se presenti;
    - foundation futura per Telegram text summary, CLI output e dashboard text block;
    - non invia messaggi, non scrive file e non assume UI.
  - Offline EventClassification -> MeteorObservation bridge:
    - funzione manuale `convert_meteor_classifications_offline(...)`;
    - legge JSONL `EventClassification` e converte solo righe con `label=meteor_candidate`;
    - scrive `MeteorObservation` append-only tramite `MeteorObservationWriter`;
    - usa `event_id` come `source_event_id`, con fallback a `timeline_id`;
    - usa `features_used.start_timestamp_utc` come `observation_timestamp`, con fallback a `created_at`;
    - imposta `status=shadow` e `validation_state=unknown`;
    - tollera file mancanti, righe malformate, label non meteor e campi opzionali mancanti;
    - non deduplica: esecuzioni ripetute appendono duplicati, come gli altri writer append-only foundation;
    - non crea `MeteorReview`, `MeteorValidation`, campi scientifici, RMS adapter, AI, dashboard o integrazione runtime.
  - Audit image/frame data per futura meteor detection:
    - immagini processate salvate sotto `IMAGE_FOLDER`, default `/var/www/html/allsky/images`;
    - path per camera/profilo: `ccd_<camera_uuid>/exposures/YYYYMMDD/day|night/DD_HH/ccd<camera_id>_YYYYMMDD_HHMMSS.<type>`;
    - `FrameMetadata` JSONL contiene `frame_id`, `timestamp`, `camera_id`, `profile_id`, `image_file_path`, exposure/gain, meter, quality flags e capture status;
    - `EventCandidate` contiene `frame_id`, `camera_id`, `profile_id`, `timestamp_utc`, quality context ed environment context, ma non contiene direttamente `image_file_path`;
    - `EventTimeline` contiene `candidate_ids` e summary quality/environment, ma non espande ancora i frame sorgente;
    - per risalire all'immagine serve join esplicito `timeline -> candidate -> frame_metadata -> image_file_path`;
    - multiple consecutive frames sono recuperabili dai metadata per `camera_id/profile_id/timestamp`, ma manca un helper ufficiale per timeline;
    - formati immagini processate supportati: `jpg/jpeg`, `png`, `webp`, `tif/tiff`; FITS e raw export sono opzionali e non garantiti per ogni frame;
    - thumbnail esistono via `IndiAllSkyDbThumbnailTable` e sono adatte a UI/review, non a detector scientifico;
    - mask e ROI esistono per SQM/ADU/star/line detection, ora con cache shape-aware multicamera;
    - logica riusabile ma non sufficiente: `detectLines.py` usa Canny + HoughLinesP dietro `DETECT_METEORS`, mentre `stars.py` usa template matching per stelle;
    - non esiste ancora un contratto detector input stabile per sequenze frame, mask, provenance e output evidence;
    - conclusione: un detector rule-based meteor e' supportabile solo come esperimento offline, non ancora responsabilmente in runtime.
- NEXT:
  - Validare il contratto rispetto ai futuri output RMS prima di implementare l'adapter.
  - Validare il bridge offline su file `EventClassification` reali quando esisteranno label `meteor_candidate`.
  - Implementare `TimelineFrameSet` / `DetectorInputBundle` offline read-only:
    - input: EventTimeline JSONL, EventCandidate JSONL e FrameMetadata JSONL;
    - output: frame ordinati con `image_file_path`, timestamp, exposure/gain, quality/environment e riferimenti candidate/timeline;
    - nessuna detection, nessuna RMS/AI, nessuna modifica runtime.
- LATER:
  - RMS adapter verso MeteorObservation.
  - Campi fisici meteor estesi: magnitude, shower, radiant, velocity, persistent train e orbit.
  - Workflow review/ground truth meteor.

### 6. AI / Smart Features

- IDEAS:
  - AI classification per frame o per sequenza.
  - Smart summaries giornalieri/notturni.
  - Anomaly detection su exposure/gain/meter/quality metadata.
  - Riconoscimento frame inutilizzabili:
    - saturi.
    - neri.
    - fuori fuoco.
    - coperti.
    - mossi/artefatti.
  - Eventuali modelli futuri devono scrivere output come metadata persistente e restare opzionali.

### 7. Future / Backlog

- Dashboard pubblica esterna piu' pulita.
- Dashboard con visione simultanea dell'ultima foto di entrambe le camere.
- Gallery multicamera con filtri per camera, giorno/notte, qualita' e reason.
- Nomi camera chiari nella UI:
  - "ASI678MC Zenith".
  - "IMX708 South Wide".
- Modalita' "science/debug day" che salva campioni raw periodici per analisi.
- Profilo "public-safe" con pubblicazione solo frame validi.
- Preset hardware:
  - ASI678MC daytime.
  - ASI678MC night.
  - IMX708 long exposure.
  - IMX708 daylight.

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
  - Save & Sync e' disponibile per tutte le sezioni Camera Settings salvabili:
    - Driver / Connection.
    - Acquisition.
    - Lens & Optics.
    - Hybrid Controller.
  - ogni Save & Sync salva prima la sezione del profilo corrente e poi sincronizza solo i campi ammessi di quella sezione verso l'altro profilo;
  - preserva identity/hardware (`profile_id`, `camera_id`, driver, `indi`, `libcamera`, lens, processing, binning, AWB);
  - `CFA / Debayer Pattern` resta profile-specific, hardware-specific e non viene copiato;
  - `CFA / Debayer Pattern` e' modificabile per-camera ma non e' sincronizzato, per evitare di copiare pattern Bayer tra sensori diversi;
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
- Stabilizzato processing multicamera con risoluzioni diverse:
  - SQM non e' piu' fatale se la mask non combacia con il frame;
  - ADU fallback usa media non mascherata se la mask non e' compatibile;
  - star detection non fa piu' crashare OpenCV con mask incompatibili;
  - cache ADU/SQM/Stars keyed da `(binning, image_width, image_height)` per evitare riuso cross-camera tra IMX708 e ASI678MC;
  - detection mask globale viene usata solo se compatibile con la shape corrente, altrimenti viene generata una ROI locale.

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
- Auto Exposure Refinement fase 1:
  - audit conferma che Auto Exposure ha trend minimale per camera/profilo e reset su cambio segno tramite stato Auto Meter;
  - non ha ancora cooldown dedicato, trend separato over/under persistente, outlier guard o parametri profile-first completi per deadband/trend/cooldown;
  - aggiunto logging diagnostico conservativo con `reason`/`blocker` in `[AUTO_EXPOSURE_DECISION]`;
  - aggiunto `[AUTO_EXPOSURE_BLOCKER]` per spiegare hold/blocchi come `inner_deadband_hold`, `trend_not_confirmed`, `gain_control_disabled`, limiti exposure/gain;
  - nessuna modifica a step, apply, UI, config o coordinamento runtime con Auto Gain.

### Metadata / Analytics Base

- Aggiunto schema `FrameMetadata` per metadata frame append-only.
- Persistenza iniziale in JSONL, senza migration DB:
  - default daily rotation: `VARLIB_FOLDER/frame_metadata/YYYY-MM-DD.jsonl`.
  - la data del file viene derivata da `FrameMetadata.timestamp`.
  - override opzionale legacy: `FRAME_METADATA_PATH` mantiene il comportamento a file singolo, salvo `FRAME_METADATA_ROTATE_DAILY=True`.
  - `FRAME_METADATA_PATH` vuoto viene trattato come non configurato, quindi usa la directory daily default.
  - ogni write riuscito logga `[FRAME_METADATA] status=written path=...` per validazione runtime a basso rumore.
- Campi persistiti:
  - `frame_id`.
  - `timestamp`.
  - `camera_id`.
  - `profile_id`.
  - `image_file_path`.
  - `exposure_us`.
  - `gain`.
  - `meter_value_raw`.
  - `meter_value_smoothed`.
  - `target_meter`.
  - `meter_error`.
  - `auto_exposure_action`.
  - `auto_gain_action`.
  - `decision_reason`.
  - `capture_status`.
  - `error_message`.
  - `quality_score`.
  - `quality_flags`.
- Scrittura best-effort dopo processing:
  - `processed` quando l'immagine viene salvata e inserita nel DB.
  - `input_missing`, `input_empty`, `bad_image`, `not_saved` per percorsi noti senza DB image id.
- Analytics reader base:
  - legge direttamente i daily JSONL, senza migration DB.
  - API iniziali: `load_day(date)`, `get_latest_frames(limit)`, `get_recent_frames(hours)`, `get_camera_summary(camera_id)`, `get_decision_statistics(camera_id=None)`.
  - summary include count, timestamp primo/ultimo, min/max/media exposure, gain e meter value.
  - statistiche decisioni includono conteggi per `auto_exposure_action`, `auto_gain_action` e `decision_reason`.
- Dashboard MVP read-only sopra `FrameMetadataAnalytics`:
  - mostra side-by-side le ultime immagini disponibili per Camera 1 e Camera 2 quando presenti;
  - mostra per camera `camera_id`, `profile_id`, timestamp, exposure, gain, meter value, target meter e decision reason;
  - visualizza serie 24h per exposure, gain e meter value senza nuove dipendenze frontend;
  - mostra statistiche decisioni Auto Exposure, Auto Gain e reason count;
  - mostra quick summary per camera con frame count, exposure/gain/meter medi/min/max;
  - funziona anche se una camera e' offline o senza metadata recenti.
- Dashboard Polish v1:
  - Quick Summary spostato subito sotto le camera cards;
  - exposure formattata in ms sotto 1s e secondi sopra 1s;
  - gain formattato come moltiplicatore `x`;
  - meter mostrato come valore misurato / target;
  - reason/action comuni convertiti in label leggibili;
  - grafici con label asse Y e tooltip timestamp/exposure/gain/meter.
- Dashboard X-axis polish:
  - grafici con label temporali locali sull'asse X;
  - subtitle `Last 24 hours` in ogni chart;
  - tooltip con timestamp locale completo.
- Nessun cambio a upload, processing, Auto Exposure o Auto Gain.

## IN TEST

### Quality Score v1

- Quality Score v1 metadata-only implementato localmente e da validare sul Raspberry:
  - usa solo meter value, target meter, exposure/gain state, capture status, action/reason dei controller ed eventuale error message;
  - non usa AI, image analysis, star detection o quality inference da pixel;
  - persiste `quality_score` 0-100 e `quality_flags` in ogni `FrameMetadata`;
  - Dashboard mostra latest quality score/flags nelle camera cards e average quality nel quick summary.
- Validare su frame buoni, saturi, quasi neri e capture error.

### Nightly Summary v1

- Nightly Summary v1 implementato localmente e da validare sul Raspberry:
  - legge daily JSONL esistenti senza schema DB nuovo;
  - produce riepilogo per camera con frame count, first/last timestamp, quality score avg/min/max, meter avg/min/max, exposure avg/min/max e gain avg/min/max;
  - mostra quality flags e decision reasons piu' comuni;
  - calcola percentuale frame nominali, low meter, high meter, exposure max, gain max e capture errors usando solo metadata esistenti;
  - calcola missing frames rilevando gap tra timestamp consecutivi oltre 2x l'intervallo atteso stimato dalla sequenza della camera;
  - calcola anomaly events metadata-only: capture errors, low quality, exposure max, gain max, meter troppo basso e meter troppo alto;
  - seleziona best/worst image tramite `quality_score` massimo/minimo, tollerando metadata legacy senza quality;
  - calcola night trend semplice per quality, meter, exposure e gain confrontando prima e seconda meta' della sequenza;
  - Dashboard mostra la sezione read-only `Nightly Summary` in layout card-based coerente con Modern Admin:
    - Summary Overview.
    - Quality Score.
    - Exposure.
    - Gain.
    - Meter.
    - Missing Frames.
    - Anomaly Events.
    - Best / Worst Image.
    - Quality Flags.
    - Decision Reasons.
    - Night Trend.
  - il layout usa card scure responsive, griglia desktop/tablet e stack verticale su schermi piccoli;
  - tollera righe JSONL legacy senza `quality_score` o `quality_flags`.
- Validare con una notte/giornata completa su entrambe le camere.

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
  - validazione runtime Raspberry 2026-06-21:
    - `gain_max_day`, `gain_max_night`, `gain_max_moonmode` persistono nel profilo corretto;
    - `[MULTI_CAMERA_RESOLVED_CONFIG]` mostra i `gain_max_*` risolti per profilo;
    - `[AUTO_GAIN_DECISION]` usa il limite `gain_max` della modalita' corrente;
    - ASI678MC in moonmode raggiunge correttamente `gain=300` quando il profilo consente `gain_max_moonmode=300`;
    - IMX708 conserva i propri limiti separati e non eredita i limiti ASI.

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

Validazione runtime Raspberry Auto Gain convergence del 2026-06-21:

- Auto Gain day/night/moonmode e' risolto per profilo e per modalita'.
- Auto Gain Apply gated funziona con default sicuro `AUTO_GAIN_APPLY_ENABLED=False` e apply reale solo quando abilitato esplicitamente.
- Le decisioni aggressive sono generate correttamente quando `abs_error > 20 ADU`.
- Per errori normali `5-20 ADU` resta il comportamento bounded normale.
- La fine convergence si attiva quando `abs_error < 5 ADU` persiste per 5 frame consecutivi.
- La convergenza fine si ferma quando `abs_error <= 1.5 ADU`.
- I log mostrano `convergence_mode=aggressive|normal|fine`, `fine_convergence`, `convergence_frames` e `step_strategy` coerenti.
- ASI678MC moonmode ha prodotto decisioni Auto Gain aggressive corrette e ha raggiunto `gain=300` rispettando il limite profile-specific.
- Il runtime resolver continua a usare target ADU e gain max profile-first, senza fallback globale inatteso.
- Auto Gain restart restore:
  - aggiunto state file runtime separato dalla config DB: `VARLIB_FOLDER/auto_gain_runtime_state.json`.
  - validazione Raspberry iniziale ha mostrato che lo state file non veniva creato quando `AUTO_GAIN_APPLY_ENABLED=False`, perche' il gain adattivo evolveva comunque tramite `GAIN_NEXT` ma il save era agganciato solo al path di apply reale.
  - il fix persiste l'ultimo gain adattivo per `profile_id:camera_id:mode` ogni volta che il runtime cambia `GAIN_NEXT`, anche se il write camera/hardware e' bloccato dall'apply gate.
  - quando Auto Gain Apply scrive davvero su `GAIN_NEXT`, salva lo stesso stato con reason `apply_applied`.
  - quando Auto Exposure o il ricalcolo legacy aggiornano `GAIN_NEXT`, salva lo stato con reason `runtime_next_changed`.
  - al restart CaptureWorker ripristina `GAIN_CURRENT`/`GAIN_NEXT` dal valore recente se profilo, camera e mode coincidono.
  - il restore clampa sempre al range corrente `gain_min/gain_max`.
  - fallback al gain configurato resta invariato se lo stato e' assente, scaduto o appartiene a un altro profilo.
  - log diagnostici: `[AUTO_GAIN_RESTORE]`, `[AUTO_GAIN_RESET]` e `[AUTO_GAIN_STATE_SAVE]`.
  - nessuna scrittura su config DB o camera hardware viene fatta dal solo save dello stato runtime.

### Auto Exposure Refinement

- Auto Exposure convergence tiers unificati, allineati alla filosofia Auto Gain:
  - finding Raspberry: con `smoothed_value=253-255`, `target_adu_day=95`, gain gia' al minimo e exposure multi-secondo, la decisione `decrease_exposure` usava ancora `day_bounded` con `day_max_step=0.005s`, rendendo il recupero dalla saturazione troppo lento.
  - `convergence_mode=aggressive` quando `abs(error) > 20 ADU`; usa stima proporzionale ADU `estimated_exposure = current_exposure * (target / max(smoothed_value, 1.0))`.
  - in aggressive decrease la stima guida la correzione ma viene limitata da cap di sicurezza: non meno del 50% dell'exposure corrente sopra `1.0s`, non meno del 70% tra `0.1s` e `1.0s`, non meno dell'85% sotto `0.1s`.
  - in aggressive increase la stima guida la crescita ma non supera lo step aggressivo bounded e resta clamped a `exposure_max`.
  - `convergence_mode=normal` per `5..20 ADU`, mantenendo il comportamento esistente.
  - `convergence_mode=fine` per `1.5..5 ADU` dopo 5 frame consecutivi con stesso segno, usando micro-step.
  - `convergence_mode=target` con `action=hold` quando `abs(error) <= 1.5 ADU`.
  - clamp sempre a `exposure_min`.
  - log `[AUTO_EXPOSURE_DECISION]` include `convergence_frames`, `fine_convergence`, `convergence_mode`, `saturated`, `estimated_exposure`, `correction_ratio`, `safety_limited`, `exposure_step` e `step_strategy`.
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
- Aggiungere blocker/reason applicativi piu' completi solo dopo validazione runtime dei nuovi log:
  - `saturated_frame`.
  - `near_black_frame`.
  - `cooldown_active`.
  - `outlier_frame`.
  - `exposure_already_max`.
  - `exposure_already_min`.
- Strategie separate ASI e Raspberry camera, senza hardcode fragile.
- Metrica esposimetrica piu' stabile per cielo diurno:
  - usare percentili bassi/medi.
  - ignorare top percentile.
  - gestire Sole/nubi molto luminose.
- Protezione frame saturi/quasi neri:
  - se raw p99 e' saturo, forzare riduzione graduale ma decisa.
  - se raw e' quasi nero, aumentare gradualmente senza salto enorme.
- Valutare se il meter per Auto Exposure debba misurare prima o dopo Hybrid AWB.

### Metadata / Analytics Follow-up

- Metadata Health & Consolidation:
  - analytics espone un report read-only su tutti i JSONL disponibili o su un giorno specifico;
  - verifica presenza dei campi core `frame_id`, `timestamp`, `camera_id`, `profile_id`, exposure/gain/meter, `capture_status`, `quality_score`, `quality_flags`;
  - valida timestamp, exposure/gain non negativi, `quality_score` 0-100, `quality_flags` lista e identita' camera/profilo;
  - righe legacy senza `quality_score`/`quality_flags` vengono conteggiate in completeness/quality coverage ma non rompono analytics e non sono invalid rows;
  - righe JSONL vuote o malformate vengono saltate dal reader, cosi' una riga corrotta non rompe Modern Admin dashboard/summary/health;
  - Dashboard mostra una card compatta `Metadata Health` con frames checked, completeness, quality coverage, invalid rows, missing fields e invalid values.
- Validare runtime JSONL su Raspberry con entrambe le camere.
- Decidere retention per `frame_metadata/YYYY-MM-DD.jsonl`.
- Aggiungere export/debug semplice per analizzare una giornata.
- Valutare se promuovere i metadata da JSONL a SQLite quando dashboard/chart richiedono query veloci.
- Popolare `quality_score` e `quality_flags` con AI/smart detection future.

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
grep -E "AUTO_EXPOSURE_BLOCKER|AUTO_EXPOSURE_DECISION" /var/log/indi-allsky/indi-allsky.log | tail -200
grep -E "AUTO_GAIN_STATE|AUTO_GAIN_DECISION|AUTO_GAIN_APPLY" /var/log/indi-allsky/indi-allsky.log | tail -200
grep -E "AUTO_GAIN_RESTORE|AUTO_GAIN_RESET" /var/log/indi-allsky/indi-allsky.log | tail -100
grep -E "ASI_FRAME_STATS|HYBRID_AWB" /var/log/indi-allsky/indi-allsky.log | tail -200
ls -l /var/lib/indi-allsky/frame_metadata/
tail -20 /var/lib/indi-allsky/frame_metadata/$(date +%F).jsonl
cat /var/lib/indi-allsky/auto_gain_runtime_state.json
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
  - `AUTO_EXPOSURE_DECISION` includes explicit `reason` and `blocker`.
  - `AUTO_EXPOSURE_BLOCKER` explains hold/blocked decisions without changing runtime behavior.
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
- Auto Gain profile limits:
  - `MULTI_CAMERA_RESOLVED_CONFIG` includes `gain_max_day`, `gain_max_night`, `gain_max_moonmode`.
  - `AUTO_GAIN_DECISION` reports the active mode `gain_max` from the profile.
  - ASI moonmode can reach `gain=300` when `gain.max_moonmode=300`.
  - IMX gain limits remain separate from ASI gain limits.
- Auto Gain convergence:
  - large errors `abs_error > 20 ADU` log `convergence_mode=aggressive` / `step_strategy=aggressive_bounded`.
  - normal errors `5-20 ADU` keep normal bounded behavior.
  - persistent small errors `abs_error < 5 ADU` for 5 frames activate `fine_convergence`.
  - `abs_error <= 1.5 ADU` returns to hold.
- Auto Gain restore:
  - `[AUTO_GAIN_RESTORE]` reports `reason=restored` after service restart when a recent adaptive gain exists.
  - `[AUTO_GAIN_RESTORE]` reports `reason=clamped` if persisted gain exceeds current profile/driver limits.
  - `[AUTO_GAIN_RESET]` explains fallback to configured gain for missing/expired/profile-changed state.
- Hybrid AWB:
  - ASI backend `postprocess_rgb`.
  - IMX backend according to profile apply mode.
- Libcamera long exposures:
  - no `--immediate` for exposure >= 1s.
  - no repeated 5x exposure cadence caused by AWB auto.
- Frame metadata JSONL:
  - `/var/lib/indi-allsky/frame_metadata/YYYY-MM-DD.jsonl` exists after new frames are processed.
  - latest rows contain `profile_id`, `camera_id`, `exposure_us`, `gain`, meter values and Auto Exposure/Gain actions.
  - `capture_status=processed` for saved frames.
  - Modern Dashboard shows the same metadata in latest-frame cards, 24h charts, decision statistics and quick summary panels.

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
- 2026-06-21: Validati su Raspberry target ADU persistente, resolver runtime corretto, `gain_max_*` profile-specific, ASI678MC moonmode fino a gain `300` e decisioni Auto Gain aggressive coerenti.
- 2026-06-21: Auto Exposure Refinement fase 1: audit controller, aggiunti `reason`/`blocker` e `[AUTO_EXPOSURE_BLOCKER]` diagnostico senza cambiare comportamento runtime.
- 2026-06-21: Implementata Metadata / Analytics Base con `FrameMetadata` e JSONL append-only per frame processed/error/not_saved.
- 2026-06-21: Implementato restore runtime Auto Gain dopo service restart tramite state file separato dalla config DB, con clamp e log restore/reset.
- 2026-06-21: Implementata rotazione giornaliera metadata JSONL in `frame_metadata/YYYY-MM-DD.jsonl`, mantenendo compatibilita' con `FRAME_METADATA_PATH`.
- 2026-06-21: Fix rotazione metadata Raspberry: path vuoto trattato come default daily, writer ritorna/logga il file effettivamente scritto.
- 2026-06-21: Implementato Metadata Analytics Reader base per daily JSONL con summary per camera, latest frames e conteggi decisioni.
- 2026-06-21: Rifattorizzata Auto Exposure convergence in tier `aggressive/normal/fine/target`, con recupero rapido da saturazione dentro il tier aggressive.
- 2026-06-21: Implementato Dashboard MVP read-only con latest frame per camera, grafici 24h exposure/gain/meter, statistiche decisioni e quick summary basati su `FrameMetadataAnalytics`.
- 2026-06-21: Dashboard Polish v1: summary riordinato sotto le camera cards, unita' piu' leggibili, reason label, axis labels e tooltip sui grafici.
- 2026-06-21: Migliorata leggibilita' asse X dashboard con tick temporali locali, subtitle `Last 24 hours` e timestamp completo nei tooltip.
- 2026-06-21: Implementato Quality Score v1 metadata-only con persistenza `quality_score`/`quality_flags` e visualizzazione read-only nel dashboard.
- 2026-06-21: Implementato Nightly Summary v1 read-only da daily JSONL con riepilogo per camera e percentuali operative.
- 2026-06-21: Completato Nightly Summary v1 locale con UI a card, missing frames, anomaly events, best/worst frame e night trend metadata-only.
- 2026-06-21: Rifinito layout Nightly Summary per evitare rendering tabellare/plain text: card scure responsive, metric tiles e cache-buster CSS dedicato.
- 2026-06-21: Implementato Metadata Health & Consolidation locale con report integrity/coverage e card dashboard read-only.
- 2026-06-21: Documentata fase Environmental Awareness: cloud detection, sky condition, condensation/dew, sky trend e weather awareness prima di Event Detection/AI.
- 2026-06-21: Implementata fondazione Sky Condition v1 metadata-only, profile-aware e multi-camera safe, senza cloud/dew/weather/AI/event detection.
- 2026-06-21: Implementata Cloud Detection v1 shadow metadata-only, integrata nel Nightly Summary analytics come `cloud_condition`, senza AI/event/runtime control.
- 2026-06-21: Implementata Sky Trend v1 shadow metadata-only, integrata nel Nightly Summary analytics come `sky_trend`, senza sostituire `night_trend`.
- 2026-06-21: Implementata Dew / Condensation Detection v1 shadow metadata-only come `possible_condensation`, senza usare sensori/heater control o image analysis.
- 2026-06-21: Esposti nel dashboard Modern Admin gli indicatori Environmental Awareness read-only (`sky_condition`, `cloud_condition`, `sky_trend`, `possible_condensation`) nella card `Sky Awareness`.
- 2026-06-21: Avviata Event Detection Foundation con `EventCandidate` v0 shadow-only, JSONL append-only e analytics minimi, senza classificazione eventi o integrazione capture.
- 2026-06-21: Aggiunta Event Timeline v0 shadow-only per raggruppare candidate `unclassified` vicine nel tempo senza AI, RMS, meteor detection o impatto runtime.
- 2026-06-21: Esposti nel Modern Admin dashboard gli analytics read-only di Event Candidates/Event Timelines esistenti, senza generazione automatica candidate o classificazione.
- 2026-06-21: Aggiunto smoke test manuale Event Foundation v0 con dati sintetici `synthetic-smoke-v0`, persistence JSONL candidate/timeline e cleanup sicuro.
- 2026-06-21: Aggiunte Candidate Trigger Rules v0 test-only metadata-based per candidate `unclassified`, senza hook runtime o classificazione eventi.
- 2026-06-21: Aggiunto Candidate Trigger Smoke Test v0 manual-only con metadata sintetici, persistence candidate/timeline, analytics dashboard e cleanup sicuro.
- 2026-06-22: Esposti in Web UI config i controlli shadow-only `EVENT_CANDIDATE_TRIGGERS.enabled` e `max_candidates_per_hour`; default resta disabilitato e la logica runtime trigger non e' stata modificata.
- 2026-06-22: Resa osservabile la Runtime Shadow Integration Event Candidate anche con zero candidate: `event_candidate_runtime.json` viene aggiornato con evaluation count e `last_status`, senza generare fake candidate o cambiare capture/runtime.
- 2026-06-22: Aggiunta Event Classification v1 foundation shadow-only: contratto JSONL, writer e classifier rule-based no-op che restituisce `unknown_event`, senza classificazione reale o impatto runtime.
- 2026-06-22: Aggiunta foundation Event Classification Rule Registry: contratti regola/risultato, registry ordinato e classifier shadow che resta no-op con registry vuoto.
- 2026-06-22: Aggiunta explainability foundation Event Classification: `rules_matched` strutturato con score/reason e `features_used` arricchito con summary quality/environment della timeline.
- 2026-06-22: Aggiunta `WeatherOrCloudEventRule` shadow-only e non registrata di default: prima regola classificazione conservativa basata solo su segnali ambientali forti.
- 2026-06-22: Aggiunto runner offline/manuale Event Classification: classifica Event Timeline JSONL in shadow mode e scrive Event Classification JSONL senza runtime hook.
- 2026-06-22: Raffinata `WeatherOrCloudEventRule`: `sky_condition_transition` e `partly_cloudy` da soli non generano piu' `weather_or_cloud_event`.
- 2026-06-22: Aggiunto report offline/read-only Event Pipeline per riassumere candidate, timeline e classification JSONL senza modificare dati o runtime.
- 2026-06-23: Stabilizzate mask processing multicamera per IMX708/ASI678MC: SQM, ADU e star detection ora usano cache shape-aware `(binning, image_width, image_height)` e fallback anti-crash quando una mask esterna non combacia con il frame.
- 2026-06-23: Ridotto rumore EventCandidate `sky_condition_transition` dopo report Raspberry con candidate/timeline eccessive durante `exposure_adjusting` e `meter_near_edge`; gli altri trigger restano invariati.
- 2026-06-23: Aggiunta analytics per candidate suppression: `suppressed_sky_condition_transition_total`, breakdown `exposure_adjusting` e `meter_near_edge` nel runtime diagnostics JSON e nell'offline event pipeline report.
- 2026-06-25: Fix affidabilita' Modern Admin dashboard: `FrameMetadataAnalytics` salta righe frame metadata JSONL vuote/malformate e continua a caricare le righe valide.
- 2026-06-25: Audit image/frame data per futura meteor detection: confermato join necessario `EventTimeline -> EventCandidate -> FrameMetadata -> image_file_path`; prossimo micro-step consigliato `TimelineFrameSet` offline read-only prima di qualsiasi detector.
- 2026-06-25: Raw-first / Scientific Source Image Architecture micro-step 1: esteso `FrameMetadata` con contratto opzionale display/source/detector/FITS/RAW/thumbnail/rendering senza cambiare processing o salvataggio immagini.
