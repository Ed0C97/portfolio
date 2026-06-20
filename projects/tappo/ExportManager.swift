//
//  ExportManager.swift
//  Tappo - portfolio excerpt, adapted.
//  One Project model out to three formats: CSV, a hand-laid-out PDF, and a
//  SwiftUI card snapshotted to UIImage. (Snapshot card view trimmed.)
//

import SwiftUI
import UniformTypeIdentifiers

@MainActor
final class ExportManager {

    // MARK: - CSV Export

    static func generateCSV(for project: Project) -> String {
        var csv = "Date,Time,Value,Note\n"
        let dateFormatter = DateFormatter(); dateFormatter.dateFormat = "yyyy-MM-dd"
        let timeFormatter = DateFormatter(); timeFormatter.dateFormat = "HH:mm:ss"

        for entry in project.history.sorted(by: { $0.timestamp < $1.timestamp }) {
            let date = dateFormatter.string(from: entry.timestamp)
            let time = timeFormatter.string(from: entry.timestamp)
            // commas in a note would split the row; swap them out rather than quote-escape
            let note = entry.note?.replacingOccurrences(of: ",", with: ";") ?? ""
            csv += "\(date),\(time),\(entry.value),\(note)\n"
        }
        return csv
    }

    static func csvFileURL(for project: Project) -> URL? {
        let csv = generateCSV(for: project)
        let name = (project.name.isEmpty ? "project" : project.name)
            .replacingOccurrences(of: " ", with: "_")
        let tempURL = FileManager.default.temporaryDirectory
            .appendingPathComponent("\(name)_export.csv")
        do {
            try csv.write(to: tempURL, atomically: true, encoding: .utf8)
            return tempURL
        } catch {
            return nil
        }
    }

    // MARK: - Snapshot Image

    /// Render the card to a UIImage at device scale so it stays sharp in the share sheet.
    static func generateSnapshot(for project: Project, theme: AppTheme) -> UIImage {
        let renderer = ImageRenderer(content: SnapshotCardView(project: project, theme: theme))
        renderer.scale = UIScreen.main.scale
        return renderer.uiImage ?? UIImage()
    }

    // MARK: - PDF Export

    static func generatePDF(for project: Project, theme: AppTheme) -> URL? {
        // US Letter at 72dpi
        let pageWidth: CGFloat = 612, pageHeight: CGFloat = 792, margin: CGFloat = 50
        let pdfRenderer = UIGraphicsPDFRenderer(
            bounds: CGRect(x: 0, y: 0, width: pageWidth, height: pageHeight)
        )

        let calendar = Calendar.current
        // floor at 1 day so a same-day project doesn't divide by zero
        let daysActive = max(1, calendar.dateComponents([.day], from: project.createdAt, to: Date()).day ?? 1)
        let avgPerDay = Double(project.history.count) / Double(daysActive)

        let data = pdfRenderer.pdfData { context in
            context.beginPage()
            // y is the running baseline; every draw advances it
            var y: CGFloat = margin
            let accent = UIColor(theme.accent)

            NSAttributedString(string: project.name.isEmpty ? "Project Report" : project.name, attributes: [
                .font: UIFont.systemFont(ofSize: 28, weight: .bold),
                .foregroundColor: UIColor.label
            ]).draw(at: CGPoint(x: margin, y: y))
            y += 40

            let divider = UIBezierPath()
            divider.move(to: CGPoint(x: margin, y: y))
            divider.addLine(to: CGPoint(x: pageWidth - margin, y: y))
            accent.setStroke(); divider.lineWidth = 2; divider.stroke()
            y += 24

            let countStr = NSAttributedString(string: "\(project.count)", attributes: [
                .font: UIFont.systemFont(ofSize: 60, weight: .heavy),
                .foregroundColor: accent
            ])
            let countSize = countStr.size()
            // center horizontally against the measured glyph width
            countStr.draw(at: CGPoint(x: (pageWidth - countSize.width) / 2, y: y))
            y += countSize.height + 30

            // left label, value flush right on the same baseline
            func drawStat(_ label: String, _ value: String) {
                NSAttributedString(string: label, attributes: [
                    .font: UIFont.systemFont(ofSize: 14),
                    .foregroundColor: UIColor.secondaryLabel
                ]).draw(at: CGPoint(x: margin, y: y))
                let valStr = NSAttributedString(string: value, attributes: [
                    .font: UIFont.systemFont(ofSize: 14, weight: .semibold),
                    .foregroundColor: UIColor.label
                ])
                valStr.draw(at: CGPoint(x: pageWidth - margin - valStr.size().width, y: y))
                y += 24
            }

            let section: [NSAttributedString.Key: Any] = [
                .font: UIFont.systemFont(ofSize: 16, weight: .bold),
                .foregroundColor: accent
            ]
            NSAttributedString(string: "Overview", attributes: section)
                .draw(at: CGPoint(x: margin, y: y)); y += 28
            drawStat("Days Active", "\(daysActive)")
            drawStat("Total Actions", "\(project.history.count)")
            drawStat("Average Per Day", String(format: "%.1f", avgPerDay))
            drawStat("Current Streak", "\(project.streak) days")
            y += 10

            NSAttributedString(string: "Progress", attributes: section)
                .draw(at: CGPoint(x: margin, y: y)); y += 28
            let pct = Int(project.progressPercentage * 100)
            drawStat("Current / Target", "\(project.currentUsers) / \(project.targetUsers) (\(pct)%)")

            // track first, then the accent fill clipped to progress
            let barWidth = pageWidth - 2 * margin, barHeight: CGFloat = 10
            UIColor.systemGray5.setFill()
            UIBezierPath(roundedRect: CGRect(x: margin, y: y, width: barWidth, height: barHeight),
                         cornerRadius: 5).fill()
            accent.setFill()
            UIBezierPath(roundedRect: CGRect(x: margin, y: y, width: barWidth * project.progressPercentage, height: barHeight),
                         cornerRadius: 5).fill()
            y += barHeight + 24

            if !project.milestones.isEmpty {
                NSAttributedString(string: "Milestones", attributes: section)
                    .draw(at: CGPoint(x: margin, y: y)); y += 28
                for milestone in project.milestones.sorted(by: { $0.targetValue < $1.targetValue }) {
                    // filled check vs hollow circle marks reached state
                    let mark = milestone.isReached ? "\u{2713}" : "\u{25CB}"
                    NSAttributedString(string: "\(mark)  \(milestone.title) \u{2014} target: \(milestone.targetValue)", attributes: [
                        .font: UIFont.systemFont(ofSize: 13, weight: milestone.isReached ? .semibold : .regular),
                        .foregroundColor: milestone.isReached ? UIColor.systemGreen : UIColor.secondaryLabel
                    ]).draw(at: CGPoint(x: margin + 10, y: y))
                    y += 22
                }
            }
        }

        let name = (project.name.isEmpty ? "project" : project.name)
            .replacingOccurrences(of: " ", with: "_")
        let tempURL = FileManager.default.temporaryDirectory
            .appendingPathComponent("\(name)_report.pdf")
        do {
            try data.write(to: tempURL)
            return tempURL
        } catch {
            return nil
        }
    }
}

// wraps the CSV file URL so it can go straight into a ShareLink
struct CSVDocument: Transferable {
    let url: URL
    static var transferRepresentation: some TransferRepresentation {
        FileRepresentation(exportedContentType: .commaSeparatedText) { doc in
            SentTransferredFile(doc.url)
        }
    }
}
