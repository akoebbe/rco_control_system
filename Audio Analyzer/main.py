import array
import math
import board
import audiobusio
from i2ctarget import I2CTarget
import adafruit_logging as logging
import struct



import board
import neopixel_write
import digitalio

pix = digitalio.DigitalInOut(board.NEOPIXEL)
pix.direction = digitalio.Direction.OUTPUT




logger = logging.getLogger('i2ctarget')
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

# emulate a target with 16 registers
regs = [0] * 16
register_index = None

logger.info("\n\ncode starting...")

# Remove DC bias before computing RMS.
def mean(values):
    return sum(values) / len(values)


def normalized_rms(values):
    minbuf = int(mean(values))
    samples_sum = sum(
        float(sample - minbuf) * (sample - minbuf)
        for sample in values
    )

    return math.sqrt(samples_sum / len(values))



mic = audiobusio.PDMIn(board.A2, board.A3, sample_rate=22050, bit_depth=16)
samples = array.array('H', [0] * 220)

# board.STEMMA_I2C()

device = I2CTarget(board.D13, board.D12, (0x40,))


# initialize an I2C target with a device address of 0x40
while True:
    # check if there's a pending device request
    i2c_target_request = device.request()

    if not i2c_target_request:
        # no request is pending
        continue

    # `with` invokes I2CTargetRequest's functions to handle the necessary opening and closing of a request
    with i2c_target_request:
        # the address associated with the request
        address = i2c_target_request.address

        if i2c_target_request.is_read:
            logger.info(f"read request to address '0x{address:02x}'")

            mic.record(samples, len(samples))
            magnitude = normalized_rms(samples)
            buffer = struct.pack('H', int(magnitude))
            i2c_target_request.write(buffer)

        else:
            pixel_color = bytearray([0, 255, 0])
            # transaction is a write request
            data = i2c_target_request.read(1)
            logger.info(f"write request to address 0x{address:02x}: {data}")
            # for our emulated device, writes have no effect



# initialize an I2C target with a device address of 0x40
with I2CTarget(board.SCL, board.SDA, (0x40,)) as device:

    while True:
        # check if there's a pending device request
        i2c_target_request = device.request()

        if not i2c_target_request:
            # no request is pending
            continue

        # work with the i2c request
        with i2c_target_request:

            if not i2c_target_request.is_read:
                # a write request

                # bytearray contains the request's first byte, the register's index
                index = i2c_target_request.read(1)[0]

                # bytearray containing the request's second byte, the data
                data = i2c_target_request.read(1)

                # if the request doesn't have a second byte, this is read transaction
                if not data:

                    # since we're only emulating 16 registers, read from a larger address is an error
                    if index > 15:
                        logger.error(f"write portion of read transaction has invalid index {index}")
                        continue

                    logger.info(f"write portion of read transaction, set index to {index}'")
                    register_index = index
                    continue

                # since we're only emulating 16 registers, writing to a larger address is an error
                if index > 15:
                    logger.error(f"write request to incorrect index {index}")
                    continue

                logger.info(f"write request to index {index}: {data}")
            else:
                # our emulated device requires a read to be part of a full write-then-read transaction
                if not i2c_target_request.is_restart:
                    logger.warning(f"read request without first writing is not supported")
                    # still need to respond, but result data is not defined
                    i2c_target_request.write(bytes([0xff]))
                    register_index = None
                    continue

                # the single read transaction case is covered above, so we should always have a valid index
                assert(register_index is not None)

                # the write-then-read to an invalid address is covered above,
                #   but if this is a restarted read, index might be out of bounds so need to check
                if register_index > 16:
                    logger.error(f"restarted read yielded an unsupported index")
                    i2c_target_request.write(bytes([0xff]))
                    register_index = None
                    continue

                # retrieve the data from our register file and respond

                # Main program
                
                mic.record(samples, len(samples))
                magnitude = normalized_rms(samples)

                logger.info(f"read request from index {register_index}: {data}")
                i2c_target_request.write(bytes([magnitude]))

                # in our emulated device, a single read transaction is covered above
                #   so any subsequent restarted read gets the value at the next index
                assert(i2c_target_request.is_restart is True)
                register_index += 1
