---
title: "Anacleto"
slug: "anacleto-instagram"
lang: "en"
oneLiner: "Vision models score Instagram grids, MCTS searches the feed order, and a scheduler publishes through the official Meta Graph API."
category: "Vision & Optimization"
status: "Beta"
statusTone: "beta"
featured: false
visible: true
order: 12
metrics:
  - value: "3 optimizers"
    label: "interchangeable engines: Greedy, Beam Search, MCTS"
  - value: "6 criteria"
    label: "weighted aesthetic score for every candidate grid"
stack: ["Python", "FastAPI", "PyTorch", "YOLO", "Gemini", "PostgreSQL", "APScheduler"]
repo: "https://github.com/Ed0C97/portfolio/tree/main/projects/anacleto-instagram"
image: "/images/projects/anacleto-instagram.svg"
---

## The problem

An Instagram profile for a business or creator account is judged as a grid before anyone opens a single post. The most recent nine images sit side by side, and their order decides whether the profile reads as curated or accidental. Getting that order right by hand is tedious: you drag thumbnails around a planning app, judge colors and composition by eye, and repeat the exercise with every new batch of photos. It is also a genuine combinatorial problem, since nine images can be laid out in 362,880 different orders, far more than anyone can compare visually. Scheduling tools automate the publishing step but not the ordering one: they post whatever sequence you hand them, at the times you set. And many of them ask for your account credentials and keep them on their own servers, which is exactly the kind of standing secret a small account owner should hesitate to give away.

## What I built

Anacleto is a platform that takes a batch of images and runs the pipeline from analysis to publication. Vision models extract color, texture, detected objects and aesthetic signals from each image. A search engine then looks for the ordering that scores highest as a grid, a caption generator writes context-aware captions and hashtags from the analysis results, and the ordered posts go into a queue. A scheduler publishes each one at its configured slot through the official Meta Graph API. All of this is exposed as a FastAPI service with registered accounts, email verification and API keys, and there is a desktop client, built with Dear PyGui and packaged for macOS and Windows, for people who prefer buttons to endpoints. One design decision runs through the whole system: the server never stores a user's Instagram, Cloudinary or Gemini secrets. Credentials travel in request headers and are used statelessly, so no store of account secrets ever sits server-side.

![anacleto-instagram detail placeholder 1](/images/projects/anacleto-instagram-2.svg)

## How it works

Three components cooperate: a FastAPI API layer, an analysis engine, and a standalone scheduler. The engine's orchestrator wires together feature extractors (coordinating Vertex AI, Replicate and Gemini vision calls), optimizers and evaluators, all configured through dataclasses with environment loaders, so algorithm and model choices are swappable without code changes. The interesting seam is the optimizer: three interchangeable strategies, Greedy, Beam Search and Monte Carlo Tree Search, search over a default 3x3 nine-image grid, and the MCTS variant uses UCB selection, candidate pre-filtering and greedy rollouts. What makes the search work is the evaluator: candidate grids are rendered and scored on six weighted criteria (color harmony, composition, visual flow, balance, theme consistency, interest), which turns a subjective judgement into a reward function all three optimizers share. The scheduler reads the queue with APScheduler and publishes at per-weekday slots, three posts per day by default in Europe/Rome, with a dry-run mode; publishing goes through Graph API v21.0 with retry logic and covers images, videos, carousels, stories and reels.

## Who it's for

Anacleto automates the content pipeline for Instagram Business and Creator accounts. It suits people who want grid curation and scheduled publishing without handing standing credentials to a third-party server, since secrets stay per-request. On the service side there is registration with OTP email verification (via Resend), API keys with optional expiry and per-IP rate limiting; the desktop client covers account management, credentials, health and stats for users who never touch the API directly.

![anacleto-instagram detail placeholder 2](/images/projects/anacleto-instagram-3.svg)

## Limits and what I'd redo

The aesthetic score is a set of hand-weighted criteria, so "best order" means best according to weights I chose, not according to measured engagement; the engine contains feedback-learning features, but they ship disabled by default. If I redid it, I would move the per-IP rate limiter out of process memory into a shared store, because in-memory state stops limiting anything the moment a second instance runs.
