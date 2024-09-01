from constants import Const
import struct
from logger import LOGGER
from varspeed import Vspeed
from eyes import Eyes
from display import ZachboxDisplay
from settings import Settings
from mouth import Mouth
from filters import SmoothingFilter, MedianFilter
from ulab import numpy as np
import microcontroller 

class CylonState:
    
    servo_target = 90
    servo_current = 90
    mic_level = 0
    mouth = [(0,0,0,0)]*8
    color = (0,255,0,0)
    servo_sequence = []
    running = False
    has_update = False
    eyes = Eyes(color)
    total_leds = Settings.led_count_left_eye + Settings.led_count_right_eye + (Settings.mouth_led_per_row * Settings.mouth_row_count)
    mouth = Mouth(Settings.mouth_led_per_row, Settings.mouth_row_count, Settings.mouth_style)
    servo_travel_secs = Settings.servo_travel_secs
    servo_steps = Settings.servo_steps
    servo_easing = Const.EASING_TO_INT_MAP[Settings.servo_easing]
    _blink_auto = Settings.eye_blink_auto

    _mic_mouth_range = (Settings.mic_min, Settings.mic_max)
    _battery = MedianFilter(window_size=10)
    _temp = MedianFilter(window_size=10)
    _zachbox_temp = MedianFilter(window_size=10)
    disp = ZachboxDisplay()
    _rssi = MedianFilter()

    def __init__(self):
        self.vs = Vspeed(init_position=90, result="int")
        self.vs.set_bounds(lower_bound=0, upper_bound=180)
        self.disp.add_status_indicator(column=0, slot=0, key="zachbox_temp", label_text="Temp", value=microcontroller.cpu.temperature)
        self.disp.add_status_indicator(column=0, slot=1, key="mic_min", label_text="Mic Min", value=self._mic_mouth_range[0])
        self.disp.add_status_indicator(column=0, slot=2, key="mic_max", label_text="Mic Max", value=self.mic_mouth_range[1])
        self.disp.add_status_indicator(column=0, slot=3, key="blink_auto", label_text="Auto Blink", value=self.blink_auto)
        self.disp.add_meter(column=0, slot=4, key="mic", label_text="Mic", full_width=True, floor=Settings.mic_min, ceiling=Settings.mic_max)
        self.disp.add_status_indicator(column=1, slot=0, key="batt", label_text="Battery", value=self.battery)
        self.disp.add_status_indicator(column=1, slot=1, key="temp", label_text="Temp", value=self.temp)
        self.disp.add_status_indicator(column=1, slot=2, key="rssi", label_text="Signal", value=self.rssi)

        # Precalculate the mic value to mouth value mappings using the mic_min and mic_max from the settings file.
        self._generate_mic_mouth_map()


    def __str__(self) -> str:
        return "Mouth: {}, Left Eye: {}, Right Eye: {} ".format(self.mic_level, self.eye_left, self.eye_right)

    def set_from_message(self, message: bytearray):
        mic_level, servo_position, *eyes = struct.unpack(f"hh{self.total_leds * 4}h", message)

        self.set_mic_level(mic_level)
        self.set_servo(servo_position)

        eyes_it = iter(eyes)
        eye_leds = list(zip(eyes_it, eyes_it, eyes_it, eyes_it))
        self.eyes.set_eyes(eye_leds[0:8], eye_leds[8:])

    def set_heartbeat_from_message(self, message: bytearray):
        battery, temp = struct.unpack('ff', message.msg)
        
        self.battery = battery
        self.temp = temp
        self.rssi = message.rssi
        
    def build_message(self):
        LOGGER.debug("Sending message: m-%s s-%s",  self.mic_level, self.servo_current)

        message = struct.pack(
            f"<hhfh{self.total_leds * 4}h", 
            self.servo_current,
            self.servo_easing,
            self.servo_travel_secs,
            self.servo_steps,
            *self._build_leds()
        )

        self.has_update = False

        return message
    
    def zachbox_update(self):
        self.zachbox_temp = microcontroller.cpu.temperature
            
    def get_battery_remaining(self):
        '''
        Seems like the spec sheet says the esp32-s3 con operate down to 3.0V
        Battery seems to max out at 3.99, so 3.00-3.99 is a rough window of power
        '''
        value = int(((self.battery - 3) / 0.85) * 255)
        return self._clamp(value, 0 , 255)

    def get_battery_percentage(self):
        value = self.get_battery_remaining() / 255 * 100
        return f"{value:.0f}%"

    def get_signal_percent(self):
        value = ((60 - self._clamp(abs(self.rssi) - 30, 0, 60)) / 60) * 100
        return value 

    @property
    def battery(self):
        return self._battery.value

    @battery.setter
    def battery(self, battery):
        self._battery.update(battery)
        self.disp.update_value("batt", self.get_battery_percentage())
        
    @property
    def temp(self):
        return self._temp.value
    
    @temp.setter
    def temp(self, temp):
        self._temp.update(temp)
        self.disp.update_value("temp", f"{self.temp}C")

    @property
    def zachbox_temp(self):
        return self._zachbox_temp.value
    
    @zachbox_temp.setter
    def zachbox_temp(self, temp):
        self._zachbox_temp.update(temp)
        self.disp.update_value("zachbox_temp", f"{self.zachbox_temp}C")

    @property
    def is_plugged_in(self):
        return self._battery > 4.1

    @property
    def rssi(self):
        return self._rssi.value        

    @rssi.setter
    def rssi(self, rssi):
        self._rssi.update(rssi)
        self.disp.update_value("rssi", f"{self.get_signal_percent():.0f}%")

    def _clamp(self, value, lower_bound, upper_bond):
        return min(upper_bond, max(value, lower_bound))

    @property
    def need_send(self):
        return self.has_update or self.eyes.has_update

    @property
    def mic_mouth_range(self):
        return self._mic_mouth_range
    
    @mic_mouth_range.setter
    def mic_mouth_range(self, mouth_range:tuple[int,int]):
        self._mic_mouth_range = mouth_range
        self.disp.update_value("mic_min", mouth_range[0])
        self.disp.update_value("mic_max", mouth_range[1])
        self._generate_mic_mouth_map()
        
    @property
    def blink_auto(self):
        return self._blink_auto
    
    @blink_auto.setter
    def blink_auto(self, enabled):
        self._blink_auto = enabled
        self.disp.update_value("blink_auto", enabled)
    
    def blink_auto_toggle(self):
        self.blink_auto = not self.blink_auto

    def _build_leds(self):
        leds = []
        for segment in Settings.led_connection_order:
            if segment == Const.LEFT_EYE:
                leds += self.eyes.render_left_leds()
            elif segment == Const.RIGHT_EYE:
                leds += self.eyes.render_right_leds()
            elif segment == Const.MOUTH:
                leds += self.mouth.render()
                    
        flattend_list = [item for sublist in leds for item in sublist]
        return flattend_list
            
    def set_mic_level(self, level: int):
        if self.mic_level != level:
            self.mic_level = level
            # TODO: Interpolate based on noise floor and ceiling 
            self.mouth.value = self.mic_mouth_map[level]
            self.has_update = True
            self.disp.update_meter("mic", level/255)
            
    def _generate_mic_mouth_map(self):
        mic_range = np.array((0,255))
        window_range = np.array(self.mic_mouth_range)
        self.mic_mouth_map = {k: round(np.interp(k, window_range, mic_range)[0]) for k in range(0,256)}
        
    def adjust_mic_mouth_range(self, delta: tuple[int, int]):
        self.mic_mouth_range = (
            self._clamp(self.mic_mouth_range[0] + delta[0], 0, 255),
            self._clamp(self.mic_mouth_range[1] + delta[1], 0, 255)
        )
        self.disp.update_meter_bounds('mic', self.mic_mouth_range[0], self.mic_mouth_range[1])
        LOGGER.info(self.mic_mouth_range)

    def set_servo(self, position: int):
        if self.servo_current != position:
            #print(f'Sequence Num: {self.vs.seq_pos}, Step: {self.vs.step}, Position: {position}')
            self.servo_current = position
            self.has_update = True
        # if self.servo_target != position:
        #     LOGGER.debug("Servo getting set to %s", position)
        #     self.move_to(position, ease_steps=20)

    async def ohnonono(self):
            last_position = self.servo_target
            servo_time=.5
            self.set_servo(0)
            send_update()
            await asyncio.sleep(servo_time)
            self.set_servo(180)
            send_update()
            await asyncio.sleep(servo_time)
            self.set_servo(0)
            send_update()
            await asyncio.sleep(servo_time)
            self.set_servo(180)
            send_update()
            await asyncio.sleep(servo_time)
            self.set_servo(0)
            send_update()
            await asyncio.sleep(servo_time)
            self.set_servo(last_position)
            send_update()
            
    # def move_to(self, target_angle: int, travel_secs: float = 0.5, ease_speed: float = 0.1, ease_steps: int = 50):
    #     self.servo_target = target_angle
    #     self.servo_sequence = [(target_angle, 0.1, 20, 'QuarticEaseOut')]
        
    #     LOGGER.debug("Servo moving from %s to %s in %s seconds", self.servo_target, target_angle, travel_secs)

    # def servo_step(self):
    #     position, self.running, changed = self.vs.sequence(sequence=self.servo_sequence)
    #     if changed:
    #         # print(f'Sequence Num: {self.vs.seq_pos}, Step: {self.vs.step}, Position: {position}')
    #         self.servo_current = position
    #         self.has_update = True
