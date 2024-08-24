from logger import LOGGER
from cylon_state import CylonState
from mouths import Kitt
from settings import Settings
from connection_espnow import ConnectionEspnow
import asyncio

HOST = "192.168.4.1"  # see below
PORT = Settings.port
TIMEOUT = None
MAXBUF = 116

LOGGER.info("Cylon")


led_count = Settings.mouth_led_count + Settings.eye_led_count * 2



state = CylonState()

mouth = Kitt(Settings.mouth_led_count)

connection = ConnectionEspnow(peer=Settings.espnow_zachbox_mac)
connection.connect()

# LOGGER.info("Starting Access Point %s", Settings.ssid)
# wifi.radio.start_ap(Settings.ssid, Settings.ssid_password, channel=Settings.ssid_channel)
# # HOST = str(wifi.radio.ipv4_address_ap)
# LOGGER.info("AP IP Address: %s", HOST)
# LOGGER.info("IP Address: %s", str(wifi.radio.ipv4_address))

# LOGGER.info("Creating socket")
# pool = socketpool.SocketPool(wifi.radio)
# sock = pool.socket(pool.AF_INET, pool.SOCK_DGRAM)
# sock.bind((HOST, PORT))
# sock.settimeout(TIMEOUT)

async def servo_smoother():
    while True:
        state.servo_step()
        await asyncio.sleep(0)
        
async def command_listener():
    msg_buffer = bytearray(MAXBUF)  # stores our incoming packet

    while True:
        try:
            msg_buffer = connection.read()
            if msg_buffer != None:
                state.set_from_message(msg_buffer)
                LOGGER.debug("Received message: m-%s s-%s", state.mic_level, state.servo_target)
        except BrokenPipeError as e:
            LOGGER.warn("UDP pipe error: %s", e)

        await asyncio.sleep(0)


async def heartbeat_pulse():
    while True:
        connection.send(state.build_heartbeat())
        LOGGER.info("Sending Heartbeat: %s", state.battery)
        await asyncio.sleep(1)

async def main():
    LOGGER.info("Starting main async loop.")
    heartbeat_task = asyncio.create_task(heartbeat_pulse())
    servo_task = asyncio.create_task(servo_smoother())
    command_task = asyncio.create_task(command_listener())

    await asyncio.gather(
        heartbeat_task,
        servo_task,
        command_task
    )

asyncio.run(main())
 
    # last_value = leds

    # LOGGER.debug("Neck updated: %s -> %s", last_value, state.servo)
    # neck.neck_servo.angle = state.servo

    # last_value = state.servo
    
        

