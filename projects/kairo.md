# Kairo

> A multi-tenant gym-management platform with a Kotlin backend and native iOS and Android apps, covering member access, bookings, subscriptions, locker tracking, and AI-assisted workout coaching.

## Overview

Kairo is a multi-tenant gym-management system for fitness clubs and their members. A single Kotlin backend serves native iOS and Android clients that share business logic through a Kotlin Multiplatform core. Members use the apps to enter the gym with a rotating access code, book classes and equipment slots, manage subscriptions and medical certificates, track personal locker contents, and receive AI-generated workout plans that adapt to their personal health data. The platform is a monorepo currently at an early beta stage.

## Highlights

- **Subscription-gated gym access** using short-lived, rotating access tokens, with check-in/check-out events recorded for each member.
- **Secure member authentication** built on token-based sessions and industry-standard password hashing, with credentials backed by hardware-secure storage on each platform.
- **Class and resource booking** against per-gym schedules, with live availability tracking and push notifications on booking events.
- **Subscriptions and payments** via Stripe, including plan management, verified payment-event handling, and member payment history.
- **AI workout coaching** that tailors plans to each member's goals, level, health conditions, and the gym's current occupancy, with a deterministic fallback so members always receive a usable plan even when the AI service is unavailable.
- **On-device plan adaptation** on iOS that scales workout intensity against the member's recent recovery and health signals, degrading gracefully to rule-based logic when needed.
- **Smart locker tracking** that lets members catalog locker contents through their lifecycle and surfaces timely reminders for items left too long.
- **Medical certificate management** with secure cloud file storage and expiry tracking.
- **Real-time messaging and live updates** over a persistent connection between clients and backend.
- **Cross-device experiences** including iOS widgets, Live Activities, a watchOS companion, Siri intents, Android home-screen widgets, and NFC access.
- **Offline-first clients** that back reads with a local database synchronized to the backend, so the apps stay usable without connectivity.

## Tech Stack

| Layer | Technologies |
| --- | --- |
| Languages | Kotlin, Swift |
| Backend framework | Ktor (Netty engine) |
| Shared core | Kotlin Multiplatform, Ktor Client, kotlinx (serialization, coroutines, datetime), Koin, Kermit |
| iOS | SwiftUI, HealthKit, CoreML, ActivityKit, WidgetKit, App Intents, watchOS companion |
| Android | Jetpack Compose, Material 3, Glance widgets, Health Connect, BiometricPrompt, ZXing, Coil, WorkManager |
| Data stores | PostgreSQL (Exposed ORM, HikariCP), Redis (Lettuce), SQLDelight (client-local) |
| Auth & security | JWT, bcrypt, Android Keystore / iOS Secure Enclave |
| Integrations | Anthropic Claude API, Stripe, Firebase Cloud Messaging, AWS S3 |
| Infra / DevOps | Docker, Docker Compose, GitHub Actions, Caddy |

## Status

Early beta. Active monorepo spanning a Ktor backend, a shared Kotlin Multiplatform core, and two native client apps, with unit test coverage across backend and clients.

Source code private and proprietary — review available on request.

---


## Code sample

A small, IP-safe excerpt is in [`kairo/`](./kairo/) — Kotlin Multiplatform secure-storage abstraction (Keychain + EncryptedSharedPreferences) and a SwiftUI design system

_© 2026 Edoardo Caciolo — all rights reserved. Proprietary and not open source; source code is private and available for review on request._
