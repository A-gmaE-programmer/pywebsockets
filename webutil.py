import queue
import select
import socket


class Client_hander_base:
    def __init__(self, conn: socket.socket, disconnect_callback) -> None:
        self.messageQueue: queue.Queue = queue.Queue()
        self.sock: socket.socket = conn
        self.handle_disconnect = lambda : disconnect_callback(self)
        self.write = self.messageQueue.put
    
    def recieve(self):
        """Called when socket can recieve data"""
        raise NotImplementedError

    def onsend(self):
        """Implementation is Optional
           Called every time queued data is sent"""
        pass

    def tick(self):
        """Implementation is Optional
           Called before select.select()
           Is not threaded seperately from select
           """
        pass

    def close(self):
        """Client handler is expected to close connection"""
        self.sock.close()

    def __enter__(self):
        return self
    def __exit__(self):
        self.close()


class EchoServer(Client_hander_base):
    def recieve(self):
        data: bytes = self.sock.recv(4096)
        if data:
            print(data.decode())
            self.write(data)
        else:
            self.handle_disconnect()

    def onsend(self):
        self.handle_disconnect()


class ServerMultiplexer:
    def __init__(self, port: int = 3001, host: str = "127.0.0.1", backlog: int = 0, connection_handler: type = EchoServer, timeout: float = 0.5) -> None:
        self.port: int = port
        self.sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setblocking(False)
        self.sock.bind((host, port))

        self.conn_has_tick = False
        if hasattr(connection_handler, 'tick'):
            self.conn_has_tick = callable(getattr(connection_handler, 'tick'))
        self.conn_has_onsend = False
        if hasattr(connection_handler, 'onsend'):
            self.conn_has_onsend = callable(getattr(connection_handler, 'onsend'))
        self.conn_handler = connection_handler
        self.connection_handlers: list[connection_handler] = []

        self.sel_timeout = timeout

        if backlog:
            self.sock.listen(backlog)
        else:
            self.sock.listen()

    def client_disconnect(self, client_handler):
        try:
            peername = client_handler.sock.getpeername()
        except OSError:
            peername = "Unknown"
        print("Client disconnect from", peername)
        client_handler.close()
        self.connection_handlers.remove(client_handler)

    def tick(self):
        if self.conn_has_tick:
            for conn_handle in self.connection_handlers:
                conn_handle.tick()
        read_fd = []
        write_fd = []
        except_fd = []
        for connection_handler in self.connection_handlers:
            read_fd.append(connection_handler.sock)
            if not connection_handler.messageQueue.empty():
                write_fd.append(connection_handler.sock)
        read_fd.append(self.sock)

        rfd, wfd, xfd = select.select(read_fd, write_fd, except_fd, self.sel_timeout)
        if len(rfd) > 0 and rfd[-1] is self.sock:
            conn, addr = rfd[-1].accept()
            print("connection from", addr)
            conn.setblocking(False)
            self.connection_handlers.append(
                    self.conn_handler(
                        conn, 
                        self.client_disconnect
                        )
                    )
            rfd.pop()
            
        # Premature optimisation
        rfd_count: int = 0
        for conn_handle in self.connection_handlers:
            if rfd_count >= len(rfd):
                break
            if rfd[rfd_count] is conn_handle.sock:
                conn_handle.recieve()
                rfd_count += 1

        wfd_count: int = 0
        for conn_handle in self.connection_handlers:
            if wfd_count >= len(wfd):
                break
            if wfd[wfd_count] is conn_handle.sock:
                try:
                    conn_handle.sock.send(conn_handle.messageQueue.get_nowait())
                except BrokenPipeError:
                    conn_handle.handle_disconnect()
                    continue
                if self.conn_has_onsend:
                    conn_handle.onsend()
                wfd_count += 1

    def __del__(self):
        for conn_handler in self.connection_handlers:
            del conn_handler


# class HTTP_server_base:
#     def __init__(self, conn: socket.socket, disconnect_callback) -> None:
#         self.messageQueue: queue.Queue = queue.Queue()
#         self.sock: socket.socket = conn
#         self.handle_disconnect = lambda : disconnect_callback(self)
#         self.write = self.messageQueue.put
#
#     def recieve(self):
#         data: bytes = self.sock.recv(4096)
#         if data:
#             print(data.decode())
#             self.write(data)
#         else:
#             self.handle_disconnect()
#
#     def __del__(self) -> None:
#         self.sock.close()


if __name__ == "__main__":
    s = ServerMultiplexer(connection_handler=EchoServer)
    while True:
        s.tick()
