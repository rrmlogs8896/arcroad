import SwiftUI

struct PlacesView: View {
    @EnvironmentObject var router: Router
    private let places = PlaceStore.all

    var body: some View {
        NavigationStack {
            List {
                Section {
                    ForEach(places.filter(\.isDriven)) { p in
                        Button { router.drive(p.id) } label: { DrivenRow(place: p) }
                            .listRowBackground(Palette.surface)
                    }
                } header: {
                    Text("Driven by arcroad")
                } footer: {
                    Text("Tap a place to ride its detour in 3D, on the clock we measured.")
                }

                Section {
                    ForEach(places.filter { !$0.isDriven }) { p in
                        HStack {
                            VStack(alignment: .leading, spacing: 3) {
                                Text(p.title).font(.body.weight(.medium)).foregroundStyle(Palette.fg)
                                Text("\(Int(p.straight.rounded())) m straight across · not driven yet")
                                    .font(.footnote).foregroundStyle(Palette.mute)
                            }
                            Spacer()
                            Button("Record it") { router.record(p.id) }
                                .buttonStyle(.bordered).controlSize(.small)
                        }
                        .listRowBackground(Palette.surface)
                    }
                } header: {
                    Text("Not driven yet")
                } footer: {
                    Text("A place gets a detour figure only after someone drives it. Until then, arcroad publishes the straight line and nothing else.")
                }
            }
            .scrollContentBackground(.hidden)
            .background(Palette.bg)
            .navigationTitle("Places")
        }
    }
}

private struct DrivenRow: View {
    let place: Place
    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text(place.title).font(.body.weight(.semibold)).foregroundStyle(Palette.fg)
                Spacer()
                Image(systemName: "chevron.right").font(.footnote).foregroundStyle(Palette.mute)
            }
            if !place.road.isEmpty { Text(place.road).font(.footnote).foregroundStyle(Palette.mute) }
            ForEach(place.driven.keys.sorted(), id: \.self) { k in
                if let d = place.driven[k] {
                    Text("\(Fmt.metres(d.m)) and \(Fmt.duration(d.s)) to cross \(Int(place.straight.rounded())) m · \(Fmt.date(d.date))")
                        .font(.subheadline).foregroundStyle(Palette.soft)
                }
            }
        }
        .padding(.vertical, 4)
    }
}
