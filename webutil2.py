import queue
import select
import socket

class EchoServer:
    def __init__(self, conn: socket.socket, disconnect_callback) -> None:
        self.messageQueue: queue.Queue = queue.Queue()
        self.sock: socket.socket = conn
        self.handle_disconnect = lambda : disconnect_callback(self)
        self.write = self.messageQueue.put

    def recieve(self):
        data: bytes = self.sock.recv(4096)
        if data:
            print(data.decode())
            self.write(data)
        else:
            self.handle_disconnect()

    def __del__(self) -> None:
        pass

class HTTPserver:
    def __init__(self) -> None:
        pass

class ServerMultiplexer:
    def __init__(self, port: int = 3001, host: str = "127.0.0.1", backlog: int = 0, connection_handler = EchoServer) -> None:
        self.port: int = port
        self.sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setblocking(False)
        self.sock.bind((host, port))

        self.conn_has_tick = False
        if hasattr(connection_handler, 'tick'):
            self.conn_has_tick = callable(getattr(connection_handler, 'tick'))
        self.conn_handler = connection_handler
        self.connection_handlers: list[connection_handler] = []

        if backlog:
            self.sock.listen(backlog)
        else:
            self.sock.listen()

    def client_disconnect(self, client_handler):
        self.connection_handlers.remove(client_handler)

    def tick(self):
        read_fd = [self.sock]
        write_fd = []
        except_fd = []
        for connection_handler in self.connection_handlers:
            read_fd.append(connection_handler.sock)
            if not connection_handler.messageQueue.empty():
                write_fd.append(connection_handler.sock)

        rfd, wfd, xfd = select.select(read_fd, write_fd, except_fd)
        for sock in rfd:
            if sock is self.sock:
                conn, addr = sock.accept()
                print("connection from", addr)
                conn.setblocking(False)
                self.connection_handlers.append(
                        self.conn_handler(
                            conn, 
                            self.client_disconnect
                            )
                        )

    def __del__(self):
        for conn_handler in self.connection_handlers:
            del conn_handler
