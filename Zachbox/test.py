import board
from adafruit_bus_device.i2c_device import I2CDevice
import time
import struct

i2c = board.STEMMA_I2C()
kb = I2CDevice(i2c=i2c, device_address=0x40)
readbuf = bytearray(2)

while True:
    with kb as mic:
        try:
            mic.readinto(readbuf)
        except OSError as e:
            pass
    print(struct.unpack('H',readbuf)[0])



# SPDX-FileCopyrightText: 2018 Kattni Rembor for Adafruit Industries
#
# SPDX-License-Identifier: MIT

import board
import audiobusio
from microcontroller import Pin


def is_hardware_PDM(clock, data):
    try:
        p = audiobusio.PDMIn(clock, data)
        p.deinit()
        return True
    except ValueError:
        return False
    except RuntimeError:
        return True


def get_unique_pins():
    exclude = ['NEOPIXEL', 'APA102_MOSI', 'APA102_SCK']
    pins = [pin for pin in [
        getattr(board, p) for p in dir(board) if p not in exclude]
            if isinstance(pin, Pin)]
    unique = []
    for p in pins:
        if p not in unique:
            unique.append(p)
    return unique


for clock_pin in get_unique_pins():
    for data_pin in get_unique_pins():
        if clock_pin is data_pin:
            continue
        if is_hardware_PDM(clock_pin, data_pin):
            print("Clock pin:", clock_pin, "\t Data pin:", data_pin)
        else:
            pass
