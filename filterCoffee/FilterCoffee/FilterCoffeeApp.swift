import SwiftUI

@main
struct FilterCoffeeApp: App {
    @StateObject private var manager = CaffeinateManager()

    var body: some Scene {
        MenuBarExtra {
            MenuBarView()
                .environmentObject(manager)
        } label: {
            Image(systemName: manager.isActive ? "cup.and.saucer.fill" : "moon.zzz.fill")
                .symbolRenderingMode(.hierarchical)
        }
        .menuBarExtraStyle(.window)
    }
}
