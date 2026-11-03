import CoreLocation
import UIKit

/// Records one crossing with the phone's GPS, on this iPhone only.
/// The track lives in memory while the screen is open; it is never written to disk or sent anywhere.
/// Scoring mirrors pipeline/groundtruth.py: a pass must come within END_REACH (10 m) of one side and later
/// of the other, within 30 minutes, with no gap in the samples longer than 15 s.
final class Recorder: NSObject, ObservableObject, CLLocationManagerDelegate {
    struct Fix { let c: CLLocationCoordinate2D; let t: Date }
    struct Result {
        let from: String, to: String      // "A" / "B"
        let metres: Double, seconds: Int
        let date: Date
    }
    enum Outcome { case none, found(Result), notFound(String) }

    static let endReach = 10.0, maxPass = 1800.0, maxGap = 15.0, maxAccuracy = 30.0

    @Published private(set) var recording = false
    @Published private(set) var authorized = false
    @Published private(set) var denied = false
    @Published private(set) var metres = 0.0
    @Published private(set) var started: Date?
    @Published private(set) var accuracy: Double?
    @Published private(set) var reachedA = false
    @Published private(set) var reachedB = false
    @Published private(set) var outcome: Outcome = .none

    private let lm = CLLocationManager()
    private var fixes: [Fix] = []
    var place: Place?

    override init() {
        super.init()
        lm.delegate = self
        lm.desiredAccuracy = kCLLocationAccuracyBest
        lm.activityType = .automotiveNavigation
        lm.distanceFilter = kCLDistanceFilterNone
        lm.pausesLocationUpdatesAutomatically = false
        update(lm.authorizationStatus)
    }

    func start() {
        guard place != nil else { return }
        if lm.authorizationStatus == .notDetermined { lm.requestWhenInUseAuthorization(); return }
        guard authorized else { return }
        fixes = []; metres = 0; reachedA = false; reachedB = false; outcome = .none
        started = Date(); recording = true
        UIApplication.shared.isIdleTimerDisabled = true
        lm.startUpdatingLocation()
    }

    func stop() {
        lm.stopUpdatingLocation()
        UIApplication.shared.isIdleTimerDisabled = false
        recording = false
        outcome = score()
        fixes = []                       // the track is dropped as soon as it is scored
    }

    func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) { update(manager.authorizationStatus) }

    private func update(_ s: CLAuthorizationStatus) {
        authorized = s == .authorizedWhenInUse || s == .authorizedAlways
        denied = s == .denied || s == .restricted
    }

    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard recording, let place else { return }
        for l in locations where l.horizontalAccuracy >= 0 && l.horizontalAccuracy <= Self.maxAccuracy {
            if let last = fixes.last {
                metres += CLLocation(latitude: last.c.latitude, longitude: last.c.longitude).distance(from: l)
            }
            fixes.append(Fix(c: l.coordinate, t: l.timestamp))
            if Self.dist(l.coordinate, place.a) <= Self.endReach { reachedA = true }
            if Self.dist(l.coordinate, place.b) <= Self.endReach { reachedB = true }
        }
        accuracy = locations.last?.horizontalAccuracy
    }

    func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {}

    static func dist(_ p: CLLocationCoordinate2D, _ q: CLLocationCoordinate2D) -> Double {
        CLLocation(latitude: p.latitude, longitude: p.longitude).distance(from: CLLocation(latitude: q.latitude, longitude: q.longitude))
    }

    /// The last time the track reaches one side, paired with the next time it reaches the other.
    private func score() -> Outcome {
        guard let place, fixes.count > 1 else { return .notFound("Too few GPS fixes to measure a crossing.") }
        var best: Result?
        for (fromP, toP, f, t) in [(place.a, place.b, "A", "B"), (place.b, place.a, "B", "A")] {
            var lastFrom: Int?
            for (j, x) in fixes.enumerated() {
                if Self.dist(x.c, fromP) <= Self.endReach { lastFrom = j; continue }
                guard let i = lastFrom, Self.dist(x.c, toP) <= Self.endReach else { continue }
                let secs = x.t.timeIntervalSince(fixes[i].t)
                lastFrom = nil
                guard secs > 0, secs <= Self.maxPass else { continue }
                var m = 0.0, gap = 0.0
                for k in i..<j {
                    m += Self.dist(fixes[k].c, fixes[k + 1].c)
                    gap = max(gap, fixes[k + 1].t.timeIntervalSince(fixes[k].t))
                }
                guard gap <= Self.maxGap else { continue }
                guard m > place.straight else { continue }   // shorter than the straight line is not a crossing
                let r = Result(from: f, to: t, metres: m, seconds: Int(secs.rounded()), date: fixes[i].t)
                if best == nil || r.date > best!.date { best = r }
            }
        }
        if let best { return .found(best) }
        if !reachedA || !reachedB {
            return .notFound("The recording did not come within \(Int(Self.endReach)) m of both sides (A \(reachedA ? "reached" : "not reached"), B \(reachedB ? "reached" : "not reached")).")
        }
        return .notFound("Both sides were reached, but not as one continuous crossing (a GPS gap of over 15 s, or more than 30 minutes).")
    }

    func summary(_ r: Result) -> String {
        guard let place else { return "" }
        let d = DateFormatter(); d.dateFormat = "d MMM yyyy, HH:mm"; d.locale = Locale(identifier: "en_IN")
        let v = Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "1.0"
        return """
        arcroad crossing · \(place.id)\(place.area.isEmpty ? "" : " (\(place.area))")
        \(r.from) → \(r.to): \(Int(r.metres.rounded())) m in \(r.seconds) s
        Straight across: \(Int(place.straight.rounded())) m
        Recorded \(d.string(from: r.date)) on an iPhone (phone GPS, arcroad app \(v))
        Summary only: the GPS track stayed on the phone and was deleted after scoring.
        """
    }
}
