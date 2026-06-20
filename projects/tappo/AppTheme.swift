//
//  AppTheme.swift
//  Tappo. Portfolio excerpt, adapted.
//  Sendable value type. One dark palette defines a theme; the light variant is derived.
//

import SwiftUI

struct AppTheme: Identifiable, Equatable, Sendable {
    let id: Int
    let name: String
    let background: Color
    let text: Color
    let accent: Color
    let secondaryAccent: Color
    let iconName: String
    let isLightMode: Bool

    init(id: Int, name: String, background: Color, text: Color,
         accent: Color, secondaryAccent: Color, iconName: String,
         isLightMode: Bool = false) {
        self.id = id
        self.name = name
        self.background = background
        self.text = text
        self.accent = accent
        self.secondaryAccent = secondaryAccent
        self.iconName = iconName
        self.isLightMode = isLightMode
    }

    // MARK: - Gradient Helpers

    var accentGradient: LinearGradient {
        LinearGradient(colors: [accent, secondaryAccent],
                       startPoint: .topLeading, endPoint: .bottomTrailing)
    }

    var backgroundGradient: LinearGradient {
        LinearGradient(colors: [background, background.opacity(0.8)],
                       startPoint: .top, endPoint: .bottom)
    }

    // MARK: - Light Variant

    /// Reuse the accent pair so light and dark stay in sync; only the surface colors swap.
    var lightVariant: AppTheme {
        AppTheme(id: id, name: name,
                 background: Color(white: 0.96),
                 text: Color(white: 0.1),
                 accent: accent, secondaryAccent: secondaryAccent,
                 iconName: iconName, isLightMode: true)
    }

    // MARK: - Contrast

    var contrastingTextColor: Color {
        isLightMode ? Color(white: 0.1) : Color(white: 0.95)
    }

    var secondaryTextColor: Color {
        isLightMode ? Color(white: 0.35) : Color(white: 0.65)
    }

    // MARK: - Palettes (two of the full set shown here)

    static let allThemes: [AppTheme] = [
        AppTheme(
            id: 0, name: "Industrial",
            background: Color(red: 0.08, green: 0.08, blue: 0.10),
            text: Color(red: 0.94, green: 0.94, blue: 0.92),
            accent: Color(red: 1.0, green: 0.28, blue: 0.0),
            secondaryAccent: .gray,
            iconName: "hammer.fill"
        ),
        AppTheme(
            id: 1, name: "Deep Sea",
            background: Color(red: 0.0, green: 0.1, blue: 0.15),
            text: Color(red: 0.9, green: 0.95, blue: 1.0),
            accent: Color(red: 0.0, green: 1.0, blue: 0.8),
            secondaryAccent: Color(red: 0.0, green: 0.4, blue: 1.0),
            iconName: "water.waves"
        )
    ]

    /// Return the theme at index, falling back to the first when out of range.
    static func theme(at index: Int, isLightMode: Bool = false) -> AppTheme {
        let base = allThemes.indices.contains(index) ? allThemes[index] : allThemes[0]
        return isLightMode ? base.lightVariant : base
    }
}
