# SPDX-FileCopyrightText: 2017 Limor Fried for Adafruit Industries
#
# SPDX-License-Identifier: MIT

import array
import board
from analogio import AnalogIn
from analogbufio import BufferedIn
from ulab import numpy as np
import math
import time
from logger import LOGGER
from filters import MedianFilter, AmplitudeFilter
import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
from audiobusio import PDMIn
from busio import I2C
from adafruit_bus_device.i2c_device import I2CDevice
import struct



# New stuff that will probably work just fine
# https://learn.adafruit.com/labo-piano-light-fx/software
# ----------------------------------------------------------------------------

n_pixels = 8 # Number of pixels you are using
dc_offset = 0  # DC offset in mic signal - if unusure, leave 0
noise = 0  # Noise/hum/interference in mic signal
lvl = 10  # Current "dampened" audio level
maxbrt = 127  # Maximum brightness of the neopixels (0-255)
wheelStart = 0  # Start of the RGB spectrum we'll use
wheelEnd = 255  # End of the RGB spectrum we'll use
sample_count = 100
last_value = 0

mic_range = np.array([0, 255])
other_range = np.array([100, 255])
brightness_range = np.array([0, maxbrt])
output_min = 100
output_max = 150

# adc = ADS.ADS1015(i2c=board.STEMMA_I2C(), gain=1, data_rate=3300, mode=ADS.Mode.SINGLE)
# chan = AnalogIn(adc, ADS.P0)
# while True:
#     #print((mic.value,))
#     print((chan.value,chan.voltage))
#     # time.sleep(.01)


# b = bytearray(200)
# pdm = PDMIn(board.A1, board.A0, sample_rate=22050)
# while True:
#     pdm.record(b, len(b))
#     print(b)



class PDM2040:
    
    range_min = 0
    # range_max = 4656
    range_max = 2656
    range_floor = 45

    
    def __init__(self, i2c, address, window_size=3):
        time.sleep(1)

        i2c = board.STEMMA_I2C()
        self.mic = I2CDevice(i2c=i2c, device_address=address)
        self.readbuf = bytearray(2)
    
        self.log_lo = math.log(self.range_floor)
        self.log_hi = math.log(self.range_max)

    def get_value(self):
        with self.mic as mic:
            try:
                mic.readinto(self.readbuf)
            except OSError as e:
                pass
        value = struct.unpack('H',self.readbuf)[0]
        value = int((math.log(float(self._clamp(value)))-self.log_lo)/(self.log_hi-self.log_lo) * 255)
        return value


    def _clamp(self, value):
        return min(self.range_max, max(value, self.range_floor))

    
    def gather_min_max(self, seconds: int):

        LOGGER.info("checking min: BE QUIET! Starting in 3 seconds")
        time.sleep(3)
        LOGGER.info("starting noise floor")
        start = time.monotonic()
        end = start + seconds
        while time.monotonic() < end:
            value = abs(self.mic.value)
            self.range_min = min(self.range_min, value)
        LOGGER.info("Noise floor detected: %s",self.range_min)


        LOGGER.info("checking min: BE LOUD! Starting in 3 seconds")
        time.sleep(3)
        LOGGER.info("starting noise floor")
        start = time.monotonic()
        end = start + seconds
        while time.monotonic() < end:
            value = abs(self.mic.value)
            self.range_max = max(self.range_max, value)
        LOGGER.info("Max amplitude detected: %s",self.range_max)

    def auto_range(self):
        self._gather_min_max(3)


### Look at these examples for filters: https://courses.ideate.cmu.edu/16-223/f2021/text/code/pico-signals.html#median-py


offset = 2300
sample_count = 10



# mic = AnalogIn(board.A5)
# while True:
#     #print((mic.value,))
#     print((mic.value,mic.reference_voltage))
#     time.sleep(.02)


sample_buffer = np.array([0]*sample_count, dtype=np.uint16)

# median = MedianFilter(window_size=5)


class ADSMicMonitor:

    range_min = 0
    # range_max = 4656
    range_max = 2656
    range_floor = 20

    def __init__(self, mic_pin, window_size=3):
        """Non-linear filter to reduce signal outliers by returning the median value
        of the recent history.  The window size determines how many samples
        are held in memory.  An input change is typically delayed by half the
        window width.  This filter is useful for throwing away isolated
        outliers, especially glitches out of range.
        """

        adc = ADS.ADS1015(i2c=board.STEMMA_I2C(), gain=16, data_rate=3300, mode=ADS.Mode.SINGLE)
        self.channels = [
            AnalogIn(adc, ADS.P2),
            AnalogIn(adc, ADS.P0, ADS.P1),
            AnalogIn(adc, ADS.P3),
        ]

        self.mic = self.channels[0] # Setting for later

        self.window_size = window_size
        self.ring = array.array("H", [0x0000] * window_size)     # ring buffer for recent time history
        #self.ring = [0] * window_size     # ring buffer for recent time history
        self.oldest = 0                   # index of oldest sample
        self.lvl = 0

        self.offset_point = 0

        self.log_lo = math.log(self.range_floor)
        self.log_hi = math.log(self.range_max)


    def update(self):
        # save the new sample by overwriting the oldest sample
        # print(self.mic.value)
        self.ring[self.oldest] = abs(self.mic.value)
        self.oldest += 1
        if self.oldest >= self.window_size:
            self.oldest = 0

        # self.mic.readinto(self.ring)
        # return the value in the middle


    # def __init__(self, mic_pin, sample_rate, sample_count):
    #     # mic_pin = AnalogIn(board.GPIO8)

    def dcoffset(self):
        print (sum(x - self.offset_point for x in self.ring) / self.window_size)

    def normalize(self):
        return [abs(x - self.offset_point) for x in self.ring]

    def amplitude(self):
        return max(self.ring) - min(self.ring)

    def median(self):
        # save the new sample by overwriting the oldest sample
        in_order = sorted(self.normalize)

        # return the value in the middle
        median = in_order[self.window_size//2]
        # print(median)
        return median

    def mean(self):
        avg = sum(self.normalize()) / self.window_size
        # print(avg)
        return int(avg)

    def _collect_samples(self):
        self.mic_pin.readinto(self.samples)

    def _normalize_samples(self, samples_in):
        #LOGGER.debug("norm in: %s", samples_in)
        norm = abs(samples_in)
        norm = np.interp(norm, [self.range_floor,self.range_max], [0,255])
        #LOGGER.debug("norm out: %s", norm)
        return norm


    def _rms_samples(self, samples_in):
        # minbuf = np.mean(samples_in)
        # LOGGER.debug("minbuf: %s", minbuf)
        sq_samples = (samples_in)**2
        LOGGER.debug("sq_samples: %s", sq_samples)
        sqrt_samples = math.sqrt(np.mean(sq_samples))
        LOGGER.debug("sqrt_samples: %s", sqrt_samples)
        return sqrt_samples

    def _dampen(self, value):
        # "Dampened" reading (else looks twitchy) - divide by 8 (2^3)
        #LOGGER.debug("lvl in: %s", self.lvl)
        self.lvl = (self.lvl * 2 + value) / 3
        #LOGGER.debug("lvl out: %s", self.lvl)
        return self.lvl

    def _clamp(self, value):
        return min(self.range_max, max(value, self.range_floor))

    def old_get_value(self):
        self._collect_samples()
        rms_value = self._rms_samples(self._normalize_samples(self.samples))
        output = self._dampen(rms_value)
        # LOGGER.info("rms:: %s", rms_value)
        # dampened_value = self._dampen(rms_value)
        return int(output)

    def get_value(self):
        self.update()
        # self.dcoffset()
        value = self.mean()
        # LOGGER.info("mean: %s", value)
        # value = int(value / self.range_max * 255)
        value = int((math.log(float(self._clamp(value)))-self.log_lo)/(self.log_hi-self.log_lo) * 255)
        # LOGGER.info("\t\tlog: %s", value)
        # value = int(self._dampen(value))
        # print(value)
        return value

    def gather_min_max(self, seconds: int):

        LOGGER.info("checking min: BE QUIET! Starting in 3 seconds")
        time.sleep(3)
        LOGGER.info("starting noise floor")
        start = time.monotonic()
        end = start + seconds
        while time.monotonic() < end:
            value = abs(self.mic.value)
            self.range_min = min(self.range_min, value)
        LOGGER.info("Noise floor detected: %s",self.range_min)


        LOGGER.info("checking min: BE LOUD! Starting in 3 seconds")
        time.sleep(3)
        LOGGER.info("starting noise floor")
        start = time.monotonic()
        end = start + seconds
        while time.monotonic() < end:
            value = abs(self.mic.value)
            self.range_max = max(self.range_max, value)
        LOGGER.info("Max amplitude detected: %s",self.range_max)

    def auto_range(self):
        self._gather_min_max(3)





class MicMonitor:

    range_min = 0
    range_max = 4656
    range_floor = 50

    def __init__(self, mic_pin, window_size=1000):
        """Non-linear filter to reduce signal outliers by returning the median value
        of the recent history.  The window size determines how many samples
        are held in memory.  An input change is typically delayed by half the
        window width.  This filter is useful for throwing away isolated
        outliers, especially glitches out of range.
        """

        adc = ADS.ADS1015(i2c=board.STEMMA_I2C(), gain=8, data_rate=3300, mode=ADS.Mode.SINGLE)
        self.channels = [
            AnalogIn(adc, ADS.P0, ADS.P1),
            AnalogIn(adc, ADS.P2),
            AnalogIn(adc, ADS.P3),
        ]

        self.input = self.channels[0] # Setting for later

        self.window_size = window_size
        self.ring = array.array("H", [0x0000] * window_size)     # ring buffer for recent time history
        #self.ring = [0] * window_size     # ring buffer for recent time history
        self.oldest = 0                   # index of oldest sample
        #self.mic = AnalogIn(mic_pin)
        self.mic = BufferedIn(mic_pin, sample_rate=44100)
        self.lvl = 0

        self.lo  = 15
        self.hi = 150

        self.offset_point = (65536 / 2) - 800

        self.log_lo = math.log(self.lo)
        self.log_hi = math.log(self.hi)


    def update(self):
        # save the new sample by overwriting the oldest sample
        # self.ring[self.oldest] = self.mic.value
        # self.oldest += 1
        # if self.oldest >= self.window_size:
        #     self.oldest = 0

        self.input.readinto(self.ring)
        # return the value in the middle


    # def __init__(self, mic_pin, sample_rate, sample_count):
    #     # mic_pin = AnalogIn(board.GPIO8)

    def dcoffset(self):
        print (sum(x - self.offset_point for x in self.ring) / self.window_size)

    def normalize(self):
        return [abs(x - self.offset_point) * 2 for x in self.ring]

    def amplitude(self):
        return max(self.ring) - min(self.ring)

    def median(self):
        # save the new sample by overwriting the oldest sample
        in_order = sorted(self.normalize)

        # return the value in the middle
        median = in_order[self.window_size//2]
        # print(median)
        return median

    def mean(self):
        avg = sum(self.normalize()) / self.window_size
        # print(avg)
        return int(avg)

    def _collect_samples(self):
        self.mic_pin.readinto(self.samples)

    def _normalize_samples(self, samples_in):
        #LOGGER.debug("norm in: %s", samples_in)
        norm = abs(samples_in - (65536 / 2))
        norm = np.interp(norm, [5000,32768-5*6400], [0,255])
        #LOGGER.debug("norm out: %s", norm)
        return norm


    def _rms_samples(self, samples_in):
        # minbuf = np.mean(samples_in)
        # LOGGER.debug("minbuf: %s", minbuf)
        sq_samples = (samples_in)**2
        LOGGER.debug("sq_samples: %s", sq_samples)
        sqrt_samples = math.sqrt(np.mean(sq_samples))
        LOGGER.debug("sqrt_samples: %s", sqrt_samples)
        return sqrt_samples

    def _dampen(self, value):
        # "Dampened" reading (else looks twitchy) - divide by 8 (2^3)
        #LOGGER.debug("lvl in: %s", self.lvl)
        self.lvl = (self.lvl * 2 + value) / 3
        #LOGGER.debug("lvl out: %s", self.lvl)
        return self.lvl

    def _clamp(self, value):
        return min(self.hi, max(value, self.lo))

    def old_get_value(self):
        self._collect_samples()
        rms_value = self._rms_samples(self._normalize_samples(self.samples))
        output = self._dampen(rms_value)
        # LOGGER.info("rms:: %s", rms_value)
        # dampened_value = self._dampen(rms_value)
        return int(output)

    def get_value(self):
        self.update()
        # self.dcoffset()
        value = self.mean()
        value = int(value / 65535 * 255)
        value = int((math.log(float(self._clamp(value)))-self.log_lo)/(self.log_hi-self.log_lo) * 255)
        # value = int(self._dampen(value))
        # print(value)
        return value

    def _gather_min_max(self, seconds: int):

        LOGGER.info("checking min: BE QUIET! Starting in 3 seconds")
        time.sleep(3)
        LOGGER.info("starting noise floor")
        start = time.monotonic()
        end = start + seconds
        while time.monotonic() < end:
            value = abs(self.input.value)
            self.range_min = min(self.range_min, value)
        LOGGER.info("Noise floor detected: %s",self.range_min)


        LOGGER.info("checking min: BE LOUD! Starting in 3 seconds")
        time.sleep(3)
        LOGGER.info("starting noise floor")
        start = time.monotonic()
        end = start + seconds
        while time.monotonic() < end:
            value = abs(self.input.value)
            self.range_max = max(self.range_max, value)
        LOGGER.info("Max amplitude detected: %s",self.range_max)

    def auto_range(self):
        self._gather_min_max(3)




    ### LED range stuff
    # result = int(np.interp(lvl, other_range, output_range)[0])
    # if result != last_value:
    #     print(result)
    #     last_value = result





#while True:

    # n = int((np.sqrt(np.mean(np.square(samples)))) / 65536) * 1000)  # 10-bit ADC format
    # n = abs(n - 512 - dc_offset)  # Center on zero

    # print("Step 1:\t {}".format(n));

    # if n >= noise:  # Remove noise/hum
    #     n = n - noise

    # print("Step 2:\t\t {}".format(n));


    # print("Step 3:\t\t\t {}".format(lvl));

    # Color pixels based on rainbow gradient
    # vlvl = np.interp(lvl, mic_range, output_range)[0]


    # print("Step 4:\t\t\t\t {}".format(brightness));

    # time.sleep(.001)

    # for i in range(0, n_pixels):
        # strip[i] = colorwheel(vlvl)
        # Set strip brightness based oncode audio level
        # strip.brightness = float(brightness) / 255.0
    # strip.show()


# ---------------------------------------------------------------------------------------------







# class MicAnalyzer():

#     n_pixels = 8  # Number of pixels you are using
#     dc_offset = 0  # DC offset in mic signal - if unusure, leave 0
#     noise = 100  # Noise/hum/interference in mic signal
#     samples = 1000  # Length of buffer for dynamic level adjustment
#     top = n_pixels  # Allow dot to go slightly off scale

#     vol_count = 0  # Frame counter for storing past volume data

#     lvl = 10  # Current "dampened" audio level
#     min_level_avg = 30  # For dynamic adjustment of graph low & high
#     max_level_avg = 200

#     # Collection of prior volume samples
#     # vol = array.array('H', [0] * samples)
#     vol = np.array([0]*samples, dtype=np.uint16)


#     mic_pin = BufferedIn(board.GPIO8, sample_rate=44100)
#     led_range = np.array((0,1,2,3,4,5,6,7,8))
#     vol_range = np.linspace(0, 2 ** 15, num=9)

#     def __init__(self, i2c):
#         self.nau7802 = NAU7802(i2c, address=0x2A, active_channels=1)


#     def remap_range(value, leftMin, leftMax, rightMin, rightMax):
#         # this remaps a value from original (left) range to new (right) range
#         # Figure out how 'wide' each range is
#         leftSpan = leftMax - leftMin
#         rightSpan = rightMax - rightMin

#         # Convert the left range into a 0-1 range (int)
#         valueScaled = int(value - leftMin) / int(leftSpan)

#         # Convert the 0-1 range into a value in the right range.
#         return int(rightMin + (valueScaled * rightSpan))


#     def getValue(self):

#         # print(self.vol_range)

#         # mic_pin = self.mic_pin
#         dc_offset = self.dc_offset
#         noise = self.noise
#         top = self.top
#         vol = self.vol
#         samples = self.samples
#         lvl = self.lvl
#         min_level_avg = self.min_level_avg
#         max_level_avg = self.max_level_avg
#         vol_count = self.vol_count

#         # mic_pin.readinto(vol)
#         return self.nau7802.read() / 2 ** 24 * 1000
#         upper = np.max(vol) - 65536 / 2
#         lower = np.min(vol) - 65536 / 2
#         lvl = max(abs(upper), abs(lower))
#         return int(np.interp(lvl, self.vol_range, self.led_range)[0])

#         return(lvl)
#         n = int((mic_pin.value / 65536) * 1000)  # 10-bit ADC format
#         n = abs(n - 512 - dc_offset)  # Center on zero

#         if n >= noise:  # Remove noise/hum
#             n = n - noise

#         # "Dampened" reading (else looks twitchy) - divide by 8 (2^3)
#         lvl = int(((lvl * 7) + n) / 8)

#         # Save sample for dynamic leveling
#         vol[vol_count] = n

#         # Advance/rollover sample counter
#         vol_count += 1

#         if vol_count >= samples:
#             vol_count = 0

#             # Get volume range of prior frames
#         min_level = vol[0]
#         max_level = vol[0]

#         for i in range(1, len(vol)):
#             if vol[i] < min_level:
#                 min_level = vol[i]
#             elif vol[i] > max_level:
#                 max_level = vol[i]

#         # minlvl and maxlvl indicate the volume range over prior frames, used
#         # for vertically scaling the output graph (so it looks interesting
#         # regardless of volume level).  If they're too close together though
#         # (e.g. at very low volume levels) the graph becomes super coarse
#         # and 'jumpy'...so keep some minimum distance between them (this
#         # also lets the graph go to zero when no sound is playing):
#         # Calculate bar height based on dynamic min/max levels (fixed point):
#         height = top * (lvl - min_level_avg) / (max_level_avg - min_level_avg)

#         # Clip output
#         if height < 0:
#             height = 0
#         elif height > top:
#             height = top

#         if (max_level - min_level) < top:
#             max_level = min_level + top

#         # Dampen min/max levels - divide by 64 (2^6)
#         min_level_avg = (min_level_avg * 63 + min_level) >> 6
#         # fake rolling average - divide by 64 (2^6)
#         max_level_avg = (max_level_avg * 63 + max_level) >> 6

#         return np.interp(n, self.vol_range, self.led_range)[0]
