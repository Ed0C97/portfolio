---
title: "Anacleto"
slug: "anacleto-instagram"
lang: "it"
oneLiner: "Modelli di visione valutano la griglia Instagram, MCTS ne cerca l'ordine, uno scheduler pubblica tramite la Meta Graph API ufficiale."
category: "Visione & Ottimizzazione"
status: "Beta"
statusTone: "beta"
featured: false
visible: true
order: 12
metrics:
  - value: "3 motori"
    label: "ottimizzatori intercambiabili: Greedy, Beam Search, MCTS"
  - value: "6 criteri"
    label: "punteggio estetico pesato per ogni griglia candidata"
stack: ["Python", "FastAPI", "PyTorch", "YOLO", "Gemini", "PostgreSQL", "APScheduler"]
repo: "https://github.com/Ed0C97/portfolio/tree/main/projects/anacleto-instagram"
image: "/images/projects/anacleto-instagram.svg"
---

## Il problema

Un profilo Instagram, per un account business o creator, viene giudicato come griglia prima ancora che qualcuno apra un singolo post. Le ultime nove immagini convivono fianco a fianco, e il loro ordine decide se il profilo appare curato o casuale. Sistemare quell'ordine a mano è un lavoro noioso: si trascinano miniature in un'app di pianificazione, si valutano colori e composizione a occhio, e si ricomincia a ogni nuovo lotto di foto. Ed è un problema combinatorio vero: nove immagini si possono disporre in 362.880 ordini diversi, molti di più di quanti se ne riescano a confrontare a occhio. Gli strumenti di programmazione automatizzano la pubblicazione ma non l'ordinamento: pubblicano la sequenza che gli viene consegnata, agli orari impostati. E in molti casi chiedono le credenziali dell'account e le conservano sui propri server: esattamente il tipo di segreto permanente che si dovrebbe esitare a cedere.

## Cosa ho costruito

Anacleto è una piattaforma che prende un lotto di immagini e gestisce la filiera dall'analisi alla pubblicazione. Modelli di visione estraggono da ogni immagine colori, texture, oggetti riconosciuti e segnali estetici. Un motore di ricerca individua l'ordinamento con il punteggio più alto come griglia, un generatore scrive didascalie e hashtag a partire dai risultati dell'analisi, e i post ordinati finiscono in coda. Uno scheduler li pubblica ai rispettivi orari attraverso la Meta Graph API ufficiale. Il tutto è esposto come servizio FastAPI con account registrati, verifica via email e chiavi API; c'è anche un client desktop, scritto con Dear PyGui e impacchettato per macOS e Windows, per chi preferisce i pulsanti agli endpoint. Una scelta attraversa l'intero sistema: il server non conserva mai i segreti Instagram, Cloudinary o Gemini dell'utente. Le credenziali viaggiano negli header delle richieste e vengono usate in modo stateless, quindi lato server non esiste alcun deposito di segreti da proteggere.

## Come funziona

Cooperano tre componenti: uno strato API in FastAPI, un motore di analisi e uno scheduler autonomo. L'orchestratore del motore collega estrattori di feature (che coordinano chiamate a Vertex AI, Replicate e Gemini), ottimizzatori e valutatori, tutti configurati tramite dataclass caricate da variabili d'ambiente: algoritmi e modelli si cambiano senza toccare il codice. Il punto interessante è la sede dell'ottimizzatore: tre strategie intercambiabili, Greedy, Beam Search e Monte Carlo Tree Search, cercano l'ordine di una griglia 3x3 di nove immagini, e la variante MCTS usa selezione UCB, pre-filtro dei candidati e rollout greedy. A far funzionare la ricerca è il valutatore: le griglie candidate vengono renderizzate e valutate su sei criteri pesati (armonia cromatica, composizione, flusso visivo, equilibrio, coerenza tematica, interesse), il che trasforma un giudizio soggettivo in una funzione di ricompensa condivisa dai tre ottimizzatori. Lo scheduler legge la coda con APScheduler e pubblica su fasce orarie per giorno della settimana, tre post al giorno di default sul fuso Europe/Rome, con una modalità dry-run; la pubblicazione passa dalla Graph API v21.0 con logica di retry e copre immagini, video, caroselli, storie e reel.

## Per chi è

Anacleto automatizza la filiera dei contenuti per gli account Instagram Business e Creator. Serve a chi vuole curare la griglia e programmare le uscite senza consegnare credenziali permanenti a un server di terzi, dato che i segreti restano legati alla singola richiesta. Lato servizio ci sono registrazione con verifica OTP via email (Resend), chiavi API con scadenza opzionale e rate limiting per IP; il client desktop copre gestione dell'account, credenziali, stato del servizio e statistiche.

## Limiti e cosa rifarei

Il punteggio estetico è un insieme di criteri con pesi scelti a mano: "ordine migliore" significa migliore secondo quei pesi, non secondo un engagement misurato; nel motore esistono funzioni di apprendimento dal feedback, ma sono disattivate di default. Se lo rifacessi, sposterei il rate limiting per IP dalla memoria del processo a uno store condiviso: uno stato in memoria smette di limitare qualcosa nel momento in cui gira una seconda istanza.
