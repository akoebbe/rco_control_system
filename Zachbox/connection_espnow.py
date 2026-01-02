from connection import Connection
from logger import LOGGER
import wifi
import espnow
from io import BytesIO
import struct
import msgpack


class ConnectionEspnow(Connection):
    
    BUFFER_END = -1
    BUFFER_ANNOUNCE = -2
    BUFFER_ANNOUNCE_ACK = -3
    
    def __init__(self, role: str=None, peer: str=""):
        self.role = role
        self.peer_mac = peer
        
        mac = ""
        for m in wifi.radio.mac_address:
            mac = mac + "\\" + str(hex(m)[1:])
        LOGGER.info("======================================")
        LOGGER.info("MAC address: %s", mac)
        LOGGER.info("======================================")
        wifi.radio.enabled = False
        
    def connect(self):
        self.e = espnow.ESPNow()
        self.peer = espnow.Peer(mac=bytearray(self.peer_mac)) # MAC of receiver e.g. b'\x80\x65\x99\xa2\x3d\x94'
        self.e.peers.append(self.peer)


    def send_buffer(self, buffer: BytesIO):
        i = 0
        buffer.seek(0) # Rewind Buffer
        # LOGGER.debug(buffer.getvalue())
        send = 0
        ack = None
        
        # Announce Buffer
        while ack != self.BUFFER_ANNOUNCE_ACK:
            self.send(struct('i',self.BUFFER_ANNOUNCE))
            while(len(self) == 0):
                continue
            ack, = struct.unpack('i', self.read())
        
        while (packet := buffer.read(240)):
            while send != ack:
                LOGGER.debug(f"Sending packet {send}: {packet}")
                self.send(struct.pack('i240s',send, packet))
                # sleep(3)
                while(len(self) == 0):
                    continue
                ack, = struct.unpack('i', self.read())
                LOGGER.debug(f"Got back: {ack}")
            send += 1
            
        self.send(struct.pack('i240s', self.BUFFER_END, bytearray(240)))

    def send(self, msg: bytearray):
        try:
            self.e.send(msg, peer=self.peer)
        except Exception as e:
            LOGGER.warning("Error: %s", e)
        
        LOGGER.debug(f"send=[{self.e.send_success} {self.e.send_failure}] read=[{self.e.read_success} {self.e.read_failure}] buf={self.e.buffer_size} phy={self.e.phy_rate}")
            
    def send_text(self, msg: str):
        self.send(msg.encode())

    def read(self):
        try:
            packet = self.e.read()
            if packet != None:
                LOGGER.debug("Packet Recieved: %s bytes, %s signal", len(packet.msg), packet.rssi)
                if packet.msg == self.BUFFER_ANNOUNCE:
                    self.send(struct.pack('i',self.BUFFER_ANNOUNCE_ACK))
                    recv_buffer = BytesIO()

                    while True:
                        msg = self.read()
                        if msg:
                            LOGGER.debug(msg)
                            send, packet = struct.unpack('i240s', msg)
                            if send == self.BUFFER_END:
                                recv_buffer.seek(0)
                                LOGGER.debug(msgpack.unpack(recv_buffer))
                                break
                            if send == 0:
                                recv_buffer.flush()
                            recv_buffer.write(packet)
                            LOGGER.debug(recv_buffer.getvalue())
                            LOGGER.debug(f"Sending Ack: {send}")
                            self.send(struct.pack('i',send))
                            LOGGER.debug(f"Read Errors: {self.read_errors}, Send Errors: {self.send_errors}, Local Error Count: {self.error_count}")
                else:
                    return packet.msg
        except ValueError as e:
            LOGGER.warning("ValueError: %s, Reconnecting", e)
            self.e.deinit()
            self.connect()

        return None
    
    def read_text(self):
        msg = self.read()
        return msg.decode()
    
    @property
    def read_errors(self):
        return self.e.read_failure

    @property
    def send_errors(self):
        return self.e.send_failure
    
    def __len__(self):
        return len(self.e)


