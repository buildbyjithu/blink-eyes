#!/usr/bin/env python3
"""blink-eyes: double-blink at your webcam to screenshot straight to the clipboard."""

import argparse
import logging
import os
import platform
import sys
import threading

from blink_eyes import config, tray
from blink_eyes.blink_detector import BlinkDetector
from blink_eyes.camera_auth import ensure_camera_authorized
from blink_eyes.clipboard import get_clipboard_backend
from blink_eyes.screenshot import (
    SCREEN_PERMISSION_HELP,
    capture_full_screen,
    request_screen_capture_access,
)


def _default_log_path() -> str:
    """A packaged app has no visible console, so mirror logs to a file too."""
    system = platform.system()
    if system == "Darwin":
        log_dir = os.path.expanduser("~/Library/Logs")
    elif system == "Windows":
        log_dir = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "blink-eyes")
    else:
        log_dir = os.path.expanduser("~/.local/state/blink-eyes")
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, "blink-eyes.log")


_log_handlers = [logging.StreamHandler()]
try:
    _log_handlers.append(logging.FileHandler(_default_log_path()))
except OSError:
    pass
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", handlers=_log_handlers
)
logger = logging.getLogger("blink-eyes")

if getattr(sys, "frozen", False):
    # Running from a PyInstaller-built app bundle: bundled data files (like
    # the model) live under sys._MEIPASS, not next to this script.
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def parse_args():
    parser = argparse.ArgumentParser(description="Double-blink to screenshot utility")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Show a debug preview window with eye landmarks and the live EAR value",
    )
    parser.add_argument(
        "--model",
        default=os.path.join(BASE_DIR, config.MODEL_PATH),
        help="Path to the MediaPipe face_landmarker.task model bundle",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not os.path.exists(args.model):
        logger.error(
            "Model file not found at %s. Download face_landmarker.task as "
            "described in README.md before running.",
            args.model,
        )
        return

    # CGRequestScreenCaptureAccess (not just the preflight check) is what
    # actually registers this app as a togglable entry in System Settings >
    # Privacy & Security > Screen Recording.
    if not request_screen_capture_access():
        logger.warning(SCREEN_PERMISSION_HELP)

    # Must happen on the main thread: AVFoundation can only show/resolve the
    # camera permission prompt from the main thread, but the camera capture
    # loop itself runs on a background thread (pystray needs the main
    # thread). Doing this here first means the background loop's camera
    # opens will already be authorized.
    logger.info("Checking camera permission (click Allow if macOS prompts you)...")
    if not ensure_camera_authorized():
        logger.warning(
            "Camera access was not granted (or the system prompt wasn't "
            "answered in time). Open System Settings > Privacy & Security "
            "> Camera, enable it for the app/terminal running blink-eyes, "
            "then restart blink-eyes."
        )

    clipboard_backend = get_clipboard_backend()
    paused = threading.Event()
    stop_event = threading.Event()

    # cv2's debug preview window needs the main thread on macOS -- same
    # constraint as pystray's tray icon and AVFoundation's camera-permission
    # prompt above. The two can't share a thread, so debug mode skips the
    # tray entirely and runs detection directly on the main thread instead.
    icon = None if args.debug else tray.build_tray_icon(paused, stop_event)

    def on_double_blink() -> None:
        logger.info("Double-blink detected, taking screenshot")
        try:
            image = capture_full_screen()
            clipboard_backend.copy_image(image)
            logger.info("Screenshot copied to clipboard")
        except Exception:
            logger.exception("Failed to capture/copy screenshot. %s", SCREEN_PERMISSION_HELP)
        if icon is not None:
            tray.flash_icon(icon, paused)

    detector = BlinkDetector(
        on_double_blink=on_double_blink,
        paused=paused,
        stop_event=stop_event,
        model_path=args.model,
        debug=args.debug,
    )

    if args.debug:
        logger.info("Debug mode: no tray icon shown. Press Ctrl+C here to quit.")
        try:
            detector.run()
        except KeyboardInterrupt:
            stop_event.set()
        return

    def setup(icon) -> None:
        icon.visible = True
        threading.Thread(target=detector.run, daemon=True).start()

    icon.run(setup=setup)


if __name__ == "__main__":
    main()
