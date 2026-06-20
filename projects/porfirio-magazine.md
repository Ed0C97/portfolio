# Porfirio Magazine

> A full-stack digital magazine platform that unifies bilingual publishing, payments, engagement analytics, and automated social-media content generation in a single product.

## Overview

Porfirio Magazine is the publishing platform behind a live online magazine. It pairs a React single-page application with a Flask REST API and a PostgreSQL database so editors can write, translate, schedule, and publish articles, while readers browse, comment, favorite, and donate. The platform also automates two normally manual editorial chores — Italian/English translation and the production of ready-to-post social-media carousels — using a generative-AI provider. It serves a real production audience with custom domains and managed infrastructure.

## Highlights

- **Bilingual publishing** — articles carry an original language and are translated on demand between Italian and English, with results cached and re-used so the same content is never re-translated unnecessarily. The UI ships full internationalization with browser language detection.
- **Rich editorial workflow** — create, edit, schedule, and categorize articles through a rich-text editor; published content is exposed via REST, an RSS feed, a sitemap, and fast client-side full-text search.
- **Automated social carousels** — turns a published article into a set of styled, ready-to-post carousel images with AI-generated slide copy, delivered as a downloadable bundle, removing a slow manual design step from the editorial cycle.
- **Payments and donations** — end-to-end Stripe integration for reader donations, with per-environment feature flags to enable or disable it.
- **Engagement analytics** — per-article and platform-wide metrics, an overview dashboard, advanced analytics, and content-generation statistics, charted in-app and exportable to CSV.
- **Accounts and community** — email/password and Google OAuth sign-in, email verification, password reset, comments, favorites, and in-app notifications, with the same API serving both the web app and token-based clients.
- **Roles and moderation** — role-based access control, a comment-moderation queue, moderation and user-activity logging, and admin tooling.
- **Media handling** — image upload and CDN delivery, plus AI-assisted cover-image generation with a curated set of style presets.
- **Directories and maps** — brand and venue directories enriched from external data sources and rendered through multiple mapping libraries and an interactive 3D globe.
- **Mobile packaging** — the built web app is wrapped as a native iOS/Android application.
- **Operational hardening** — Redis-backed rate limiting, security headers and HSTS, response compression, caching, and scheduled maintenance jobs.

## Tech Stack

| Category | Technology |
|----------|------------|
| **Languages** | JavaScript (JSX), Python 3.11, HTML, CSS/SCSS, Swift (iOS wrapper) |
| **Frontend** | React 18, Vite, React Router, Radix UI, Tailwind CSS, Framer Motion, Recharts, Zustand, i18next, React Hook Form, React Quill, Fuse.js |
| **Maps / visualization** | Google Maps, Mapbox GL, Leaflet, react-globe.gl |
| **Mobile** | Capacitor (iOS/Android) |
| **Backend** | Flask 3, Gunicorn |
| **Data stores** | PostgreSQL (SQLAlchemy 2 + Alembic), Redis |
| **Background / async** | Celery (Redis broker), Flask-Limiter, Flask-Compress |
| **Auth** | Flask-Login, PyJWT, Authlib (Google OAuth) |
| **Payments** | Stripe |
| **Media / AI** | Cloudinary, generative-AI provider, Pillow |
| **Automation** | Playwright (HTML-to-image rendering), BeautifulSoup |
| **Google integrations** | Sheets, Calendar API, google-auth |
| **Infra / DevOps** | Render, Docker, Nginx, pnpm |

## Status

Production application, deployed with custom domains and managed PostgreSQL, and actively maintained. Source code is private and proprietary — code review available on request.

---


## Code sample

A small, IP-safe excerpt is in [`porfirio-magazine/`](./porfirio-magazine/) — a graceful-degradation Redis cache layer, SQLAlchemy N+1 prevention with threaded-comment assembly, and a memoized Fuse.js fuzzy-search hook.

_© 2026 Edoardo Caciolo — all rights reserved. Proprietary and not open source; source code is private and available for review on request._
