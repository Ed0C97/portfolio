---
title: "Tay"
slug: "tay"
lang: "en"
oneLiner: "Native Swift 6 app that recognizes artworks and monuments on-device and anchors real-time AR experiences to them."
category: "AR & On-Device ML"
status: "Early development"
statusTone: "prototype"
featured: false
visible: true
order: 11
metrics:
  - value: "3 modes"
    label: "Wearable canvas, temporal AR and universal cultural guide"
  - value: "5 platforms"
    label: "iPhone, iPad, Vision Pro, Apple Watch and macOS"
stack: ["Swift 6", "SwiftUI", "ARKit", "RealityKit", "Core ML", "SwiftData", "Tuist 4"]
repo: "https://github.com/Ed0C97/portfolio/tree/main/projects/tay"
image: "/images/projects/tay.svg"
---

## The problem

A painting on a museum wall, a ruined temple, an artwork printed on a jacket: none of them can explain themselves. Audio guides follow fixed routes and numbered stops, and say nothing about the thing you actually happen to be standing in front of. Apps that recognize art in the cloud need a connection that museum basements and archaeological sites often lack, and they add a round trip between pointing the camera and getting an answer. Augmented reality has a gap of its own: AR frameworks anchor content to rigid geometry, so an experience pinned to a printed canvas breaks the moment that canvas is worn on a moving body, because cloth folds and deforms. And for merchandise that carries licensed artwork, there is no way to tie a digital experience to the genuine object rather than to any copy of the image.

## What I built

Tay is a native Swift 6 app for iPhone, iPad, Apple Vision Pro, Apple Watch and macOS. You point the camera at an artwork or a monument; the app identifies it directly on the device, without sending frames to a server, and starts an augmented-reality experience anchored to what you are looking at. There are three modes. The wearable canvas mode authenticates licensed printed artwork and spawns an AR character that lives on the canvas and reacts to its surroundings. The temporal mode overlays a historical reconstruction of a site, with a time slider to scrub between past and present while standing there. The universal cultural guide recognizes monuments and artworks and delivers AI narration, with a real-time voice conversation for questions. Around the camera sits the rest of the app: SwiftData persistence with CloudKit mirroring, widgets, Live Activities, App Intents, an App Clip, a watch app, a visionOS surface and a macOS dashboard.

![tay detail placeholder 1](/images/projects/tay-2.svg)

## How it works

Recognition runs on each camera frame through a pipeline: motion-stability gating decides when a frame is worth classifying, results are cached, a Core ML model classifies through Vision on the Apple Neural Engine, and a location-aware step confirms the match. Photorealistic 3D reconstructions are rendered with Gaussian Splatting. The non-obvious choice is non-rigid surface tracking: standard AR anchoring assumes rigid geometry, so to keep characters attached to a canvas worn on a body, the app tracks the deforming cloth with GPU-accelerated mesh deformation. Characters respond to ambient light, audio, motion, speech and gestures through environment listeners feeding a state machine; the voice loop is duplex, over a WebSocket. ML models ship bundled with the app and are updated through a signed, integrity-verified over-the-air manifest, with bundled-model fallback. The codebase is a Tuist-generated workspace of layered modules (TayCore, TayUI, TayML, TayAR, feature modules), compiled under Swift 6 complete strict concurrency with warnings treated as errors.

## Who it's for

Museums and archaeological sites that want a guide anchored to what the visitor is actually looking at, cultural tourism, and fashion or merchandise carrying licensed printed artwork. The status is stated plainly: early development, single author. The voice pipeline and the infrastructure are real; several recognition models are still placeholders. The repository builds through a GitHub Actions pipeline with unit, snapshot and Maestro end-to-end tests.

![tay detail placeholder 2](/images/projects/tay-3.svg)

## Limits and what I'd redo

The main limit is the gap between the shell and the core: the platform surfaces exist (phone, watch, Mac, Vision Pro, App Clip, widgets), but several of the recognition models they depend on are placeholders, and the app relies on non-public sibling repositories, so a clean clone does not run end to end. If I started again, I would take one mode, the cultural guide on iPhone, to a real model and real users before building the watch, Mac and Vision Pro surfaces around it.
