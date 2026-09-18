"""Eye Aspect Ratio (EAR) calculation from MediaPipe face landmarks.

Landmark indices follow the standard 478-point MediaPipe face mesh topology
(unchanged between the deprecated solutions API and the current Tasks API).
Each 6-tuple is (outer corner, top-outer, top-inner, inner corner,
bottom-inner, bottom-outer), per Soukupova & Cech (2016).
"""

LEFT_EYE_IDX = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_IDX = [362, 385, 387, 263, 373, 380]


def _dist(a, b) -> float:
    return ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5


def eye_aspect_ratio(landmarks, idx) -> float:
    p1, p2, p3, p4, p5, p6 = (landmarks[i] for i in idx)
    return (_dist(p2, p6) + _dist(p3, p5)) / (2.0 * _dist(p1, p4))


def average_ear(landmarks) -> float:
    left = eye_aspect_ratio(landmarks, LEFT_EYE_IDX)
    right = eye_aspect_ratio(landmarks, RIGHT_EYE_IDX)
    return (left + right) / 2.0
