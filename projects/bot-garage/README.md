# bot-garage: code samples

Curated, self-contained excerpts from **bot-garage**, a self-hosted Python application that tracks a small vehicle fleet (maintenance catalogue, expenses, stock, and WhatsApp reminders). These three files are chosen to show engineering craft, security thinking, a clean cryptography abstraction, and a tidy presentation layer, without reproducing any product-specific logic.

**Context:** see [../bot-garage.md](../bot-garage.md) for the full project write-up.

**Stack:** Python 3.10+ (stdlib `urllib`, `sqlite3`, `ipaddress`), `cryptography` (Fernet), `openpyxl`, `pydantic`/dataclasses. Runs as a local FastAPI app with optional Postgres backend.

## What each file shows

- **`ssrf_guarded_client.py`**: A dependency-free HTTP client for a *local-only* gateway. Before any outbound request it validates the configured base URL: scheme must be `http(s)` and the host must resolve to loopback, which rejects `file://`, link-local metadata endpoints (`169.254.169.254`), and arbitrary internal hosts. Shows SSRF defence-in-depth on an unauthenticated local API, plus wrapped-response error handling over stdlib `urllib`.
- **`field_encryption.py`**: Transparent application-level encryption for sensitive columns using Fernet (AES-CBC + HMAC). Ciphertext is tagged with an `enc:` prefix so encrypted state is visible for audit/debugging; `encrypt()` is idempotent, and `decrypt()` fails *explicitly* (returns the ciphertext untouched, never invented plaintext) when the key is missing or wrong. Includes the read/write wrapping pattern that keeps crypto at the data layer instead of scattered across endpoints.
- **`workbook_theme.py`**: A declarative openpyxl presentation layer: one frozen `Theme` dataclass plus module-level style constants drive headers, banded tables, native Excel tables, freeze panes, drop-down data validation, and conditional-formatting rules. One change to the palette radiates across every generated worksheet.

## Deliberately omitted

To keep the product's value private and these files readable standalone, the following were stripped or excluded:

- All credentials, seeded dev keys, environment-variable values, and `.env` handling.
- The gateway's full API contract, session lifecycle, QR/pairing flow, and every notification message template (the domain-specific reminder logic and copy).
- The complete database schema (about 18 tables), the per-vehicle store classes, the Postgres adapter, migrations, and all domain field names.
- The scheduling/cost/maintenance-classification engines and the LLM-facing data model.
- Business-specific category names, thresholds, branding strings, and any data that identifies real vehicles or owners.

Imports are stubbed or minimised and the excerpts are lightly trimmed; the author's real structure, naming style, and comments are preserved.

_© 2026 Edoardo Caciolo, all rights reserved. Portfolio excerpt shared to demonstrate engineering; not licensed for reuse. Full source is private._
