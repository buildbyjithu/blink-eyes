# Blink Eyes

Double-blink at your webcam to take a full-screen screenshot and copy it
straight to the clipboard — no keyboard shortcut needed.

**Privacy-first and secure: everything runs entirely on your own machine.**
There are no network calls, no cloud processing, and no LLM or third-party
service involved anywhere in the pipeline. Webcam frames are read, analyzed
on-device with a local MediaPipe model, and discarded — nothing is streamed,
uploaded, or stored, and the app has no server component of any kind.

Runs quietly as a background menu-bar app.

**Platform support:** fully working on **macOS**. The core detection code
is cross-platform Python, and a Windows clipboard backend is implemented,
but Windows/Linux installers haven't been built or tested on real hardware
yet (see [Known limitations](#known-limitations)).

## How it works

A background thread reads webcam frames, runs MediaPipe's on-device
face-landmark model to compute the Eye Aspect Ratio (EAR — how open each
eye is) every frame, and watches for two blinks in quick succession. When
it sees that pattern, it grabs a full-screen screenshot and copies it to
the system clipboard.

At startup it briefly calibrates against *your* face and camera (look at
the camera normally for ~2 seconds) rather than using one fixed sensitivity
for everyone — this matters more than it sounds like it should, since the
raw EAR number varies a lot by camera, distance, and face shape.

## Installing (macOS)

**Download:** grab `Blink Eyes.dmg` or `Blink Eyes.pkg` from the
[latest release](https://github.com/buildbyjithu/blink-eyes/releases/latest) —
drag the `.app` from the DMG into `/Applications`, or double-click the
`.pkg` to run the installer.

Prefer to build it yourself instead? It's one script (see
[docs/BUILDING.md](docs/BUILDING.md) for details):

```
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-build.txt
./packaging/build_macos.sh
```

This produces `dist/Blink Eyes.dmg` and `dist/Blink Eyes.pkg` locally.

**These builds are unsigned** (no Apple Developer ID was used yet), and
macOS tags anything downloaded from a browser with a quarantine flag. On
first launch you'll get a **"'Blink Eyes' Not Opened — Apple could not
verify..."** dialog with only "Move to Trash" / "Done" (no "Open Anyway",
since recent macOS versions don't always show that button even via
right-click → Open).

The reliable fix: click **Done**, then open Terminal and run:

```
xattr -dr com.apple.quarantine "/Applications/Blink Eyes.app"
```

Then open the app normally from `/Applications`. If System Settings →
Privacy & Security *does* show an "Open Anyway" button for Blink Eyes
after the blocked attempt, that works too instead of the Terminal command.

Note this isn't a true one-time fix: macOS re-applies the quarantine flag
any time the app is freshly downloaded or re-copied out of the DMG/PKG, so
you'll need to repeat this after every update until the app is
code-signed and notarized with an Apple Developer ID.

Prefer running from source instead of installing? See
[Running from source](docs/BUILDING.md#running-from-source).

## Permissions (macOS)

Two separate, unrelated permissions are required. **Each distinct build**
(the installed app vs. running from source with plain `python3`) is a
different app identity to macOS and needs these granted separately.

- **Camera** — Blink Eyes requests this itself at startup, before the tray
  icon appears (up to a 30s wait for you to click Allow). If it's missed or
  the dialog doesn't appear, go to **System Settings → Privacy & Security →
  Camera**, enable it manually, and relaunch.
- **Screen Recording** — needed to actually take the screenshot. Blink Eyes
  registers itself in **System Settings → Privacy & Security → Screen
  Recording** at startup, but you must enable the toggle yourself. If
  screenshots come out black or don't copy at all, this is almost always
  why.

  Important: macOS caches this permission for the lifetime of the running
  process. Toggling the setting while Blink Eyes is still open does
  **nothing** — you must **Quit** it (from the tray menu) and relaunch
  after granting the permission.

## Usage

- The tray icon is **green** while actively watching for blinks, briefly
  flashes **blue** to confirm a trigger, and turns **grey** when paused.
- **Pause detection** in the tray menu stops watching (and releases the
  camera); click again to resume.
- **Quit** fully exits and releases the camera.
- Blink twice, at normal speed, in quick succession (like a fast
  "blink-blink," not two slow deliberate closes) to trigger a screenshot.
  Then paste (Cmd+V) into any app that accepts image data.

Camera sharing with video call apps (Meet, FaceTime, Zoom) generally works
fine — macOS lets multiple processes read the same camera in most setups —
so you can use Blink Eyes while on a call.

### Debug mode

Run from source with `python main.py --debug` to open a live preview window
showing your camera feed with the eye landmark points and the current EAR
number overlaid — useful for seeing exactly why a blink isn't registering.
Debug mode doesn't show the tray icon (OpenCV's preview window and pystray's
tray icon both need macOS's main thread, and can't share it, so debug mode
runs the detector directly instead of under the tray). Press Ctrl+C in the
terminal to quit.

### Logs

Since the installed app has no visible console, it also writes logs to a
file:

- macOS: `~/Library/Logs/blink-eyes.log`
- Windows: `%LOCALAPPDATA%\blink-eyes\blink-eyes.log`
- Linux: `~/.local/state/blink-eyes/blink-eyes.log`

Check this if something isn't working and you're not running with a
terminal attached.

## Tuning

All detection thresholds live in `blink_eyes/config.py`:

- `CALIBRATION_DURATION_SEC` / `EAR_CLOSED_RATIO` — at startup, Blink Eyes
  measures your baseline "eyes open" EAR for `CALIBRATION_DURATION_SEC`
  seconds, then treats eyes as closed once EAR drops below
  `EAR_CLOSED_RATIO` × that baseline (default 75%). If blinks aren't
  registering, or everyday eye movement is triggering false positives,
  this ratio is the first thing to adjust.
- `EAR_THRESHOLD_FALLBACK` — only used if calibration finds no face at all
  (e.g. you weren't in frame yet).
- `BLINK_MIN_DURATION_SEC` / `BLINK_MAX_DURATION_SEC` — a closed-eye period
  must last between these bounds to count as a real blink (rejects both
  frame noise and long deliberate eye-closures).
- `DOUBLE_BLINK_WINDOW_SEC` — max gap between two blinks to count as one
  double-blink gesture.
- `TRIGGER_COOLDOWN_SEC` — minimum time between triggers.

## Known limitations

- Best used in normal indoor lighting, facing the camera — low light or
  strong backlight can cause landmark jitter.
- Single face only (`num_faces=1`); if multiple faces are in frame, only
  one is tracked.
- Windows clipboard support is implemented (`blink_eyes/clipboard/windows.py`,
  via `pywin32`) but hasn't been run on real Windows hardware — the MSI
  build script (`packaging/build_windows.ps1`) is written but untested,
  since it requires Windows-only tooling (PyInstaller doesn't cross-compile,
  and WiX's `heat`/`candle`/`light` are Windows-only).
- Linux clipboard support is a documented stub (`blink_eyes/clipboard/linux.py`)
  — not implemented.

## Building from source / for developers

See [docs/BUILDING.md](docs/BUILDING.md) for running from source, project
layout, and how to build the macOS DMG/PKG and (on Windows) the MSI.

## License

Apache License 2.0 — see [LICENSE](LICENSE).
