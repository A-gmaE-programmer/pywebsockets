import socket
from hashlib import sha1
from base64 import b64encode
from io import BytesIO

import webutil

class Websocketframe:
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

        return self.RAWFRAME

    def __init__(self,
                 payload: str | int | bytes = 'Hi',
                 fin: int = 1,
                 rsv1: int = 0,
                 rsv2: int = 0,
                 rsv3: int = 0,
                 opcode: int = 1,
                 maskSet: int = 0,
                 mask: int = 0,
                 ) -> None:

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
            self.OPCODE = 2
        elif isinstance(payload, bytes):
            self.PAYLOAD_SIZE = len(payload)
            self.PAYLOAD: bytearray = bytearray(payload)
            self.OPCODE = 2
        else:
            self.PAYLOAD = bytearray()
            self.PAYLOAD_SIZE = 0

    def readBytearr(self, stream: BytesIO, num: int) -> bytes:
        """Throw error if reading nothing from stream"""
        data = stream.read(num)
        if data == b'':
            raise Exception("Empty stream")
        return data

    def recv(self, stream: BytesIO) -> bytearray:
        def read(n):
            return self.readBytearr(stream, n)
        self.RAWFRAME = bytearray(read(2))
        self.FIN = (self.RAWFRAME[0] & 128) >> 7
        self.RSV1 = (self.RAWFRAME[0] & 64) >> 6
        self.RSV1 = (self.RAWFRAME[0] & 32) >> 5
        self.RSV1 = (self.RAWFRAME[0] & 16) >> 4
        self.OPCODE = self.RAWFRAME[0] & 15

        self.MASKSET = (self.RAWFRAME[1] & 128) >> 7
        self.PAYLOAD_SIZE = self.RAWFRAME[1] & 127
        if self.PAYLOAD_SIZE == 126:
            self.PAYLOAD_SIZE = int.from_bytes(read(2))
        elif self.PAYLOAD_SIZE == 127:
            self.PAYLOAD_SIZE = int.from_bytes(read(8))
        
        if self.MASKSET:
            self.MASK = read(4) 
            raw_payload = read(self.PAYLOAD_SIZE) 
            self.PAYLOAD = bytearray(self.PAYLOAD_SIZE)
            for i in range(self.PAYLOAD_SIZE):
                self.PAYLOAD[i] = raw_payload[i] ^ self.MASK[i % 4]
        return self.PAYLOAD

    def send(self, conn: socket.socket | None = None) -> None | bytes:
        self._toRaw()
        if conn is None:
            return self.RAWFRAME + self.PAYLOAD
        else:
            conn.send(self.RAWFRAME + self.PAYLOAD)

def wss_handshake_payload(
        request: BytesIO, 
        headers: dict[str, list[str]] = {}
        ) -> bytes | int:
    request_type = request.read(4)
    if request_type != b"GET ":
        return -1
    path, httpversion = request.readline().strip().split()

    while True:
        line = request.readline().decode().strip()
        if not line:
            break
        values = line.split(": ", 1)
        k = values[0].strip()
        v = values[1].strip().split(", ")
        headers[k] = v

    # Make sure the correct headers are present
    if "Connection" not in headers:
        return -2
    if "Upgrade" not in headers["Connection"]:
        return -3

    if "Upgrade" not in headers:
        return -4
    if "websocket" not in headers["Upgrade"]:
        return -5

    if "Sec-WebSocket-Key" not in headers:
        return -6
    
    wskey = headers["Sec-WebSocket-Key"][0]
    wskey += "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    wskey = b64encode(sha1(wskey.encode()).digest()).decode()

    payload = \
"""\

HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: {}

""".format(wskey)
    return payload.encode()

class WebsocketServer(webutil.Client_hander_base):
    def __init__(self, conn: socket.socket, disconnect_callback) -> None:
        self.send_count = 0
        self.recv_count = 0
        self.handshake  = 0
        self.fragmentBits: bytes = bytes()
        '''In case a websocket frame gets split up'''
        super().__init__(conn, disconnect_callback)

    def processFrame(self, frame: Websocketframe):
        frame.MASKSET = 0
        # Close frame
        if frame.OPCODE == 8:
            self.write(frame.send())
            self.handle_disconnect()
        # Ping pong
        if frame.OPCODE == 9:
            frame.OPCODE = 10
            self.write(frame.send())
            self.send_count += 1
            return
        if frame.OPCODE == 10:
            print("Recieved Pong")
            return
        # self.write(frame.send())
        # self.send_count += 1

    def recieve(self):
        request = BytesIO(self.fragmentBits)
        request.seek(0, 2)
        rlen = request.tell()
        while True:
            recieved = self.sock.recv(8192)
            length = len(recieved)
            rlen += length
            request.write(recieved)
            if length < 8192:
                break

        self.recv_count += 1
        request.seek(0)

        if self.handshake < 1:
            payload = wss_handshake_payload(request)
            if isinstance(payload, int):
                print("bad request from", self.sock.getpeername())
                print("error code: ", payload)
                self.handle_disconnect()
            else:
                print("websocket handshake from", self.sock.getpeername())
                self.write(payload)
                self.send_count += 1
                print("payload sent")
                self.handshake = 1
            return

        if rlen == 0:
            print("Did not read any data? Something went wrong")
            return

        frameQueue = []
        while request.tell() < rlen:
            frame = Websocketframe()
            lastFrameLoc = request.tell()
            try:
                _ = frame.recv(request)
                # print("Recieved:", frame.recv(request))
            except Exception as err:
                if err != "Empty stream":
                    raise Exception(err)
                print("Incomplete frame recieved")
                request.seek(lastFrameLoc)
                self.fragmentBits = request.read()
                break
            frameQueue.append(frame)
        
        for frame in frameQueue:
            self.processFrame(frame)
