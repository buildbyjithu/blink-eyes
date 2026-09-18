# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the Windows build.

Must be run on Windows (PyInstaller does not cross-compile). Produces a
one-directory build at dist/blink-eyes/ containing blink-eyes.exe plus all
dependencies -- this is what build_windows.ps1 feeds into WiX to build the
.msi.

Build with (from the project root, inside a venv with
requirements-build.txt installed):

    pyinstaller packaging\\blink-eyes-windows.spec --noconfirm
"""

import os

PROJECT_ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))

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
    console=False,  # background/tray app, no console window
    icon=os.path.join(PROJECT_ROOT, "packaging", "icon", "AppIcon.ico"),
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
