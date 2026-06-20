# basil — crossword generator (portfolio excerpts)

A CLI crossword generator that packs a word list into a 2D grid by finding letter intersections, validating each placement against boundary/conflict/adjacency rules, and rendering the result. These are trimmed, self-contained excerpts of the core algorithm and the input layer.

**Context:** see [../basil.md](../basil.md)

**Stack:** Python 3 (standard library; Pillow for rendering in the full project — not needed by these excerpts).

## What each file shows

- **`intersection_placement.py`** — the placement search. Given a candidate word and the already-placed words, it scans for shared letters and works out the exact `(row, col, direction)` where the new word would cross an existing one. The geometric reasoning is the interesting part: intersecting a horizontal word with a vertical one (and vice versa) requires different coordinate transforms, derived inline from the intersection equations.
- **`placement_validation.py`** — the guardrail that makes the grid legal. It separates three distinct failure modes — out of bounds, a letter conflict, and an unintended adjacency that would visually fuse two words — and applies different logic to intersection cells vs. fresh cells, plus dedicated checks on the cells just before and after the word's ends.
- **`input_loaders.py`** — three input handlers (JSON, pipe-delimited text, interactive) that all return the same `(words, …)` shape to the caller. Shows graceful error handling, comment/blank-line skipping, and sensible defaults.

## Deliberately omitted

- Image rendering (Pillow drawing, font fallbacks, bounding-box cropping), grid numbering, clue formatting, and the interactive menu loop — all present in the real project, omitted here to keep each excerpt focused.
- The "secret phrase" highlighting feature and any project-specific copy/labels.
- All file paths, banners, and I/O wiring from the original CLI.

_© 2026 Edoardo Caciolo — all rights reserved. Portfolio excerpt shared to demonstrate engineering; not licensed for reuse. Full source is private._
