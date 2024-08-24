import adafruit_debouncer as debouncer
import adafruit_wii_classic as controller
from ulab import numpy as np
from logger import LOGGER
from timeit import TimeIt

class WiiController:
    map = {}
    
    changed = {}

    increment_size = 6
    joy_range = np.array((6,56))
    servo_range = np.array((0,180/increment_size))
    last_x = 128

    def __init__(self, i2c) -> None:
        self.wc = controller.Wii_Classic(i2c=i2c)
        self.last_values = self.wc.values
        self._init_button_map()
        self.timeit = TimeIt()
        # Precalculate the joystick to servo value mappings
        self.joy_servo_map = {k: round(np.interp(k, self.joy_range, self.servo_range)[0] * self.increment_size) for k in range(0,256)}
    
    def __str__(self) -> str:
        return str(self.wc.buttons)
    
    def update(self):
        # self.timeit = TimeIt()
        values = self.wc.values
        
        changed = {}
        
        if values != self.last_values :
            # print(values)
            for attr in ["d_pad", "buttons"]:
                # print(f"Attr: {attr}")
                subset = getattr(values, attr)
                for name in dir(subset)[1:]:
                    if self.get_button_value(name) != getattr(subset, name):
                        changed[name] = getattr(subset, name)
        
        self.changed = changed
        self.last_values = values

        # print("update time:")
        # self.timeit.stop()
        
        # print("process events time:")
        # self.timeit = TimeIt()
        self.process_events()
        # self.timeit.stop()        

    def process_events(self):
        for button_name, value in self.changed.items():
            if value:
                self.map[button_name].press_event(context_values=self.last_values)
        
    def _init_button_map(self):
        for attr in ["d_pad", "buttons"]:
            subset = getattr(self.last_values, attr)
            for name in dir(subset)[1:]:
                self.map[name] = ButtonMap(name)

    def add_button_map(self, button_name, callback, modifier_button=None):
        button_map = self.map[button_name]
        button_map.add_callback(callback=callback, modifier_name=modifier_button)
        

    def joystick_servo(self):
        left_x, left_y = self.wc.joystick_l
        return self.joy_servo_map[left_x]

    def get_button_value(self, button_name, haystack = None):
        if haystack == None:
            haystack = self.last_values
        if hasattr(haystack.buttons, button_name):
            return getattr(haystack.buttons, button_name)
        if hasattr(haystack.d_pad, button_name):
            return getattr(haystack.d_pad, button_name)
        raise Exception("can't find input group")
    



class ButtonMap:
    
    
    def __init__(self, button_name) -> None:
        self.button_name = button_name
        self.callbacks = {}
        
    def add_callback(self, callback, modifier_name: None):
        self.callbacks[modifier_name] = callback
        
    def press_event(self, context_values):
        LOGGER.debug(f"Button {self.button_name} pressed!")
        for modifier_name, callback in self.callbacks.items():
            if modifier_name == None:
                continue
            if self._get_button_value(modifier_name, haystack=context_values):
                LOGGER.debug(f"Running callback because {modifier_name} was also pressed.")
                callback()
                return  
        if None in self.callbacks:
            LOGGER.debug(f"Running default callback because no modifiers setup or pressed")
            self.callbacks[None]()
        else:
            LOGGER.debug(f"No default callback set for {self.button_name}.")
            
    def _get_button_value(self, button_name, haystack = None):
        if haystack == None:
            haystack = self.last_values
        if hasattr(haystack.buttons, button_name):
            return getattr(haystack.buttons, button_name)
        if hasattr(haystack.d_pad, button_name):
            return getattr(haystack.d_pad, button_name)
        raise Exception("can't find input group")
            



# class WiiController:
#     buttons = []
#     map = {}

#     increment_size = 6
#     joy_range = np.array((6,56))
#     servo_range = np.array((0,180/increment_size))
#     last_x = 128

#     def __init__(self, i2c) -> None:
#         self.wc = controller.Wii_Classic(i2c=i2c)
#         self.timeit = TimeIt()
#         # Precalculate the joystick to servo value mappings
#         self.joy_servo_map = {k: round(np.interp(k, self.joy_range, self.servo_range)[0] * self.increment_size) for k in range(0,256)}
    
#     def __str__(self) -> str:
#         return str(self.wc.buttons)
    
#     def update(self):
#         self.timeit.stop()
#         # print(self.wc.values)

#         for button in self.buttons:
#             button.update()

#         self.timeit = TimeIt()
        
#     def add_button_map(self, button, callback, modifier_button=None):
#         self.buttons.append(ButtonMap(wc=self.wc, button_name=button, callback=callback, modifier_name=modifier_button))

#     def joystick_servo(self):
#         left_x, left_y = self.wc.joystick_l
#         return self.joy_servo_map[left_x]

# class ButtonMap:
#     modifier = None

#     def __init__(self, wc, button_name, callback, modifier: None) -> None:

#         self.wc = wc
#         self.button_name = button_name
#         self.button = debouncer.Button(lambda: self.get_button_value(button_name))
#         if modifier != None:
#             self.modifier = debouncer.Button(lambda: self.get_button_value(modifier))
#         self.callback = callback
    
#     def update(self):
#         self.button.update()
#         if self.button.rose:
#             if self.modifier != None:
#                 self.modifier.update()
#                 if not self.modifier.value:
#                     return
#             self.callback()
            
#     def get_button_value(self, button):
#         if hasattr(self.wc.buttons, button):
#             return getattr(self.wc.buttons, button)
#         if hasattr(self.wc.d_pad, button):
#             return getattr(self.wc.d_pad, button)
#         raise Exception("can't find input group")