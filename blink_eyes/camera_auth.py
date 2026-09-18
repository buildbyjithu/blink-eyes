"""macOS camera-permission warm-up.

OpenCV's AVFoundation backend can only *request* camera authorization from
the process's main thread (spinning the main run loop); it cannot do so
from a background thread. Since the blink-detection camera loop runs on a
background thread (the tray icon needs the main thread instead), the first
camera-authorization prompt must be triggered here, on the main thread,
before the background detection loop ever calls cv2.VideoCapture(). Once
granted, the OS remembers it for later background-thread camera opens.
"""

import platform
import time


def ensure_camera_authorized(timeout_sec: float = 30.0) -> bool:
    """Block on the main thread until the camera permission prompt is answered.

    Returns True if access is authorized (or already was), False if denied,
    restricted, or the user didn't respond within timeout_sec.
    """
    if platform.system() != "Darwin":
        return True

    try:
        import AVFoundation
        from Foundation import NSDate, NSRunLoop
    except ImportError:
        # pyobjc-framework-AVFoundation not installed; let the camera loop
        # attempt to open the camera directly and surface any failure there.
        return True

    media_type = AVFoundation.AVMediaTypeVideo
    status = AVFoundation.AVCaptureDevice.authorizationStatusForMediaType_(media_type)

    if status == AVFoundation.AVAuthorizationStatusAuthorized:
        return True
    if status in (
        AVFoundation.AVAuthorizationStatusDenied,
        AVFoundation.AVAuthorizationStatusRestricted,
    ):
        return False

    # AVAuthorizationStatusNotDetermined: trigger the OS prompt and pump the
    # run loop on this (main) thread until the user answers or we time out.
    result = {}

    def _completion(granted):
        result["granted"] = bool(granted)

    AVFoundation.AVCaptureDevice.requestAccessForMediaType_completionHandler_(
        media_type, _completion
    )

    deadline = time.monotonic() + timeout_sec
    run_loop = NSRunLoop.currentRunLoop()
    while "granted" not in result and time.monotonic() < deadline:
        run_loop.runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.1))

    return result.get("granted", False)
