import Foundation
import AppKit

struct RunningProcess: Identifiable, Hashable {
    let pid: Int32
    let name: String
    var id: Int32 { pid }
    var label: String { "\(name)  (\(pid))" }
}

class CaffeinateManager: ObservableObject {
    @Published var isActive = false
    @Published var preventDisplaySleep = true
    @Published var preventSystemSleep = false
    @Published var preventDiskSleep = false
    @Published var useTimer = false
    @Published var timerMinutes: Double = 60
    @Published var elapsedSeconds: Int = 0

    // -w support
    @Published var waitForProcess = false
    @Published var runningProcesses: [RunningProcess] = []
    @Published var selectedPID: Int32? = nil

    private var process: Process?
    private var elapsedTimer: Timer?

    var timerLabel: String {
        let mins = Int(timerMinutes)
        if mins < 60 { return "\(mins) min" }
        let h = mins / 60
        let m = mins % 60
        return m == 0 ? "\(h) hr" : "\(h)h \(m)m"
    }

    var elapsedLabel: String {
        let h = elapsedSeconds / 3600
        let m = (elapsedSeconds % 3600) / 60
        let s = elapsedSeconds % 60
        return h > 0
            ? String(format: "%d:%02d:%02d", h, m, s)
            : String(format: "%02d:%02d", m, s)
    }

    init() {
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(handleAppTerminate),
            name: NSApplication.willTerminateNotification,
            object: nil
        )
    }

    func refreshProcessList() {
        let ws = NSWorkspace.shared
        let apps = ws.runningApplications
        runningProcesses = apps
            .filter { $0.processIdentifier > 0 && $0.activationPolicy != .prohibited }
            .map { RunningProcess(pid: $0.processIdentifier,
                                  name: $0.localizedName ?? $0.bundleIdentifier ?? "<unknown>") }
            .sorted { $0.name.localizedCaseInsensitiveCompare($1.name) == .orderedAscending }
        // Deselect if the previously selected process no longer exists
        if let sel = selectedPID, !runningProcesses.contains(where: { $0.pid == sel }) {
            selectedPID = nil
        }
    }

    @objc private func handleAppTerminate() {
        stop()
    }

    deinit {
        stop()
    }

    func toggle() {
        isActive ? stop() : start()
    }

    func start() {
        guard process == nil else { return }

        var args: [String] = []
        if preventDisplaySleep { args.append("-d") }
        if preventDiskSleep    { args.append("-m") }
        if preventSystemSleep  { args.append("-s") }
        if waitForProcess, let pid = selectedPID { args += ["-w", "\(pid)"] }
        // Fall back to idle-sleep prevention when nothing else is selected
        if args.isEmpty        { args.append("-i") }
        if useTimer            { args += ["-t", "\(Int(timerMinutes) * 60)"] }

        let p = Process()
        p.executableURL = URL(fileURLWithPath: "/usr/bin/caffeinate")
        p.arguments = args
        p.terminationHandler = { [weak self] _ in
            DispatchQueue.main.async {
                self?.isActive = false
                self?.process = nil
                self?.stopElapsedTimer()
            }
        }

        do {
            try p.run()
            process = p
            isActive = true
            elapsedSeconds = 0
            startElapsedTimer()
        } catch {
            print("Filter Coffee — failed to launch caffeinate: \(error)")
        }
    }

    func stop() {
        process?.terminate()
        process = nil
        isActive = false
        stopElapsedTimer()
    }

    private func startElapsedTimer() {
        let t = Timer(timeInterval: 1.0, repeats: true) { [weak self] _ in
            self?.elapsedSeconds += 1
        }
        RunLoop.main.add(t, forMode: .common)
        elapsedTimer = t
    }

    private func stopElapsedTimer() {
        elapsedTimer?.invalidate()
        elapsedTimer = nil
    }
}
