# Basil

> A command-line tool that builds printable crossword puzzles from a word list and can hide a secret phrase in the grid for scavenger-hunt-style play.

## Overview

Basil turns a set of words and clues into an intersecting crossword grid, then exports the grid as a numbered image and the clues as a text file. It can optionally mark a chosen secret phrase by highlighting the grid cells that spell it out, letting puzzle authors layer a scavenger hunt on top of a standard crossword. It runs as an interactive terminal application for anyone creating printable puzzles, and ships with sample word lists.

## Highlights

- Arranges words into a compact, intersecting crossword grid where words join only at shared letters.
- Optionally hides a secret phrase by highlighting the grid cells that spell it, with warnings when the phrase cannot be placed from the available letters.
- Numbers entries in standard crossword order and groups clues into across and down lists.
- Accepts input several ways: a structured JSON file, a simple pipe-separated text file, or manual entry through prompts.
- Exports a clean, print-ready image with numbered entries and distinct highlighting for secret-phrase cells, plus a companion clues file.
- Renders a color preview of the grid directly in the terminal.

## Tech Stack

| Category | Details |
| --- | --- |
| Language | Python |
| Image rendering | Pillow (PIL) |
| Interface | Interactive terminal CLI with ANSI color output |

## Status

Prototype, single-author. Source code private — review available on request.

---


## Code sample

A small, IP-safe excerpt is in [`basil/`](./basil/) — 2D-grid intersection geometry, defensive placement validation, and clean multi-format CLI input loading in Python.

_© 2026 Edoardo Caciolo — all rights reserved. Proprietary and not open source; source code is private and available for review on request._
