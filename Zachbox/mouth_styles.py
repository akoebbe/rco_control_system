import math

class MouthStyle():
    
    _color=(0,255,0,0)

    def __init__(self, leds_per_row: int, rows: int, color: tuple[int,int,int,int] = (0,255,0,0)):
        self.led_count = leds_per_row
        self.rows = rows
        self._color = color

    def render(self, value: int) -> list[tuple[int,int,int,int]]:
        raise NotImplemented
    
    @property
    def color(self):
        return self._color
    
    @color.setter
    def color(self, color: tuple[int,int,int,int]):
        self._color = color

    def partial_color(self, percent: float):
        return tuple([int(x * percent) for x in self.color])

class Kitt(MouthStyle):
    def render(self, value: int) -> list[tuple[int,int,int,int]]:
        led_strength = (value / 255 * 4)
        # print(led_strength)
        full_leds = math.floor(led_strength)
        partial_led = led_strength % 1

        color = self.color

        half = int(self.led_count/2)
        leds = [(0,0,0,0)] * self.led_count

        leds[half-full_leds:half] = [color] * full_leds
        leds[half:half+full_leds] = [color] * full_leds
        if partial_led > 0:
            partial_color = self.partial_color(partial_led)
            leds[half - 1 - full_leds] = partial_color
            leds[full_leds + half] = partial_color
        
        return leds * self.rows

