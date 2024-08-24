class Connection:
    ROLE_HOST = "host"
    ROLE_CLIENT = "client"

    def __init__(self, peer: str):
        raise NotImplementedError
    
    def connect(self):
        raise NotImplementedError
    
    def disconnect(self):
        raise NotImplementedError
    
    def send(self, msg: bytearray):
        raise NotImplementedError
    
    def read():
        raise NotImplementedError