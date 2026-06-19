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

## 6. Log operativo

- 2026-06-19: Consolidata roadmap Hybrid AllSky come documento operativo principale.
- 2026-06-19: Stabilizzato runtime multicamera con gain/exposure/profile resolver per IMX708 e ASI678MC.
- 2026-06-19: Introdotto metering per-camera selezionabile in shadow mode.
- 2026-06-19: Introdotto Auto Exposure Controller con decisioni shadow, smoothing e deadband trend-aware.
- 2026-06-19: Aggiunto toggle per-camera `AUTO_EXPOSURE_ENABLED`, default OFF, per applicazione runtime controllata.
