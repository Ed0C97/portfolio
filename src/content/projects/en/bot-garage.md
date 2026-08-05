---
title: "BOT Garage"
slug: "bot-garage"
lang: "en"
oneLiner: "Local-first vehicle maintenance app with fully on-device OCR of registration and invoice PDFs; no document leaves the machine."
category: "Local-First & On-Device AI"
status: "Active personal app"
statusTone: "beta"
featured: true
visible: true
order: 7
metrics:
  - value: "~6 GB"
    label: "vision-language OCR model running fully on-device (MPS)"
  - value: "3 reports"
    label: "audience-specific PDFs: owner, mechanic, buyer dossier"
stack: ["Python", "FastAPI", "SQLite", "dots.mocr", "PyTorch", "Ollama", "Electron"]
repo: "https://github.com/Ed0C97/portfolio/tree/main/projects/bot-garage"
image: "/images/projects/bot-garage.svg"
---

## The problem

Everything about a vehicle lives on paper. The maintenance history sits in a drawer of workshop invoices, the deadlines for insurance, road tax and inspection live in someone's memory, and the registration document carries the plate, the VIN and the owner's personal data. Keeping all of this in a spreadsheet means typing it in by hand, which is tedious enough that most people stop after a month. The obvious shortcut, a cloud app with OCR, has a cost that is easy to overlook: it means uploading identity-bearing documents about you and your vehicle to someone else's server. There is a second, quieter problem with OCR itself. A model reading a blurry invoice will happily guess, and a guessed VIN or a guessed mileage figure is worse than an empty field, because it looks like a record. For maintenance data that will later feed a buyer's dossier or a mechanic's briefing, silent guessing is not acceptable.

## What I built

BOT Garage is a web application that runs entirely on my own machine. One local database holds, per vehicle, a maintenance catalogue, service records that group completed work, a parts and consumables inventory with reorder thresholds, an administrative deadline tracker and an expense ledger. A new vehicle is added by importing its registration PDF: the OCR extracts plate, VIN, make, model, registration year, emissions class and engine displacement, each with a confidence score. A workshop invoice imports the same way, header plus line items, and becomes completed maintenance items grouped into a service record. From that single database the app generates a multi-sheet Excel workbook with live formulas, ODS and ODT documents, JSON and CSV exports, and three PDF reports written for different readers: the owner, the mechanic, and a prospective buyer, whose dossier omits personal data. A local assistant called Walter, running on Ollama, acts on the database through tool calling, and WhatsApp notifications for deadlines and reorders go through a self-hosted gateway with per-event deduplication.

![bot-garage detail placeholder 1](/images/projects/bot-garage-2.svg)

## How it works

A FastAPI backend serves a JSON API and a static HTML/CSS/JavaScript frontend; the data layer is a relational schema with foreign keys, keyed by vehicle, including an append-only event log. Storage is SQLite by default and switches to a remote Postgres (Neon) via environment variable; with a key set, sensitive fields (registration, VIN, plate, owner) are encrypted with Fernet before leaving the process. OCR uses the vendored ocr-toolkit and the dots.mocr vision-language model, about 6 GB, running on Apple Silicon through Metal Performance Shaders, with a patch that makes flash_attn optional and falls back to scaled dot-product attention. The non-obvious choice is the honesty-of-data rule: the model's transcription is ephemeral, only structured fields are stored, and any field read with low confidence stays empty or flagged and requires manual confirmation before saving. Nothing enters the record without a human deciding it is true. An optional Electron shell wraps the app for desktop use.

## Who it's for

Written for one user: me. It is a working personal application, actively developed and oriented to a single owner's setup, with seed data built around a specific motorcycle, a Triumph Bonneville T120. The schema is keyed per vehicle and supports several, so it grows with the garage. The application itself is proprietary; the vendored ocr-toolkit inside it is MIT.

![bot-garage detail placeholder 2](/images/projects/bot-garage-3.svg)

## Limits and what I'd redo

The OCR path requires Apple Silicon, since dots.mocr runs through MPS, so on other hardware the import feature simply does not exist. Default paths and seed data are still hardcoded for my own setup, which is the real cost of building for one user first. If I redid it, I would generalize that configuration from the start and skip the Tkinter desktop UI that now sits deprecated in the repository as a fallback.
