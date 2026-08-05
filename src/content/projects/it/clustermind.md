---
title: "ClusterMind"
slug: "clustermind"
lang: "it"
oneLiner: "CLI deterministica che trasforma la descrizione di un servizio in un piano di capacità verificabile e nel TCO cloud, formula per formula."
category: "Capacity planning & CLI"
status: "Beta"
statusTone: "beta"
featured: false
visible: true
order: 10
metrics:
  - value: "Ogni numero"
    label: "riconducibile alla sua formula stampata nel report"
  - value: "5 fasi"
    label: "pipeline riprendibile su un unico file di configurazione"
stack: ["Python 3.11-3.13", "Typer", "Rich", "PyYAML", "psutil", "reportlab", "Quarto"]
repo: "https://github.com/Ed0C97/portfolio/tree/main/projects/clustermind"
image: "/images/projects/clustermind.svg"
---

## Il problema

"Quanti server servono, e quanto costerà all'anno?" è una domanda a cui ogni team risponde prima del lancio, e quasi sempre la risposta arriva da un foglio di calcolo, dall'istinto o, ultimamente, da una chiacchierata con un modello linguistico. Tutte e tre le strade falliscono lo stesso esame: la revisione del budget. Il foglio di calcolo nasconde le proprie ipotesi; l'istinto non va oltre i sistemi che hai già gestito; il modello linguistico produce un numero plausibile che nessuno può ricavare di nuovo, e domani ne produce un altro. Eppure le domande di fondo non hanno niente di vago. Quanti server servono a un livello per rispettare un obiettivo di latenza è teoria delle code; quanti token al secondo può generare una GPU è aritmetica sulla banda di memoria; quanto è incerto il costo annuale dipende da quali dati conosci davvero. Quello che manca non è la matematica, ma uno strumento che la applichi, mostri i passaggi riga per riga e si rifiuti di indovinare dove un modello lo farebbe.

## Cosa ho costruito

ClusterMind è uno strumento a riga di comando che trasforma una breve descrizione di un servizio web, SaaS o di inferenza LLM self-hosted (traffico, endpoint, obiettivi di latenza, crescita, vincoli di conformità) in un piano di capacità e in un costo totale di gestione. Propone il numero di istanze per livello, tipi di istanza concreti su AWS, GCP o Azure, cifre di storage e banda, politiche di autoscaling e un'economia unitaria che arriva al costo per richiesta e per milione di token. Tutto gira su un unico file di configurazione versionato in Git, quindi il lavoro si può interrompere e riprendere in qualunque fase: un questionario in linguaggio comune raccoglie i dati, una scansione statica del codice individua rotte e concorrenza nei progetti FastAPI, Flask e Django, una fase facoltativa di benchmark genera e interpreta test di carico per k6, wrk, locust e vegeta, poi il calcolo dimensiona i livelli e il report esce in Markdown, HTML, JSON, PDF o Quarto. C'è anche un livello facoltativo con un LLM locale, ma riformula le domande e racconta i risultati: non produce mai un numero.

![clustermind detail placeholder 1](/images/projects/clustermind-2.svg)

## Come funziona

La matematica vive in uno strato puro, senza orologi, casualità né I/O: lo stesso file di ingresso produce sempre un output identico al byte, e ogni valore calcolato viene registrato come FormulaRecord (nome, espressione, dati di ingresso, risultato, unità) stampato nel report, così chiunque può rifare i conti a mano. Il dimensionamento usa un modello di code M/M/c (Erlang-C) guidato da un obiettivo di latenza; le configurazioni instabili restituiscono infinito, e lo strato di dimensionamento aggiunge server invece di fallire. Per l'inferenza LLM self-hosted c'è un roofline di primo ordine: memoria dei pesi, decodifica limitata dalla banda di memoria, batch limitato dalla KV-cache, con un solo fattore di efficienza (0,35 di default) che un benchmark tara. Una passata Monte Carlo a seme fisso propaga l'incertezza degli input in bande P10/P50/P90/P95, ordina i fattori di costo con un'analisi tornado e assegna alla stima un voto da A a D in base alla larghezza della banda P10-P90. La scelta non ovvia è il determinismo come invariante: la verificabilità che lo strumento promette non sopravviverebbe a una dipendenza stocastica nella pipeline.

## Per chi è

Per gli SRE, i team di piattaforma e chiunque debba difendere una decisione di dimensionamento davanti a chi approva il budget. Lo stato è una beta dichiarata: un progetto che porto avanti da solo, con licenza MIT, una suite pytest di circa 20 moduli di test e CI su Python 3.11, 3.12 e 3.13.

![clustermind detail placeholder 2](/images/projects/clustermind-3.svg)

## Limiti e cosa rifarei

I prezzi vengono da un listino fotografato a una certa data, quindi il TCO di un piano invecchia con quella fotografia, e il roofline resta una stima di primo ordine finché un benchmark non ne tara il fattore di efficienza. Rifacendolo, ridurrei i formati di report (oggi sono cinque: Markdown, HTML, JSON, PDF, Quarto) e userei quel tempo per tenere aggiornati i dati di prezzo: la freschezza delle cifre di costo è la prima cosa che un lettore controlla.
