---
title: "Progetti d'esame di ML e grafica"
slug: "academic-coursework"
lang: "it"
oneLiner: "Progetti d'esame alla Sapienza: benchmark di sei classificatori, CNN alla guida in simulazione e sei progetti di grafica da zero in WebGL."
category: "Progetti universitari ML & Grafica"
status: "Progetti d'esame completati"
statusTone: "spec"
featured: false
visible: true
order: 14
metrics:
  - value: "6 modelli"
    label: "benchmark di classificatori, dalla logistica a XGBoost"
  - value: "0 librerie"
    label: "sei progetti di grafica in JavaScript e GLSL puri"
stack: ["Python", "scikit-learn", "XGBoost", "TensorFlow/Keras", "Gymnasium", "JavaScript", "WebGL/GLSL"]
repo: "https://github.com/Ed0C97/portfolio/tree/main/projects/academic-coursework"
image: "/images/projects/academic-coursework.svg"
---

## Il problema

Sia nel machine learning sia nella grafica, gli strumenti sono ormai così comodi da nascondere la disciplina. Poche righe di scikit-learn restituiscono un classificatore addestrato; un motore di rendering, una scena illuminata e testurizzata. Quello che gli strumenti non dicono è ciò che sta sotto: quale modello valga davvero il suo costo di calcolo su quei dati, se un'accuratezza misurata offline racconti qualcosa del comportamento dentro un sistema in esecuzione, e cosa succeda davvero tra un triangolo e un pixel. Per un ingegnere sono le domande che contano: scelta del modello, disegno della valutazione e lavoro su GPU si riducono a queste. Il modo onesto di rispondere è lavorare sotto le astrazioni: confrontare i modelli con una metodologia fissa tenendo il conto dei costi, valutare un controllore nel loop che deve chiudere, e scrivere da zero il codice di rendering e di simulazione, senza librerie su cui appoggiarsi.

## Cosa ho costruito

Due gruppi di progetti d'esame universitari (Sapienza), per i corsi di Machine Learning e di Interactive Graphics. Per il machine learning, due lavori. Il primo è un benchmark di sei classificatori (regressione logistica, albero decisionale, Random Forest, SVM, KNN, XGBoost) su due dataset sintetici a 10 classi, uno da 100 e uno da 1000 feature, eseguito con e senza cross-validation a 5 fold, ottimizzato con GridSearchCV e profilato per tempo e risorse di sistema accanto all'accuratezza. Il secondo addestra due architetture CNN in Keras su fotogrammi di gioco etichettati 96x96 per guidare un'auto nell'ambiente Gymnasium CarRacing-v2. Per la grafica, sei progetti autonomi che girano nel browser, adattati dagli assignment CS4600 dell'Università dello Utah: alpha compositing su buffer di pixel grezzi, trasformazioni 2D a matrici, rendering di mesh testurizzate in WebGL, shading Blinn-Phong per frammento, un ray tracer su GPU scritto in un fragment shader GLSL e una simulazione fisica massa-molla. Ogni progetto di grafica gira interamente lato client, senza dipendenze e senza build: si apre il file HTML e funziona.

![academic-coursework detail placeholder 1](/images/projects/academic-coursework-2.svg)

## Come funziona

Il benchmark registra per ogni modello le metriche di qualità e l'uso di risorse via psutil, così la selezione pesa l'accuratezza contro il costo. Il lavoro sulle CNN esplora in grid search batch size, learning rate ed epoche, salvando ogni modello come file .h5 col nome dei suoi iperparametri; la valutazione è doppia: matrici di confusione su un test set tenuto da parte, e una corsa in anello chiuso in cui il modello salvato mappa ogni fotogramma 96x96 in un'azione discreta e viene giudicato dalla ricompensa totale dell'episodio. È la scelta non ovvia: l'accuratezza offline non dice cosa fa un controllore quando i suoi errori tornano indietro nei suoi ingressi. Sul lato grafica: matrici di trasformazione 3x3 in ordine column-major, un MeshDrawer WebGL con parsing OBJ e matrici MVP, intersezione raggio-sfera con ombre nette e riflessioni ricorsive tenute sotto un tetto di rimbalzi con fallback su cube map, e integrazione di Eulero semi-implicita con forze elastiche di Hooke e collisioni con restituzione contro un cubo unitario.

## Risultati

Tutti i progetti sono completi e funzionanti. Il benchmark si chiude con una scelta che tiene conto dei costi: SVM sul dataset da 100 feature, Random Forest su quello da 1000. Le CNN sono valutate sia con le metriche offline sia con la ricompensa d'episodio in simulazione, e ogni lavoro di ML consegna codice, relazione scritta e artefatti dei risultati. I sei progetti di grafica girano così come sono in un browser moderno.

![academic-coursework detail placeholder 2](/images/projects/academic-coursework-3.svg)

## Limiti e cosa rifarei

Sono progetti d'esame congelati alla consegna: il repository ML non ha un manifest delle dipendenze, e dataset e modelli addestrati non sono versionati, quindi gli script girano solo dopo aver fornito gli asset a mano. Il controllore di CarRacing, poi, è pura classificazione supervisionata fotogramma per fotogramma, senza contesto temporale. Rifacendolo, renderei tutto riproducibile da un checkout pulito e userei la ricompensa in anello chiuso, non l'accuratezza offline, come criterio primario di selezione fin dall'inizio.
