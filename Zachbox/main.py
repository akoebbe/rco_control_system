# import test

import board
import asyncio
from busio import I2C
from ulab import numpy as np
from logger import LOGGER
import adafruit_logging as logging
from settings import Settings
from cylon_state import CylonState
from mic import PDM2040 as MicMonitor
from connection_espnow import ConnectionEspnow
from wii_controller import WiiController
import time
import random

LOGGER.setLevel(logging.INFO)

state = CylonState()

last_position = None

state.set_mic_level(0)
state.set_servo(90)

# connection = ConnectionWifi(role=ConnectionWifi.ROLE_HOST, peer="192.168.4.2")
connection = ConnectionEspnow(peer=Settings.espnow_cylon_mac)
connection.connect()
i2c = board.STEMMA_I2C()


async def mic_check():
    mic = MicMonitor(board.STEMMA_I2C(), 0x40)
    last_value = None

    while True:
        state.set_mic_level(mic.get_value())
        if last_value is None or state.mic_level != last_value:
            send_update()
            last_value = state.mic_level
        await asyncio.sleep(0)

async def button_watcher():
    wc = WiiController(i2c=board.STEMMA_I2C())

    wc.add_button_map(Settings.controller_mic_min_up[0], lambda: state.adjust_mic_mouth_range((1,0)), modifier_button=Settings.controller_mic_min_up[1])
    wc.add_button_map(Settings.controller_mic_min_down[0], lambda: state.adjust_mic_mouth_range((-1,0)), modifier_button=Settings.controller_mic_min_down[1])
    wc.add_button_map(Settings.controller_mic_max_up[0], lambda: state.adjust_mic_mouth_range((0,1)) , modifier_button=Settings.controller_mic_max_up[1])
    wc.add_button_map(Settings.controller_mic_max_down[0], lambda: state.adjust_mic_mouth_range((0,-1)) , modifier_button=Settings.controller_mic_max_down[1])

    wc.add_button_map(Settings.controller_eyecolor_next[0], lambda: state.eyes.build_blink_frames(state.eyes.color_next(False)), modifier_button=Settings.controller_eyecolor_next[1])
    wc.add_button_map(Settings.controller_eyecolor_prev[0], lambda: state.eyes.build_blink_frames(state.eyes.color_prev(False)), modifier_button=Settings.controller_eyecolor_prev[1])
    wc.add_button_map(Settings.controller_mouthcolor_next[0], lambda: state.mouth.next_color(), modifier_button=Settings.controller_mouthcolor_next[1])
    wc.add_button_map(Settings.controller_mouthcolor_prev[0], lambda: state.mouth.prev_color(), modifier_button=Settings.controller_mouthcolor_prev[1])
    
    wc.add_button_map(Settings.controller_blink[0], state.eyes.build_blink_frames, modifier_button=Settings.controller_blink[1])
    wc.add_button_map(Settings.controller_blink_auto_toggle[0], state.blink_auto_toggle, modifier_button=Settings.controller_blink_auto_toggle[1])
    wc.add_button_map(Settings.controller_ohnono[0], state.ohnonono, modifier_button=Settings.controller_ohnono[1])
    wc.add_button_map(Settings.controller_togglescreen[0], state.disp.toggle_display, Settings.controller_togglescreen[1])

    LOGGER.info(wc)
    last_servo_position = 128

    while True:
        try:
            wc.update()
            position = wc.joystick_servo()
            
            if position != last_servo_position:
                state.set_servo(position)
                last_servo_position = position
                send_update()
            
        except OSError as e:
            LOGGER.info("Lost connection to Wii Controller. Will try to reconnect.")
            continue

        await asyncio.sleep(0)

async def animator():
    while True:
        if state.eyes.has_animation:
            state.eyes.animate()
            send_update()
        await asyncio.sleep(0.02)

async def heartbeat_listener():
    while True:
        state.zachbox_update()
        heartbeat_msg = connection.read()
        if heartbeat_msg != None:
            state.set_heartbeat_from_message(heartbeat_msg)
            LOGGER.info("Battery: %sv, %s life, %sC, %s%%", state.battery, state.get_battery_remaining(), state.temp, state.get_signal_percent())
        await asyncio.sleep(.5)

async def auto_blink():
    next_blink_time = time.monotonic() + (random.random() * (Settings.eye_blink_max_secs - Settings.eye_blink_min_secs)) + Settings.eye_blink_min_secs
    
    while True:
        if state.blink_auto and time.monotonic() > next_blink_time:
            state.eyes.build_blink_frames()
            next_blink_time = time.monotonic() + (random.random() * (Settings.eye_blink_max_secs - Settings.eye_blink_min_secs)) + Settings.eye_blink_min_secs
        await asyncio.sleep(.3)

def send_update():
    #LOGGER.debug("Sending %s %s", mic_value, position)
    if not state.need_send:
        return

    message = state.build_message()
    # LOGGER.info("Build Time: %s", time.monotonic() - start)
    # struct.pack('hh56h', mic_value, int(position), *eyes.renderLeds())
    # udp_message = bytes(f"{mic_value},{position}", 'utf-8')
    #LOGGER.debug("Sending to %s:%s message: %s", HOST, PORT, message)
    connection.send(message)  # send packet


async def main():
    LOGGER.info("Starting main async loop.")
    mic_task = asyncio.create_task(mic_check())
    nc_task = asyncio.create_task(button_watcher())
    animate_task = asyncio.create_task(animator())
    heartbeat_task = asyncio.create_task(heartbeat_listener())
    auto_blink_task = asyncio.create_task(auto_blink())

    await asyncio.gather(mic_task, nc_task, animate_task, heartbeat_task, auto_blink_task) 

asyncio.run(main())

LOGGER.warning("Completed asyncio main loop. This shouldn't happen.")
