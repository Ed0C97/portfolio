# Tay

> A native Apple-platform app that recognizes physical artworks and monuments through the camera and anchors real-time augmented-reality experiences on top of them.

## Overview

Tay is a multi-platform Swift application spanning iPhone, iPad, Apple Vision Pro, Apple Watch, and macOS. A user points the device camera at art, on a museum wall, a historical site, or a branded physical object, and the app identifies it on-device and activates an AR experience anchored to it. It targets museums, cultural tourism, and fashion or merchandise carrying licensed printed artwork. The product unifies three experiences: a wearable canvas mode that authenticates licensed artwork and spawns AR characters, a temporal mode that overlays historical reconstructions of a site, and a universal cultural guide that recognizes monuments and delivers AI-generated narration. It is an early-stage, single-author project under active development.

## Highlights

- **On-device visual recognition**: identifies artworks and monuments from a live camera feed entirely on-device, fusing the visual match with location context to produce fast, stable results without a network round-trip.
- **Authenticated canvas experiences**: verifies that printed artwork is genuinely licensed before unlocking its AR content, so only authorized physical canvases activate the experience.
- **Environment-reactive AR characters**: AR characters respond to ambient light, sound, motion, on-scene events, speech, and gestures, producing believable in-context behavior.
- **Tracking on deforming surfaces**: anchors AR content accurately to cloth and other non-rigid, moving surfaces, not just flat rigid targets.
- **Temporal reconstructions**: overlays historical reconstructions of a site with an interactive control to move between past and present states while on location.
- **Photorealistic 3D rendering**: renders and streams high-fidelity 3D reconstructions, with robust tracking of characters and particles across real-world motion and occlusion.
- **AI narration and live voice**: delivers AI-generated narration with spatial audio and a real-time, two-way conversational voice experience.
- **Offline-first data layer**: mirrors catalog, scan, favorite, and share data across devices and resolves experiences offline, so the app remains useful without connectivity.
- **Camera coaching**: detects poor capture conditions (motion blur, low light, lens smudges, depth issues) and guides the user toward a usable shot.
- **Securely updatable ML assets**: ships models in-app and can update them over the air through a verified, signed delivery path, with bundled fallbacks.
- **Broad surface coverage**: App Clip, home-screen and Lock Screen widgets, Live Activities, App Intents and Shortcuts, Spotlight indexing, plus dedicated macOS, watchOS, and visionOS surfaces.
- **Full-stack, not just the app**: owned end-to-end: a FastAPI backend on AWS (ECS Fargate), supporting microservices for licensed-artwork authentication and image-embedding similarity, and Terraform-managed infrastructure across dev, staging, and production.

## Tech Stack

| Category | Technology |
|----------|------------|
| Languages | Swift 6, Metal, Python, Ruby, Shell |
| UI | SwiftUI, Observation, TipKit, WidgetKit, App Intents |
| AR and 3D | ARKit, RealityKit, Gaussian Splatting, USDZ |
| Machine learning | Core ML, Vision, Apple Neural Engine, Apple Foundation Models |
| Audio and speech | AVFoundation, PHASE spatial audio, Speech, real-time WebSocket voice |
| Data | SwiftData with CloudKit-mirrored container |
| Networking | URLSession, WebSocket client |
| Build and tooling | Tuist, mise, SwiftLint, SwiftFormat, Fastlane, Maestro |
| Observability | Sentry, PostHog, GrowthBook |
| Testing | XCTest, swift-snapshot-testing |
| CI | GitHub Actions on macOS runners with Xcode 26 |
| Backend | FastAPI, Python, AWS (ECS Fargate), Application Load Balancer |
| Infrastructure | Terraform (AWS), multi-environment (dev / staging / production) |

## Architecture

The app is organized as a layered set of Swift frameworks, foundation services (models, camera, audio, persistence, networking), capability layers (recognition, AR and rendering, environment-reactive sessions, narration, conversation), and user-facing feature modules, consumed by per-platform app targets. Inference runs on-device via the Apple Neural Engine, with separate backend services handling real-time conversation and signed model delivery. Engineering decisions emphasize Swift 6 strict concurrency, protocol-oriented services with mock and real implementations for testability, and a multi-platform module structure that scopes each framework to the OSes it supports.

## Status

Early-stage development; single-author project under active development, with several ML models and backend integrations in progress. Source code private and proprietary (all rights reserved), code review available on request.

---


## Code sample

A small, IP-safe excerpt is in [`tay/`](./tay/): a real-time camera-quality engine (Swift/AVFoundation), a RealityKit animation driver, and a per-user LLM rate limiter (Python/FastAPI), supporting craft with the recognition/anti-counterfeit moat deliberately excluded.

_© 2026 Edoardo Caciolo, all rights reserved. Proprietary and not open source; source code is private and available for review on request._
