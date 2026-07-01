// CharacterAnimator.swift - portfolio excerpt, adapted.
// Loads a USDZ character and drives RealityKit animations from a
// character finite-state-machine's transitions.

import Combine
import Foundation
import os.log
import RealityKit

// MARK: - Stubs (the real character FSM lives elsewhere in the app)

/// High-level character state. Each case names a clip in the USDZ; that mapping
/// is the contract between the FSM and the asset.
public enum CharacterState {
    case idle, greeting, talking, pointing

    var animationClipName: String {
        switch self {
        case .idle:     return "Idle_Breathing"
        case .greeting: return "Greeting_Wave"
        case .talking:  return "Talk_Loop"
        case .pointing: return "Point_Forward"
        }
    }
}

@MainActor
public final class CharacterAnimator: ObservableObject {
    private let logger = Logger(subsystem: "com.tay.app", category: "CharacterAnimator")
    private var entity: Entity?
    private var availableAnimations: [String: AnimationResource] = [:]
    private var currentPlayback: AnimationPlaybackController?

    /// Clip name currently playing.
    @Published public private(set) var currentClip: String = ""

    public init() {}

    public func load(from url: URL, anchor: AnchorEntity) async throws {
        let loaded = try await Entity(contentsOf: url)
        anchor.addChild(loaded)
        entity = loaded
        cacheAnimations(in: loaded)
        let animationCount = availableAnimations.count
        logger.notice(
            "character_loaded: \(url.lastPathComponent, privacy: .public), animations=\(animationCount)"
        )
    }

    private func cacheAnimations(in entity: Entity) {
        availableAnimations.removeAll(keepingCapacity: true)
        for animation in entity.availableAnimations {
            // key off the asset's own names; the enum mapping is a convenience layer on top
            let name = animation.name ?? "anim_\(availableAnimations.count)"
            availableAnimations[name] = animation
        }
    }

    public func play(state: CharacterState) {
        guard let entity, let resource = animation(for: state) else { return }
        currentPlayback?.stop()
        currentPlayback = entity.playAnimation(
            resource,
            transitionDuration: 0.25,
            startsPaused: false
        )
        currentClip = state.animationClipName
    }

    /// Cross-fade to a named clip, falling back to Idle_Breathing or any cached clip if absent.
    ///
    /// - Parameters:
    ///   - clipName: clip name in the loaded USDZ.
    ///   - crossfade: blend duration in seconds.
    ///   - lookAt: optional world-space point to turn the rig toward.
    public func transition(to clipName: String, crossfade: TimeInterval, lookAt: SIMD3<Float>?) {
        guard let entity else { return }
        let resource = availableAnimations[clipName]
            ?? availableAnimations["Idle_Breathing"]
            ?? availableAnimations.values.first
        guard let resource else {
            logger.warning("transition_no_animation: \(clipName, privacy: .public)")
            return
        }
        currentPlayback?.stop()
        currentPlayback = entity.playAnimation(
            resource,
            transitionDuration: crossfade,
            startsPaused: false
        )
        currentClip = clipName
        if let lookAt {
            entity.look(at: lookAt, from: entity.position(relativeTo: nil), relativeTo: nil)
        }
    }

    public func stop() {
        currentPlayback?.stop()
        currentPlayback = nil
    }

    public func place(at position: SIMD3<Float>) {
        entity?.position = position
    }

    private func animation(for state: CharacterState) -> AnimationResource? {
        let clipName = state.animationClipName
        if let direct = availableAnimations[clipName] { return direct }
        return availableAnimations["Idle_Breathing"]
            ?? availableAnimations.values.first
    }
}
