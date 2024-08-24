# servo_animation_code.py -- show simple servo animation list
import time, random, board
from pwmio import PWMOut
from adafruit_motor import servo
from logger import LOGGER

class CylonServo():
    in_motion = False

    animation_frames = []

    def __init__(self, servo_pin):
        LOGGER.info("Setting up PWM and servo")
        pwm = PWMOut(servo_pin, frequency=50)
        self.neck_servo = servo.Servo(pwm_out=pwm, min_pulse=700, max_pulse=2400)
        self.neck_servo.angle = 90

    def move_to(self, angle: int, travel_secs: float = 0.5, ease_speed: float = 0.1, ease_steps: int = 50):
        self.neck_servo.angle = angle
        return
        LOGGER.debug("Servo moving from %s to %s in %s seconds", self.neck_servo.angle, angle, travel_secs)
        
        self.animation_frames.clear()

        current_angle = self.neck_servo.angle
        for i in range(ease_steps):
            current_angle += (angle - self.neck_servo.angle) * ease_speed
            self.animation_frames.append(current_angle)

    def step(self):
        return
        if len(self.animation_frames) > 0:
            self.in_motion = True
            self.neck_servo.angle = self.animation_frames.pop(0)
        else:
            if self.in_motion:
                self.in_motion = False
                LOGGER.debug("Servo move complete")



