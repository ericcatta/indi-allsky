# Hybrid AllSky Roadmap

## Stato attuale
- Raspberry/IMX708: immagine giorno buona.
- ZWO ASI678MC: immagine giorno troppo chiara, white balance errato.
- Auto exposure: funziona, ma ci sono possibili conflitti con valori default/profile/runtime.
- Valore sospetto: esposizione che riparte spesso da 8s.

## Priorità 1 - Stabilizzare acquisizione
- [ ] Capire da dove arriva CCD_EXPOSURE_DEF=8.
- [ ] Separare chiaramente parametri giorno/notte per ogni camera.
- [ ] Verificare che ogni camera mantenga il proprio stato exposure/gain.
- [ ] Ridurre conflitti tra config globale, camera, profilo e runtime.
- [ ] Sistemare ASI678MC: exposure giorno, gain giorno, white balance.

## Priorità 2 - Audit configurazione
- [ ] Esportare config completa corrente.
- [ ] Classificare impostazioni: Basic / Advanced / Developer.
- [ ] Identificare valori inutili, ridondanti o pericolosi.
- [ ] Ripristinare default sensati senza cancellare opzioni.
- [ ] Nascondere opzioni avanzate nella UI.

## Priorità 3 - UI/UX
- [ ] Aggiungere descrizioni/didascalie ai parametri.
- [ ] Rendere chiaro quale parametro è globale e quale è per-camera.
- [ ] Migliorare pagina multicamera/gallery.
- [ ] Preparare layout web più professionale.

## Bug notes
- [ ] ASI678MC sovraesposta di giorno.
- [ ] ASI678MC white balance sbagliato.
- [ ] Possibile reset periodico a exposure 8s.
- [ ] Log mostra cicli multipli Image-1-xxxxx dopo restart.
