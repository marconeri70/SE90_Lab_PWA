# SE90 Lab v7 — Motore Evolutivo

Questa versione mantiene `history.json` aggiornato automaticamente dall'archivio ufficiale SuperEnalotto.

## Come funziona
- L'app (`index.html`) prova a leggere `history.json` a ogni apertura.
- Se è online, usa il file più recente.
- Se non c'è rete, usa la cache locale.
- Se non esiste ancora una cache, usa lo storico incorporato nell'app.
- `scripts/update_history.py` legge gli archivi mensili ufficiali e conserva una finestra mobile di 183 giorni dall'ultima estrazione ufficiale disponibile.
- GitHub Actions esegue il controllo martedì, giovedì, venerdì e sabato dopo l'orario di estrazione.

## Pubblicazione su GitHub Pages
1. Crea un repository GitHub, per esempio `SE90-Lab`.
2. Carica TUTTO il contenuto di questa cartella, comprese `.github` e `scripts`.
3. In GitHub vai in **Settings > Pages**.
4. In **Build and deployment** scegli **Deploy from a branch**.
5. Seleziona il branch `main` e la cartella `/ (root)`.
6. Salva. Dopo la pubblicazione apri l'indirizzo Pages dal telefono.
7. Installa l'app dalla voce del browser “Installa app” / “Aggiungi a schermata Home”.

## Aggiornamento manuale
GitHub > Actions > “Aggiorna storico SuperEnalotto” > Run workflow.

## Nota tecnica
La pagina non fa scraping diretto dal browser: molti siti impediscono richieste cross-origin (CORS). L'aggiornamento avviene lato GitHub Actions e l'app legge un JSON sul proprio dominio, una soluzione più stabile e compatibile con PWA/offline.

## Importante
Lo storico serve a backtest e analisi descrittiva. Non rende più probabili i numeri già usciti o ritardatari.


## Facsimile stampabile
La v6.2 permette di:
- visualizzare l'anteprima delle combinazioni su una griglia 1–90;
- evidenziare i 6 numeri selezionati;
- scegliere 4, 6 o 8 facsimili per pagina A4;
- stampare tutte le combinazioni o solo le prime 5, 10 o 20;
- usare la funzione di stampa del browser per salvare in PDF.

Il facsimile è intenzionalmente non ufficiale e non contiene marchi o codici di convalida.


## Vincite storiche reali
L'aggiornamento automatico recupera anche le quote reali delle categorie 2, 3, 4, 5, 5+1 e 6 dal dettaglio ufficiale di ogni concorso.
Nel confronto storico l'app:
- determina tutte le sestine del sistema che avrebbero vinto;
- riconosce il 5+1 usando anche il Jolly;
- somma tutte le quote ipotetiche dello stesso concorso;
- mostra il dettaglio delle categorie vinte;
- calcola totale ipotetico del periodo e miglior concorso.

Le quote sono importi lordi/ufficiali visualizzati dall'archivio del concorso; eventuali aspetti fiscali o di riscossione non sono calcolati dall'app.


## Motore evolutivo v7
La v7 aggiunge:
- algoritmo genetico con popolazione, selezione a torneo, crossover e mutazioni;
- simulated annealing sui migliori sistemi;
- Monte Carlo adattivo: campione rapido per tutti i finalisti e campione profondo solo per i migliori;
- intervalli di confidenza Wilson al 95% per 2/3/4/5;
- benchmark fino a 1.000 sistemi casuali equivalenti;
- stabilità su finestre 6, 12 e 24 mesi;
- aggiornamento automatico dello storico fino a circa 24 mesi;
- confronto dell'efficienza marginale dei budget 5–30 €.

La ricerca resta euristica: non esiste un metodo che renda una specifica sestina più probabile in un'estrazione equa.
