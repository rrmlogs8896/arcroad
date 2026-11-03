import SwiftUI

struct RecordView: View {
    @EnvironmentObject var router: Router
    @StateObject private var rec = Recorder()
    @State private var placeID: String = PlaceStore.all.first(where: { !$0.isDriven })?.id ?? "S18"
    private let places = PlaceStore.all

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 18) {
                    Text("Drive a crossing and measure it. Your phone records the distance and time from one side of the median to the other, and nothing leaves this iPhone unless you share the summary.")
                        .font(.subheadline).foregroundStyle(Palette.mute)

                    card {
                        Text("PLACE").font(.caption.monospaced()).foregroundStyle(Palette.mute)
                        Picker("Place", selection: $placeID) {
                            ForEach(places) { p in Text(p.isDriven ? "\(p.title) · driven" : p.title).tag(p.id) }
                        }
                        .pickerStyle(.menu).disabled(rec.recording)
                        if let p = PlaceStore.place(placeID) {
                            Text("\(Int(p.straight.rounded())) m straight across. Start on one side; finish when you are on the other.")
                                .font(.footnote).foregroundStyle(Palette.mute)
                        }
                    }

                    card {
                        Label("Safety first", systemImage: "exclamationmark.triangle.fill").font(.subheadline.weight(.semibold)).foregroundStyle(Palette.soft)
                        Text("Press Start before you set off, then hand the phone to a passenger or leave it in a mount. Never handle the phone while you drive. Follow every traffic rule; arcroad measures the legal route, not a shortcut.")
                            .font(.footnote).foregroundStyle(Palette.fg)
                    }

                    if rec.recording { live }
                    controls
                    outcome
                }
                .padding(20)
            }
            .background(Palette.bg)
            .navigationTitle("Record a crossing")
        }
        .onAppear { if let id = router.recordPlace { placeID = id; router.recordPlace = nil }; rec.place = PlaceStore.place(placeID) }
        .onChange(of: placeID) { _, id in rec.place = PlaceStore.place(id) }
        .onChange(of: router.recordPlace) { _, id in if let id, !rec.recording { placeID = id; router.recordPlace = nil } }
    }

    private var live: some View {
        card {
            HStack(alignment: .firstTextBaseline) {
                Text(Fmt.metres(rec.metres)).font(.system(size: 44, weight: .semibold)).monospacedDigit().foregroundStyle(Palette.fg)
                Spacer()
                if let s = rec.started {
                    TimelineView(.periodic(from: s, by: 1)) { ctx in
                        Text(Fmt.duration(Int(ctx.date.timeIntervalSince(s)))).font(.title3.monospacedDigit()).foregroundStyle(Palette.mute)
                    }
                }
            }
            HStack(spacing: 14) {
                side("A", rec.reachedA); side("B", rec.reachedB)
                Spacer()
                if let a = rec.accuracy { Text("GPS ±\(Int(a)) m").font(.caption.monospaced()).foregroundStyle(Palette.mute) }
            }
        }
    }

    private func side(_ n: String, _ ok: Bool) -> some View {
        Label(ok ? "\(n) reached" : "\(n)", systemImage: ok ? "checkmark.circle.fill" : "circle")
            .font(.footnote.weight(.medium)).foregroundStyle(ok ? Palette.accent : Palette.mute)
    }

    @ViewBuilder private var controls: some View {
        if rec.denied {
            Text("Location is off for arcroad. Turn it on in Settings › arcroad › Location › While Using the App.")
                .font(.footnote).foregroundStyle(Palette.soft)
            Button("Open Settings") { if let u = URL(string: UIApplication.openSettingsURLString) { UIApplication.shared.open(u) } }
                .buttonStyle(.bordered)
        } else {
            Button {
                rec.recording ? rec.stop() : rec.start()
            } label: {
                Text(rec.recording ? "Stop and measure" : (rec.authorized ? "Start recording" : "Allow location and start"))
                    .font(.headline).frame(maxWidth: .infinity).padding(.vertical, 14)
            }
            .buttonStyle(.borderedProminent)
            .tint(rec.recording ? Color(red: 0.85, green: 0.25, blue: 0.2) : Palette.accent)
        }
    }

    @ViewBuilder private var outcome: some View {
        switch rec.outcome {
        case .none: EmptyView()
        case .notFound(let why):
            card {
                Text("No crossing found").font(.headline).foregroundStyle(Palette.fg)
                Text(why).font(.footnote).foregroundStyle(Palette.mute)
            }
        case .found(let r):
            card {
                Text("\(r.from) → \(r.to)").font(.caption.monospaced()).foregroundStyle(Palette.accent)
                Text("\(Fmt.metres(r.metres)) and \(Fmt.duration(r.seconds))").font(.title2.weight(.semibold)).foregroundStyle(Palette.fg)
                if let p = rec.place { Text("to cross \(Int(p.straight.rounded())) m.").font(.subheadline).foregroundStyle(Palette.mute) }
                Text("Your recording, measured on this iPhone. It is not an arcroad figure until we have checked it; send the summary to help.")
                    .font(.footnote).foregroundStyle(Palette.mute)
                let text = rec.summary(r)
                HStack {
                    ShareLink(item: text, subject: Text("arcroad crossing"), message: Text(text)) { Label("Share summary", systemImage: "square.and.arrow.up") }
                        .buttonStyle(.borderedProminent)
                    if let mail = URL(string: "mailto:hello@arcroad.org?subject=arcroad%20crossing&body=\(text.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? "")") {
                        Link(destination: mail) { Label("Email arcroad", systemImage: "envelope") }.buttonStyle(.bordered)
                    }
                }
                Text("hello@arcroad.org").font(.caption).foregroundStyle(Palette.mute).textSelection(.enabled)
            }
        }
    }

    private func card<C: View>(@ViewBuilder _ c: () -> C) -> some View {
        VStack(alignment: .leading, spacing: 8, content: c)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(16)
            .background(Palette.surface, in: RoundedRectangle(cornerRadius: 16))
            .overlay(RoundedRectangle(cornerRadius: 16).stroke(Palette.line, lineWidth: 1))
    }
}
