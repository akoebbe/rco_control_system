import board
import displayio
from adafruit_display_shapes.rect import Rect
from adafruit_display_shapes.sparkline import Sparkline
from vectorio import Rectangle
import terminalio
from adafruit_display_text import label
from adafruit_displayio_layout.layouts.page_layout import PageLayout
from adafruit_displayio_layout.layouts.grid_layout import GridLayout
from adafruit_bitmap_font import bitmap_font
from font_free_sans_14 import FONT
import icons
import vectorio
from timeit import TimeIt


# Checkout https://github.com/shulltronics/displayio-universal-ui
class ZachboxDisplay:
    

    TEXT_COLOR = 0xFFFF00

    indicators = {}

    font = bitmap_font.load_font("fonts/Silkscreen-10.bdf")

    display = board.DISPLAY
    display_grid_size = (12,5)

    def __init__(self) -> None:
        # Make the display context
        self.root = displayio.Group()
        self.display.root_group = self.root
        print("width:",self.display.width)
        print("height:",self.display.height)
        self.topbar = GridLayout(
            x=0,
            y=0,
            width=self.display.width,
            height=self.display.height,
            grid_size=(12,5),
            divider_lines=True,
        )
        self.display_grid_cell_pixels = self.topbar.cell_size_pixels
        self.is_enabled = self.display.brightness > 0
        self.root.append(self.topbar)

    def add_status_indicator(self, column:int, slot:int, key:str, label_text:str,  value):
        w, h = self.display_grid_cell_pixels
        inner_group = GridLayout(x=0, y=0, width=w*6, height=h, grid_size=(6,1), cell_padding=5)
        self.topbar.add_content(inner_group, grid_position=(column*6,slot), cell_size=(6,1))

        self.indicators[key] = {
            "label": label.Label(
                FONT, scale=1, text=label_text 
            ),
            "value": label.Label(
                FONT, scale=1, text=str(value)
            )
        }
        inner_group.add_content(self.indicators[key]["label"], grid_position=(0,0), cell_size=(3,1), cell_anchor_point=(0,0.5))
        inner_group.add_content(self.indicators[key]["value"], grid_position=(3,0), cell_size=(3,1), cell_anchor_point=(1,0.5))

    def update_value(self, key, value):
        self.indicators[key]["value"].text = str(value)

    def add_meter(self, column:int, slot:int, key:str, label_text:str, floor:int, ceiling:int, full_width:bool=False):
        inner_group_slots = 12 if full_width else 6
        grid_span = 12 if full_width else 6
        w, h = self.display_grid_cell_pixels
        inner_group = GridLayout(x=0, y=0, width=w * grid_span, height=h, grid_size=(inner_group_slots,1), cell_padding=0)
        self.topbar.add_content(inner_group, grid_position=(column*6,slot), cell_size=(grid_span,1))

        palette = displayio.Palette(3)
        palette[0] = 0x125690
        palette[1] = 0x00ff00
        palette[2] = 0xff0000
        
        indicator = {
            "label": label.Label(
                FONT, scale=1, text=label_text 
            ),
            "value": Rectangle(
                x=0, y=2, width=1, height=h-4, pixel_shader=palette
            ),
            "floor": Rectangle(pixel_shader=palette, width=2, height=h, x=int(w * 9 * floor/255), y=0),
            "ceiling": Rectangle(pixel_shader=palette, width=2, height=h, x=int(w * 9 * ceiling/255), y=0),
        }
        vu_group = BoxLayout()
        vu_group.append(indicator["value"])
        vu_group.append(indicator["floor"])
        vu_group.append(indicator["ceiling"])
        indicator["floor"].color_index = 1
        indicator["ceiling"].color_index = 2
        inner_group.add_content(indicator["label"], grid_position=(0,0), cell_size=(3,1), cell_anchor_point=(0,0.5))
        inner_group.add_content(vu_group, grid_position=(3,0), cell_size=(9,1))
        
        self.indicators[key] = indicator
        
    def update_meter(self, key, percent:float):
        w, h = self.topbar.cell_size_pixels
        self.indicators[key]["value"].width = self._clamp(int(w * 9 * percent), 1, w * 9)
        
    def update_meter_bounds(self, key, min=int, max=int):
        w, h = self.display_grid_cell_pixels
        self.indicators[key]["floor"].x = int(w * 9 * min/255)
        self.indicators[key]["ceiling"].x = int(w * 9 * max/255)
        
    def add_sparkline(self, column:int, slot:int, key:str, label_text:str):
        w, h = self.topbar.cell_size_pixels
        self.indicators[key] = {
            "label": label.Label(
                FONT, scale=1, text=label_text 
            ),
            "value": Sparkline(
                x=0, y=0, width=w, height=h, color=0xFFFFFF, max_items=20
            )
        }
        group = GridLayout(x=0, y=0, width=w, height=h, grid_size=(2,1), cell_padding=5)
        group.add_content(self.indicators[key]["label"], grid_position=(0,0), cell_size=(1,1), cell_anchor_point=(0,0.5))
        group.add_content(self.indicators[key]["value"], grid_position=(1,0), cell_size=(1,1))
        self.topbar.add_content(group, grid_position=(column,slot), cell_size=(1,1))
        
    def update_sparkline(self, key, value:int):
        w, h = self.topbar.cell_size_pixels
        self.indicators[key]["value"].add_value(value)


    def toggle_display(self):
        if self.is_enabled:
            self.display.brightness = 0
            self.is_enabled = False
            self.display.auto_refresh = 0
        else:
            self.display.auto_refresh = 1
            self.display.refresh()
            self.display.brightness = 1
            self.is_enabled = True
        
    def _clamp(self, value, lower_bound, upper_bond):
        return min(upper_bond, max(value, lower_bound))



class BoxLayout(displayio.Group):
    @property
    def width(self):
        return max([w.x + w.width for w in self])  
        
    @property
    def height(self):
        return max([w.y + w.height for w in self]) 
       
# create the page layout

class OutlinedRectagle(displayio.Group):
    def __init__(self, *, scale: int = 1, x: int = 0, y: int = 0) -> None:
        super().__init__(scale=scale, x=x, y=y)
        

def make_icon(paths, width, height, color=0xffffff, x=0, y=0):
    pal = displayio.Palette(1)
    pal[0] = color
    points0 = []
    for i in range(len(paths)):
        (dx,dy) = icons.batt[i]
        dx = int(dx * width)
        dy = int(dy * height)
        points0.append((dx,dy))
    icon = vectorio.Polygon(pixel_shader=pal, points=points0, x=x, y=y)
    svg_group = displayio.Group()
    svg_group.append(icon)
    return svg_group




