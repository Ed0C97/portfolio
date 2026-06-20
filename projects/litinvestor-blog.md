# LitInvestor Blog

> A full-stack publishing platform for a financial-literacy blog that also repurposes published articles into ready-to-post social media image sets.

## Overview

LitInvestor Blog is the production web application behind a financial-education and investing blog. It combines a Flask REST API with a React single-page application, covering the full lifecycle of an editorial product: authoring and publishing, reader accounts and interactions, a newsletter, donations, and analytics. Its standout capability is an AI-assisted content-repurposing pipeline that converts a published article into a downloadable set of Instagram-ready image slides, letting the author extend reach without manual design work.

## Highlights

- **End-to-end publishing workflow**: rich-text/Markdown authoring, slugs, categories, draft and published states, and scheduled publishing.
- **Reader engagement**: comments with moderation, likes, favorites, and share tracking.
- **Multi-method authentication**: session login, Google OAuth, email verification, and password reset, with role-based access control gating admin and author areas.
- **Automated social content generation**: turns a published article into a packaged set of branded, length-constrained image slides ready for posting, combining LLM text condensation with templated browser-rendered graphics.
- **Monetization and growth**: Stripe-based donations, newsletter subscription and subscriber management, and a contact inbox with email notifications.
- **Search and discovery**: client-side fuzzy matching paired with server-side search endpoints.
- **Analytics**: dashboards for article and social-generation statistics plus a user-activity log.
- **SEO**: server-rendered meta endpoints, meta-tag management, robots directives, and a build-time sitemap generated from live content.
- **Performance and security**: response caching, Redis-backed rate limiting, response compression, security and HSTS headers, content sanitization, and offloaded image storage.
- **Rich article rendering**: math typesetting and Markdown extensions with sanitized output.

## Architecture (high level)

The system is a two-service deployment plus shared data stores:

- **Frontend** — a React SPA (Vite) with client-side routing and a context-based auth state, served as static assets.
- **Backend** — a Flask REST API using the application-factory pattern, organized into modular route groups for articles, auth, interactions, payments, search, moderation, content generation, analytics, and admin tooling. Cross-subdomain authenticated requests are supported via CORS and proxy-aware configuration.
- **Data and async** — relational database via SQLAlchemy with managed migrations; Redis for caching and rate limiting; a task queue for asynchronous jobs such as email delivery; and scheduled jobs for housekeeping.
- **External services** — managed image storage, payments, an LLM provider for text summarization, and transactional email.

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| Languages | Python, JavaScript (ES modules) |
| Backend framework | Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-Login, Flask-Cors, Flask-Limiter, Flask-Compress |
| Frontend framework | React, Vite, React Router |
| UI | Radix UI primitives, Tailwind CSS, lucide-react, sonner, Recharts |
| Data stores | PostgreSQL (production), SQLite (local dev), Redis (cache + rate limiting) |
| ORM / migrations | SQLAlchemy, Alembic |
| Async / tasks | Celery (Redis broker) |
| Auth | Flask-Login, Authlib (Google OAuth) |
| Payments | Stripe |
| Media / AI | Cloudinary, Pillow, Playwright, BeautifulSoup, Google Gemini |
| Content rendering | marked, react-markdown, remark/rehype, KaTeX, DOMPurify |
| Search | fuse.js |
| Infra / DevOps | Render, Docker, Gunicorn, Nginx, pnpm |

## Status

Production — deployed and live, serving a public audience. Role: sole architect and full-stack developer.

Source code private/proprietary — review available on request.

---

_© 2026 Edoardo Caciolo — all rights reserved. Proprietary and not open source; source code is private and available for review on request._
