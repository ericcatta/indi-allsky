# Hybrid AllSky UX / Configuration Roadmap

Questo documento raccoglie il lavoro futuro su esperienza utente, configurazione,
dashboard, reporting e operativita'. La roadmap tecnica principale resta
`HYBRID_ROADMAP.md`; questo file serve a evitare che scelte UX, concetti utente
e chiarezza di configurazione vengano perse dentro i dettagli di runtime,
detector o infrastruttura scientifica.

## Scopo

- Rendere Hybrid AllSky comprensibile come sistema multicamera scientifico, non
  solo come raccolta di impostazioni legacy di indi-allsky.
- Esporre concetti utente stabili e leggibili invece di nomi interni grezzi.
- Separare chiaramente configurazione operativa, fallback legacy, diagnostica,
  rendering/display, archiviazione scientifica e futuri detector.
- Rendere chiaro cosa si configura per-camera/profile e cosa e' davvero globale.
- Mantenere UX e configurazione separate dall'implementazione dei detector.

## Principi

- Hybrid AllSky deve esporre concetti user-facing, non solo chiavi config interne.
- Profile-first e multi-camera devono essere evidenti in ogni pagina operativa.
- I Global Settings devono essere presentati come fallback legacy/advanced quando
  una camera/profile ha una configurazione specifica.
- Safe defaults devono essere ovvi; opzioni avanzate devono restare disponibili.
- Dashboard e report devono essere read-only finche' non esiste un motivo chiaro
  per renderli operativi.
- UX work non deve implementare detector, RMS, AI o logiche scientifiche nuove.
- Telegram/reporting deve consumare summary/domain objects, non dettagli interni
  dei detector.
- Help text, tooltip e descrizioni devono spiegare l'impatto operativo e i rischi
  delle impostazioni critiche.

## Concetti Utente Da Rendere Espliciti

### Immagini Scientifiche vs Rendering

- Scientific source image:
  - dato non distruttivo usato come archivio scientifico e futuro input detector;
  - preferenza FITS, poi RAW export, mai JPEG display con overlay.
- Detector input image:
  - sorgente scelta per detector futuri;
  - puo' coincidere con FITS/RAW, ma non deve essere un rendering con overlay.
- Display/review image:
  - immagine destinata a dashboard, gallery, pubblico e review visuale.
- Thumbnail:
  - asset piccolo per UI, non detector input.
- Rendered image with overlay:
  - immagine display con testo, watermark, cerchi, stretch, statistiche o
    annotazioni.

Overlay e stretch sono concetti di rendering/display. Non devono essere descritti
come trasformazioni distruttive del dato scientifico sorgente.

### Persistenza Sorgente Scientifica

La UI dovra' rendere comprensibile una policy ad alto livello:

- Never:
  - non salvare sorgenti scientifiche;
  - adatto a installazioni con storage minimo;
  - i futuri detector offline avranno solo metadata/display images.
- Periodic:
  - salvare FITS/RAW ogni N secondi/minuti;
  - utile per diagnostica e campionamento scientifico leggero.
- Every frame:
  - salvare sorgente scientifica per ogni frame;
  - adatto a detector e archiviazione, ma con impatto disco molto alto.
- Event-window buffered:
  - salvare finestre attorno a eventi sospetti;
  - deve considerare esplicitamente eventi a singolo frame come meteore e
    lightning: senza pre-event buffer, l'evento puo' essere gia' perso.

Queste modalita' sono concetti UX futuri. La UI potra' mapparle alle chiavi
interne `IMAGE_SAVE_FITS`, `IMAGE_SAVE_FITS_PERIOD`, `IMAGE_EXPORT_RAW` e
policy future senza esporre solo quei nomi.

## DONE

### Modern Admin e Configurazione

- Modern Admin e' diventato il centro operativo principale.
- Camera Profile Settings e' il punto operativo per gain, exposure, target ADU,
  AWB, processing e Auto Exposure.
- Global Capture Defaults / Full Settings sono stati de-enfatizzati come
  fallback legacy/advanced.
- Badge e messaggi distinguono:
  - Per-camera.
  - Global.
  - Legacy fallback.
  - Read-only.
- Modern Cameras page mostra profili multicamera e link Settings per profilo.
- Camera Profile Settings include Save & Sync controllato verso l'altra camera:
  - copia solo blocchi comuni ammessi;
  - preserva identity/hardware, driver, camera binding, lens, binning, AWB e CFA;
  - crea una nuova config row.
- CFA / Debayer Pattern e' modificabile per-camera e non sincronizzato.
- Gallery Modern supporta filtro camera/profile e mantiene il filtro con infinite
  scroll.
- Topbar Modern Admin include toggle Start/Stop Capture, Restart indi-allsky e
  badge stato servizio.

### Dashboard e Reporting Read-only

- Dashboard MVP read-only con latest frame, camera cards, chart 24h,
  decision statistics e quick summary.
- Dashboard Polish v1:
  - unita' exposure/gain/meter piu' leggibili;
  - reason label;
  - chart axis labels;
  - tooltip;
  - X-axis temporale leggibile.
- Nightly Summary v1:
  - layout a card responsive;
  - overview, quality, exposure, gain, meter, missing frames, anomaly events,
    best/worst frame, flags, reasons e trend.
- Metadata Health card:
  - completeness;
  - quality coverage;
  - invalid rows;
  - missing/invalid field counts.
- Sky Awareness read-only:
  - `sky_condition`;
  - `cloud_condition`;
  - `sky_trend`;
  - `possible_condensation`.
- Event Foundation dashboard read-only:
  - candidate/timeline counts;
  - reason/camera breakdown;
  - runtime trigger diagnostics.

## IN TEST

### Profile-first Usability

- Verificare sul Raspberry che Camera Profile Settings sia percepibile come unica
  UI operativa per camera.
- Verificare che Full Settings/Global Defaults siano comprensibili come legacy
  fallback/advanced, non come sorgente primaria.
- Validare che Save & Sync non induca l'utente a copiare parametri
  hardware-specifici tra ASI678MC e IMX708.
- Migliorare descrizioni per parametri critici:
  - gain day/night/moon;
  - exposure min/default/max;
  - Auto Exposure Enabled;
  - day bounded step;
  - Hybrid AWB apply mode;
  - CFA/bit depth;
  - gain max day/night/moonmode;
  - target ADU day/night/dev.

### Dashboard Multicamera

- Validare l'obiettivo di mostrare simultaneamente l'ultima immagine di entrambe
  le camere, non una sola.
- Ogni camera card deve mostrare:
  - nome camera chiaro;
  - timestamp;
  - age ultimo frame;
  - exposure/gain correnti;
  - quality/status;
  - link gallery filtrata.
- Se una camera non ha frame recente, deve apparire uno stato chiaro senza
  nascondere l'altra camera.

### Scientific Source Persistence UX

- Tradurre FITS/RAW in concetti utente:
  - source image;
  - detector input;
  - display image;
  - rendering.
- Documentare nella UI che `IMAGE_SAVE_FITS_PERIOD=0` significa every frame e
  puo' avere impatto storage molto alto.
- Rendere visibile se la camera/profilo sta producendo `fits_path`,
  `raw_path`, `source_image_path` e `detector_image_path` nei metadata.
- Validare un safe workflow per test breve:
  - periodic FITS a 30/60 secondi;
  - controllo spazio disco;
  - ritorno a periodicita' normale.

## NEXT

### Configurazione Scientific Source

- Disegnare una sezione UI dedicata, probabilmente in Camera Profile Settings >
  Storage / Scientific Source.
- Esporre policy di alto livello:
  - Never.
  - Periodic.
  - Every frame.
  - Event-window buffered.
- Mostrare stima impatto storage per camera:
  - FITS/RAW per frame;
  - per ora;
  - per notte;
  - per entrambe le camere.
- Mostrare warning specifico per `Every frame`.
- Spiegare che Event-window buffered richiede pre-event buffer per eventi a
  singolo frame come meteore e lightning.
- Non implementare buffer/event windows finche' la parte tecnica non e' pronta.

### Dashboard / Gallery

- Dashboard piu' professionale e meno admin-centric.
- Stato camere in una vista unica:
  - Running/Stopped;
  - ultimo frame per camera;
  - last image age;
  - current exposure/gain;
  - processing mode;
  - AWB backend;
  - scientific source status.
- Grafici:
  - brightness/meter;
  - exposure;
  - gain;
  - quality score;
  - storage/source persistence rate;
  - temperatura/health.
- Gallery multicamera:
  - filtri per camera;
  - filtri giorno/notte;
  - filtri qualita';
  - filtri reason/event diagnostics;
  - badge qualita' immagine;
  - confronto rapido ASI/IMX nello stesso intervallo temporale.
- Pagina pubblica esterna pulita:
  - senza controlli admin;
  - camera primaria;
  - camera secondaria opzionale;
  - metadati essenziali;
  - stato osservatorio leggibile.

### Review Workflow

- Definire UX review read-only prima di introdurre azioni operative:
  - timeline;
  - frame correlati;
  - candidate reasons;
  - quality/environment context;
  - scientific source availability;
  - display/review rendering.
- Preparare concetti per review futura:
  - accepted;
  - rejected;
  - needs more evidence;
  - ground truth;
  - benchmark.
- Tenere review UX separata da detector implementation.

### Telegram / Reporting

- Telegram deve consumare text/domain summaries, non raw detector internals.
- Fondazioni gia' disponibili da riusare:
  - nightly summary;
  - meteor intelligence text summary;
  - metadata health;
  - event pipeline report.
- Disegnare output:
  - daily/nightly operational summary;
  - meteor summary futuro;
  - storage/source persistence warning;
  - camera health warning.
- Nessun invio automatico finche' policy, rate limit e contenuto non sono chiari.

### Help / Tooltips / Documentation

- Aggiungere help text contestuale a:
  - Scientific source persistence.
  - FITS period.
  - RAW export.
  - Display vs source vs detector image.
  - Overlay/stretch.
  - Auto Exposure vs Auto Gain.
  - Target ADU.
  - CFA/debayer.
  - Profile-first vs global fallback.
- Aggiungere onboarding per:
  - single camera;
  - dual camera ASI678MC + IMX708;
  - storage-safe defaults;
  - debug/science mode.

## LATER

### Configuration Organization

- Riorganizzare settings in:
  - Basic.
  - Advanced.
  - Developer.
- Ridurre esposizione diretta di chiavi legacy quando esiste un concetto utente
  migliore.
- Aggiungere preset hardware:
  - ASI678MC daytime;
  - ASI678MC night;
  - IMX708 long exposure;
  - IMX708 daylight.
- Profilo `public-safe` con pubblicazione solo frame validi.
- Modalita' `science/debug day` che salva campioni source periodici per analisi.

### Operational Usability

- Pagina health operativa:
  - ultimo frame per camera;
  - eta' ultimo frame;
  - stato capture worker;
  - stato image worker;
  - spazio disco;
  - dimensione metadata/source images;
  - errori recenti.
- Storage manager:
  - retention metadata;
  - retention display images;
  - retention FITS/RAW;
  - stima crescita.
- Export/debug semplificato per una giornata o una notte.

### Future Public / Observatory Experience

- Public page con estetica pulita.
- Summary giornaliero comprensibile a non tecnici.
- Stati osservativi:
  - sky usable;
  - cloudy;
  - poor visibility;
  - possible condensation.
- Event/review presentation solo quando il framework tecnico e' maturo.

## IDEAS

- Setup wizard per nuova installazione Hybrid.
- Guided storage calculator.
- Visual diff tra profili camera.
- Config linter che segnala:
  - global setting che maschera profile setting;
  - FITS enabled ma profile runtime lo disabilita;
  - source persistence troppo costosa;
  - detector configurato senza source images.
- Natural-language explanation futura dei settings, alimentata da documentation
  locale e non da decisioni AI opache.
