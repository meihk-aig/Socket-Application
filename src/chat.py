import const_val as c
import socket as sk
import threading as thd


class ChatMananger:
    def __init__(self, tcp_port, host):
        self.max_length = 1024 * 1024

        self.tcp_port = tcp_port
        self.host = host
        self.connections = {}
        self.active_chat = None

        self.lock = thd.Lock()

        self.stop_event = thd.Event()

        self.listen_socket = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
        self.listen_socket.setsockopt(sk.SOL_SOCKET, sk.SO_REUSEADDR, True)

        self.listen_socket.bind(("", tcp_port))
        self.listen_socket.listen()
        self.listen_socket.settimeout(2)

        # self.listen_thread = thd.Thread
        # self.listen_thread.start()
