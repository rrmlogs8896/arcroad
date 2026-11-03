import Foundation
import CoreLocation

/// A place from the bundled site's globe data (web/globe/data/places.json), named from web/kit/pairs.js.
/// Only driven passes carry a published detour; for every other place the app shows the straight line alone.
struct Place: Identifiable, Hashable {
    let id: String
    let a: CLLocationCoordinate2D
    let b: CLLocationCoordinate2D
    let straight: Double
    let driven: [String: Pass]          // "ab" / "ba"
    let road: String
    let area: String

    struct Pass: Hashable { let m: Double; let s: Int; let date: String }

    var isDriven: Bool { !driven.isEmpty }
    var title: String { area.isEmpty ? id : "\(id) · \(area)" }

    static func == (l: Place, r: Place) -> Bool { l.id == r.id }
    func hash(into h: inout Hasher) { h.combine(id) }
}

enum PlaceStore {
    private struct File: Decodable { let spots: [Spot] }
    private struct Spot: Decodable {
        let id: String; let a: [Double]; let b: [Double]; let straight: Double
        let driven: [String: D]?
        struct D: Decodable { let m: Double; let s: Int; let date: String }
    }
    private struct Pair: Decodable { let road: String?; let area: String? }

    static let all: [Place] = load()

    static func place(_ id: String?) -> Place? { all.first { $0.id == id } }

    private static func load() -> [Place] {
        guard let data = try? Data(contentsOf: Site.file("globe/data/places.json")),
              let file = try? JSONDecoder().decode(File.self, from: data) else { return [] }
        let names = pairNames()
        return file.spots.compactMap { s in
            guard s.a.count == 2, s.b.count == 2 else { return nil }
            var passes: [String: Place.Pass] = [:]
            s.driven?.forEach { passes[$0.key] = Place.Pass(m: $0.value.m, s: $0.value.s, date: $0.value.date) }
            let n = names[s.id]
            return Place(id: s.id, a: CLLocationCoordinate2D(latitude: s.a[1], longitude: s.a[0]),
                         b: CLLocationCoordinate2D(latitude: s.b[1], longitude: s.b[0]),
                         straight: s.straight, driven: passes, road: n?.road ?? "", area: n?.area ?? "")
        }
        .sorted { ($0.isDriven ? 0 : 1, $0.id) < ($1.isDriven ? 0 : 1, $1.id) }
    }

    /// pairs.js is "window.ARCROAD_PAIRS = { ...JSON... };" after a comment.
    private static func pairNames() -> [String: Pair] {
        guard let text = try? String(contentsOf: Site.file("kit/pairs.js"), encoding: .utf8),
              let eq = text.range(of: "ARCROAD_PAIRS = "),
              let end = text.range(of: "};", options: .backwards) else { return [:] }
        let json = String(text[eq.upperBound..<end.lowerBound]) + "}"
        return (try? JSONDecoder().decode([String: Pair].self, from: Data(json.utf8))) ?? [:]
    }
}

enum Fmt {
    static func metres(_ m: Double) -> String {
        m >= 1000 ? String(format: "%.2f km", m / 1000) : "\(Int(m.rounded())) m"
    }
    static func duration(_ s: Int) -> String {
        let m = s / 60, x = s % 60
        return m > 0 ? "\(m) min \(x) s" : "\(x) s"
    }
    static func date(_ iso: String) -> String {
        let f = DateFormatter(); f.dateFormat = "yyyy-MM-dd"; f.locale = Locale(identifier: "en_IN")
        guard let d = f.date(from: iso) else { return iso }
        let o = DateFormatter(); o.dateFormat = "d MMM yyyy"; o.locale = Locale(identifier: "en_IN")
        return o.string(from: d)
    }
}
