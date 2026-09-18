import platform

from PIL import Image, ImageGrab


class ScreenPermissionError(RuntimeError):
    """Raised when the OS has not granted screen-capture permission."""


def capture_full_screen() -> Image.Image:
    return ImageGrab.grab()


def preflight_screen_capture_access() -> bool:
    """Best-effort check for macOS Screen Recording permission.

    This only *queries* status — it does not register an entry in System
    Settings > Privacy & Security > Screen Recording. Use
    request_screen_capture_access() for that.

    Returns True if capture should be permitted (or the check isn't
    applicable on this platform), False if it's known to be denied.
    """
    if platform.system() != "Darwin":
        return True

    try:
        import Quartz

        return bool(Quartz.CGPreflightScreenCaptureAccess())
    except ImportError:
        # pyobjc-framework-Quartz not available; fall back to attempting
        # capture and letting the caller handle failure.
        return True


def request_screen_capture_access() -> bool:
    """Actively request macOS Screen Recording permission.

    Unlike preflight_screen_capture_access(), this call is what actually
    causes the app to appear as a togglable entry in System Settings >
    Privacy & Security > Screen Recording (and shows the OS prompt, the
    first time it's called for a not-yet-decided app). If permission was
    already denied previously, this will not re-prompt — the user must
    toggle it on manually in System Settings.

    Returns the current authorization state (True if granted).
    """
    if platform.system() != "Darwin":
        return True

    try:
        import Quartz

        return bool(Quartz.CGRequestScreenCaptureAccess())
    except ImportError:
        return True


SCREEN_PERMISSION_HELP = (
    "Screen Recording permission is required to take screenshots.\n"
    "Open System Settings > Privacy & Security > Screen Recording, "
    "enable it for the app/terminal running blink-eyes, then fully quit "
    "and relaunch blink-eyes (macOS caches this permission for the "
    "lifetime of the process, so toggling it while running has no effect)."
)
