// Profile data, both languages. Every fact here comes from the verified
// content library in the CV repository (cv_master/content/): nothing is
// invented, statuses are honest, and the Caelus wording follows the
// 2026-08-04 correction (no "production", no "institutional stakeholders").
import type { Lang } from '../i18n/ui';

export const identity = {
  name: 'Edoardo Caciolo',
  email: 'caciolo.edoardo@gmail.com',
  github: 'https://github.com/Ed0C97',
  linkedin: 'https://www.linkedin.com/in/edoardo-caciolo',
  portfolioRepo: 'https://github.com/Ed0C97/portfolio',
  location: { en: 'Rome, Italy', it: 'Roma, Italia' },
};

export const hero = {
  roles: {
    en: ['AI Engineer', 'Full-Stack Software Engineer', 'Software & ML Engineer'],
    it: ['AI Engineer', 'Ingegnere Software', 'Full-Stack Software Engineer'],
  },
  tagline: {
    en: 'I build AI systems that have to prove what they say: every answer bound to its source evidence, everything ungrounded discarded.',
    it: 'Costruisco sistemi AI che devono dimostrare quello che dicono: ogni risposta legata alla sua fonte, e quello che non lo e viene scartato.',
  },
};

export const stats = {
  en: [
    { value: '4+', label: 'years building software' },
    { value: '6', label: 'AI applications shipped for 4 clients' },
    { value: '2', label: 'platforms live in production' },
    { value: '12', label: 'backend APIs and services designed' },
  ],
  it: [
    { value: '4+', label: 'anni di sviluppo software' },
    { value: '6', label: 'applicazioni AI consegnate a 4 clienti' },
    { value: '2', label: 'piattaforme online in produzione' },
    { value: '12', label: 'API e servizi backend progettati' },
  ],
};

export const about = {
  en: [
    'Electronic engineering background at Sapienza University of Rome (automation and control), with over four years of software and applied machine learning built in parallel with my studies.',
    'Most of that time went into independent development: 6 full-stack AI applications for 4 paying clients, taken from requirements to release, plus two editorial platforms that are live today. In between, about a year part-time on the cloud and ML infrastructure of a nuclear-energy startup.',
    'The last year and a half has been about one problem: verifying that what a model says is actually written in the document it cites. Grounding, hallucination detection, and finding the exact sentence inside a PDF.',
  ],
  it: [
    "Vengo da ingegneria elettronica alla Sapienza, indirizzo automazione e controlli, con oltre quattro anni di software e machine learning applicato costruiti in parallelo allo studio.",
    'La parte piu grande e stata lo sviluppo indipendente: 6 applicazioni AI full-stack per 4 clienti, seguite dai requisiti al rilascio, piu due piattaforme editoriali oggi online. In mezzo, circa un anno part-time su infrastruttura cloud e ML in una startup del nucleare.',
    "L'ultimo anno e mezzo e andato quasi tutto su un problema solo: verificare che quello che dice un modello sia davvero scritto nel documento che cita. Ancoraggio alle fonti, rilevamento delle allucinazioni, e ritrovare la frase esatta dentro un PDF.",
  ],
};

export type ExperienceEntry = {
  org: string;
  role: string;
  dates: string;
  place: string;
  bullets: string[];
};

export const experience: Record<Lang, ExperienceEntry[]> = {
  en: [
    {
      org: 'Independent Developer',
      role: 'AI / Full-Stack Software Engineer',
      dates: 'Jan 2022 – Present',
      place: 'Remote',
      bullets: [
        'Designed and shipped 6 full-stack AI applications for 4 clients, owning the whole lifecycle from requirements to production release.',
        'Built LLM and agentic systems across 3 model families and 10 AI workflows (semantic search, structured extraction, recommendation, multi-agent), each with its own evaluation pipeline.',
        'Designed 12 backend APIs and services in async Python, containerized on GCP and AWS, managing 4 production environments with versioned contracts and idempotency.',
      ],
    },
    {
      org: 'Caelus (nuclear energy startup)',
      role: 'Cloud & ML Infrastructure Engineer',
      dates: 'Jan 2023 – Mar 2024',
      place: 'Rome, Italy · Part-time',
      bullets: [
        'Designed fault-tolerant AWS infrastructure as code (Terraform, CI/CD, autoscaling) for 3 safety-critical HPC simulation workloads; full release time went from about 120 to about 75 minutes.',
        'Deployed and monitored 4 forecasting models with an observability and anomaly-detection stack; fault-detection time went from about 15 to about 5 minutes.',
      ],
    },
    {
      org: 'Sapienza Fast Charge ADAS / S.A.S.A. Flight Team',
      role: 'Software & ML Engineer',
      dates: 'Oct 2022 – Jan 2026',
      place: 'Rome, Italy',
      bullets: [
        'Real-time control and sensor-fusion software for 2 autonomous platforms (driverless vehicle and UAV) in Python, C++ and ROS.',
        'Deterministic state-machine validator for the UAV ground-control station, handling 10 error conditions under degraded communication.',
      ],
    },
  ],
  it: [
    {
      org: 'Sviluppatore indipendente',
      role: 'AI / Full-Stack Software Engineer',
      dates: 'Gen 2022 – Presente',
      place: 'Remoto',
      bullets: [
        'Progettate e consegnate 6 applicazioni AI full-stack per 4 clienti, seguendo tutto il ciclo dai requisiti al rilascio in produzione.',
        'Sistemi LLM e agentici su 3 famiglie di modelli e 10 flussi AI (ricerca semantica, estrazione strutturata, raccomandazione, multi-agente), ognuno con la sua pipeline di valutazione.',
        'Progettati 12 tra API e servizi backend in Python asincrono, containerizzati su GCP e AWS, con 4 ambienti di produzione, contratti versionati e idempotenza.',
      ],
    },
    {
      org: 'Caelus (startup energia nucleare)',
      role: 'Ingegnere Cloud & Infrastruttura ML',
      dates: 'Gen 2023 – Mar 2024',
      place: 'Roma · Part-time',
      bullets: [
        "Infrastruttura AWS fault-tolerant come codice (Terraform, CI/CD, autoscaling) per 3 carichi di simulazione HPC safety-critical; il tempo di rilascio completo e passato da circa 120 a circa 75 minuti.",
        'Deploy e monitoraggio di 4 modelli di previsione con osservabilita e anomaly detection; il tempo di rilevamento di un guasto e passato da circa 15 a circa 5 minuti.',
      ],
    },
    {
      org: 'Team Sapienza Fast Charge ADAS / S.A.S.A. Flight',
      role: 'Software & ML Engineer',
      dates: 'Ott 2022 – Gen 2026',
      place: 'Roma, Italia',
      bullets: [
        'Software di controllo in tempo reale e sensor fusion per 2 piattaforme autonome (veicolo driverless e UAV) in Python, C++ e ROS.',
        'Validatore deterministico a stati per la stazione di terra UAV, con gestione di 10 condizioni di errore in comunicazione degradata.',
      ],
    },
  ],
};

export type SkillGroup = { name: string; items: string[] };

export const skills: Record<Lang, SkillGroup[]> = {
  en: [
    { name: 'AI / LLM & Agents', items: ['LangGraph', 'RAG', 'DSPy', 'LiteLLM', 'Instructor', 'pgvector'] },
    { name: 'Retrieval', items: ['Hybrid full-text + vector', 'Knowledge graphs', 'RRF', 'Reranking', 'Qdrant', 'Pinecone', 'Neo4j'] },
    { name: 'Evaluation & Grounding', items: ['Golden sets', 'LLM-as-a-judge', 'Hallucination detection', 'CI evaluation gates'] },
    { name: 'Backend & Data', items: ['Python', 'FastAPI', 'asyncio', 'Pydantic v2', 'SQLAlchemy', 'PostgreSQL', 'Redis', 'Celery'] },
    { name: 'Serving & DevOps', items: ['vLLM', 'ONNX Runtime', 'Docker', 'Kubernetes', 'Terraform', 'GitHub Actions', 'OpenTelemetry', 'Langfuse'] },
    { name: 'ML Training', items: ['PyTorch', 'Stable-Baselines3', 'PPO', 'Gymnasium', 'CycleGAN', 'Domain randomization'] },
    { name: 'Embedded & Control', items: ['ROS 2', 'MPC', 'Control barrier functions', 'Kalman filtering (UKF)', 'MATLAB/Simulink', 'C++'] },
  ],
  it: [
    { name: 'AI / LLM e agenti', items: ['LangGraph', 'RAG', 'DSPy', 'LiteLLM', 'Instructor', 'pgvector'] },
    { name: 'Retrieval', items: ['Ibrida full-text + vettoriale', 'Knowledge graph', 'RRF', 'Reranking', 'Qdrant', 'Pinecone', 'Neo4j'] },
    { name: 'Valutazione e grounding', items: ['Golden set', 'LLM-as-a-judge', 'Rilevamento allucinazioni', 'Gate di valutazione in CI'] },
    { name: 'Backend e dati', items: ['Python', 'FastAPI', 'asyncio', 'Pydantic v2', 'SQLAlchemy', 'PostgreSQL', 'Redis', 'Celery'] },
    { name: 'Serving e DevOps', items: ['vLLM', 'ONNX Runtime', 'Docker', 'Kubernetes', 'Terraform', 'GitHub Actions', 'OpenTelemetry', 'Langfuse'] },
    { name: 'Training ML', items: ['PyTorch', 'Stable-Baselines3', 'PPO', 'Gymnasium', 'CycleGAN', 'Domain randomization'] },
    { name: 'Embedded e controlli', items: ['ROS 2', 'MPC', 'Control barrier functions', 'Filtri di Kalman (UKF)', 'MATLAB/Simulink', 'C++'] },
  ],
};

export type EducationEntry = { title: string; org: string; dates: string; detail?: string };

export const education: Record<Lang, EducationEntry[]> = {
  en: [
    {
      title: 'B.Sc. in Electronic Engineering',
      org: 'La Sapienza University of Rome',
      dates: 'Expected 2026',
      detail:
        'Thesis: "Hybrid Control Architectures for Robust Autonomous Driving: A Multi-Layer Approach". Coursework: automation, control theory, digital and analog electronics, probability and statistics.',
    },
    {
      title: 'M.Sc. in AI and Robotics Engineering',
      org: 'La Sapienza University of Rome',
      dates: 'Incoming 2026',
    },
  ],
  it: [
    {
      title: 'Laurea Triennale in Ingegneria Elettronica',
      org: 'Sapienza Universita di Roma',
      dates: 'Prevista 2026',
      detail:
        'Tesi: "Architetture di controllo ibride per la guida autonoma robusta: un approccio multi-livello". Corsi: automatica, teoria del controllo, elettronica digitale e analogica, probabilita e statistica.',
    },
    {
      title: "Laurea Magistrale in Ingegneria dell'Intelligenza Artificiale e della Robotica",
      org: 'Sapienza Universita di Roma',
      dates: 'In ingresso 2026',
    },
  ],
};

export const certifications = [
  'EITCA/AI - Artificial Intelligence Academy (European IT Certification Institute)',
  'EITCA/IS - Information Technologies Security Programme (European IT Certification Institute)',
  'Google Cybersecurity Professional Certificate (Coursera)',
];

export const spokenLanguages = {
  en: [
    { name: 'Italian', level: 'native' },
    { name: 'English', level: 'B2, daily working use' },
  ],
  it: [
    { name: 'Italiano', level: 'madrelingua' },
    { name: 'Inglese', level: 'B2, uso lavorativo quotidiano' },
  ],
};
