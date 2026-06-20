// Portfolio excerpt, adapted.
import SwiftUI

// MARK: - Design tokens (stubbed so this excerpt stands alone)

enum Spacing {
    static let sm: CGFloat = 8
    static let base: CGFloat = 16
}

extension Font {
    static let kairoBody: Font = .system(size: 17)
    static let kairoBodyBold: Font = .system(size: 17, weight: .semibold)
}

extension Color {
    static let kairoPrimary = Color(red: 0.36, green: 0.30, blue: 0.96) // placeholder, not the real brand value
    static let kairoError = Color(red: 0.94, green: 0.27, blue: 0.27)   // placeholder, not the real brand value
}

// MARK: - Button

struct KairoButton: View {
    enum Style: Sendable {
        case primary
        case secondary
        case ghost
        case destructive
    }

    let title: String
    let style: Style
    let icon: String?
    let isLoading: Bool
    let isDisabled: Bool
    let action: @MainActor () -> Void

    init(
        _ title: String,
        style: Style = .primary,
        icon: String? = nil,
        isLoading: Bool = false,
        isDisabled: Bool = false,
        action: @MainActor @escaping () -> Void
    ) {
        self.title = title
        self.style = style
        self.icon = icon
        self.isLoading = isLoading
        self.isDisabled = isDisabled
        self.action = action
    }

    var body: some View {
        Button {
            triggerHaptic()
            action()
        } label: {
            HStack(spacing: Spacing.sm) {
                if isLoading {
                    ProgressView()
                        .tint(foregroundColor)
                } else {
                    if let icon {
                        Image(systemName: icon)
                            .font(.kairoBody)
                    }
                    Text(title)
                        .font(.kairoBodyBold)
                }
            }
            .frame(maxWidth: .infinity)
            .padding(.horizontal, 20)
            .padding(.vertical, 14)
            .background(backgroundColor)
            .foregroundStyle(foregroundColor)
            .clipShape(RoundedRectangle(cornerRadius: 14))
        }
        .disabled(isLoading || isDisabled)
        .opacity(isDisabled ? 0.5 : 1.0)
    }

    private var backgroundColor: Color {
        switch style {
        case .primary: .kairoPrimary
        case .secondary: .kairoPrimary.opacity(0.1)
        case .ghost: .clear
        case .destructive: .kairoError
        }
    }

    private var foregroundColor: Color {
        switch style {
        case .primary, .destructive: .white
        case .secondary, .ghost: .kairoPrimary
        }
    }

    @MainActor
    private func triggerHaptic() {
        // heavier styles carry more weight, so hit harder on the tap
        let intensity: UIImpactFeedbackGenerator.FeedbackStyle = switch style {
        case .primary, .destructive: .medium
        case .secondary, .ghost: .light
        }
        UIImpactFeedbackGenerator(style: intensity).impactOccurred()
    }
}

// MARK: - Card modifiers

struct KairoCardModifier: ViewModifier {
    func body(content: Content) -> some View {
        content
            .padding(Spacing.base)
            .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 20))
            .shadow(color: .black.opacity(0.06), radius: 16, x: 0, y: 6)
    }
}

struct KairoGlassCardModifier: ViewModifier {
    func body(content: Content) -> some View {
        content
            .padding(Spacing.base)
            .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 20))
            .shadow(color: .black.opacity(0.06), radius: 16, x: 0, y: 6)
    }
}

extension View {
    func kairoCard() -> some View { modifier(KairoCardModifier()) }
    func kairoGlassCard() -> some View { modifier(KairoGlassCardModifier()) }
}
