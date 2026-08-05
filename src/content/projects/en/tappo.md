---
title: "Tappo"
slug: "tappo"
lang: "en"
oneLiner: "iOS counter and goal tracker with streaks, heatmaps, widgets and Lock Screen Live Activities, built on SwiftUI and SwiftData."
category: "iOS & SwiftUI"
year: "2026"
status: "Prototype"
statusTone: "prototype"
featured: false
visible: true
order: 13
metrics:
  - value: "4 models"
    label: "SwiftData @Model types linked by cascade-delete relations"
  - value: "12 badges"
    label: "achievements from count, streak and time-of-day rules"
stack: ["Swift", "SwiftUI", "SwiftData", "WidgetKit", "ActivityKit", "App Intents"]
repo: "https://github.com/Ed0C97/portfolio/tree/main/projects/tappo"
image: "/images/projects/tappo.svg"
---

## The problem

Counting something over time sounds like the simplest tracking problem there is, and that is exactly why it usually fails. A bare number tells you where you are but not how you got there: without a record of every single step there are no daily totals, no streak, and no way to see whether a habit is alive or quietly dying. The second failure is friction. If checking or updating the count means unlocking the phone, opening the app and finding the right project, the tracking stops within days; the number has to live where the eyes already are, on the Home Screen and on the Lock Screen. And there is a third, quieter requirement: the things people count, habits and small personal goals, are private. A counter has no business asking for an account or copying that record to someone else's server.

## What I built

Tappo is a native iOS app in which each project is a counter with an optional target, an optional deadline, and a full history of timestamped entries. Every increment and decrement is logged, so the app can show daily totals, the current streak, an activity heatmap and the average entries per day. A project can be split into independent sub-counters, given milestones that are checked automatically as the count crosses them, and organized with search, categories, favorites and archiving. A 12-badge achievement system unlocks on count, streak, time-of-day and project-count conditions. The same data lives outside the app: a Home Screen widget shows count, streak, progress and days remaining; Live Activities put the counter on the Lock Screen and in the Dynamic Island; App Intents expose projects to Shortcuts and interactive widgets. There are per-project daily reminders, export to CSV, a summary report and a snapshot card image. The interface adapts between tabs on iPhone and a split view on iPad, in English and Italian. Everything stays on the device: iCloud sync is deliberately disabled.

## How it works

The app is MVVM on SwiftUI and SwiftData. Four @Model types (Project, CounterEntry, Milestone, SubCounter) are linked by cascade-delete relationships; a single @Observable, @MainActor view model owns selection and filter state, performs every mutation against the model context, and then triggers the side effects: haptics, milestone checks, Live Activity updates. The non-obvious choice is where the database lives. The SwiftData store is a SQLite file inside a shared App Group container, with CloudKit explicitly set to none. That one decision does two jobs at once: it guarantees the data never leaves the device, and it lets the widget extension open the very same store instead of talking to the app through a serialized copy. The widget's TimelineProvider fetches the most recently updated non-archived project and refreshes roughly every 30 minutes, reading theme and appearance settings from a shared UserDefaults suite. Export goes through ImageRenderer for the snapshot card, with PDFKit included for PDF output. The deployment target is iOS 26.0.

## Who it's for

Tappo is a prototype at version 1.0, a single-developer app under active development. It is for anyone who wants to count something toward a goal with a real history behind the number, without an account and without the data leaving the phone. It is also the project where I deliberately worked across the modern iOS system surface end to end: SwiftData, WidgetKit, App Intents, ActivityKit, and full localization in English and Italian, 151 strings.

## Limits and what I'd redo

The flip side of disabling iCloud is that there is no sync and no backup: the data lives on one device and dies with it. And the widget always shows the most recently updated project, which is the right default but also a ceiling; I would redo it as a configurable widget that lets the user pin a specific project, something the entities already exposed through App Intents make natural.
