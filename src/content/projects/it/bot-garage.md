---
title: "BOT Garage"
slug: "bot-garage"
lang: "it"
oneLiner: "App local-first per la manutenzione dei veicoli, con OCR interamente on-device di libretti e fatture: nessun documento esce dal computer."
category: "Local-first & AI on-device"
status: "App personale attiva"
statusTone: "beta"
featured: true
visible: true
order: 7
metrics:
  - value: "~6 GB"
    label: "modello visione-linguaggio OCR eseguito on-device (MPS)"
  - value: "3 report"
    label: "PDF distinti per proprietario, meccanico e acquirente"
stack: ["Python", "FastAPI", "SQLite", "dots.mocr", "PyTorch", "Ollama", "Electron"]
repo: "https://github.com/Ed0C97/portfolio/tree/main/projects/bot-garage"
image: "/images/projects/bot-garage.svg"
---

## Il problema

Tutto ciò che riguarda un veicolo vive su carta. La storia della manutenzione sta in un cassetto di fatture d'officina, le scadenze di assicurazione, bollo e revisione stanno nella memoria di qualcuno, e il libretto di circolazione porta targa, numero di telaio e i dati personali del proprietario. Tenere tutto in un foglio di calcolo significa ricopiarlo a mano, ed è abbastanza noioso da far mollare quasi tutti dopo un mese. La scorciatoia ovvia, un'app in cloud con OCR, ha un costo che si tende a non vedere: caricare sui server di qualcun altro documenti che identificano te e il tuo veicolo. E c'è un secondo problema, più silenzioso, nell'OCR stesso: un modello che legge una fattura sbiadita tira a indovinare volentieri, e un numero di telaio indovinato è peggio di un campo vuoto, perché ha l'aspetto di un dato. Per una storia di manutenzione che finirà nel dossier di un acquirente o sul banco di un meccanico, indovinare in silenzio non è accettabile.

## Cosa ho costruito

BOT Garage è un'applicazione web che gira interamente sulla mia macchina. Un unico database locale contiene, per ogni veicolo, il piano di manutenzione, i tagliandi che raggruppano i lavori completati, un magazzino di ricambi e consumabili con soglie di riordino, le scadenze amministrative e il registro delle spese. Un veicolo nuovo si aggiunge importando il PDF del libretto: l'OCR estrae targa, telaio, marca, modello, anno di immatricolazione, classe di emissioni e cilindrata, ognuno con un punteggio di confidenza. Una fattura d'officina si importa allo stesso modo, intestazione e righe, e diventa interventi completati raggruppati in un tagliando. Da quello stesso database l'app genera un file Excel multi-foglio con formule attive, documenti ODS e ODT, esportazioni JSON e CSV e tre report PDF pensati per lettori diversi: il proprietario, il meccanico e un potenziale acquirente, il cui dossier omette i dati personali. Un assistente locale di nome Walter, su Ollama, agisce sul database tramite tool calling, e le notifiche WhatsApp per scadenze e riordini passano da un gateway self-hosted con deduplicazione per evento.

![bot-garage detail placeholder 1](/images/projects/bot-garage-2.svg)

## Come funziona

Un backend FastAPI espone una API JSON e serve un frontend statico in HTML, CSS e JavaScript; il livello dati è uno schema relazionale con chiavi esterne, organizzato per veicolo, con un registro eventi in sola aggiunta. Lo storage è SQLite di default e passa a un Postgres remoto (Neon) con una variabile d'ambiente; con una chiave impostata, i campi sensibili (libretto, telaio, targa, proprietario) vengono cifrati con Fernet prima di lasciare il processo. L'OCR usa l'ocr-toolkit incluso nel repository e il modello visione-linguaggio dots.mocr, circa 6 GB, eseguito su Apple Silicon tramite Metal Performance Shaders, con una patch che rende flash_attn opzionale e ripiega sulla scaled dot-product attention. La scelta non ovvia è la regola di onestà del dato: la trascrizione del modello è effimera, si salvano solo campi strutturati, e ogni campo letto con confidenza bassa resta vuoto o segnalato e richiede conferma manuale prima del salvataggio. Niente entra nel registro senza che una persona decida che è vero. Una shell Electron opzionale incapsula l'app per l'uso desktop.

## Per chi è

È scritta per un utente solo: io. È un'applicazione personale funzionante, in sviluppo attivo e orientata alla configurazione di un singolo proprietario, con dati iniziali costruiti intorno a una moto precisa, una Triumph Bonneville T120. Lo schema è però organizzato per veicolo e ne regge più d'uno, quindi cresce con il garage. L'applicazione è proprietaria; l'ocr-toolkit incluso è distribuito con licenza MIT.

![bot-garage detail placeholder 2](/images/projects/bot-garage-3.svg)

## Limiti e cosa rifarei

Il percorso OCR richiede Apple Silicon, perché dots.mocr gira su MPS: su altro hardware la funzione di importazione semplicemente non esiste. Percorsi di default e dati iniziali sono ancora scritti nel codice per la mia configurazione, ed è il prezzo reale di costruire prima per un solo utente. Rifacendola, generalizzerei quella configurazione fin dall'inizio e salterei l'interfaccia desktop in Tkinter che oggi resta nel repository, deprecata, come ripiego.
