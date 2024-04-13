from io import BytesIO
from websock import Websocketframe, WebsocketServer

from typing import Literal
byteorder: Literal['little', 'big'] = 'little'

class MyWSS(WebsocketServer):
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
        if frame.OPCODE == 2:
            # Check if we have recieved client data
            pl = frame.PAYLOAD
            if pl[0] == 0x00:
                data = pl[4:pl[1]]
                # for i in range(len(data) // 4):
                #     print(int.from_bytes(data[i*4:i*4+4], byteorder))
                if len(data) == 20:
                    global canvasX, canvasY, mouseX, mouseY, mousePressed
                    canvasX      = int.from_bytes(data[0 :4 ], byteorder)
                    canvasY      = int.from_bytes(data[4 :8 ], byteorder)
                    mouseX       = int.from_bytes(data[8 :12], byteorder)
                    mouseY       = int.from_bytes(data[12:16], byteorder)
                    mousePressed = int.from_bytes(data[16:20], byteorder)

    def tick(self):
        if self.handshake < 1:
            return
        # Send messages in buffer
        global msgq
        if msgq:
            payload = BytesIO()
            for msg in msgq:
                # print("Getting message")
                payload.write(msg)

            frame = Websocketframe(payload.getvalue())
            self.write(frame.send())
            msgq.clear()

        # tosend = msgq
        # Using queue
        # while not tosend.empty():
        #     print("Getting message")
        #     frame = Websocketframe(tosend.get_nowait())
        #     self.write(frame.send())

def drawTriangle(x1: int, y1: int, x2: int, y2: int, x3: int, y3: int, outline=False):
    payload = bytearray(2)
    if outline:
        payload[0] = 0x31
    else:
        payload[0] = 0x30
    
    payload.extend(int.to_bytes(x1, 4, byteorder, signed=True))
    payload.extend(int.to_bytes(y1, 4, byteorder, signed=True))
    payload.extend(int.to_bytes(x2, 4, byteorder, signed=True))
    payload.extend(int.to_bytes(y2, 4, byteorder, signed=True))
    payload.extend(int.to_bytes(x3, 4, byteorder, signed=True))
    payload.extend(int.to_bytes(y3, 4, byteorder, signed=True))

    payload[1] = len(payload)
    msgq.append(bytes(payload))

def drawCircle(x: int, y: int, radius: int, outline=False):
    payload = bytearray(2)
    if outline:
        payload[0] = 0x33
    else:
        payload[0] = 0x32

    payload.extend(int.to_bytes(x, 4, byteorder, signed=True))
    payload.extend(int.to_bytes(y, 4, byteorder, signed=True))
    payload.extend(int.to_bytes(radius, 4, byteorder, signed=True))

    payload[1] = len(payload)
    msgq.append(bytes(payload))

def drawRect(x: int, y: int, width: int, height: int, outline=False):
    payload = bytearray(2)
    # Payload layout [OPCODE|SIZE|DATA...]
    if outline:
        payload[0] = 0x02
    else:
        payload[0] = 0x01

    payload.extend(int.to_bytes(x, 4, byteorder, signed=True))
    payload.extend(int.to_bytes(y, 4, byteorder, signed=True))
    payload.extend(int.to_bytes(width, 4, byteorder, signed=True))
    payload.extend(int.to_bytes(height, 4, byteorder, signed=True))

    payload[1] = len(payload)
    msgq.append(bytes(payload))

def clear(x=0, y=0, width=2000, height=2000):
    payload = bytearray(2)
    payload[0] = 0x03
    payload.extend(int.to_bytes(x, 4, byteorder, signed=True))
    payload.extend(int.to_bytes(y, 4, byteorder, signed=True))
    payload.extend(int.to_bytes(width, 4, byteorder, signed=True))
    payload.extend(int.to_bytes(height, 4, byteorder, signed=True))

    payload[1] = len(payload)
    msgq.append(bytes(payload))
    pass

def path(command: str):
    """
    Run a canvas path command

    :param str command: 'begin' | 'close' | 'stroke' | 'fill'
    """
    payload = bytearray(2)
    match command:
        case 'begin':
            payload[0] = 0x10
        case 'close':
            payload[0] = 0x11
        case 'stroke':
            payload[0] = 0x12
        case 'fill':
            payload[0] = 0x13
    payload[1] = len(payload)
    msgq.append(bytes(payload))

def setColor(css_col: str):
    strlen = len(css_col)
    if strlen > 253:
        print("Color string too long")
        return
    payload = bytearray(2)
    payload[0] = 0xFF
    payload[1] = strlen + 2
    msgq.append(bytes(payload) + css_col.encode())

msgq = []
# Canvas dimensions
canvasX = 2000
canvasY = 2000
# Mouse data
mouseX = 0
mouseY = 0
mousePressed = 0b000
# Any combination of 
# 0b000 -> No Buttons pressed
# 0b001 -> RMB Pressed
# 0b010 -> LMB Pressed
# 0b100 -> MMB Pressed
