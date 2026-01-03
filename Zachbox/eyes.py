from settings import Settings
import asyncio
import array
from eye_gaze import gaze_intensity

class Eyes:
    eye_count = 2
    leds_per_eye = 7
    black = (0, 0, 0, 0)
    debug_colors = (
        (255, 0, 0, 0),      # 0 - red
        (0, 255, 0, 0),      # 1 - green
        (0, 0, 255, 0),      # 2 - blue
        (255, 255, 0, 0),    # 3 - yellow
        (255, 0, 255, 0),    # 4 - magenta
        (0, 255, 255, 0),    # 5 - cyan
        (255, 255, 255, 0),  # 6 - white (center)
    )


    #   _____
    #  /  2  \
    # / 1   3 \
    # |   7   |
    # \ 6   4 /
    #  \  5  /
    #   -----

    close_animation_frames = [
        [True, True, True, True, True, True, True],
        [True, False, True, True, True, True, True],
        [False, False, False, True, True, True, False],
        [False, False, False, False, False, False, False],
    ]

    open_animation_frames = [
        [False, False, False, True, True, True, False],
        [True, False, True, True, True, True, True],
        [True, True, True, True, True, True, True],
    ]

    def __init__(self, color: tuple[int,int,int,int]):
        self.color = color
        self.current_frame = 0
        self.current_color_idx = 0
        self.has_update = False
        self.animation_queue = []
        self.left_buffer = [self.black] * self.leds_per_eye
        self.right_buffer = [self.black] * self.leds_per_eye
        self.eyelid_mask = [True] * self.leds_per_eye
        self.last_gaze = (0.0, 0.0)
        self.gaze_config = {
            "center_deadzone": Settings.eye_gaze_center_deadzone,
            "pupil_radius": Settings.eye_gaze_pupil_radius,
            "pupil_range": Settings.eye_gaze_pupil_range,
            "pupil_edge_softness": Settings.eye_gaze_pupil_edge_softness,
        }
        self.fill()

    def fill(self):
        self.left_buffer = [self.color]*len(self.left_buffer)
        self.right_buffer = [self.color]*len(self.right_buffer)
        self.has_update = True

    def blank(self):
        self.left_buffer = [self.black]*len(self.left_buffer)
        self.right_buffer = [self.black]*len(self.right_buffer)
        self.has_update = True

    def build_blink_frames(self, color_change: tuple[int, int, int, int]|None = None):
        for frame in self.close_animation_frames:
            self.animation_queue.append(frame)
        if color_change:
            self.animation_queue.append(("color", color_change))
        for frame in self.open_animation_frames:
            self.animation_queue.append(frame)

    @property
    def has_animation(self):
        return len(self.animation_queue) > 0

    def animate(self):
        if not self.has_animation:
            return
        while self.animation_queue:
            frame = self.animation_queue.pop(0)
            if isinstance(frame, tuple) and frame[0] == "color":
                self._apply_color_change(frame[1])
                continue
            self.eyelid_mask = frame
            self.has_update = True
            break

    def blink_animate(self):
        if self.current_frame >= len(self.close_animation_frames):
            self.current_frame = 0
            return False
        self.eyelid_mask = self.close_animation_frames[self.current_frame]
        self.current_frame = self.current_frame + 1
        self.has_update = True
        return True

    def render_leds(self):
        left = self._apply_eyelid(self.left_buffer)
        right = self._apply_eyelid(self.right_buffer)
        flattend_list = [item for sublist in left + right for item in sublist]
        self.has_update = False
        return flattend_list
    
    def render_left_leds(self):
        self.has_update = False
        return self._apply_eyelid(self.left_buffer)
        
    def render_right_leds(self):
        self.has_update = False
        return self._apply_eyelid(self.right_buffer)
    
    def set_color(self, color: tuple[int,int,int,int]):
        self.color = color
        self.fill()

    def set_gaze(self, gaze: tuple[float, float]):
        """
        Set gaze direction as a vector (x, y) in eye-space and render a moving pupil.
        """
        self.last_gaze = gaze
        intensities = gaze_intensity(gaze, config=self.gaze_config)
        def apply_intensity(intensity):
            return tuple(int(c * intensity) for c in self.color)
        frame = [apply_intensity(level) for level in intensities]
        self.left_buffer = frame
        self.right_buffer = frame
        self.has_update = True

    def set_debug_colors(self):
        """
        Set distinct colors per LED to verify physical index ordering.
        """
        self.left_buffer = list(self.debug_colors)
        self.right_buffer = list(self.debug_colors)
        self.has_update = True

    def color_next(self, set_color: bool = True) -> tuple[int,int,int,int]:
        next_idx = (self.current_color_idx + 1) % len(Settings.eye_colors)
        if set_color:
            self.set_color(Settings.eye_colors[next_idx])
        self.current_color_idx = next_idx
        return Settings.eye_colors[next_idx]

    def color_prev(self, set_color: bool = True) -> tuple[int,int,int,int]:
        prev_idx = (self.current_color_idx - 1) % len(Settings.eye_colors)
        if set_color:
            self.set_color(Settings.eye_colors[prev_idx])
        self.current_color_idx = prev_idx
        return Settings.eye_colors[prev_idx]
        
    def set_left_eye(self, leds: list[tuple[int,int,int,int]]):
        if self.left_buffer != leds:
            self.left_buffer = leds
            self.has_update = True

    def set_right_eye(self, leds: list[tuple[int,int,int,int]]):
        if self.right_buffer != leds:
            self.right_buffer = leds
            self.has_update = True

    def set_eyes(self, left_leds: list[tuple[int,int,int,int]], right_leds: list[tuple[int,int,int,int]]):
        self.set_left_eye(left_leds)
        self.set_right_eye(right_leds)

    def _apply_color_change(self, color: tuple[int,int,int,int]):
        self.color = color
        self.set_gaze(self.last_gaze)

    def _apply_eyelid(self, buffer):
        if not self.eyelid_mask or all(self.eyelid_mask):
            return buffer
        return [pixel if self.eyelid_mask[idx] else self.black for idx, pixel in enumerate(buffer)]
