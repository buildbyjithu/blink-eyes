# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the macOS "Blink Eyes.app" bundle.

Build with (from the project root, inside the venv with requirements-build.txt
installed):

    pyinstaller packaging/blink-eyes.spec --noconfirm

Produces dist/Blink Eyes.app.
"""

import os

PROJECT_ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))
APP_VERSION = "1.0.0"

block_cipher = None

a = Analysis(
    [os.path.join(PROJECT_ROOT, "main.py")],
    pathex=[PROJECT_ROOT],
    binaries=[],
    datas=[
        (os.path.join(PROJECT_ROOT, "models", "face_landmarker.task"), "models"),
    ],
    hiddenimports=[],
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
