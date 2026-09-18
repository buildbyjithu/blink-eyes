"""macOS camera-permission warm-up.

OpenCV's AVFoundation backend can only *request* camera authorization from
the process's main thread (spinning the main run loop); it cannot do so
from a background thread. Since the blink-detection camera loop runs on a
background thread (the tray icon needs the main thread instead), the first
camera-authorization prompt must be triggered here, on the main thread,
before the background detection loop ever calls cv2.VideoCapture(). Once
granted, the OS remembers it for later background-thread camera opens.
"""

import logging
import platform
import time

logger = logging.getLogger(__name__)


def ensure_camera_authorized(timeout_sec: float = 30.0) -> bool:
    """Block on the main thread until the camera permission prompt is answered.

    Returns True if access is authorized (or already was), False if denied,
    restricted, or the user didn't respond within timeout_sec.
    """
    if platform.system() != "Darwin":
        return True

    try:
        import AVFoundation
    except ImportError:
        # pyobjc-framework-AVFoundation not installed; let the camera loop
        # attempt to open the camera directly and surface any failure there.
        return True

    media_type = AVFoundation.AVMediaTypeVideo
    status = AVFoundation.AVCaptureDevice.authorizationStatusForMediaType_(media_type)
    logger.info("Camera authorization status: %s", status)

    if status == AVFoundation.AVAuthorizationStatusAuthorized:
        return True
    if status in (
        AVFoundation.AVAuthorizationStatusDenied,
        AVFoundation.AVAuthorizationStatusRestricted,
    ):
        return False

    # AVAuthorizationStatusNotDetermined: trigger the OS prompt and wait for
    # the answer. Apple's docs state the completion handler fires on an
    # arbitrary background dispatch queue -- it does NOT require the caller
    # to pump a run loop -- so a plain sleep-poll is used here instead of
    # NSRunLoop.runUntilDate_(), which was found to hang indefinitely on at
    # least one Mac (likely an environment where the "current run loop" on
    # this thread doesn't behave as expected for a windowless, unsigned
    # process).
    result = {}

    def _completion(granted):
        result["granted"] = bool(granted)

    logger.info("Requesting camera access...")
    AVFoundation.AVCaptureDevice.requestAccessForMediaType_completionHandler_(
        media_type, _completion
    )

    deadline = time.monotonic() + timeout_sec
    while "granted" not in result and time.monotonic() < deadline:
        time.sleep(0.1)

    logger.info("Camera access request result: %s", result.get("granted", "<timed out>"))
    return result.get("granted", False)
