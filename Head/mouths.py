import math

class Mouth():

    def __init__(self, led_count: int):
        self.led_count = led_count

    def render(self, value: int) -> list[tuple[int,int,int,int]]:
        raise NotImplemented


class Kitt(Mouth):
    def render(self, value: int) -> list[tuple[int,int,int,int]]:
        led_strength = (value / 255 * 4)
        # print(led_strength)
        full_leds = math.floor(led_strength)
        partial_led = led_strength % 1

        half = int(self.led_count/2)
        leds = [(0,0,0,0)] * self.led_count

        leds[half-full_leds:half] = [(0,255,0,0)] * full_leds
        leds[half:half+full_leds] = [(0,255,0,0)] * full_leds
        if partial_led > 0:
            leds[half - 1 - full_leds] = (0,int(partial_led * 255),0,0)
            leds[full_leds + half] = (0,int(partial_led * 255),0,0)
        
        return leds

