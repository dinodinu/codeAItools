import SwiftUI

struct MenuBarView: View {
    @EnvironmentObject var manager: CaffeinateManager

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {

            // ── Header ──────────────────────────────────────────────────────
            HStack(spacing: 12) {
                ZStack {
                    Circle()
                        .fill(manager.isActive
                              ? Color.brown.opacity(0.15)
                              : Color.secondary.opacity(0.08))
                        .frame(width: 44, height: 44)
                    Image(systemName: manager.isActive
                          ? "cup.and.saucer.fill"
                          : "moon.zzz.fill")
                        .font(.title2)
                        .foregroundStyle(manager.isActive ? Color.brown : Color.secondary)
                }

                VStack(alignment: .leading, spacing: 2) {
                    Text("Filter Coffee")
                        .font(.headline)
                    Text(manager.isActive ? "Mac is staying awake" : "Mac may sleep normally")
                        .font(.caption)
                        .foregroundStyle(manager.isActive ? Color.green : Color.secondary)
                }

                Spacer()

                if manager.isActive {
                    Text(manager.elapsedLabel)
                        .font(.caption)
                        .monospacedDigit()
                        .foregroundStyle(Color.secondary)
                        .padding(.trailing, 4)
                }
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 12)

            Divider()

            // ── Options ─────────────────────────────────────────────────────
            VStack(alignment: .leading, spacing: 2) {
                Text("PREVENT")
                    .font(.caption2)
                    .foregroundStyle(Color.secondary)
                    .padding(.horizontal, 16)
                    .padding(.top, 10)
                    .padding(.bottom, 4)

                optionToggle("Display sleep", isOn: $manager.preventDisplaySleep)
                optionToggle("System sleep  (AC power only)", isOn: $manager.preventSystemSleep)
                optionToggle("Disk idle sleep", isOn: $manager.preventDiskSleep)
            }
            .disabled(manager.isActive)
            .padding(.bottom, 8)

            Divider()

            // ── Timer ────────────────────────────────────────────────────────
            VStack(alignment: .leading, spacing: 6) {
                Toggle(isOn: $manager.useTimer) {
                    Text("Auto-stop after \(manager.timerLabel)")
                        .font(.callout)
                }
                .padding(.horizontal, 16)

                if manager.useTimer {
                    HStack(spacing: 8) {
                        Slider(value: $manager.timerMinutes, in: 5...480, step: 5)
                        Text(manager.timerLabel)
                            .font(.caption)
                            .monospacedDigit()
                            .foregroundStyle(Color.secondary)
                            .frame(width: 44, alignment: .trailing)
                    }
                    .padding(.horizontal, 16)
                }
            }
            .disabled(manager.isActive)
            .padding(.vertical, 10)

            Divider()

            // ── Wait-for-Process (-w) ─────────────────────────────────────
            VStack(alignment: .leading, spacing: 6) {
                Toggle(isOn: $manager.waitForProcess) {
                    Text("Stop when a process exits  (-w)")
                        .font(.callout)
                }
                .padding(.horizontal, 16)
                .onChange(of: manager.waitForProcess) { on in
                    if on { manager.refreshProcessList() }
                }

                if manager.waitForProcess {
                    HStack(spacing: 6) {
                        Picker(selection: $manager.selectedPID) {
                            Text("Select a process…").tag(Optional<Int32>.none)
                            ForEach(manager.runningProcesses) { proc in
                                Text(proc.label).tag(Optional(proc.pid))
                            }
                        } label: { EmptyView() }
                        .labelsHidden()
                        .frame(maxWidth: .infinity)

                        Button {
                            manager.refreshProcessList()
                        } label: {
                            Image(systemName: "arrow.clockwise")
                        }
                        .buttonStyle(.plain)
                        .foregroundStyle(Color.secondary)
                        .help("Refresh process list")
                    }
                    .padding(.horizontal, 16)
                }
            }
            .disabled(manager.isActive)
            .padding(.vertical, 10)

            Divider()

            // ── Action ───────────────────────────────────────────────────────
            VStack(spacing: 6) {
                Button(action: { manager.toggle() }) {
                    Label(
                        manager.isActive ? "Stop — Let Mac Sleep" : "Keep Mac Awake",
                        systemImage: manager.isActive ? "stop.fill" : "play.fill"
                    )
                    .frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
                .tint(manager.isActive ? .red : .green)
                .controlSize(.large)
                .keyboardShortcut(.return, modifiers: [])
                .disabled(manager.waitForProcess && manager.selectedPID == nil && !manager.isActive)

                Button("Quit Filter Coffee") {
                    NSApplication.shared.terminate(nil)
                }
                .buttonStyle(.plain)
                .font(.caption)
                .foregroundStyle(Color.secondary)
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
        }
        .frame(width: 320)
    }

    private func optionToggle(_ label: String, isOn: Binding<Bool>) -> some View {
        Toggle(isOn: isOn) {
            Text(label)
                .font(.callout)
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 3)
    }
}
