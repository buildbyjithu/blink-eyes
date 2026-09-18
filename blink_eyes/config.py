"""Tunable thresholds for camera capture and blink-gesture detection."""

# Camera
CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
WARMUP_FRAMES = 5  # frames to discard after opening the camera before trusting readings

# Model
MODEL_PATH = "models/face_landmarker.task"

# EAR / single-blink detection
#
# MediaPipe's face-mesh eye landmarks don't line up with dlib's classic
# 68-point contour that the "EAR < ~0.2 = closed" rule of thumb was
# calibrated against, and the absolute EAR value also swings a lot with
# head distance/pose (observed range on one test camera: ~0.24 open-low to
# ~0.75 open-high, with real blinks only dipping to ~0.24-0.28). A fixed
# absolute threshold can't work reliably across users/cameras, so the
# "closed" threshold is calibrated at startup as a fraction of that user's
# own measured open-eye baseline EAR instead.
CALIBRATION_DURATION_SEC = 2.0  # collect baseline "eyes open" EAR for this long at startup
EAR_CLOSED_RATIO = 0.75  # eyes count as closed when EAR drops below this fraction of the baseline
EAR_THRESHOLD_FALLBACK = 0.21  # used only if calibration collects zero samples (e.g. no face found)
BLINK_MIN_DURATION_SEC = 0.05
BLINK_MAX_DURATION_SEC = 0.4

# Double-blink gesture
DOUBLE_BLINK_WINDOW_SEC = 0.6
TRIGGER_COOLDOWN_SEC = 2.0

# If no face has been detected for this long, reset blink state to avoid
# combining stale timestamps once a face reappears.
NO_FACE_RESET_SEC = 1.0
