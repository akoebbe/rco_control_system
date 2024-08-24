from settings import Settings
import asyncio
import array

class Eyes:
    eye_count = 2
    leds_per_eye = 7
    left_buffer = [(0, 0, 0, 0)]*leds_per_eye
    right_buffer = [(0, 0, 0, 0)]*leds_per_eye
    black = (0, 0, 0, 0)
    current_frame = 0
    current_color_idx = 0
    has_update = False
    # Should make the queue a tuple (frame[], timing)
    animation_queue = []


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
        color = self.color
        for frame in self.close_animation_frames:
            self.animation_queue.append([color if x else self.black for x in frame])
        if color_change:
            color = color_change
        for frame in self.open_animation_frames:
            self.animation_queue.append([color if x else self.black for x in frame])
        if color_change:
            self.color = color_change

    @property
    def has_animation(self):
        return len(self.animation_queue) > 0

    def animate(self):
        if not self.has_animation:
            return
        frame = self.animation_queue.pop(0)
        self.left_buffer = frame
        self.right_buffer = frame
        self.has_update = True

    def blink_animate(self):
        if self.current_frame >= len(self.close_animation_frames):
            self.current_frame = 0
            self.color = color_change
            return False
        self.left_buffer = [self.color if x else self.black for x in self.close_animation_frames[self.current_frame]]
        self.right_buffer = [self.color if x else self.black for x in self.close_animation_frames[self.current_frame]]
        self.current_frame = self.current_frame + 1
        self.has_update = True
        return True

    def render_leds(self):
        flattend_list = [item for sublist in self.left_buffer+self.right_buffer for item in sublist]
        self.has_update = False
        return flattend_list
    
    def render_left_leds(self):
        self.has_update = False
        return self.left_buffer
        
    def render_right_leds(self):
        self.has_update = False
        return self.right_buffer
    
    def set_color(self, color: tuple[int,int,int,int]):
        self.color = color
        self.fill()

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
