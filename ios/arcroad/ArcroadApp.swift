import SwiftUI

@main
struct ArcroadApp: App {
    @StateObject private var router = Router()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(router)
                .preferredColorScheme(.dark)
                .tint(Palette.accent)
        }
    }
}

/// Which tab is showing, and which place the recorder should start on.
final class Router: ObservableObject {
    enum Tab: Hashable { case home, drive, places, record, about }
    @Published var tab: Tab = .home
    @Published var recordPlace: String?
    @Published var drivePlace: String = "S18"

    func record(_ id: String) { recordPlace = id; tab = .record }
    func drive(_ id: String) { drivePlace = id; tab = .drive }
}

enum Palette {
    static let bg = Color(red: 0.043, green: 0.051, blue: 0.063)        // #0B0D10
    static let surface = Color(red: 0.067, green: 0.078, blue: 0.102)   // #11141A
    static let line = Color(red: 0.110, green: 0.125, blue: 0.149)      // #1C2026
    static let fg = Color(red: 0.902, green: 0.910, blue: 0.922)        // #E6E8EB
    static let mute = Color(red: 0.545, green: 0.576, blue: 0.612)      // #8B939C
    static let accent = Color(red: 0.886, green: 0.455, blue: 0.231)    // #E2743B
    static let soft = Color(red: 0.941, green: 0.761, blue: 0.627)      // #F0C2A0
}
