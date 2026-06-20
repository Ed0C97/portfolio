// Portfolio excerpt, adapted.

#if os(iOS)

@preconcurrency import AVFoundation
import CoreVideo
import Foundation
import QuartzCore

// MARK: - Stubs (real types live elsewhere in the app)

/// Gyro-backed motion tracker. The monitor reads only `rotationRMS`.
public protocol CameraMotionTracker: AnyObject {
    /// RMS of recent device rotation; higher means shakier.
    var rotationRMS: Double { get }
}

public enum CameraLightLevel: Sendable { case dark, low, normal, overexposed }
public enum CameraStability: Sendable { case steady, slightShake, moving }
public enum CameraFocusState: Sendable { case adjusting, locked, unfocused }
public enum CameraLensCondition: Sendable { case clear, suspect }

public enum CameraQualityIssue: Sendable {
    case lowLight, overexposed, motionBlur, focusAdjusting, lensObstruction

    /// Rank for which issue to surface in the UI.
    var priorityScore: Int {
        switch self {
        case .lensObstruction: return 100
        case .lowLight, .overexposed: return 70
        case .focusAdjusting: return 50
        case .motionBlur: return 40
        }
    }

    /// Weight in the aggregate severity score.
    var severityContribution: Int {
        switch self {
        case .lensObstruction: return 60
        case .lowLight, .overexposed: return 45
        case .motionBlur: return 30
        case .focusAdjusting: return 20
        }
    }
}

public struct CameraQualityReport: Sendable {
    public let light: CameraLightLevel
    public let stability: CameraStability
    public let focus: CameraFocusState
    public let lens: CameraLensCondition
    public let severity: Int            // 0...100
    public let primaryIssue: CameraQualityIssue?
    public let timestamp: TimeInterval

    public static let initial = CameraQualityReport(
        light: .normal, stability: .steady, focus: .locked, lens: .clear,
        severity: 0, primaryIssue: nil, timestamp: 0
    )
}

// MARK: - Monitor

/// Fuse frame buffers, the motion tracker, and the AVCaptureDevice into a report at ~2 Hz.
///
/// Focus/exposure come from the device via KVO; pixels come through observe(pixelBuffer:).
@MainActor
@Observable
public final class CameraQualityMonitor {
    /// Latest snapshot, replaced on every analysis (~2 Hz).
    public private(set) var report: CameraQualityReport = .initial

    // MARK: - Dependencies

    @ObservationIgnored
    private weak var motionTracker: CameraMotionTracker?

    // MARK: - KVO

    @ObservationIgnored private var focusObservation: NSKeyValueObservation?
    @ObservationIgnored private var exposureObservation: NSKeyValueObservation?
    @ObservationIgnored private var isAdjustingFocus = false
    @ObservationIgnored private var isAdjustingExposure = false

    // MARK: - Throttling

    private var lastAnalyzedAt: TimeInterval = 0
    /// Min gap between pixel-buffer analyses; 0.5 s is 2 Hz.
    private let minAnalysisInterval: TimeInterval

    // MARK: - Persistence trackers (used to derive stable issues)

    /// when all three obstruction indices first went out of bounds, or nil
    private var lensObstructionSuspectSince: TimeInterval?
    /// when sharpness first dropped below the unfocused threshold, or nil
    private var unfocusedSince: TimeInterval?

    // MARK: - Thresholds (calibratable)

    private let lightDarkCutoff: Double = 30           // mean Y < dark -> .dark
    private let lightLowCutoff: Double = 60            // mean Y < low  -> .low
    private let lightOverexposedCutoff: Double = 220   // mean Y > this -> .overexposed
    private let stabilitySteadyCutoff: Double = 0.05   // rotation RMS below -> .steady
    private let stabilityShakeCutoff: Double = 0.20    // rotation RMS below -> .slightShake
    private let sharpnessUnfocusedCutoff: Double = 100 // Laplacian variance below -> blur
    private let lumVarianceUniformCutoff: Double = 200 // luma variance below -> flat frame
    private let satStdDevUniformCutoff: Double = 10    // saturation stddev below -> flat color
    private let lensObstructionPersistenceSeconds: TimeInterval = 3.0
    private let unfocusedPersistenceSeconds: TimeInterval = 1.0

    public init(
        motionTracker: CameraMotionTracker? = nil,
        minAnalysisInterval: TimeInterval = 1.0 / TayCameraMonitorTuning.defaultFrequencyHz
    ) {
        self.motionTracker = motionTracker
        self.minAnalysisInterval = minAnalysisInterval
    }

    deinit {
        focusObservation?.invalidate()
        exposureObservation?.invalidate()
    }

    // MARK: - Binding

    /// Observe the device's isAdjustingFocus/isAdjustingExposure via KVO.
    ///
    /// KVO fires on AVFoundation's thread, so the callbacks hop to the main actor.
    public func bind(device: AVCaptureDevice) {
        unbind()
        focusObservation = device.observe(\.isAdjustingFocus, options: [.initial, .new]) {
            [weak self] _, change in
            let value = change.newValue ?? false
            Task { @MainActor in self?.isAdjustingFocus = value }
        }
        exposureObservation = device.observe(\.isAdjustingExposure, options: [.initial, .new]) {
            [weak self] _, change in
            let value = change.newValue ?? false
            Task { @MainActor in self?.isAdjustingExposure = value }
        }
    }

    /// Drop the KVO observers. Idempotent.
    public func unbind() {
        focusObservation?.invalidate()
        exposureObservation?.invalidate()
        focusObservation = nil
        exposureObservation = nil
    }

    // MARK: - Frame ingestion

    /// Analyze a frame, throttled internally, so it's safe to call per frame.
    public func observe(pixelBuffer: CVPixelBuffer) {
        let now = CACurrentMediaTime()
        guard now - lastAnalyzedAt >= minAnalysisInterval else { return }
        lastAnalyzedAt = now

        let metrics = CameraFrameAnalysis.analyze(buffer: pixelBuffer)
        recomputeReport(metrics: metrics, now: now)
    }

    /// Recompute from pre-built metrics, bypassing the analyzer. For tests and previews.
    public func injectMetrics(_ metrics: CameraFrameMetrics, at time: TimeInterval = CACurrentMediaTime()) {
        recomputeReport(metrics: metrics, now: time)
    }

    // MARK: - Recompute

    private func recomputeReport(metrics: CameraFrameMetrics, now: TimeInterval) {
        let light = classifyLight(meanLuminance: metrics.meanLuminance)
        let stability = classifyStability()
        let sharpnessLow = metrics.laplacianVariance < sharpnessUnfocusedCutoff
        let focus = classifyFocus(sharpnessLow: sharpnessLow, now: now)
        let lens = classifyLens(metrics: metrics, focus: focus, now: now)

        let issues = collectIssues(light: light, stability: stability, focus: focus, lens: lens)
        let primary = issues.max(by: { $0.priorityScore < $1.priorityScore })
        let severity = aggregateSeverity(issues: issues)

        report = CameraQualityReport(
            light: light, stability: stability, focus: focus, lens: lens,
            severity: severity, primaryIssue: primary, timestamp: now
        )
    }

    // MARK: - Classifiers

    private func classifyLight(meanLuminance: Double) -> CameraLightLevel {
        if meanLuminance < lightDarkCutoff { return .dark }
        if meanLuminance < lightLowCutoff { return .low }
        if meanLuminance > lightOverexposedCutoff { return .overexposed }
        return .normal
    }

    private func classifyStability() -> CameraStability {
        let rms = motionTracker?.rotationRMS ?? 0
        if rms < stabilitySteadyCutoff { return .steady }
        if rms < stabilityShakeCutoff { return .slightShake }
        return .moving
    }

    private func classifyFocus(sharpnessLow: Bool, now: TimeInterval) -> CameraFocusState {
        // low sharpness is expected while AF reconverges, so wait for AF to settle and
        // sharpness to stay low past the persistence window before calling it unfocused
        if isAdjustingFocus { return .adjusting }
        if sharpnessLow {
            if unfocusedSince == nil { unfocusedSince = now }
            if now - (unfocusedSince ?? now) >= unfocusedPersistenceSeconds {
                return .unfocused
            }
            return .locked
        } else {
            unfocusedSince = nil
            return .locked
        }
    }

    private func classifyLens(
        metrics: CameraFrameMetrics,
        focus: CameraFocusState,
        now: TimeInterval
    ) -> CameraLensCondition {
        // obstruction needs uniform luma AND uniform saturation AND unstable focus held >= 3s;
        // the conjunction plus the hold rules out plain surfaces and one-off AF hunts
        let lumUniform = metrics.luminanceVariance < lumVarianceUniformCutoff
        let satUniform = metrics.saturationStdDev < satStdDevUniformCutoff
        let focusUnstable = focus == .adjusting || focus == .unfocused
        let suspectNow = lumUniform && satUniform && focusUnstable

        if suspectNow {
            if lensObstructionSuspectSince == nil { lensObstructionSuspectSince = now }
            if now - (lensObstructionSuspectSince ?? now) >= lensObstructionPersistenceSeconds {
                return .suspect
            }
            return .clear
        } else {
            lensObstructionSuspectSince = nil
            return .clear
        }
    }

    private func collectIssues(
        light: CameraLightLevel,
        stability: CameraStability,
        focus: CameraFocusState,
        lens: CameraLensCondition
    ) -> [CameraQualityIssue] {
        var issues: [CameraQualityIssue] = []
        switch light {
        case .dark, .low: issues.append(.lowLight)
        case .overexposed: issues.append(.overexposed)
        case .normal: break
        }
        if stability != .steady { issues.append(.motionBlur) }
        if focus == .adjusting { issues.append(.focusAdjusting) }
        if lens == .suspect { issues.append(.lensObstruction) }
        return issues
    }

    private func aggregateSeverity(issues: [CameraQualityIssue]) -> Int {
        // dominant issue's contribution plus half of each remaining one, clamped to 100;
        // grows with issue count without blowing past the cap
        guard !issues.isEmpty else { return 0 }
        let sorted = issues.sorted { $0.severityContribution > $1.severityContribution }
        let dominant = sorted[0].severityContribution
        let tail = sorted.dropFirst().reduce(0) { $0 + $1.severityContribution / 2 }
        return min(100, dominant + tail)
    }
}

// MARK: - Tuning constants

public enum TayCameraMonitorTuning {
    /// Analysis frequency (Hz); override per-monitor via minAnalysisInterval.
    public static let defaultFrequencyHz: Double = 2.0
}

// MARK: - Frame metrics

/// Raw metrics from a single BGRA frame. Public for tests, previews, and logging.
public struct CameraFrameMetrics: Equatable, Sendable {
    public let meanLuminance: Double      // 0...255
    public let luminanceVariance: Double
    public let laplacianVariance: Double  // sharpness proxy
    public let saturationStdDev: Double   // stddev of an HSV-like S channel

    public init(
        meanLuminance: Double,
        luminanceVariance: Double,
        laplacianVariance: Double,
        saturationStdDev: Double
    ) {
        self.meanLuminance = meanLuminance
        self.luminanceVariance = luminanceVariance
        self.laplacianVariance = laplacianVariance
        self.saturationStdDev = saturationStdDev
    }

    public static let neutral = CameraFrameMetrics(
        meanLuminance: 128, luminanceVariance: 1500,
        laplacianVariance: 800, saturationStdDev: 40
    )
}

// MARK: - Frame analyzer

/// Single-pass BGRA analyzer: strided downsample (default 8), all four metrics in one loop.
///
/// ~250 us on iPhone 13 at hd1280x720.
public enum CameraFrameAnalysis {
    /// Analyze a BGRA buffer. Locks read-only for the duration.
    public static func analyze(buffer: CVPixelBuffer, stride: Int = 8) -> CameraFrameMetrics {
        CVPixelBufferLockBaseAddress(buffer, .readOnly)
        defer { CVPixelBufferUnlockBaseAddress(buffer, .readOnly) }

        let width = CVPixelBufferGetWidth(buffer)
        let height = CVPixelBufferGetHeight(buffer)
        let bytesPerRow = CVPixelBufferGetBytesPerRow(buffer)
        guard let base = CVPixelBufferGetBaseAddress(buffer) else { return .neutral }
        let ptr = base.assumingMemoryBound(to: UInt8.self)

        var sumY = 0.0, sumY2 = 0.0
        var sumSat = 0.0, sumSat2 = 0.0
        var sumLap2 = 0.0
        var count = 0.0

        // Rec. 601 luma weights
        @inline(__always) func luma(_ off: Int) -> Double {
            0.299 * Double(ptr[off + 2]) + 0.587 * Double(ptr[off + 1]) + 0.114 * Double(ptr[off])
        }

        var y = stride
        while y < height - stride {
            var x = stride
            while x < width - stride {
                let off = y * bytesPerRow + x * 4
                let b = Double(ptr[off]), g = Double(ptr[off + 1]), r = Double(ptr[off + 2])
                let lum = 0.299 * r + 0.587 * g + 0.114 * b

                let mx = max(r, max(g, b)), mn = min(r, min(g, b))
                let sat = mx > 0 ? (mx - mn) / mx * 255 : 0

                // approximate Laplacian on luma: 4*center - (L + R + U + D)
                let yL = luma(y * bytesPerRow + (x - stride) * 4)
                let yR = luma(y * bytesPerRow + (x + stride) * 4)
                let yU = luma((y - stride) * bytesPerRow + x * 4)
                let yD = luma((y + stride) * bytesPerRow + x * 4)
                let lap = 4 * lum - yL - yR - yU - yD

                sumY += lum;  sumY2 += lum * lum
                sumSat += sat; sumSat2 += sat * sat
                sumLap2 += lap * lap
                count += 1

                x += stride
            }
            y += stride
        }

        guard count > 0 else { return .neutral }

        let meanY = sumY / count
        let varY = max(0, (sumY2 / count) - (meanY * meanY))
        let meanSat = sumSat / count
        let varSat = max(0, (sumSat2 / count) - (meanSat * meanSat))
        // mean(L) ~= 0 for high-frequency signal, so E[L^2] is the variance
        let lapVar = sumLap2 / count

        return CameraFrameMetrics(
            meanLuminance: meanY,
            luminanceVariance: varY,
            laplacianVariance: lapVar,
            saturationStdDev: varSat.squareRoot()
        )
    }
}

#endif // os(iOS)
