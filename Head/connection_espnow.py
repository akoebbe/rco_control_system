from connection import Connection
from logger import LOGGER
import wifi
import espnow

class ConnectionEspnow(Connection):
    
    def __init__(self, role: str=None, peer: str=""):
        self.role = role
        self.peer_mac = peer
        
        mac = ""
        for m in wifi.radio.mac_address:
            mac = mac + "\\" + str(hex(m)[1:])
        LOGGER.info("======================================")
        LOGGER.info("MAC address: %s", mac)
        LOGGER.info("======================================")
        
    def connect(self):
        self.e = espnow.ESPNow()
        self.peer = espnow.Peer(mac=bytearray(self.peer_mac)) # MAC of receiver e.g. b'\x80\x65\x99\xa2\x3d\x94'
        self.e.peers.append(self.peer)

    def send(self, msg: bytearray):
        try:
            self.e.send(msg, peer=self.peer)
        except Exception as e:
            LOGGER.warning("Error: %s", e)

    def read(self):
        try:
            packet = self.e.read()
            if packet != None:
                LOGGER.debug("Packet Recieved: %s bytes, %s signal", len(packet.msg), packet.rssi)
                return packet.msg
        except ValueError as e:
            LOGGER.warning("[READ] ValueError: %s, Reconnecting", e)
            self.e.deinit()
            self.connect()

        return None