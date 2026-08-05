---
title: "Sentinel"
slug: "sentinel"
lang: "it"
oneLiner: "Piattaforma multi-tenant che estrae, valuta e attesta il rischio in documenti legali e finanziari con una pipeline multi-agente verificata."
category: "Document AI & Multi-agente"
status: "Beta"
statusTone: "beta"
featured: true
visible: true
order: 2
metrics:
  - value: "2 app"
    label: "API di analisi più un piano di controllo multi-tenant"
  - value: "1,6-2x"
    label: "Sovraccosto di latenza per il serving deterministico"
stack: ["Python", "FastAPI", "LangGraph", "DSPy", "LiteLLM", "PostgreSQL", "Terraform"]
repo: "https://github.com/Ed0C97/portfolio/tree/main/projects/sentinel"
image: "/images/projects/sentinel.svg"
---

## Il problema

Report di due diligence, contratti, comfort letter e term sheet muovono soldi veri, e qualcuno deve leggerli. Nei team bancari e di credit intelligence quella lettura è lenta, costosa e difficile da difendere a posteriori: il revisore segnala un rischio, ma il legame tra la segnalazione e la frase che la giustifica resta nella sua testa. Il riassunto generico con un LLM peggiora le cose invece di migliorarle: il modello produce rilievi scorrevoli, ma niente li ancora al testo di partenza, lo stesso documento può dare rilievi diversi a ogni esecuzione, e chi chiede "dove esattamente lo dice il documento?" resta senza risposta. Perché l'analisi documentale automatica sia usabile in quel contesto devono valere tre proprietà insieme: ogni rilievo deve essere riconducibile a un'evidenza nel documento, l'analisi deve essere riproducibile, e il risultato deve essere attestabile, cioè dimostrabile a posteriori che una certa analisi ha prodotto un certo esito.

## Cosa ho costruito

Sentinel è una piattaforma multi-tenant che analizza documenti legali e finanziari in italiano e inglese e restituisce rilievi strutturati con punteggi di rischio calibrati. Il documento attraversa una pipeline di agenti specializzati: alcuni estraggono clausole e rischi, altri verificano il lavoro dei primi. Gli agenti di verifica intervengono dopo l'estrazione: controllano che ogni rilievo sia ancorato al testo di partenza, ne ricalibrano la gravità e filtrano la copertura prima che qualcosa venga accettato; i risultati non ancorati vengono scartati. Ogni analisi termina con due artefatti: un report esportato in PDF, DOCX, PPTX o XLSX, e un Analysis Attestation Token firmato e cifrato, che si può recuperare, verificare e scaricare in seguito come prova di cosa è stato analizzato e con quale esito. Intorno al nucleo di analisi c'è un prodotto completo: autenticazione enterprise (SAML, OIDC, passkey, MFA), fatturazione con Stripe, interfaccia web, app desktop Electron e SDK Python.

## Come funziona

Il monorepo contiene due applicazioni FastAPI: l'API di analisi e un piano di controllo separato per il provisioning, che gestisce ciclo di vita dei tenant, quote, migrazioni e amministrazione. Gli agenti sono privi di stato, con tutto lo stato mutabile in un AgentContext, quindi le esecuzioni procedono in parallelo sotto un semaforo configurabile; i moduli di analisi vengono compilati offline e caricati a runtime. Il recupero è ibrido: ricerca full-text, indice vettoriale e knowledge graph. Gli agenti di verifica girano dopo l'estrazione: controllano l'ancoraggio alle fonti, ricalibrano la gravità e presidiano la copertura prima che qualcosa venga accettato. La scelta meno ovvia è il serving deterministico su kernel batch-invariant per l'inferenza locale: senza batch invariance il risultato dipende da quali altri tenant capitano nello stesso batch, e l'unica alternativa per conservare la riproducibilità sarebbe stata servire le richieste una alla volta. Ho accettato un sovraccosto di latenza misurato di 1,6-2x per richiesta pur di mantenere il batching tra tenant e restare deterministico.

## Per chi è

Team bancari e di credit intelligence che hanno bisogno di un'analisi documentale difendibile: rilievi legati all'evidenza nel testo, lo stesso insieme di rilievi a ogni esecuzione sullo stesso documento, e un'attestazione crittografica per ogni analisi. Sentinel è in beta, con licenza proprietaria, in sviluppo attivo.

## Limiti e cosa rifarei

La garanzia di riproducibilità ha un prezzo pagato su ogni singola richiesta: il sovraccosto di latenza di 1,6-2x del serving batch-invariant. E ho costruito quattro superfici di distribuzione (web, desktop, SDK, landing page) intorno a un nucleo ancora in beta: rifacendolo, pubblicherei prima l'API e l'SDK e lascerei il resto per quando il cuore dell'analisi avesse smesso di muoversi.
