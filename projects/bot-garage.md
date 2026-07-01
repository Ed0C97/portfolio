# BOT Garage

> A local-first workshop management application that tracks vehicle maintenance, costs, and documents, with OCR import of data straight from registration and invoice PDFs.

## Overview

BOT Garage is a single-user maintenance manager for one or more vehicles. It keeps a maintenance catalogue, service records, a parts and consumables inventory, administrative deadlines, and an expense ledger in a single local database, then generates spreadsheets, documents, and PDF reports from that data. It is designed around a motorcycle use case but the data model is keyed per vehicle and supports a multi-vehicle fleet. Everything runs on the user's own machine, including document OCR and the optional AI assistant, so vehicle documents and personal data never leave the device.

## Highlights

- Per-vehicle maintenance catalogue tracking status, cost, mileage interval, priority, and safety level, with grouped service records and per-record PDF generation.
- Consumables inventory with stock levels, reorder thresholds, and stock movements tied back to maintenance work.
- Administrative deadline tracker (insurance, road tax, inspection, garage rent) with automatic due-date calculation and recurring-cost accrual.
- Expense ledger with per-year and per-category roll-ups, plus an insurance card covering annual premiums.
- OCR import of a new vehicle from a registration PDF and of work items from a workshop invoice PDF, extracting structured fields and line items from scanned documents.
- A built-in honesty-of-data discipline: low-confidence OCR fields are never silently accepted: they are surfaced for manual confirmation, and only verified structured data is persisted, so the database stays trustworthy.
- Multi-format document generation, including spreadsheets with live formulas, ODS/ODT/PDF manuals, and JSON/CSV exports, all driven from the same source of truth.
- Audience-specific PDF reports for the owner, the mechanic, and a prospective buyer (the buyer dossier automatically omits owner personal data).
- A local conversational assistant that acts on the database through tool calling (for example, managing the parts shopping list) without any cloud dependency.
- Deadline, reorder, and mileage-based notifications delivered over a self-hosted WhatsApp gateway, with per-event deduplication so alerts never repeat.
- Optional remote Postgres backend and optional field-level encryption for sensitive vehicle data, both toggled by configuration.

## Tech Stack

| Category | Technologies |
|---|---|
| Language | Python; JavaScript for the frontend and desktop shell |
| Backend / framework | FastAPI, Uvicorn, Pydantic |
| Frontend | Static HTML/CSS/JavaScript, Lucide icons |
| Data stores | SQLite (default), PostgreSQL (optional) |
| OCR / ML | Local vision-language OCR model on PyTorch / Transformers (Apple Silicon / MPS) |
| AI assistant | Local LLM with tool calling (Ollama) |
| Documents | openpyxl, XlsxWriter, pandas, NumPy, odfpy, reportlab, PyMuPDF, Pillow |
| Security | Field-level encryption (cryptography / Fernet), dotenv configuration |
| Notifications | Self-hosted WhatsApp gateway (HTTP) |
| Desktop / packaging | Electron, electron-builder |

## Status

Working personal application, actively developed, with a local web UI and an optional Electron desktop shell. All inference (OCR and the assistant) runs locally with no cloud dependency. Source code private and proprietary (all rights reserved), code review available on request.

---


## Code sample

A small, IP-safe excerpt is in [`bot-garage/`](./bot-garage/): confidence-gated OCR field extraction that persists a field only when the OCR confidence clears a threshold (weaker matches go to human review), an SSRF-guarded stdlib HTTP client, transparent Fernet field-encryption at the data layer, and a declarative openpyxl theming layer.

_© 2026 Edoardo Caciolo, all rights reserved. Proprietary and not open source; source code is private and available for review on request._
