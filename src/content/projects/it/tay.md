---
title: "Tay"
slug: "tay"
lang: "it"
oneLiner: "App nativa in Swift 6 che riconosce opere d'arte e monumenti sul dispositivo e vi ancora esperienze AR in tempo reale."
category: "AR & ML on-device"
status: "Sviluppo iniziale"
statusTone: "prototype"
featured: false
visible: true
order: 11
metrics:
  - value: "3 modalità"
    label: "Canvas indossabile, AR temporale e guida culturale"
  - value: "5 OS"
    label: "iOS, iPadOS, visionOS, watchOS e macOS"
stack: ["Swift 6", "SwiftUI", "ARKit", "RealityKit", "Core ML", "SwiftData", "Tuist 4"]
repo: "https://github.com/Ed0C97/portfolio/tree/main/projects/tay"
image: "/images/projects/tay.svg"
---

## Il problema

Un quadro su una parete di museo, un tempio in rovina, un'opera stampata su una giacca: nessuno di questi oggetti sa raccontarsi da solo. Le audioguide seguono percorsi fissi e tappe numerate, e tacciono su ciò che hai davvero davanti. Le app che riconoscono le opere in cloud richiedono una connessione che nei sotterranei dei musei e nei siti archeologici spesso manca, e aggiungono un viaggio di andata e ritorno tra l'inquadratura e la risposta. La realtà aumentata ha un limite tutto suo: i framework AR ancorano i contenuti a geometrie rigide, quindi un'esperienza appoggiata a una tela stampata si rompe nel momento in cui quella tela viene indossata, perché il tessuto si piega e si deforma. E per gli oggetti che portano opere d'arte su licenza non esiste un modo per legare un'esperienza digitale all'esemplare autentico invece che a una qualunque copia dell'immagine.

## Cosa ho costruito

Tay è un'app nativa in Swift 6 per iPhone, iPad, Apple Vision Pro, Apple Watch e macOS. Si inquadra un'opera o un monumento con la fotocamera; l'app la identifica direttamente sul dispositivo, senza mandare fotogrammi a un server, e avvia un'esperienza di realtà aumentata ancorata a ciò che si sta guardando. Le modalità sono tre. La modalità canvas indossabile autentica le opere stampate su licenza e fa comparire un personaggio AR che vive sulla tela e reagisce all'ambiente intorno. La modalità temporale sovrappone la ricostruzione storica di un sito, con un cursore per scorrere tra passato e presente restando sul posto. La guida culturale universale riconosce monumenti e opere e offre una narrazione generata dall'AI, con una conversazione vocale in tempo reale per le domande. Intorno alla fotocamera c'è il resto dell'app: persistenza SwiftData con mirroring CloudKit, widget, Live Activities, App Intents, App Clip, un'app per Apple Watch, una superficie visionOS e una dashboard per macOS.

## Come funziona

Il riconoscimento gira su ogni fotogramma attraverso una pipeline: un filtro di stabilità del movimento decide quando un fotogramma merita la classificazione, i risultati finiscono in cache, un modello Core ML classifica tramite Vision sull'Apple Neural Engine, e un passaggio consapevole della posizione conferma la corrispondenza. Le ricostruzioni 3D fotorealistiche sono renderizzate con Gaussian Splatting. La scelta meno ovvia è il tracciamento delle superfici non rigide: l'ancoraggio AR standard presuppone geometrie rigide, quindi per tenere i personaggi attaccati a una tela indossata l'app segue la deformazione del tessuto con una mesh deformata su GPU. I personaggi reagiscono a luce ambientale, audio, movimento, parlato e gesti attraverso listener che alimentano una macchina a stati; la voce è un loop duplex su WebSocket. I modelli ML arrivano inclusi nell'app e si aggiornano tramite un manifest over-the-air firmato e verificato nell'integrità, con ripiego sui modelli inclusi. Il codice è un workspace generato con Tuist, a moduli stratificati (TayCore, TayUI, TayML, TayAR, moduli feature), compilato con la strict concurrency completa di Swift 6 e i warning trattati come errori.

## Per chi è

Musei e siti archeologici che vogliono una guida ancorata a ciò che il visitatore sta guardando, turismo culturale, e moda o merchandising che porta opere stampate su licenza. Lo stato è dichiarato senza abbellimenti: sviluppo iniziale, un solo autore. La pipeline vocale e l'infrastruttura sono reali; diversi modelli di riconoscimento sono ancora segnaposto. Il repository compila in una pipeline GitHub Actions con test unitari, snapshot e flussi end-to-end Maestro.

## Limiti e cosa rifarei

Il limite principale è lo scarto tra il guscio e il nucleo: le superfici di piattaforma esistono (telefono, watch, Mac, Vision Pro, App Clip, widget), ma diversi modelli di riconoscimento da cui dipendono sono segnaposto, e l'app poggia su repository fratelli non pubblici, quindi un clone pulito non gira da capo a fondo. Ripartendo, porterei una sola modalità, la guida culturale su iPhone, fino a un modello vero e a utenti veri, prima di costruirle intorno le superfici per watch, Mac e Vision Pro.
