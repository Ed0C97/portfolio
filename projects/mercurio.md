# Mercurio

> An adaptive operations console for small businesses that unifies orders, inventory, calendar, chat, and contacts in a single screen whose terminology and workflow reshape themselves around each trade.

## Overview

Mercurio is a lightweight business-management tool aimed at solo operators and small teams (tattoo studios, artisans, restaurants, beauty salons, photographers, jewelers, tailors). It collapses the daily sprawl of WhatsApp / Instagram / Facebook messages, paper notes, and spreadsheets into one dashboard that relabels itself per trade: a tattoo studio sees *Sessioni*, *Materiali*, and *Appuntamenti*, while a restaurant sees *Ordini*, *Magazzino*, and *Prenotazioni*. The premise is that existing management software is too expensive, too complex, and disconnected from the social channels small merchants actually use. This repository contains the React single-page application that realizes the front end of that vision; the backend, AI, and channel integrations described in the product plan are not yet built.

## Highlights

- **Adaptive per-trade configuration.** A declarative configuration maps each of eight business types (tattoo, restaurant, artisan, beauty, jewelry, photography, fashion, generic) to its own terminology, default product categories, order-status pipeline, and feature flags, with a `generic` fallback, so the same app shell speaks each merchant's language.
- **One screen, not many tools.** Orders, inventory, calendar, chat, contacts, and analytics are routes inside a single app shell rather than separate products, with a collapsible desktop sidebar and a mobile bottom-nav for small screens.
- **Live operational signals.** The navigation surfaces real-time badge counts (open orders, low-stock items, today's events, unread messages) derived from a single shared state store.
- **Unified social inbox (demo).** A chat view models a combined inbox of Instagram, WhatsApp, and Facebook conversations with per-thread message history, prototyping the channel unification the product plan targets.
- **Themed design system.** A Tailwind-based "Datum" token system with Radix UI primitives provides light/dark modes and accent theming persisted across sessions.
- **Honest, navigable prototype.** The UI runs end-to-end on in-memory demo data (a stubbed login signs the user into a sample studio), so the full experience is explorable without any backend.

## Architecture

Mercurio is a client-side single-page application built with React and Vite. Routing is handled by `react-router-dom` behind a client-side auth guard, with pages code-split via `React.lazy` and `Suspense` and composed inside an app shell (sidebar, header, mobile nav). Application state lives in a single Zustand store exposing orders, inventory, calendar events, contacts, chat conversations, and notifications, each with CRUD actions and derived selectors (filtered orders, low-stock items, today's events, unread counts), while auth and theme are kept in separate stores persisted to `localStorage`. Per-trade behavior is data-driven: a configuration module supplies terminology, categories, and status pipelines that the rest of the UI reads through a `getTerminology()` helper. The product vision (a Python/FastAPI + PostgreSQL backend, AI extraction of orders from chat, live WhatsApp/Instagram/Facebook integrations, payments) is documented in the plan but deliberately out of scope for this repository.

## Tech Stack

| Category | Details |
| --- | --- |
| Language | JavaScript (JSX), React 19 |
| Build tool | Vite 6 (`@vitejs/plugin-react`), dev server on port 3000, `@` aliased to `src/`, manual vendor chunking |
| Routing | react-router-dom 6 (lazy pages, `BrowserRouter`) |
| State | Zustand 5 (unified app store; persisted auth/theme via `persist`) |
| UI primitives | Radix UI (dialog, dropdown, select, tabs, tooltip, popover, avatar, checkbox, progress, scroll-area, separator, switch) |
| Styling | Tailwind CSS 3 ("Datum" CSS-variable tokens, light/dark + accent), PostCSS, Autoprefixer |
| Charts & motion | Recharts, Framer Motion |
| Misc | lucide-react, react-hot-toast, date-fns, clsx / tailwind-merge / class-variance-authority |

## Status

Early-stage frontend prototype. The UI is navigable end-to-end on demo data; no backend, authentication, AI, or third-party integrations are wired up yet. The full product and go-to-market vision is documented separately in the project's startup plan.

---


## Code sample

A small, IP-safe excerpt is in [`mercurio/`](./mercurio/): the data-driven per-trade configuration, the badge-counting navigation model, and the unified Zustand application store.

_© 2026 Edoardo Caciolo, all rights reserved. Proprietary and not open source; source code is private and available for review on request._
