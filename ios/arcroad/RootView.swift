import SwiftUI

struct RootView: View {
    @EnvironmentObject var router: Router

    var body: some View {
        TabView(selection: $router.tab) {
            WebScreen(path: "index.html")
                .ignoresSafeArea(edges: .bottom)
                .background(Palette.bg)
                .tabItem { Label("arcroad", systemImage: "road.lanes") }
                .tag(Router.Tab.home)

            WebScreen(path: router.drivePlace == "S18" ? "drive/index.html" : "drive/index.html?place=\(router.drivePlace)")
                .id(router.drivePlace)
                .background(Palette.bg)
                .tabItem { Label("Drive it", systemImage: "car.rear.road.lane") }
                .tag(Router.Tab.drive)

            PlacesView()
                .tabItem { Label("Places", systemImage: "mappin.and.ellipse") }
                .tag(Router.Tab.places)

            RecordView()
                .tabItem { Label("Record", systemImage: "record.circle") }
                .tag(Router.Tab.record)

            AboutView()
                .tabItem { Label("About", systemImage: "info.circle") }
                .tag(Router.Tab.about)
        }
    }
}
