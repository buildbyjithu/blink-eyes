#!/usr/bin/env bash
# Builds Blink Eyes.app with PyInstaller, then packages it as both a DMG
# (drag-to-Applications) and a PKG (double-click installer).
#
# Usage (from the project root):
#   python3 -m venv .venv && source .venv/bin/activate
#   pip install -r requirements-build.txt
#   ./packaging/build_macos.sh
#
# Requires the MediaPipe model at models/face_landmarker.task (see README).
#
# NOTE: the resulting .app/.dmg/.pkg are NOT code-signed or notarized (that
# requires a paid Apple Developer ID). Gatekeeper will show an "unidentified
# developer" warning on other Macs; the user must right-click > Open the
# first time, or you can sign+notarize yourself if you have a Developer ID
# (see the commented-out codesign/notarytool steps below).

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

APP_NAME="Blink Eyes"
APP_VERSION="1.0.0"
BUNDLE_ID="com.blinkeyes.app"
DIST_DIR="$PROJECT_ROOT/dist"
APP_PATH="$DIST_DIR/$APP_NAME.app"

if [ ! -f "models/face_landmarker.task" ]; then
    echo "Missing models/face_landmarker.task -- download it first (see README.md)." >&2
    exit 1
fi

echo "==> Building $APP_NAME.app with PyInstaller"
rm -rf build dist
pyinstaller packaging/blink-eyes.spec --noconfirm

if [ ! -d "$APP_PATH" ]; then
    echo "Build did not produce $APP_PATH" >&2
    exit 1
fi

# --- Optional: code signing + notarization -----------------------------
# If you have an Apple Developer ID, uncomment and set your identity/team
# to produce a Gatekeeper-clean build:
#
# codesign --deep --force --options runtime \
#   --sign "Developer ID Application: Your Name (TEAMID)" "$APP_PATH"
# xcrun notarytool submit "$DMG_PATH" --keychain-profile "your-profile" --wait
# xcrun stapler staple "$APP_PATH"
# -------------------------------------------------------------------------

echo "==> Building DMG"
DMG_PATH="$DIST_DIR/$APP_NAME.dmg"
STAGING_DIR="$(mktemp -d)"
trap 'rm -rf "$STAGING_DIR"' EXIT

cp -R "$APP_PATH" "$STAGING_DIR/"
ln -s /Applications "$STAGING_DIR/Applications"
rm -f "$DMG_PATH"
hdiutil create -volname "$APP_NAME" -srcfolder "$STAGING_DIR" -ov -format UDZO "$DMG_PATH"
echo "    -> $DMG_PATH"

echo "==> Building PKG"
PKG_ROOT="$(mktemp -d)"
mkdir -p "$PKG_ROOT/Applications"
cp -R "$APP_PATH" "$PKG_ROOT/Applications/"

COMPONENT_PKG="$DIST_DIR/${APP_NAME}-component.pkg"
PKG_PATH="$DIST_DIR/$APP_NAME.pkg"

pkgbuild \
    --root "$PKG_ROOT" \
    --install-location / \
    --identifier "$BUNDLE_ID" \
    --version "$APP_VERSION" \
    "$COMPONENT_PKG"

productbuild --package "$COMPONENT_PKG" "$PKG_PATH"
rm -f "$COMPONENT_PKG"
rm -rf "$PKG_ROOT"
echo "    -> $PKG_PATH"

echo ""
echo "Done. Unsigned artifacts in $DIST_DIR:"
echo "  - $APP_NAME.app"
echo "  - $APP_NAME.dmg"
echo "  - $APP_NAME.pkg"
echo ""
echo "These are unsigned -- on another Mac, Gatekeeper will block the first"
echo "launch. Right-click the app (or run the installer) and choose Open to"
echo "bypass it once, or sign+notarize with a Developer ID for a clean install."
