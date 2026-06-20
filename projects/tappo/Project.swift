//
//  Project.swift
//  Tappo - portfolio excerpt, adapted.
//  SwiftData domain model. Stored relationships cascade-delete; the computed
//  properties below are read-only and exist for the views.
//

import Foundation
import SwiftData

// MARK: - Project Model

@Model
final class Project {
    var id: UUID
    var name: String
    var count: Int
    var currentUsers: Int
    var targetUsers: Int
    var targetDate: Date?
    var createdAt: Date
    var updatedAt: Date
    var iconName: String
    var stepSize: Int

    // cascade so deleting a project also clears its history
    @Relationship(deleteRule: .cascade, inverse: \CounterEntry.project)
    var history: [CounterEntry] = []

    @Relationship(deleteRule: .cascade, inverse: \Milestone.project)
    var milestones: [Milestone] = []

    init(
        name: String = "",
        count: Int = 0,
        currentUsers: Int = 0,
        targetUsers: Int = 100,
        targetDate: Date? = Date().addingTimeInterval(86400 * 7),
        iconName: String = "number.circle.fill",
        stepSize: Int = 1
    ) {
        self.id = UUID()
        self.name = name
        self.count = count
        self.currentUsers = currentUsers
        self.targetUsers = targetUsers
        self.targetDate = targetDate
        self.createdAt = Date()
        self.updatedAt = Date()
        self.iconName = iconName
        self.stepSize = stepSize
    }

    // MARK: - Computed Properties

    var daysRemaining: Int? {
        guard let targetDate else { return nil }
        let calendar = Calendar.current
        let startOfToday = calendar.startOfDay(for: Date())
        let startOfTarget = calendar.startOfDay(for: targetDate)
        return calendar.dateComponents([.day], from: startOfToday, to: startOfTarget).day ?? 0
    }

    var isOverdue: Bool {
        guard let days = daysRemaining else { return false }
        return days < 0
    }

    /// Return progress toward the target, clamped to [0, 1].
    var progressPercentage: Double {
        guard targetUsers > 0 else { return 0 }
        return min(Double(currentUsers) / Double(targetUsers), 1.0)
    }

    var todayTotal: Int {
        let calendar = Calendar.current
        let startOfToday = calendar.startOfDay(for: Date())
        return history
            .filter { calendar.startOfDay(for: $0.timestamp) == startOfToday }
            .reduce(0) { $0 + $1.value }
    }

    /// Return the run of consecutive days ending today that each have an entry.
    var streak: Int {
        let calendar = Calendar.current
        var currentDate = calendar.startOfDay(for: Date())
        var streakCount = 0

        let entriesByDay = Dictionary(grouping: history) { entry in
            calendar.startOfDay(for: entry.timestamp)
        }

        while entriesByDay[currentDate] != nil {
            streakCount += 1
            guard let previousDay = calendar.date(byAdding: .day, value: -1, to: currentDate) else { break }
            currentDate = previousDay
        }

        return streakCount
    }
}

// MARK: - Counter Entry (history)

@Model
final class CounterEntry {
    var id: UUID
    var value: Int
    var timestamp: Date
    var note: String?
    var project: Project?

    init(value: Int, note: String? = nil) {
        self.id = UUID()
        self.value = value
        self.timestamp = Date()
        self.note = note
    }
}

// MARK: - Milestone

@Model
final class Milestone {
    var id: UUID
    var title: String
    var targetValue: Int
    var isReached: Bool
    var reachedAt: Date?
    var project: Project?

    init(title: String, targetValue: Int) {
        self.id = UUID()
        self.title = title
        self.targetValue = targetValue
        self.isReached = false
        self.reachedAt = nil
    }
}
