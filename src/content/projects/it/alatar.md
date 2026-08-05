---
title: "Alatar"
slug: "alatar"
lang: "it"
oneLiner: "Piattaforma di career intelligence che confronta CV e annuncio e restituisce un punteggio verificabile, con citazioni nei due documenti."
category: "Career Intelligence & LLM"
status: "Prototipo"
statusTone: "prototype"
featured: true
visible: true
order: 6
metrics:
  - value: "3 livelli"
    label: "Motore di match: deterministico, LLM in batch, punteggio"
  - value: "~25 motori"
    label: "Dalla riscrittura del CV alla simulazione del selezionatore"
stack: ["Python 3.12", "FastAPI", "LangGraph", "LiteLLM", "PostgreSQL + pgvector", "Next.js 16", "TypeScript"]
repo: "https://github.com/Ed0C97/portfolio/tree/main/projects/alatar"
image: "/images/projects/alatar.svg"
---

## Il problema

Quando è un software a filtrare una candidatura, il risultato è quasi sempre un numero senza spiegazione. Il candidato viene scartato senza sapere su quale requisito è caduto; il selezionatore riceve una classifica che non saprebbe difendere se qualcuno gli chiedesse come è stata calcolata. Nessuno dei due può verificare la decisione. Il rimedio apparente, far confrontare CV e annuncio a un modello linguistico, porta problemi suoi: ogni confronto costa una chiamata, lo stesso input può dare punteggi diversi in giorni diversi, e il ragionamento resta chiuso dentro il modello. In più, l'AI Act europeo colloca i sistemi di intelligenza artificiale usati nelle decisioni di assunzione nella categoria ad alto rischio (Allegato III): la tracciabilità smette di essere una cortesia e diventa un obbligo. Uno strumento di selezione che non sa mostrare le proprie prove non è soltanto frustrante per chi lo subisce: in Europa è avviato a essere non conforme.

## Cosa ho costruito

Alatar prende un CV e un annuncio di lavoro e restituisce un confronto che entrambe le parti possono ispezionare. Analizza i due documenti, ne estrae il profilo del candidato e i requisiti del ruolo, e produce un punteggio complessivo di compatibilità, la scomposizione per categoria, l'elenco delle lacune e l'analisi della sovrapposizione con le parole chiave che un sistema di tracciamento delle candidature (ATS) andrebbe a cercare. Ogni requisito arriva con un verdetto (pass, review o redflag) e un elemento di evidenza che cita i passaggi esatti di entrambi i documenti: il punteggio si può controllare, non solo credere sulla parola. La piattaforma serve due pubblici in un unico sistema: chi adatta il proprio CV a un ruolo preciso e chi seleziona e ha bisogno di uno screening spiegabile. La conformità sta dentro la pipeline, non aggiunta dopo: la catena di evidenze è mappata sugli obblighi dell'AI Act per l'ambito occupazionale, e accanto ci sono gli endpoint GDPR di cancellazione, esportazione e rettifica, più un modulo di valutazione d'impatto (DPIA).

![alatar detail placeholder 1](/images/projects/alatar-2.svg)

## Come funziona

Il motore di match ha tre livelli, ordinati per costo. Un livello deterministico normalizza le competenze, risolve gli alias e fa matching approssimato di tutto ciò che può, senza toccare l'LLM. Ciò che resta ambiguo passa a un'unica chiamata LLM in batch, che classifica ogni requisito in una di sei fasce, dalla corrispondenza esatta all'assenza. Un livello di punteggio calcola infine l'aggregato pesato per categoria, con moltiplicatori di fascia e sovrapposizione delle parole chiave ATS. La scelta meno ovvia è proprio quest'ordine: prima il deterministico, poi l'LLM, una sola chiamata in batch, così il costo per confronto resta limitato invece di crescere col numero dei requisiti. Attorno al motore c'è un monorepo: backend FastAPI con circa 25 motori di dominio (riscrittura del CV, simulazione del selezionatore nei panni di HR, tecnico e hiring manager, adattatori ATS, ontologie di competenze), client Next.js 16 alimentato via server-sent events, isolamento multi-tenant con la Row-Level Security di PostgreSQL, sette toolkit gemelli con versioni CalVer allineate, e un eval-gate in CI con test avversari di red team.

## Per chi è

Niente è ancora stato misurato su utenti reali, quindi niente numeri di prestazioni. Alatar è pensato per chi si candida e vuole sapere, requisito per requisito, dove il proprio CV regge e dove no, e per chi seleziona e deve poter difendere ogni verdetto con citazioni in entrambi i documenti.

![alatar detail placeholder 2](/images/projects/alatar-3.svg)

## Limiti e cosa rifarei

È un prototipo: diversi comandi della CLI e alcuni punti di ingresso dei motori sono dichiarati ma rimandati a fasi successive, quindi non tutto ciò che si vede nel codice è già percorribile. Se ricominciassi, restringerei la prima versione: venticinque motori di dominio sono tanta superficie per una persona sola, e preferirei avere pipeline di match, catena di evidenze e moduli di conformità pienamente operativi prima di allargare il catalogo.
