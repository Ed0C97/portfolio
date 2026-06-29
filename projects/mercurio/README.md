# Mercurio: portfolio excerpts

Selected internals from Mercurio, an adaptive operations console for small businesses whose terminology and workflow reshape themselves around each trade. These excerpts show the data-driven configuration and shared-state layers that make the single app shell behave differently per business type; they are faithful frontend source files and contain no secrets, credentials, or backend logic.

**Context:** see [../mercurio.md](../mercurio.md) for the project overview.

**Stack:** JavaScript / React 19, Zustand 5 for state, plain ES modules, no backend, no network calls.

## What each file shows

- **`businessTypes.js`**: The heart of the "adaptive" idea. A declarative map from eight business types (tattoo, restaurant, artisan, beauty, jewelry, photography, fashion, generic) to per-trade terminology, default product categories, order-status pipelines, and feature flags, plus a `getTerminology()` accessor with a `generic` fallback. Adding or retuning a trade is a data edit, not a code change.
- **`navigation.js`**: The navigation model that drives the sidebar and mobile bar, declaring routes, icons, and which live counts (open orders, low-stock items, today's events, unread messages) each item badges, keeping navigation structure separate from the components that render it.
- **`useAppStore.js`**: The single Zustand application store: orders, inventory, calendar events, contacts, chat conversations, and notifications, each with add/update/delete actions and derived selectors (filtered orders, low-stock items, today's events, unread counts) over in-memory demo data.

## Deliberately omitted

- All page and component code, the design-system tokens, and the app shell.
- The auth/onboarding flow and the persisted theme store.
- The product/business plan and any aspirational backend, AI, or channel-integration code (none of which exists in the repository).

These files are faithful excerpts shared for standalone reading.

_© 2026 Edoardo Caciolo, all rights reserved. Portfolio excerpt shared to demonstrate engineering; not licensed for reuse. Full source is private._
