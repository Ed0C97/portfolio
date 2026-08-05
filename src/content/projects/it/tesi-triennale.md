---
title: "Controllo ibrido RL-MPC per la guida autonoma"
slug: "tesi-triennale"
lang: "it"
oneLiner: "Tesi triennale e digital twin in Python: uno stack di controllo RL-MPC a livelli per una vettura driverless con aderenza incerta."
category: "Controlli & RL"
year: "2026"
status: "Prototipo di ricerca"
statusTone: "prototype"
featured: true
visible: true
order: 1
metrics:
  - value: "3 livelli"
    label: "policy RL, filtro di sicurezza CBF, supervisore MPC-LPV"
  - value: "100 Hz"
    label: "frequenza di stima, policy e filtro di sicurezza"
stack: ["Python", "Stable-Baselines3", "Gymnasium", "PyTorch", "OSQP", "ROS 2", "MATLAB/Simulink"]
repo: "https://github.com/Ed0C97/portfolio/tree/main/projects/tesi-triennale"
image: "/images/projects/tesi-triennale.svg"
---

## Il problema

Una vettura da corsa senza pilota lavora al limite dell'aderenza, e l'aderenza è proprio ciò che non può conoscere con certezza. L'attrito cambia con l'asfalto, la temperatura e l'usura delle gomme; la rigidezza di deriva si sposta con il carico. Un controllore classico basato su modello porta garanzie formali, ma si fida di parametri che dopo pochi minuti di sessione sono già sbagliati. Una policy di reinforcement learning si adatta a ciò che incontra, ma una rete neurale da sola non garantisce nulla la volta in cui conta. Le squadre di Formula Student Driverless vivono dentro questo compromesso: tarare il controllo con prudenza e perdere tempo sul giro, oppure spingere e accettare che una stima sbagliata dell'attrito chiuda la prova contro le barriere. La domanda della tesi è se i due approcci debbano escludersi, o se una policy appresa possa correre dentro un recinto imposto dalla teoria del controllo.

## Cosa ho costruito

La mia tesi triennale in Ingegneria Elettronica alla Sapienza di Roma, insieme a digital_twin_pkg, un framework di simulazione in Python che implementa e verifica l'architettura descritta nel testo. Il sistema non è un controllore unico ma una pila di livelli specializzati. Un livello di stima misura online le grandezze che nessun sensore legge direttamente: velocità laterale, velocità di imbardata, attrito e rigidezza di deriva. Una policy appresa trasforma lo stato del veicolo in comandi di sterzo e accelerazione. Un filtro di sicurezza corregge ogni comando prima che arrivi al veicolo, e un supervisore basato su modello osserva un indice di sicurezza e prende il controllo quando la situazione peggiora. Ogni livello gira come nodo ROS 2; un bridge li alimenta con una simulazione interna oppure con NVIDIA Isaac Sim, e una dashboard PyQt5 mostra il loop in tempo reale. Accanto al codice Python, script MATLAB verificano la matematica della tesi in modo indipendente dall'implementazione.

## Come funziona

La stima è un Unscented Kalman Filter selettivo con stato aumentato [vy, r, mu, Cf0]: aggiorna attrito e rigidezza solo quando la curva li eccita e la stima supera un controllo di coerenza. La policy è PPO (Stable-Baselines3) su un ambiente Gymnasium su misura, osservazione a 7 dimensioni, azione normalizzata a 2, con un addestramento registrato di 500k passi in domain randomization a curriculum dal 5% al 100%. Il filtro di sicurezza è un QP a Control Barrier Function risolto con OSQP, con tre barriere: bordo pista, cerchio di attrito (Kamm) e un vincolo di ordine superiore sull'angolo di assetto (HOCBF, grado relativo 2). Il supervisore è un MPC su modello LPV schedulato su velocità e attrito, orizzonte N=20, costo terminale dalla DARE. Stima, policy e CBF girano a 100 Hz; il supervisore arbitra a 10 Hz tramite un indice di sicurezza con isteresi. La scelta non ovvia è tenere separati controllo e sicurezza: le stime dell'UKF alimentano sia l'osservazione della policy sia il modello dell'MPC, così l'intera pila chiude il loop sull'incertezza.

## Risultati

È un prototipo di ricerca e nessuna misura su veicolo reale è registrata. Ciò che esiste ed è verificato: il loop completo gira in simulazione su un modello monotraccia Pacejka integrato con RK4, con modelli di rumore per IMU, encoder e camera; una CycleGAN si occupa dell'adattamento sim-to-real delle immagini; script MATLAB confermano in modo indipendente la matematica: QP delle CBF, trasformata unscented, modello LPV, poli ad anello aperto, grado relativo e LQR inverso. Un digital twin MATLAB/Simulink a 14 gradi di libertà affianca il modello Python.

## Limiti e cosa rifarei

Il limite onesto è che l'intera pila ha guidato solo un'auto simulata: per quanto randomizzati, il modello Pacejka e i modelli di rumore restano mie ipotesi sulla realtà. Se ricominciassi, metterei in piedi prima il filtro CBF e il supervisore MPC e solo dopo addestrerei la policy, così ogni passo di training avverrebbe già dentro il recinto di sicurezza, invece di aggiungere le garanzie attorno a una policy finita.
