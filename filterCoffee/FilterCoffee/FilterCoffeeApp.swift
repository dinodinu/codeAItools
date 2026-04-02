import SwiftUI

@main
struct FilterCoffeeApp: App {
    @StateObject private var manager = CaffeinateManager()

    var body: some Scene {
        MenuBarExtra {
            MenuBarView()
                .environmentObject(manager)
        } label: {
            Image("FilterCoffeeGlyph")
                .renderingMode(.template)
                .resizable()
                .aspectRatio(contentMode: .fit)
                .frame(width: 18, height: 18)
                .opacity(manager.isActive ? 1.0 : 0.65)
        }
        .menuBarExtraStyle(.window)
    }
}
