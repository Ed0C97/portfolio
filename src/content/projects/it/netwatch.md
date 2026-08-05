---
title: "NETWATCH"
slug: "netwatch"
lang: "it"
oneLiner: "Monitor di sicurezza per endpoint Linux: cattura eBPF nel kernel, regole più ML, correlazione degli incidenti, avvisi in formato SIEM."
category: "Sicurezza & eBPF"
status: "Beta"
statusTone: "beta"
featured: true
visible: true
order: 8
metrics:
  - value: "4 programmi"
    label: "cattura eBPF: syscall, rete, filesystem, processi"
  - value: "25 regole"
    label: "rilevazioni deterministiche mappate su MITRE ATT&CK"
stack: ["Python", "C (eBPF)", "FastAPI", "PyTorch", "scikit-learn", "TimescaleDB", "React 18"]
repo: "https://github.com/Ed0C97/portfolio/tree/main/projects/netwatch"
image: "/images/projects/netwatch.svg"
---

## Il problema

Quando un attaccante mette piede su una macchina Linux, tutto quello che fa da quel momento lascia tracce al confine del kernel: processi che nascono, chiamate di sistema, connessioni di rete, file letti e scritti. La maggior parte degli strumenti di monitoraggio osserva questa attività dallo spazio utente, un passo più in là, interrogando /proc o leggendo i log. Quella distanza pesa due volte. Primo: un malware che gira in spazio utente può interferire con un osservatore in spazio utente molto più facilmente che con il kernel stesso, quindi la telemetria di cui un analista si fida di più è proprio quella che questi strumenti non producono. Secondo: l'attività del kernel è un fiume in piena, un solo host genera più eventi di quanti una persona possa leggerne, e l'evento isolato non dice niente senza il contesto. Servono tre cose insieme: la cattura dentro il kernel, un modo per trasformare gli eventi in rilevazioni, e un modo per condensarle in pochi incidenti su cui agire, consegnati dove i team di sicurezza lavorano già, cioè nel SIEM.

## Cosa ho costruito

NETWATCH è un monitor di sicurezza per endpoint Linux che osserva l'attività da dentro il kernel. Piccoli programmi in C, caricati tramite eBPF, si agganciano ai tracepoint del kernel e registrano cosa fa ogni processo: le chiamate di sistema, le connessioni che apre, i file che tocca, i figli che genera. Il flusso di eventi alimenta un motore di rilevazione che applica prima regole deterministiche, ognuna mappata su una tecnica MITRE ATT&CK con severità, confidenza e risposta consigliata, e solo dopo consulta i modelli di machine learning. Le rilevazioni collegate vengono raggruppate in incidenti invece di essere sollevate una per una. Gli avvisi partono in parallelo su Syslog, webhook, file e WebSocket, nei formati CEF e LEEF che piattaforme SIEM come Splunk, ArcSight e IBM QRadar leggono direttamente. Una dashboard React mostra in tempo reale eventi, incidenti e alberi dei processi, e tutto il sistema si distribuisce con Docker Compose.

## Come funziona

Quattro programmi eBPF coprono syscall, rete, filesystem e processi; spingono gli eventi verso lo spazio utente attraverso ring buffer, e ogni 60 secondi vengono estratte 24 feature per processo per il livello di rilevazione. Il set di regole conta 25 rilevazioni distribuite sulle fasi della Cyber Kill Chain. La parte ML le affianca con un Isolation Forest che apprende una baseline comportamentale e una LSTM che cerca i pattern di beaconing verso server di comando e controllo. La scelta non ovvia è l'ordine: le regole deterministiche girano sempre per prime e il percorso ML è una riserva, perché una regola che scatta è spiegabile e riproducibile mentre un punteggio di anomalia non lo è; senza modelli caricati il sistema funziona comunque in modalità solo regole. A valle, un correlatore raggruppa le rilevazioni per prossimità temporale, discendenza dei processi e progressione lungo la kill chain; i canali di avviso sono isolati, con retry, backoff e soppressione dei duplicati; gli eventi persistono su PostgreSQL con hypertable TimescaleDB tramite SQLAlchemy asincrono e migrazioni Alembic, insieme a feed di indicatori di compromissione inclusi.

## Per chi è

Non c'è ancora un benchmark di rilevazione misurato, quindi questa sezione resta onesta: NETWATCH è un progetto personale in beta, completo nelle funzioni su cattura, rilevazione, ML, avvisi, API, dashboard, migrazioni e distribuzione Docker/Compose, ma non una release di produzione pubblicata. Si rivolge a ingegneri e analisti di sicurezza che vogliono rilevazione host-based su macchine Linux che controllano, e a team che hanno già un SIEM e vogliono telemetria a livello kernel nei formati che i loro strumenti leggono nativamente.

## Limiti e cosa rifarei

Richiede un kernel recente (5.15 o successivo) e privilegi BPF elevati, quindi non si installa su un host qualunque. Soprattutto, la qualità della rilevazione è ancora un'affermazione e non un numero: nessun tasso di falsi positivi è stato misurato su carichi reali di lunga durata. Se ricominciassi, costruirei prima l'impianto di valutazione e solo dopo allargherei il set di regole: 25 regole non misurate valgono meno di 10 misurate.
