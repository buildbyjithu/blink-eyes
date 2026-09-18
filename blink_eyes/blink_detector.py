"""Camera capture + MediaPipe face-landmark loop with a double-blink state machine."""

import logging
import threading
import time
from collections import deque
from typing import Callable, Optional

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision

from . import config
from .ear import LEFT_EYE_IDX, RIGHT_EYE_IDX, average_ear

logger = logging.getLogger(__name__)


class BlinkDetector:
    def __init__(
        self,
        on_double_blink: Callable[[], None],
        paused: threading.Event,
        stop_event: threading.Event,
        model_path: str = config.MODEL_PATH,
        debug: bool = False,
    ):
        self._on_double_blink = on_double_blink
        self._paused = paused
        self._stop_event = stop_event
        self._model_path = model_path
        self._debug = debug

    def _create_landmarker(self) -> mp_vision.FaceLandmarker:
        base_options = mp_python.BaseOptions(model_asset_path=self._model_path)
        options = mp_vision.FaceLandmarkerOptions(
            base_options=base_options,
            running_mode=mp_vision.RunningMode.VIDEO,
            num_faces=1,
            # Lower than the 0.5 default: this is a single known user close
            # to their own webcam, and losing face tracking mid-blink (low
            # eye visibility can dip detector confidence right when it
            # matters most) is worse here than an occasional false positive.
            min_face_detection_confidence=0.3,
            min_face_presence_confidence=0.3,
            min_tracking_confidence=0.3,
        )
        return mp_vision.FaceLandmarker.create_from_options(options)

    def _skip_warmup_frames(self, cap: cv2.VideoCapture) -> None:
        for i in range(config.WARMUP_FRAMES):
            logger.info("Warmup frame %d/%d: reading...", i + 1, config.WARMUP_FRAMES)
            ret, _ = cap.read()
            logger.info("Warmup frame %d/%d: ret=%s", i + 1, config.WARMUP_FRAMES, ret)

    def _detect(self, landmarker: mp_vision.FaceLandmarker, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        timestamp_ms = int(time.monotonic() * 1000)
        return landmarker.detect_for_video(mp_image, timestamp_ms)

    def _calibrate(self, cap: cv2.VideoCapture, landmarker: mp_vision.FaceLandmarker) -> float:
        """Measure this user/camera's baseline "eyes open" EAR and derive a
        closed-eye threshold from it, since the raw EAR value is not
        comparable across different landmark sets, cameras, or head
        distances (see config.py for details)."""
        logger.info(
            "Calibrating blink sensitivity — look at the camera with your eyes "
            "open normally for %.0fs...",
            config.CALIBRATION_DURATION_SEC,
        )
        ear_samples = []
        deadline = time.monotonic() + config.CALIBRATION_DURATION_SEC
        while time.monotonic() < deadline:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.02)
                continue
            result = self._detect(landmarker, frame)
            if result.face_landmarks:
                ear_samples.append(average_ear(result.face_landmarks[0]))

        if ear_samples:
            ear_samples.sort()
            baseline = ear_samples[len(ear_samples) // 2]  # median
            threshold = baseline * config.EAR_CLOSED_RATIO
            logger.info(
                "Calibration done: baseline EAR=%.3f, closed-eye threshold=%.3f "
                "(%d samples)",
                baseline,
                threshold,
                len(ear_samples),
            )
        else:
            threshold = config.EAR_THRESHOLD_FALLBACK
            logger.warning(
                "Calibration found no face; using fallback threshold=%.3f. "
                "Make sure your face is visible to the camera.",
                threshold,
            )
        return threshold

    def run(self) -> None:
        """Blocking loop; intended to be run on a dedicated background thread."""
        landmarker = self._create_landmarker()
        cap: Optional[cv2.VideoCapture] = None
        ear_threshold = config.EAR_THRESHOLD_FALLBACK

        state = "OPEN"
        closed_start_time = 0.0
        blink_timestamps: deque = deque(maxlen=2)
        last_trigger_time = 0.0
        last_face_seen_time = time.monotonic()

        try:
            while not self._stop_event.is_set():
                if self._paused.is_set():
                    if cap is not None:
                        cap.release()
                        cap = None
                    state = "OPEN"
                    blink_timestamps.clear()
                    time.sleep(0.2)
                    continue

                if cap is None:
                    logger.info("Opening camera index %d...", config.CAMERA_INDEX)
                    cap = cv2.VideoCapture(config.CAMERA_INDEX)
                    logger.info("cap.isOpened() = %s", cap.isOpened())
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
                    self._skip_warmup_frames(cap)
                    ear_threshold = self._calibrate(cap, landmarker)
                    state = "OPEN"
                    blink_timestamps.clear()
                    last_face_seen_time = time.monotonic()

                ret, frame = cap.read()
                if not ret:
                    time.sleep(0.05)
                    continue

                result = self._detect(landmarker, frame)

                now = time.monotonic()
                landmarks = result.face_landmarks[0] if result.face_landmarks else None

                if landmarks is None:
                    if now - last_face_seen_time > config.NO_FACE_RESET_SEC:
                        state = "OPEN"
                        blink_timestamps.clear()
                    if self._debug:
                        self._show_debug_frame(frame, None, None, ear_threshold)
                    continue

                last_face_seen_time = now
                ear = average_ear(landmarks)
                eyes_closed = ear < ear_threshold

                if eyes_closed and state == "OPEN":
                    state = "CLOSED"
                    closed_start_time = now
                elif not eyes_closed and state == "CLOSED":
                    state = "OPEN"
                    duration = now - closed_start_time
                    if config.BLINK_MIN_DURATION_SEC <= duration <= config.BLINK_MAX_DURATION_SEC:
                        if now - last_trigger_time >= config.TRIGGER_COOLDOWN_SEC:
                            blink_timestamps.append(now)
                            if (
                                len(blink_timestamps) == 2
                                and blink_timestamps[1] - blink_timestamps[0]
                                <= config.DOUBLE_BLINK_WINDOW_SEC
                            ):
                                blink_timestamps.clear()
                                last_trigger_time = now
                                self._on_double_blink()

                if self._debug:
                    self._show_debug_frame(frame, landmarks, ear, ear_threshold)
        finally:
            if cap is not None:
                cap.release()
            landmarker.close()
            if self._debug:
                cv2.destroyAllWindows()

    def _show_debug_frame(self, frame, landmarks, ear: Optional[float], ear_threshold: float) -> None:
        display = frame.copy()
        if landmarks is not None:
            h, w = frame.shape[:2]
            for idx in LEFT_EYE_IDX + RIGHT_EYE_IDX:
                lm = landmarks[idx]
                cv2.circle(display, (int(lm.x * w), int(lm.y * h)), 2, (0, 255, 0), -1)
            if ear is not None:
                cv2.putText(
                    display,
                    f"EAR: {ear:.3f} (thr {ear_threshold:.3f})",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 0, 255),
                    2,
                )
        cv2.imshow("blink-eyes debug", display)
        cv2.waitKey(1)
