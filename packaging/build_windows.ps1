# Builds blink-eyes.exe with PyInstaller, then packages it as an MSI using
# the WiX Toolset (v3).
#
# THIS MUST BE RUN ON WINDOWS -- PyInstaller does not cross-compile, and
# WiX's heat/candle/light tools are Windows-only. Run it on a real Windows
# machine, a Windows VM, or a Windows CI runner (e.g. GitHub Actions'
# windows-latest).
#
# Prerequisites:
#   - Python 3.11+ on PATH, with requirements-build.txt installed
#       python -m venv .venv
#       .venv\Scripts\Activate.ps1
#       pip install -r requirements-build.txt
#   - WiX Toolset v3.11+ installed, with heat.exe/candle.exe/light.exe on
#     PATH (https://wixtoolset.org/releases/)
#   - models\face_landmarker.task downloaded (see README.md)
#
# Usage (from the project root, in PowerShell):
#   .\packaging\build_windows.ps1

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path "$PSScriptRoot\.."
Set-Location $ProjectRoot

if (-not (Test-Path "models\face_landmarker.task")) {
    Write-Error "Missing models\face_landmarker.task -- download it first (see README.md)."
}

Write-Host "==> Building blink-eyes.exe with PyInstaller"
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
pyinstaller packaging\blink-eyes-windows.spec --noconfirm
if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed" }

$AppSourceDir = Join-Path $ProjectRoot "dist\blink-eyes"
if (-not (Test-Path $AppSourceDir)) {
    throw "Build did not produce $AppSourceDir"
}

Write-Host "==> Harvesting app files with heat.exe"
$WindowsPkgDir = Join-Path $ProjectRoot "packaging\windows"
$AppFilesWxs = Join-Path $WindowsPkgDir "AppFiles.wxs"
heat.exe dir "$AppSourceDir" `
    -cg AppFiles `
    -gg -scom -sreg -sfrag -srd `
    -dr INSTALLFOLDER `
    -var var.AppSourceDir `
    -out "$AppFilesWxs"
if ($LASTEXITCODE -ne 0) { throw "heat.exe failed" }

Write-Host "==> Compiling WiX sources with candle.exe"
$ObjDir = Join-Path $ProjectRoot "build\wix"
New-Item -ItemType Directory -Force -Path $ObjDir | Out-Null

candle.exe -ext WixUtilExtension `
    -dProjectRoot="$ProjectRoot" `
    -dAppSourceDir="$AppSourceDir" `
    -out "$ObjDir\" `
    "$WindowsPkgDir\blink-eyes.wxs" `
    "$AppFilesWxs"
if ($LASTEXITCODE -ne 0) { throw "candle.exe failed" }

Write-Host "==> Linking MSI with light.exe"
$MsiPath = Join-Path $ProjectRoot "dist\Blink Eyes.msi"
light.exe -ext WixUtilExtension `
    -sw1076 `
    -out "$MsiPath" `
    "$ObjDir\blink-eyes.wixobj" `
    "$ObjDir\AppFiles.wixobj"
if ($LASTEXITCODE -ne 0) { throw "light.exe failed" }

Write-Host ""
Write-Host "Done. Unsigned artifact: $MsiPath"
Write-Host "This is not code-signed -- Windows SmartScreen will warn on first"
Write-Host "run on other machines unless you sign it with an Authenticode"
Write-Host "certificate (signtool.exe sign /a `"$MsiPath`")."
