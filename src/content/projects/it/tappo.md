---
title: "Tappo"
slug: "tappo"
lang: "it"
oneLiner: "App iOS per contare e seguire obiettivi, con serie giornaliere, heatmap, widget e Live Activities, su SwiftUI e SwiftData."
category: "iOS & SwiftUI"
year: "2026"
status: "Prototipo"
statusTone: "prototype"
featured: false
visible: true
order: 13
metrics:
  - value: "4 modelli"
    label: "tipi @Model SwiftData legati da cancellazione a cascata"
  - value: "12 badge"
    label: "sbloccati da conteggio, serie e ora del giorno"
stack: ["Swift", "SwiftUI", "SwiftData", "WidgetKit", "ActivityKit", "App Intents"]
repo: "https://github.com/Ed0C97/portfolio/tree/main/projects/tappo"
image: "/images/projects/tappo.svg"
---

## Il problema

Contare qualcosa nel tempo sembra il problema di tracciamento più banale che esista, ed è proprio per questo che di solito fallisce. Un numero secco dice a che punto sei, non come ci sei arrivato: senza la registrazione di ogni singolo passo non esistono totali giornalieri, non esiste una serie di giorni consecutivi, e non si vede se un'abitudine è viva o sta morendo in silenzio. Il secondo punto è l'attrito: se per aggiornare il conteggio bisogna sbloccare il telefono, aprire l'app e cercare il progetto giusto, dopo pochi giorni non lo si fa più; il numero deve stare dove passano già gli occhi, sulla schermata Home e su quella di blocco. C'è poi un requisito più silenzioso: abitudini e piccoli obiettivi personali sono faccende private, e un contatore non ha alcun bisogno di un account né di copiare quel registro sul server di qualcun altro.

## Cosa ho costruito

Tappo è un'app nativa per iOS in cui ogni progetto è un contatore con un obiettivo facoltativo, una scadenza facoltativa e la cronologia completa delle voci con data e ora. Ogni incremento e decremento viene registrato: da lì escono totali giornalieri, serie di giorni attiva, heatmap dell'attività e media di voci al giorno. Un progetto si può dividere in sotto-contatori indipendenti, dotare di traguardi verificati in automatico quando il conteggio li supera, e organizzare con ricerca, categorie, preferiti e archiviazione. Un sistema di 12 badge si sblocca in base a conteggio, serie, ora del giorno e numero di progetti. Gli stessi dati vivono anche fuori dall'app: un widget in Home mostra conteggio, serie, avanzamento e giorni rimanenti; le Live Activities portano il contatore sulla schermata di blocco e nella Dynamic Island; le App Intents espongono i progetti a Comandi Rapidi e ai widget interattivi. Ci sono promemoria giornalieri per progetto, l'esportazione in CSV, un riepilogo e una card immagine. L'interfaccia si adatta tra tab su iPhone e vista divisa su iPad, in italiano e in inglese. Tutto resta sul dispositivo: la sincronizzazione iCloud è disattivata di proposito.

![tappo detail placeholder 1](/images/projects/tappo-2.svg)

## Come funziona

L'app è un MVVM su SwiftUI e SwiftData. Quattro tipi @Model (Project, CounterEntry, Milestone, SubCounter) sono legati da relazioni con cancellazione a cascata; un unico view model @Observable e @MainActor tiene lo stato di selezione e filtro, esegue ogni mutazione sul model context e innesca poi gli effetti collaterali: feedback aptico, verifica dei traguardi, aggiornamento della Live Activity. La scelta meno ovvia riguarda dove sta il database. Lo store SwiftData è un file SQLite dentro un container App Group condiviso, con CloudKit impostato esplicitamente a none. Quella singola decisione fa due lavori insieme: i dati non lasciano mai il dispositivo, e l'estensione widget apre lo stesso identico store invece di parlare con l'app attraverso una copia serializzata. Il TimelineProvider del widget carica il progetto non archiviato aggiornato più di recente e si aggiorna circa ogni 30 minuti. L'esportazione della card passa da ImageRenderer; PDFKit è incluso per l'output in PDF. Il target di deployment è iOS 26.0.

## Per chi è

Tappo è un prototipo alla versione 1.0, un'app di un singolo sviluppatore in sviluppo attivo. Serve a chi vuole contare qualcosa verso un obiettivo con una vera cronologia dietro al numero, senza account e senza che i dati escano dal telefono. Ed è anche il progetto in cui ho attraversato di proposito la superficie di sistema di iOS moderno: SwiftData, WidgetKit, App Intents, ActivityKit e la localizzazione completa in inglese e italiano, 151 stringhe.

![tappo detail placeholder 2](/images/projects/tappo-3.svg)

## Limiti e cosa rifarei

Il rovescio della medaglia di disattivare iCloud è che non c'è né sincronizzazione né backup: i dati vivono su un solo dispositivo e con quello muoiono. E il widget mostra sempre il progetto aggiornato più di recente, che è il default giusto ma anche un tetto: lo rifarei configurabile, lasciando scegliere all'utente il progetto da fissare, cosa che le entità già esposte via App Intents rendono naturale.
