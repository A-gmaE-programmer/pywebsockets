import queue
import select
import socket

class Server:
    def __init__(self, port: int = 3001, host: str = "127.0.0.1", backlog: int = 0) -> None:
        self.port: int = port
        self.sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setblocking(False)
        self.sock.bind((host, port))
        self.read_fd: list = []
        self.write_fd: list = []
        self.messageQueues: dict = {}

        if backlog:
            self.sock.listen(backlog)
        else:
            self.sock.listen()

        self.read_fd.append(self.sock)

    def write(self, conn: socket.socket, data: bytes):
        self.messageQueues[conn].put(data)
        if conn not in self.write_fd:
            self.write_fd.append(conn)

    def read(self, conn: socket.socket):
        data: bytes = conn.recv(4096)
        if data:
            print(data.decode())
            self.write(conn, data)
        else:
            if conn in self.write_fd:
                self.write_fd.remove(conn)
            self.read_fd.remove(conn)
            conn.close()
            del self.messageQueues[conn]

    def accept(self):
        rfd, wfd, xfd = select.select(self.read_fd, self.write_fd, self.read_fd)
        for sock in rfd:
            if sock is self.sock:
                conn, addr = sock.accept()
                print("connection from", addr)
                conn.setblocking(False)
                self.read_fd.append(conn)
                self.messageQueues[conn] = queue.Queue(-1)
            else:
                self.read(sock)
        for sock in wfd:
            try:
                to_send = self.messageQueues[sock].get_nowait()
            except queue.Empty:
                self.write_fd.remove(sock)
            else:
                sock.send(to_send)

    def __del__(self) -> None:
        for sock in self.read_fd:
            sock.close()

serv = Server()
while True:
    serv.accept()
