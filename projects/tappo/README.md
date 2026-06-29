# Tappo: code samples

Three excerpts from Tappo, a native iOS counter/goal-tracking app (SwiftUI + SwiftData), chosen to show domain modeling, drawing-level export code, and a clean design system.

**Context:** see [../tappo.md](../tappo.md) for the project overview.

**Stack:** Swift 5.9+, SwiftUI, SwiftData (`@Model`), PDFKit / UIKit graphics (`UIGraphicsPDFRenderer`, `ImageRenderer`), iOS 17+.

## What each file shows

- **`Project.swift`**: the SwiftData `@Model` entity with cascade relationships, plus the read-only computed interface views consume: `daysRemaining`, clamped `progressPercentage`, and a `streak` calculation that groups history by normalized day and walks backward from today. No business logic leaks into the views.
- **`ExportManager.swift`**: a `@MainActor` export pipeline producing three formats from the same model: escaped CSV, a manually laid-out PDF (coordinate math, typographic attributes, a drawn progress bar, milestone listing), and a SwiftUI card rendered to a `UIImage` via `ImageRenderer`. Clean helper decomposition (`drawStat`) and temp-file management.
- **`AppTheme.swift`**: a `Sendable`, value-typed theme with gradient/contrast helpers and an auto-generated `lightVariant`, backed by curated dark palettes with semantic color slots. All colors are data-driven; nothing is hardcoded at the call site.

## Deliberately omitted

- The full app: views, navigation, the `ProjectManager` view model, persistence wiring, and the App Intents / Widget targets.
- Haptics, Live Activity, notification scheduling, and the achievement-unlock side effects.
- App Group identifiers, bundle IDs, store URLs, and any configuration/secret values.
- Most of the eight palettes are trimmed to two representative ones; the export pipeline is shown end-to-end but standalone.

_© 2026 Edoardo Caciolo, all rights reserved. Portfolio excerpt shared to demonstrate engineering; not licensed for reuse. Full source is private._
