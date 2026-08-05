---
title: "Porfirio Magazine"
slug: "porfirio-magazine"
lang: "it"
oneLiner: "Piattaforma editoriale bilingue in produzione, con donazioni Stripe, traduzioni via Gemini e caroselli Instagram automatici."
category: "Prodotto Full-Stack"
status: "In produzione"
statusTone: "production"
featured: true
visible: true
order: 5
metrics:
  - value: "30+"
    label: "blueprint Flask dietro un'unica API REST"
  - value: "~178"
    label: "componenti React su circa 27 pagine dell'app"
stack: ["React 18", "Flask 3", "PostgreSQL", "Redis", "Celery", "Stripe", "Google Gemini"]
repo: "https://github.com/Ed0C97/portfolio/tree/main/projects/porfirio-magazine"
image: "/images/projects/porfirio-magazine.svg"
---

## Il problema

Mandare avanti una piccola rivista online significa fare parecchi lavori che con la scrittura non c'entrano. Ogni articolo destinato sia al pubblico italiano che a quello inglese richiede una traduzione, che costa un traduttore esterno o un pomeriggio di redazione. Promuovere ogni pezzo su Instagram vuol dire disegnare a mano le immagini del carosello, una slide alla volta, a ogni uscita. E intorno ai contenuti serve tutto il resto: gli account dei lettori, i commenti da moderare, le donazioni, un minimo di visibilità su cosa fanno davvero i lettori. I CMS pronti coprono una parte di questi bisogni, ma mettere insieme un CMS, un servizio di traduzione, uno strumento di grafica per i social, un gestore di pagamenti e un prodotto di analytics lascia alla redazione cinque abbonamenti da gestire e i buchi tra l'uno e l'altro. Per una rivista con una squadra piccola questi costi non sono astratti: fanno la differenza tra pubblicare ogni settimana e pubblicare quando avanza tempo.

## Cosa ho costruito

Porfirio Magazine è la piattaforma dietro una rivista vera, online su magazine.porfirioholding.com. È una single-page application React che parla con una API REST in Flask e un database PostgreSQL, il tutto in produzione su Render. La redazione scrive, programma e categorizza gli articoli in un editor rich-text; i lettori sfogliano in italiano o in inglese, commentano, salvano i preferiti e donano tramite Stripe. Due incombenze redazionali sono automatizzate. Gli articoli vengono tradotti tra italiano e inglese su richiesta da Google Gemini, e ogni traduzione resta in cache: il modello viene richiamato solo se l'articolo cambia davvero. Il carosello Instagram di un articolo lo genera il backend: Gemini scrive i testi delle slide entro limiti di caratteri per tipo di slide, le slide vengono impaginate come schede HTML, catturate come immagini e consegnate in uno ZIP pronto da pubblicare. Attorno ci sono gli account con accesso Google e verifica dell'email via OTP, i permessi per ruolo con una coda di moderazione, un pannello di analytics e un involucro Capacitor che impacchetta lo stesso frontend come app iOS.

## Come funziona

Il backend è un'applicazione Flask montata da una factory, con più di 30 blueprint di rotte su circa 22 modelli SQLAlchemy; il frontend conta circa 178 componenti React su circa 27 pagine, tutte caricate in modo differito tranne la home per spezzare il bundle. La scelta meno ovvia è l'autenticazione: una richiesta può portare un cookie di sessione Flask-Login oppure un token JWT, risolti entrambi da un unico request_loader personalizzato, così la stessa API serve la SPA web e i client a token senza duplicare gli endpoint. La cache delle traduzioni è indicizzata su un hash SHA-256 del contenuto dell'articolo, e l'invalidazione diventa automatica: modifichi l'articolo, cambia l'hash. Le slide per Instagram sono screenshot di HTML impaginato, presi con Playwright headless invece di disegnare le immagini via codice, poi caricati su Cloudinary. I worker Celery su broker Redis gestiscono le email; Redis regge anche rate limiting e caching. Il manifesto render.yaml descrive tre servizi più il PostgreSQL gestito, con un cron settimanale che ripulisce i log.

## Risultati

La rivista è in produzione: pubblicata su Render con domini personalizzati e PostgreSQL gestito, e mantenuta attivamente. Le donazioni passano da Stripe, con un endpoint webhook lato server e feature flag per attivarle o disattivarle a seconda dell'ambiente. L'engagement viene misurato: le metriche per articolo e le statistiche sulle generazioni Instagram sono registrate, tracciate nel pannello con Recharts ed esportabili in CSV.

## Limiti e cosa rifarei

La traduzione avviene su richiesta, quindi il primo lettore che apre un articolo nell'altra lingua aspetta la chiamata a Gemini; tradurre al momento della pubblicazione sposterebbe quel costo fuori dal percorso del lettore. E il frontend porta quattro librerie di mappe e globi (Google Maps, Mapbox GL, Leaflet, react-globe.gl), cresciute un'integrazione alla volta: le consoliderei in una sola, perché ognuna aggiunge peso al bundle che il lettore scarica.
