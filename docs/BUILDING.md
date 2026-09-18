# Building Blink Eyes

## Project layout

```
blink-eyes/
├── main.py                     # Entrypoint: permission checks, wires tray + detector
├── blink_eyes/
│   ├── config.py                # All tunable thresholds
│   ├── ear.py                    # Eye Aspect Ratio math + landmark indices
│   ├── camera_auth.py             # macOS main-thread camera-permission warm-up
│   ├── blink_detector.py          # Camera loop, MediaPipe FaceLandmarker, calibration, blink state machine
│   ├── screenshot.py               # Full-screen grab + Screen Recording permission
│   ├── clipboard/                   # Per-platform clipboard backends (macos.py implemented; windows.py implemented but untested on real hardware; linux.py stub)
│   └── tray.py                       # pystray icon + menu
├── models/face_landmarker.task        # MediaPipe model bundle (gitignored, download separately)
├── packaging/
│   ├── icon/generate_icon.py           # Generates AppIcon.icns (macOS) and AppIcon.ico (Windows)
│   ├── blink-eyes.spec                  # PyInstaller spec for macOS
│   ├── blink-eyes-windows.spec           # PyInstaller spec for Windows
│   ├── build_macos.sh                     # Builds .app, then .dmg and .pkg
│   ├── build_windows.ps1                   # Builds .exe, then .msi (Windows-only, see below)
│   └── windows/blink-eyes.wxs               # WiX product definition for the MSI
└── requirements.txt / requirements-build.txt
```

## Running from source

```
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Download the MediaPipe face-landmark model into `models/`:

```
curl -L -o models/face_landmarker.task \
  https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task
```

(See the [MediaPipe Face Landmarker docs](https://ai.google.dev/edge/mediapipe/solutions/vision/face_landmarker)
if that URL moves — any `face_landmarker.task` bundle from that page works;
the blendshapes variant isn't needed.)

Run it:

```
python main.py
```

or with a live debug preview: `python main.py --debug` (see the main
[README](../README.md#debug-mode)).

### A note on the mediapipe version pin

`requirements.txt` pins `mediapipe==0.10.35`. mediapipe 1.0.x's
`FaceLandmarker` was found (empirically, on this project's dev machine) to
crash with a Metal/GPU graph-service abort (`Check failed: service_
Service is unavailable`) inside `TensorsToDetectionsCalculator::Open()` on
some macOS setups. 0.10.35 is the last pre-1.0 release and works reliably.
If you want to try a newer mediapipe release, test `FaceLandmarker` creation
in isolation first before assuming it's fixed.

## Building the macOS installer

```
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-build.txt
./packaging/build_macos.sh
```

This runs PyInstaller against `packaging/blink-eyes.spec` (which bundles
`models/face_landmarker.task` into the app's Resources, sets
`NSCameraUsageDescription` and `LSUIElement=1` in Info.plist, and uses
`packaging/icon/AppIcon.icns`), then wraps the resulting `.app` into:

- `dist/Blink Eyes.dmg` — a drag-to-Applications disk image
- `dist/Blink Eyes.pkg` — a double-click installer (via `pkgbuild`/`productbuild`)

Both are **unsigned** (no Apple Developer ID configured). To distribute a
Gatekeeper-clean build, get a Developer ID Application certificate and
uncomment the `codesign`/`notarytool` block near the top of
`build_macos.sh`.

To regenerate the app icon (e.g. after changing its design), edit
`packaging/icon/generate_icon.py` and rerun it — it regenerates both
`AppIcon.icns` and `AppIcon.ico` (the macOS step additionally requires
macOS's built-in `iconutil`, so the icns half only regenerates on macOS).

## Building the Windows installer

**This must be run on a real Windows machine or a Windows CI runner**
(e.g. GitHub Actions' `windows-latest`) — PyInstaller does not
cross-compile, and the WiX Toolset's `heat.exe`/`candle.exe`/`light.exe`
are Windows-only. It cannot be produced from macOS or Linux.

It has been written but **not run/tested** on real Windows hardware, since
none was available while building this. Treat it as a solid starting point
that likely needs a debugging pass on first real use, not a proven script.

Prerequisites on the Windows machine:

- Python 3.11+, with `pip install -r requirements-build.txt` (this also
  pulls in `pywin32` for the clipboard backend)
- [WiX Toolset v3.11+](https://wixtoolset.org/releases/) installed, with
  `heat.exe`, `candle.exe`, and `light.exe` on `PATH`
- `models\face_landmarker.task` downloaded (same URL as above)

Then, from PowerShell in the project root:

```powershell
.\packaging\build_windows.ps1
```

This: (1) builds `blink-eyes.exe` via PyInstaller using
`packaging/blink-eyes-windows.spec`, (2) harvests the resulting output
directory's file list with `heat.exe` into `packaging/windows/AppFiles.wxs`
(this is regenerated every run — it's not meant to be hand-maintained,
since the exact file list depends on mediapipe/opencv's bundled DLLs),
(3) compiles `packaging/windows/blink-eyes.wxs` + the harvested fragment
with `candle.exe`, and (4) links them into `dist/Blink Eyes.msi` with
`light.exe`.

The result is unsigned; Windows SmartScreen will warn on first run on other
machines unless you sign it with an Authenticode certificate
(`signtool.exe sign /a "dist\Blink Eyes.msi"`).

## Linux

No installer packaging is provided for Linux. The clipboard backend
(`blink_eyes/clipboard/linux.py`) is an unimplemented stub — see the
docstring there for the intended approach (`xclip`/`wl-copy` via
subprocess) before attempting to package for Linux.
