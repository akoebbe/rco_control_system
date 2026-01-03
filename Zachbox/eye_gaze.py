import math

# Approximate LED positions for the 7-pixel jewel, centered at origin.
#   _____
#  /  2  \
# / 1   3 \
# |   7   |
# \ 6   4 /
#  \  5  /
#   -----
# LED positions index order matches observed colors:
# 0 = center, then clockwise starting at top.
LED_POSITIONS = [
    (0.0, 0.0),   # 0 - center
    (0.0, 1.0),   # 1 - top
    (0.7, 0.7),   # 2 - upper right
    (0.7, -0.7),  # 3 - lower right
    (0.0, -1.0),  # 4 - bottom
    (-0.7, -0.7), # 5 - lower left
    (-0.7, 0.7),  # 6 - upper left
]

DEFAULT_CENTER_DEADZONE = 0.1
DEFAULT_PUPIL_RADIUS = 1
DEFAULT_PUPIL_RANGE = 1.4
DEFAULT_PUPIL_EDGE_SOFTNESS = 0.2

def gaze_intensity(gaze: tuple[float, float], positions=LED_POSITIONS, *, config=None) -> list[float]:
    """
    Convert a gaze vector into per-LED brightness multipliers (0..1).
    Treats the pupil as a filled circle that moves within the eye, with a soft edge.
    """
    if config is None:
        config = {}
    center_deadzone = config.get("center_deadzone", DEFAULT_CENTER_DEADZONE)
    pupil_radius = config.get("pupil_radius", DEFAULT_PUPIL_RADIUS)
    pupil_range = config.get("pupil_range", DEFAULT_PUPIL_RANGE)
    pupil_edge_softness = config.get("pupil_edge_softness", DEFAULT_PUPIL_EDGE_SOFTNESS)

    positions_list = list(positions)
    mag = math.sqrt(gaze[0] * gaze[0] + gaze[1] * gaze[1])
    if mag < center_deadzone:
        return [1.0] * len(positions_list)
    mag = min(1.0, mag)
    nx = gaze[0] / mag
    ny = gaze[1] / mag
    pupil_center = (nx * pupil_range * mag, ny * pupil_range * mag)

    intensities = []
    for px, py in positions_list:
        dx = px - pupil_center[0]
        dy = py - pupil_center[1]
        dist = math.sqrt(dx * dx + dy * dy)
        if dist <= pupil_radius:
            intensities.append(1.0)
        elif dist >= (pupil_radius + pupil_edge_softness):
            intensities.append(0.0)
        else:
            fade = (dist - pupil_radius) / pupil_edge_softness
            intensities.append(1.0 - fade)
    return intensities
