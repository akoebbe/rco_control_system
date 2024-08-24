from mouth_styles import MouthStyle, Kitt
from settings import Settings

class Mouth:
    
    value = 0
    colors = Settings.mouth_colors
    color_idx = 0
    
    def __init__(self, leds_per_row:int=8, rows:int=2, style:MouthStyle=Kitt) -> None:
        self.style = style(leds_per_row=leds_per_row, rows=rows, color=self.colors[self.color_idx])

    def next_color(self):
        new_color_idx = (self.color_idx + 1) % len(self.colors)
        self.style.color = self.colors[new_color_idx]
        self.color_idx = new_color_idx
    
    def prev_color(self):
        new_color_idx = (self.color_idx - 1) % len(self.colors)
        self.style.color = self.colors[new_color_idx]
        self.color_idx = new_color_idx
    
    def render(self):
        return self.style.render(value=self.value)