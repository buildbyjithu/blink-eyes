# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the macOS "Blink Eyes.app" bundle.

Build with (from the project root, inside the venv with requirements-build.txt
installed):

    pyinstaller packaging/blink-eyes.spec --noconfirm

Produces dist/Blink Eyes.app.
"""

import os

from PyInstaller.utils.hooks import collect_all

PROJECT_ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))
APP_VERSION = "1.0.0"

block_cipher = None

# mediapipe loads at least one native library (mediapipe/tasks/c/libmediapipe.dylib)
# via importlib.resources using a runtime-constructed module name
# ("mediapipe.tasks.c"), which PyInstaller's static import scanner can't
# trace back to a literal `import` statement -- it silently omits the file,
# producing a `ModuleNotFoundError: No module named 'mediapipe.tasks.c'`
# crash the first time FaceLandmarker.create_from_options() runs in the
# frozen app (this doesn't happen when running from source, only from the
# packaged build). collect_all() forces every data/binary/hidden-import for
# the whole package to be bundled instead of relying on that scanner.
mp_datas, mp_binaries, mp_hiddenimports = collect_all("mediapipe")

a = Analysis(
    [os.path.join(PROJECT_ROOT, "main.py")],
    pathex=[PROJECT_ROOT],
    binaries=mp_binaries,
    datas=[
        (os.path.join(PROJECT_ROOT, "models", "face_landmarker.task"), "models"),
    ]
    + mp_datas,
    hiddenimports=mp_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="blink-eyes",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="blink-eyes",
)

app = BUNDLE(
    coll,
    name="Blink Eyes.app",
    icon=os.path.join(PROJECT_ROOT, "packaging", "icon", "AppIcon.icns"),
    bundle_identifier="com.blinkeyes.app",
    info_plist={
        "CFBundleName": "Blink Eyes",
        "CFBundleDisplayName": "Blink Eyes",
        "CFBundleShortVersionString": APP_VERSION,
        "CFBundleVersion": APP_VERSION,
        "NSCameraUsageDescription": (
            "Blink Eyes watches your webcam for a double-blink gesture to "
            "trigger a screenshot."
        ),
        "NSHighResolutionCapable": True,
        # Menu-bar-only accessory app: no Dock icon, no app-switcher entry.
        "LSUIElement": True,
    },
)
