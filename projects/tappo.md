# Tappo

> A native iOS app for tracking counts, habits, and goal progress across multiple projects, with Home Screen widgets and Lock Screen Live Activities that stay in sync with the app.

## Overview

Tappo is a native iOS counter and goal tracker. Each project holds a running count, an optional progress target, an optional deadline, and a full history of timestamped entries. Recording every change lets the app compute daily totals, streaks, and activity heatmaps, and surface the same data outside the app through widgets, Shortcuts actions, and Live Activities. All data is stored locally on device.

## Highlights

- **Multiple projects** with create, duplicate, archive, favorite, and delete operations, plus search, category filtering, and multiple sort orders.
- **Flexible counter operations** (increment, decrement, set, reset) with per-project step sizes, sub-counters for independently tracked sub-counts, and notes on individual entries.
- **Goals, deadlines, and milestones** with computed progress percentage, days-remaining and overdue tracking, and automatic milestone detection.
- **Streaks, stats, and an activity heatmap** derived from full entry history (current streak, daily totals, averages, intensity over time).
- **Achievement system** awarding badges from count, streak, time-of-day, and project-count conditions.
- **Home Screen widgets, Shortcuts/App Intents, and Lock Screen / Dynamic Island Live Activities** that mirror the in-app state and update as counts change.
- **Local reminders** scheduled per project.
- **Data export** to CSV, summary reports, shareable snapshot images, and PDF.
- **Theming and feedback**: selectable color themes and app icons, light/dark/system appearance, animated backgrounds, glassmorphism UI, confetti, haptics, and sound.
- **Adaptive UI** for iPhone and iPad, localized in English and Italian.

## Tech Stack

| Area | Technologies |
| --- | --- |
| Language | Swift |
| UI | SwiftUI |
| Persistence | SwiftData (local, on-device) |
| System frameworks | WidgetKit, App Intents, ActivityKit, UserNotifications, PDFKit |
| Architecture | MVVM with an observable view model |
| Platform | iOS |

## Status

Prototype / version 1.0, single-developer iOS app under active development. Source code private, review available on request.

---


## Code sample

A small, IP-safe excerpt is in [`tappo/`](./tappo/): typed domain model with a streak algorithm, a coordinate-rendered PDF/CSV/image export pipeline, and a data-driven theme system.

_© 2026 Edoardo Caciolo, all rights reserved. Proprietary and not open source; source code is private and available for review on request._
