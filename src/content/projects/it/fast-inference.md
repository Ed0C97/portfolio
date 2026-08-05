---
title: "fast-inference"
slug: "fast-inference"
lang: "it"
oneLiner: "Server di inferenza self-hosted compatibile OpenAI, con quantizzazione INT8, kernel Triton e batching dinamico asincrono."
category: "Inferenza & Prestazioni"
year: "2026"
status: "Prototipo"
statusTone: "prototype"
featured: true
visible: true
order: 4
metrics:
  - value: "10,25 ms"
    label: "p50 contro 19,58 ms FP32, stesso provider CoreML, Apple M3 Pro, bge-small"
  - value: "-47,9%"
    label: "grafo INT8 vs sorgente FP32, da 127,4 a 66,4 MB"
stack: ["Python", "Triton", "ONNX Runtime", "PyTorch", "FastAPI", "httpx", "Docker"]
repo: "https://github.com/Ed0C97/portfolio/tree/main/projects/fast-inference"
image: "/images/projects/fast-inference.svg"
---

## Il problema

Una pipeline di retrieval-augmented generation fa tre tipi di chiamate a modelli: calcola gli embedding di documenti e query, riordina i candidati, genera la risposta. La strada comoda è mandare tutto a una API cloud, ma ogni richiesta paga un giro di rete e ogni documento esce dalla macchina. Con dati riservati, o con budget di latenza nell'ordine delle decine di millisecondi, è uno scambio che non conviene.

Portare i modelli in locale sembra la soluzione, ma un server ingenuo è lento a modo suo. Servire una richiesta alla volta lascia l'acceleratore fermo tra una chiamata e l'altra, i pesi a precisione piena sprecano banda di memoria, e a batch piccoli l'inferenza dei transformer è limitata dalla memoria, non dal calcolo: il chip passa il tempo a spostare pesi. Perché il serving locale regga il confronto bisogna lavorare su tutto lo stack insieme: modelli quantizzati, esecuzione a batch, uso attento della memoria e un instradamento che sopravviva alla caduta di un worker. Questo progetto costruisce quello stack da cima a fondo, in un unico codice.

## Cosa ho costruito

fast-inference è un server di inferenza self-hosted per modelli di embedding, reranking e generazione di testo. Espone una sola API HTTP che replica gli schemi di richiesta e risposta di OpenAI e Cohere: un client già scritto per quei servizi può puntare al server senza modifiche, con embedding, chat completion in streaming, reranking e gli endpoint di stato e metriche.

Lo stesso codice gira su GPU NVIDIA, su Apple Silicon e su CPU: un livello di runtime risolve dispositivo e profilo del modello in un punto solo, e all'avvio il server sceglie il backend migliore tra quelli disponibili. Intorno ai modelli c'è quello che serve a un sistema di serving: un batcher asincrono che raggruppa le richieste in arrivo, una pipeline di quantizzazione INT8, un router che distribuisce il carico tra i worker, un orchestratore di benchmark che misura ogni backend eseguibile e registra i risultati insieme all'hardware, e una dashboard operativa, servita alla radice del server, con la coda di batching visualizzata in tempo reale.

![fast-inference detail placeholder 1](/images/projects/fast-inference-2.svg)

## Come funziona

Le richieste entrano in un batcher dinamico che spedisce un batch al raggiungimento di 32 richieste o dopo 10 ms di attesa; ogni richiesta ha il suo future asyncio e un errore viene propagato a tutti i chiamanti in attesa. Sul percorso torch, buffer pre-allocati e suddivisi per lunghezza vengono riciclati tra le richieste, con uscite verificate identiche bit per bit con e senza pool. La quantizzazione è INT8 statica via ONNX Runtime, calibrata su dati rappresentativi, con gli operatori sensibili alla precisione (LayerNorm, Softmax, GELU, gather degli embedding) lasciati di proposito in float. Il livello distribuito assegna a ogni worker un punteggio basato su latenza e profondità della coda (pesi 0,7 e 0,3), dietro un circuit breaker a tre stati con controlli di stato ogni due secondi.

La scelta meno ovvia è il router: il round-robin funziona male perché il tempo di una richiesta cresce con la lunghezza della sequenza, quindi due worker con lo stesso numero di richieste possono portare carichi molto diversi. Il punteggio su latenza osservata e coda manda il lavoro dove finirà prima.

## Risultati

Misurato su un Apple M3 Pro con bge-small-en-v1.5, batch 1, 10 iterazioni cronometrate dopo il warmup: il passaggio da FP32 a INT8 sullo stesso provider CoreML ha portato la latenza p50 da 19,58 a 10,25 ms. Il grafo INT8 è più piccolo del 47,9% rispetto al sorgente FP32 (da 127,4 a 66,4 MB), con 41 operatori su 549 lasciati in float per proteggere la precisione. Sono numeri da laptop su un modello di embedding piccolo, non da datacenter: l'orchestratore salva ogni esecuzione in JSON e Markdown con l'hardware indicato, così ogni cifra porta con sé il proprio contesto.

![fast-inference detail placeholder 2](/images/projects/fast-inference-3.svg)

## Limiti e cosa rifarei

I kernel Triton scritti a mano vivono in un livello di ottimizzazione separato, con i propri benchmark: il percorso di serving non li importa, quindi le latenze qui sopra vengono da ONNX Runtime, non dai miei kernel. Il reranking passa dalla coda ma non viene raggruppato in batch sulla GPU. Ripartendo, costruirei per prima cosa la struttura di benchmark: la documentazione iniziale citava obiettivi di riferimento come se fossero risultati, e li ho poi ritirati in favore di misure registrate con l'hardware dichiarato.
