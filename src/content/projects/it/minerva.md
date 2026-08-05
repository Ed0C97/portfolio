---
title: "MINERVA"
slug: "minerva"
lang: "it"
oneLiner: "Motore OSINT multi-sorgente: correla dati pubblici sulle minacce in un grafo Neo4j e risponde a domande in linguaggio naturale."
category: "OSINT & Knowledge graph"
status: "Beta"
statusTone: "beta"
featured: false
visible: true
order: 9
metrics:
  - value: "5 sorgenti"
    label: "Collector asincroni: Shodan, OTX, CVE/NVD, DNS, WHOIS"
  - value: "20 profili"
    label: "Profili APT curati per un'attribuzione basata su evidenze"
stack: ["Python", "FastAPI", "LangGraph", "Cohere", "Neo4j", "PostgreSQL", "Docker"]
repo: "https://github.com/Ed0C97/portfolio/tree/main/projects/minerva"
image: "/images/projects/minerva.svg"
---

## Il problema

Le informazioni pubbliche sulle minacce informatiche abbondano, ma allo stato grezzo sono quasi inutilizzabili. Shodan sa quali host espongono quali porte, AlienVault OTX pubblica indicatori di compromissione, il database NVD cataloga le vulnerabilità, i record DNS e WHOIS descrivono l'infrastruttura. Ogni sorgente ha la sua API, i suoi limiti di richiesta, i suoi identificatori, e ignora l'esistenza delle altre. Lo stesso indirizzo IP compare in tre feed come tre record scollegati. Un analista che indaga un incidente salta da una scheda del browser all'altra, elimina i doppioni a mano, e la vera intelligence, cioè i legami tra un attore, le sue tecniche e la sua infrastruttura, resta nella sua testa o in un foglio di calcolo. I database a grafo saprebbero conservare quei legami, ma interrogarli richiede un linguaggio di query che pochi analisti hanno il tempo di imparare. E una pipeline costruita su feed pubblici deve sopravvivere ai feed stessi: le chiavi scadono, le API cadono, e un collector che si blocca trasforma una sorgente mancante in zero risultati.

## Cosa ho costruito

MINERVA automatizza da capo a fondo quel ciclo di raccolta e correlazione. Interroga cinque sorgenti pubbliche (Shodan, OTX, CVE/NVD, DNS, WHOIS), riconosce quando sorgenti diverse stanno descrivendo lo stesso artefatto reale e fonde tutto in un unico grafo di conoscenza: indirizzi IP, domini, organizzazioni, vulnerabilità, tecniche, attori e campagne. Sopra il grafo c'è un'interfaccia in linguaggio naturale: l'analista fa una domanda e riceve una risposta in prosa, ancorata al grafo e non alla fantasia di un modello. I risultati escono dal sistema come bundle STIX 2.1, il formato standard di scambio per la threat intelligence, oppure come report PDF, Markdown e JSON. Il tutto è pensato API-first: gira in autonomia con Docker ed espone una API REST con autenticazione e controllo degli accessi per ruolo, così un'altra piattaforma può usarlo come servizio di threat intelligence invece che come ennesimo strumento da presidiare.

## Come funziona

Cinque collector asincroni interrogano le API delle sorgenti, ciascuno con il proprio rate limiting e progettato per degradare senza rompersi: se manca una chiave o una sorgente è giù, l'esecuzione produce comunque un grafo con quello che resta. Una pipeline LangGraph orchestra raccolta, correlazione e arricchimento, poi scrive in Neo4j nodi e relazioni tipizzate (ATTRIBUTED_TO, USES_TTP, EXPLOITS_CVE). Le tecniche vengono validate contro MITRE ATT&CK con un punteggio di confidenza, e un motore di attribuzione confronta un'entità con 20 profili APT documentati, restituendo per ogni candidato le evidenze, non solo un nome. Le domande in linguaggio naturale diventano query sul grafo tramite un modello di ragionamento Cohere ancorato allo schema. La scelta meno ovvia sta qui: il motore di query è in sola lettura per costruzione, con un passo di validazione prima dell'esecuzione, perché lasciare che un modello linguistico scriva query arbitrarie su un archivio di intelligence è il modo migliore per corromperlo. La raccolta gira come job asincroni (202 Accepted, avanzamento via SSE), con JWT, RBAC e audit log in sola aggiunta.

## Per chi è

MINERVA si rivolge agli analisti di cyber threat intelligence e, tramite la API REST, alle piattaforme in cui lavorano: è fatto per essere integrato come servizio, non adottato come ennesima dashboard. Il progetto è in beta alla versione 1.0.0, completo nelle funzionalità, con un deployment Docker Compose, ma resta un progetto personale.

## Limiti e cosa rifarei

L'attribuzione è larga quanto il suo insieme di profili: con 20 profili APT curati, un attore fuori da quell'insieme non può essere nominato, e nessun punteggio di confidenza rimedia a un buco di copertura. Se lo rifacessi partirei dal lato analista: il valore del sistema è il grafo, e merita un'interfaccia che permetta di percorrerlo, non solo di interrogarlo tramite API.
