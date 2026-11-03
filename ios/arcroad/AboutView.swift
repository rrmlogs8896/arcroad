import SwiftUI

struct AboutView: View {
    private var version: String {
        let i = Bundle.main.infoDictionary
        return "\(i?["CFBundleShortVersionString"] as? String ?? "1.0") (\(i?["CFBundleVersion"] as? String ?? "1"))"
    }

    var body: some View {
        NavigationStack {
            List {
                Section {
                    Text("arcroad measures what crossing your own road costs: the detour a divided road forces on people who live beside it. Every figure comes from open map data and is checked by driving it. A place you can see across the median can be more than a kilometre away by road.")
                        .font(.subheadline).foregroundStyle(Palette.fg)
                }
                Section("Your privacy") {
                    row("No account, no tracking", "The app has no sign-in, no analytics, no advertising and no third-party code. It stores nothing about you.")
                    row("Location only while recording", "When you record a crossing, GPS is used on this iPhone to measure it. The track is kept in memory, deleted once scored, and never sent. Only a summary you choose to share leaves the phone.")
                    row("Works offline", "The site is built into the app. The globe's base map loads from OpenFreeMap when you open it, which sees your IP address like any website.")
                }
                Section("How it works") {
                    link("Every pass we drove", "https://arcroad.org/field/")
                    link("Help, corrections and contact", "https://arcroad.org/help/")
                    link("Open data", "https://arcroad.org/data/")
                }
                Section("Contact") {
                    link("hello@arcroad.org", "mailto:hello@arcroad.org")
                    Text("hello@arcroad.org").font(.footnote).foregroundStyle(Palette.mute).textSelection(.enabled)
                }
                Section {
                    Text("Map data © OpenStreetMap contributors (ODbL). Measurements by arcroad (ODbL). Land outlines from Natural Earth (public domain). Three.js (MIT). Inter and JetBrains Mono (SIL Open Font License). arcroad is independent and not affiliated with any government or company.")
                        .font(.footnote).foregroundStyle(Palette.mute)
                    Text("Version \(version)").font(.footnote.monospaced()).foregroundStyle(Palette.mute)
                }
            }
            .scrollContentBackground(.hidden)
            .background(Palette.bg)
            .navigationTitle("About")
        }
    }

    private func row(_ t: String, _ d: String) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(t).font(.subheadline.weight(.semibold)).foregroundStyle(Palette.fg)
            Text(d).font(.footnote).foregroundStyle(Palette.mute)
        }
        .padding(.vertical, 2)
    }

    private func link(_ t: String, _ u: String) -> some View {
        Link(destination: URL(string: u)!) {
            HStack { Text(t).foregroundStyle(Palette.fg); Spacer(); Image(systemName: "arrow.up.right").font(.footnote).foregroundStyle(Palette.mute) }
        }
    }
}
