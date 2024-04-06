import socket
from hashlib import sha1
from base64 import b64encode
HOST = "127.0.0.1"
PORT = 3001

MAX_GET_DATA = 8192

class Websocket:
    class Frame:
        def _toRaw(self):
            self.RAWFRAME: bytearray = bytearray(2)
            self.RAWFRAME[0] ^= (self.FIN << 7) & 128
            self.RAWFRAME[0] ^= (self.RSV1 << 6) & 64
            self.RAWFRAME[0] ^= (self.RSV2 << 5) & 32
            self.RAWFRAME[0] ^= (self.RSV3 << 4) & 16
            self.RAWFRAME[0] ^= self.OPCODE & 15
            self.RAWFRAME[1] ^= (self.MASKSET << 7) & 128

            if self.PAYLOAD_SIZE < 126:
                self.RAWFRAME[1] ^= self.PAYLOAD_SIZE & 127
            elif self.PAYLOAD_SIZE < 65536:
                self.RAWFRAME[1] ^= 126
                self.RAWFRAME += bytearray(int.to_bytes(self.PAYLOAD_SIZE, 2))
            else:
                self.RAWFRAME[1] ^= 127
                self.RAWFRAME += bytearray(int.to_bytes(self.PAYLOAD_SIZE, 8))

            if self.MASKSET:
                self.RAWFRAME += self.MASK

        def __init__(self,
                     payload: str | int | socket.socket = '\xff',
                     fin: int = 1,
                     rsv1: int = 0,
                     rsv2: int = 0,
                     rsv3: int = 0,
                     opcode: int = 1,
                     maskSet: int = 0,
                     mask: int = 0,
                     ) -> None:
            if isinstance(payload, socket.socket):
                self.recv(payload)
                return

            self.RAWFRAME: bytearray = bytearray()

            self.FIN:  int = fin
            self.RSV1: int = rsv1
            self.RSV2: int = rsv2
            self.RSV3: int = rsv3
            self.OPCODE: int = opcode

            self.MASKSET: int = maskSet
            self.MASK: bytes = int.to_bytes(mask)
            if isinstance(payload, str):
                self.PAYLOAD_SIZE: int = len(payload)
                self.PAYLOAD: bytearray = bytearray(payload.encode())
            elif isinstance(payload, int):
                self.PAYLOAD_SIZE = 4
                self.PAYLOAD: bytearray = bytearray(int.to_bytes(payload, 4))
            else:
                self.PAYLOAD = bytearray()
                self.PAYLOAD_SIZE = 0

        def recv(self, conn: socket.socket) -> bytearray:
            self.RAWFRAME = bytearray(conn.recv(2))
            self.FIN = (self.RAWFRAME[0] & 128) >> 7
            self.RSV1 = (self.RAWFRAME[0] & 64) >> 6
            self.RSV1 = (self.RAWFRAME[0] & 32) >> 5
            self.RSV1 = (self.RAWFRAME[0] & 16) >> 4
            self.OPCODE = self.RAWFRAME[0] & 15

            self.MASKSET = (self.RAWFRAME[1] & 128) >> 7
            self.PAYLOAD_SIZE = self.RAWFRAME[1] & 127
            if self.PAYLOAD_SIZE == 126:
                self.PAYLOAD_SIZE = int.from_bytes(conn.recv(2))
            elif self.PAYLOAD_SIZE == 127:
                self.PAYLOAD_SIZE = int.from_bytes(conn.recv(8))
            
            if self.MASKSET:
                self.MASK = conn.recv(4)
                raw_payload = conn.recv(self.PAYLOAD_SIZE)
                self.PAYLOAD = bytearray(self.PAYLOAD_SIZE)
                for i in range(self.PAYLOAD_SIZE):
                    self.PAYLOAD[i] = raw_payload[i] ^ self.MASK[i % 4]
            return self.PAYLOAD

        def send(self, conn: socket.socket) -> None:
            self._toRaw()
            conn.send(self.RAWFRAME + self.PAYLOAD)
    def __init__(self) -> None:
        pass

def websocketHandshake(conn: socket.socket):
    data = conn.recv(MAX_GET_DATA).decode()
    if not data:
        print("No data recieved")
        return -1
    print(data)

    # Check if it is a GET request that upgrades to websocket and send handshake
    headers = data.splitlines()[:-1]
    request = headers.pop(0)
    if request[:3] != "GET":
        print("Not GET request")
        return -2
    upgradeWebsocket = False

    wskey = "nothing"

    for line in headers:
        values = line.split(":", 1)
        header = values[0].strip()
        value = values[1].strip()
        if header == "Upgrade" and value == "websocket":
            upgradeWebsocket = True
        if header == "Sec-WebSocket-Key":
            wskey = value
    
    if not upgradeWebsocket:
        print("Connection did not upgrade to websocket")
        return -3

    # Calculate websocket key
    wskey += "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    wskey = b64encode(sha1(wskey.encode()).digest()).decode()

    # Send handshake
    payload = \
f"""\

HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: {wskey}

"""
    conn.sendall(payload.encode())
    print(f"payload sent, key = {wskey}")
    return


def getFrame(conn: socket.socket):
    frame = bytes(conn.recv(2))
    print("Frame recieved, processing")

    if frame[0] & 128:
        print("Full payload")
    else:
        print("Partial payload")
    print(f"RSV1 {'SET' if frame[0] & 64 else 'NOT SET'}")
    print(f"RSV2 {'SET' if frame[0] & 32 else 'NOT SET'}")
    print(f"RSV3 {'SET' if frame[0] & 16 else 'NOT SET'}")
    opcode = frame[0] & 15
    print(f"OPCODE { opcode }")
    
    if not frame[1] & 128:
        print("Mask bit not set, disconnecting")
        conn.close()
        return -1

    payload_len = frame[1] - 128
    if payload_len < 126:
        # That's the length of the payload
        print(f"Payload length: {payload_len}")
    elif payload_len == 126:
        # Extended payload length
        payload_len = int.from_bytes(conn.recv(2))
        print(f"Payload length: {payload_len}")
    elif payload_len == 127:
        # Extended payload length continued
        payload_len = int.from_bytes(conn.recv(8))
        print(f"Payload length: {payload_len}")

    mask_key = bytes(conn.recv(4))
    
    # unmask data
    payload = bytearray(conn.recv(payload_len))
    for i in range(payload_len):
        payload[i] = payload[i] ^ mask_key[i % 4]

    if opcode == 1:
        print(f"Message recieved: {payload.decode()}")

def main() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        conn, addr = s.accept()
        print(type(conn))
        with conn:
            print(f"Connection from {addr}")
            websocketHandshake(conn)
            while True:
                print(f"Client: {Websocket.Frame(conn).PAYLOAD.decode()}")
                Websocket.Frame("Hello from the server!").send(conn)

if __name__ == "__main__":
    main()
