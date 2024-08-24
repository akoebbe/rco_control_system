from connection import Connection
import wifi
import socketpool
from logger import LOGGER
from settings import Settings

class ConnectionWifi(Connection):
    
    def __init__(self, role: str, peer: str):
        
        self.role = role

        pool = socketpool.SocketPool(wifi.radio)
        self.sock = pool.socket(pool.AF_INET, pool.SOCK_DGRAM) # UDP, and we'l reuse it each time
        
    def connect(self):
        SSID = Settings.ssid
        SSID_PW = Settings.ssid_password
        SSID_CH = Settings.ssid_channel

        TIMEOUT = None
        HOST = Settings.head_ip_address
        PORT = Settings.port

        # If we're the host, fire up an access point
        if self.role == self.ROLE_HOST:
            LOGGER.warning("Attempting to reconnect to Wifi")
            while not wifi.radio.connected:
                # if self.sock:
                #     self.sock.close()
                LOGGER.info("Connecting to %s on channel %s", SSID, SSID_CH)
                try:
                    wifi.radio.connect(SSID, SSID_PW, channel=SSID_CH)
                except ConnectionError as e:
                    LOGGER.warning("Connection error: %s", e)
                    continue
                    
            LOGGER.info("Conected to %s. My IP address is %s", SSID, wifi.radio.ipv4_address)
            self.sock.connect((HOST, PORT))
        else: # We're the client
            pass

    def send(self, msg: bytearray):
        try:
            self.sock.send(msg)
        except BrokenPipeError as e:
            LOGGER.warning("Couldn't connect to head: %s", e)
        except ConnectionError as e:
            LOGGER.warning("Connection Error to head: %s", e)
        except OSError as e:
            LOGGER.warning("OSError: %s", e)
