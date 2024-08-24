import struct
import analogio
import board
import microcontroller
from constants import Const
from cylon_servo import CylonServo
from logger import LOGGER
from varspeed import Vspeed
from settings import Settings
import neopixel



class CylonState:
    servo_target = 90
    servo_current = 90
    mic_level = 0
    mounth = [(0,0,0,0)]*8
    color = (0,255,0,0)
    eye_right = [color]*7
    eye_left = [color]*7
    battery = 0
    servo_sequence = []
    running = False


    has_update = False

    def __init__(self) -> None:
        self.vs = Vspeed(init_position=90, result="int")
        self.vs.set_bounds(lower_bound=0, upper_bound=180)
        self.battery_in = analogio.AnalogIn(board.A2)
        self.neck = CylonServo(Settings.servo_pin)
        self.strip = neopixel.NeoPixel(Settings.led_pin, Settings.total_leds, brightness=Settings.led_max_brightness, auto_write=False, pixel_order=neopixel.GRBW)
        self.strip.fill((0,255,0,0))


    def __str__(self) -> str:
        return "Mouth: {}, Left Eye: {}, Right Eye: {} ".format(self.mic_level, self.eye_left, self.eye_right)

    def _get_voltage(self):
        # Adafruit doesn't say anything about mulptiplying by 2, but it's going through a 50% voltage diviver, so...
        return (self.battery_in.value / 65535) * self.battery_in.reference_voltage * 2

    def set_from_message(self, message: bytearray):
        servo_position, servo_easing_int, servo_travel_secs, servo_steps,  *flat_leds = struct.unpack(f"<hhfh{Settings.total_leds * 4}h", message)

        self.set_servo(
            position=servo_position, 
            easing=Const.INT_TO_EASING_MAP[servo_easing_int], 
            travel_secs=servo_travel_secs, 
            ease_steps=servo_steps
        )

        leds_it = iter(flat_leds)
        leds = list(zip(leds_it, leds_it, leds_it, leds_it))
        self.strip[0:Settings.total_leds] = leds
        self.strip.show()

    def build_heartbeat(self):
        self.update_battery()
        message = struct.pack('ff', self.battery, microcontroller.cpu.temperature)
        
        return message

    def build_message(self):
        message = struct.pack(
            '<hs20fhh56h', 
            self.mic_level, 
            self.servo_target, 
            self.eye_left + self.eye_right
        )

        return message
    
    def update_battery(self):
        self.battery = self._get_voltage()

    def set_mic_level(self, level: int):
        self.mic_level = level

    def set_left_eye(self, leds: list[tuple[int,int,int,int]]):
        self.eye_left = leds

    def set_right_eye(self, leds: list[tuple[int,int,int,int]]):
        self.eye_right = leds

    def set_eyes(self, left_leds: list[tuple[int,int,int,int]], right_leds: list[tuple[int,int,int,int]]):
        self.set_left_eye(left_leds)
        self.set_right_eye(right_leds)
        
    def set_servo(self, position: int, easing: str = "QuadEaseOut", travel_secs: float = 0.5, ease_steps: int = 30):
        if self.servo_target != position:
            LOGGER.debug("Servo getting set to %s", position)
            self.move_to(position, ease_steps=ease_steps, travel_secs=travel_secs, easing=easing)

    def move_to(self, target_angle: int, travel_secs: float = 0.5, ease_steps: int = 30, easing: str = "QuadEaseInOut"):
        self.servo_target = target_angle
        self.servo_sequence = [(target_angle, travel_secs, ease_steps, easing)]
        
        LOGGER.debug("Servo moving from %s to %s in %s seconds", self.servo_target, target_angle, travel_secs)

    def servo_step(self):
        position, self.running, changed = self.vs.sequence(sequence=self.servo_sequence)
        if changed:
            # print(f'Sequence Num: {self.vs.seq_pos}, Step: {self.vs.step}, Position: {position}')
            self.neck.move_to(position)