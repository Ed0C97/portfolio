## Kairo: code samples

A few self-contained excerpts from Kairo, a Kotlin Multiplatform and native-SwiftUI iOS/Android app. They show platform-craft (bridging native cryptography from common code) and UI-craft (a small, consistent SwiftUI design system) without exposing any product logic.

**Context:** see the project page at [../kairo.md](../kairo.md) for the full overview.

### Stack
- **Kotlin Multiplatform** (`commonMain` / `iosMain` / `androidMain`), `expect`/`actual`
- **iOS:** Kotlin/Native cinterop with `Security.framework` (Keychain), SwiftUI (`@Observable`, `@MainActor`, `ViewModifier`)
- **Android:** AndroidX Security Crypto (`EncryptedSharedPreferences`, `MasterKey`, AES-256)

### What each file shows
- **`SecureStorage.expect.kt`**: the single `expect` contract consumed by shared repositories: one tiny key/value interface for credentials, plus the biometric-capability enums. UI and data layers depend only on this, never on a platform.
- **`SecureStorageIos.kt`**: the iOS `actual`: Keychain access via cinterop. Builds Core Foundation query dictionaries with `CFDictionaryCreate` over the `Security.framework` `CFString` constants, handles `NSData` to/from `ByteArray` marshalling, `memScoped` result pointers, delete-before-add for overwrite semantics, and `AfterFirstUnlockThisDeviceOnly` accessibility.
- **`SecureStorageAndroid.kt`**: the Android `actual`: `EncryptedSharedPreferences` backed by an AES-256 `MasterKey`, built once and reused via `lazy`, with a one-time context init from `Application.onCreate()`.
- **`KairoDesignSystem.swift`**: a slice of the SwiftUI design system: a `KairoButton` with four styles, loading/disabled states and style-aware haptics, plus card `ViewModifier`s. Minimal token stubs (spacing/typography/colors) are inlined so the file reads standalone.

### Deliberately omitted
- All repositories, use cases, and DI wiring that consume `SecureStorage`, that is, the actual app/domain logic.
- The biometric `actual` implementations and any auth/session flow.
- Backend (Ktor) auth, payments/Stripe, and storage routes; all server-side business rules and alert generation.
- Every secret, key, token, endpoint set, and any real customer/business data. Service identifiers and brand color values are illustrative only.

_© 2026 Edoardo Caciolo, all rights reserved. Portfolio excerpt shared to demonstrate engineering; not licensed for reuse. Full source is private._
