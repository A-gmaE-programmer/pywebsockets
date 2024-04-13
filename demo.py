import time
from threading import Thread

import webutil
from server import MyWSS, drawTriangle, drawCircle, drawRect, clear, path, setColor
import server

s = webutil.ServerMultiplexer(connection_handler=MyWSS, timeout=1/60)

def drawRectsFromCmdline():
    # msgcount = 1
    while True:
        # msgq.append("Message #{}".format(msgcount))
        # print("t2 -> Putting message", msgcount)
        # msgcount += 1
        a = input().strip().split()
        if not a:
            continue
        if   a[0] == 'rect':
            b = list(map(int, a[1:]))
            drawRect(b[0], b[1], b[2], b[3])
        elif a[0] == 'recto':
            b = list(map(int, a[1:]))
            drawRect(b[0], b[1], b[2], b[3], True)
        elif a[0] == 'clear':
            if a[1:]:
                b = list(map(int, a[1:]))
                clear(b[0], b[1], b[2], b[3])
            else:
                clear()
        elif a[0] == 'tri':
            b = list(map(int, a[1:]))
            drawTriangle(*b, outline=False)

# from random import randrange
def loop():
    while True:
        # Send a blank frame to get mouse data
        server.msgq.append(b'')
        time.sleep(1/60)
        if len(s.connection_handlers) == 0:
            continue
        # drawRect(mouseX-25, mouseY-25, 50, 50)
        drawCircle(server.mouseX, server.mouseY, 50)
        # drawRect(randrange(50, 150)*5, randrange(50, 150)*5, 100, 100)
        # clear(randrange(50, 150)*5, randrange(50, 150)*5, 100, 100)


def serve():
    while True:
        s.tick()
t2 = Thread(target=drawRectsFromCmdline)
t3 = Thread(target=serve)
t2.start()
t3.start()

# t4 = Thread(target=loop)
# t4.start()
def on_connect():
    while s.connection_handlers == 0:
        time.sleep(0.5)
    setColor("CornflowerBlue")
    print("Color changed to blue")
Thread(target=on_connect).start()
