---
title: "ARBOR"
slug: "arbor"
lang: "it"
oneLiner: "Piattaforma AI multi-tenant che scopre, arricchisce e ragiona su entità del mondo reale con knowledge graph e ricerca vettoriale."
category: "Sistemi distribuiti & Ricerca AI"
status: "In sviluppo"
statusTone: "beta"
featured: true
visible: true
order: 3
metrics:
  - value: "4 archivi"
    label: "PostgreSQL, Neo4j, Qdrant e Redis dietro un'unica API"
  - value: "5 stadi"
    label: "Pipeline di arricchimento Temporal con retry per attività"
stack: ["Python 3.12", "FastAPI", "PostgreSQL", "Neo4j", "Qdrant", "Temporal.io", "Kubernetes"]
repo: "https://github.com/Ed0C97/portfolio/tree/main/projects/arbor"
image: "/images/projects/arbor.svg"
---

## Il problema

Le informazioni sulle entità del mondo reale (un locale, un marchio, un prodotto) sono sparse tra schede di mappe, profili social e siti web, e invecchiano in fretta. Un prodotto che vuole consigliare "un'enoteca tranquilla con vini naturali vicino alla stazione" ha bisogno di più di una riga in tabella: servono gli attributi dell'entità, le sue relazioni con altre entità, una rappresentazione semantica del posto e una traccia di dove arriva ogni affermazione. Le scorciatoie abituali si rompono tutte da qualche parte. La ricerca per parole chiave su un database relazionale non risponde alle domande semantiche. Un indice vettoriale da solo perde relazioni e struttura. Gli script di arricchimento improvvisati sovrascrivono i dati di ieri con quelli di oggi: quando una pipeline AI scrive una cosa sbagliata non c'è storia a cui tornare né traccia da ispezionare. E se il sistema serve più clienti, ognuno con il proprio catalogo, i dati devono restare rigorosamente separati.

## Cosa ho costruito

ARBOR (Advanced Reasoning By Ontological Rules) è una piattaforma multi-tenant che raccoglie entità da fonti esterne, le arricchisce con una pipeline AI a più stadi e le espone alla ricerca semantica e all'interrogazione conversazionale. Gli scraper raccolgono materiale grezzo da Google Maps, Instagram e pagine web generiche; una pipeline di arricchimento lo analizza, gli assegna punteggi e lo valida; il risultato finisce in un grafo di conoscenza, in un indice vettoriale e in un registro event-sourced. Sopra c'è un flusso di ricerca agentico: la domanda viene classificata, instradata in parallelo verso la ricerca vettoriale e quella sui metadati, e assemblata in risposta da un passo curatore. La piattaforma è un monorepo con backend FastAPI, client web React, client mobile Expo e uno strato infrastrutturale su Kubernetes. Il comportamento di dominio (categorie di entità, dimensioni di punteggio, prompt, ontologie) sta nella configurazione YAML, non nel codice: un nuovo verticale si aggiunge modificando file di configurazione. I dati di ogni tenant vivono in uno schema di database dedicato.

## Come funziona

La scelta meno ovvia è il modello di persistenza: la fonte di verità è un event store PostgreSQL append-only con concorrenza ottimistica, snapshot e proiezioni di lettura, e un outbox transazionale pubblica gli eventi di dominio su Kafka. Ho scelto l'event sourcing perché l'arricchimento riscrive le entità di continuo: con la storia completa degli eventi, una scrittura sbagliata generata dall'AI si può rintracciare e rigiocare, invece di sostituire in silenzio dati buoni. La ricerca gira su una macchina a stati LangGraph (router di intento, agenti vettoriale e sui metadati in parallelo, storico, curatore) compilata una volta all'avvio, con un checkpointer PostgreSQL che permette di riprendere una sessione dove si era fermata. L'arricchimento è un workflow Temporal in cinque stadi (raccolta, analisi, punteggio, validazione, persistenza) con retry e timeout per singola attività. Il recupero combina ricerca ibrida densa più sparsa con reranking BGE su Qdrant, e GraphRAG e HippoRAG sul grafo Neo4j. Quattro archivi si dividono il lavoro: PostgreSQL con PostGIS, Neo4j, Qdrant e Redis. Le decisioni di progetto sono registrate come ADR.

## Per chi è

Per chi costruisce prodotti di scoperta contestuale e raccomandazione su dati di entità curati: app di scoperta locale, directory di marchi e locali, ricerca verticale. È un progetto privato attivo, non in produzione: il backend riporta la versione 1.1.0 e il codice, oltre 4 MB di Python, è coperto da suite di test unitari, di integrazione, end-to-end, di chaos, di carico (k6) e di red team (promptfoo).

## Limiti e cosa rifarei

Il limite onesto è l'ampiezza: copertura e maturità variano da modulo a modulo, e il backend dipende da toolkit privati, quindi non si può eseguire senza accesso a quei repository. Se ricominciassi, porterei un solo verticale fino in fondo prima di costruirci intorno un client web, uno mobile e un intero strato GitOps. Il nucleo dell'architettura (event store, grafo di agenti, workflow di arricchimento) è la parte che terrei così com'è.
