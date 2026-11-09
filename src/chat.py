import const_val as c
import socket as sk
import threading as thd
import os


class ChatManager:
    def __init__(self, tcp_port, host):
        self.max_length = 1024 * 1024
        self.file_chunk = 64 * 1024

        self.tcp_port = tcp_port
        self.host = host

        # A lock to connections data
        self.lock = thd.Lock()
        self.connections = {}

        # Current peer that we are chatting with
        self.active_chat = None

        # A lock to protect file sending data
        self.file_send_lock = thd.Lock()

        self.stop_event = thd.Event()

        # Waiting for other peers to connect
        self.listen_socket = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
        self.listen_socket.setsockopt(sk.SOL_SOCKET, sk.SO_REUSEADDR, True)

        self.listen_socket.bind(("", tcp_port))
        self.listen_socket.listen()
        self.listen_socket.settimeout(2)

        self.listen_thread = thd.Thread(target=self.accept, daemon=True)
        self.listen_thread.start()

    # Listen and accept connection requests
    def accept(self):
        while not self.stop_event.is_set():
            try:
                conn, addr = self.listen_socket.accept()
            except sk.timeout:
                continue

            # Indicate the connection type: file transfer or message
            kind = self.recv_exact(conn, c.HEADER)

            if kind is None:
                conn.close()
                continue

            kind = kind.decode(c.FORMAT).strip()

            # Name of the peer that are requesting a connection
            name_data = self.recv_exact(conn, c.HEADER)

            if name_data is None:
                conn.close()
                continue

            peer_name = name_data.decode(c.FORMAT).strip()

            if kind not in ("CHAT", "FILE"):
                conn.close()
                continue

            # Xác định peer dựa trên IP
            with self.host.peers_lock:
                peers = [
                    name
                    for name, info in self.host.peers.items()
                    if info.get("ip") == addr[0] and name == peer_name
                ]

            if len(peers) != 1:
                conn.close()
                continue

            connection_type = "message" if kind == "CHAT" else "file"

            self.register_connection(peer_name, connection_type, conn)

    # Register a connection to self.connection based on peer_name and the type of the connection
    def register_connection(self, peer_name, connection_type, conn):
        with self.lock:
            if peer_name not in self.connections:
                self.connections[peer_name] = {"message": None, "file": None}

            if self.connections[peer_name][connection_type] is not None:
                conn.close()
                return

            self.connections[peer_name][connection_type] = conn

        if connection_type == "message":
            thread = thd.Thread(
                target=self.message_receive_loop, args=(peer_name, conn), daemon=True
            )
        else:
            thread = thd.Thread(
                target=self.file_receive_loop, args=(peer_name, conn), daemon=True
            )

        thread.start()

    # Connect to a peer
    def connect_to_peer(self, peer_name):
        # Reuse the connections if established
        with self.lock:
            connections = self.connections.get(peer_name)

            if connections and all(connections.values()):
                return True

        with self.host.peers_lock:
            info = self.host.peers.get(peer_name)

        if info is None:
            print(f"[*] {peer_name} not found.")
            return False

        addr = (info["ip"], info["port"])

        # Establish two types of connections
        connection_types = [("CHAT", "message"), ("FILE", "file")]

        for kind, connection_type in connection_types:

            # Check if the connection has been created or not
            with self.lock:
                connections = self.connections.get(peer_name)

                if connections and connections[connection_type] is not None:
                    continue

            conn = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
            try:
                conn.connect(addr)
            except ConnectionRefusedError:
                conn.close()
                return False

            # Create handshake message which the self.accept() method of the other peer will
            # receive to determine the type of connection
            handshake = kind.ljust(c.HEADER).encode(c.FORMAT) + self.host.name.ljust(
                c.HEADER
            ).encode(c.FORMAT)

            conn.sendall(handshake)

            self.register_connection(peer_name, connection_type, conn)

        # Check if the connection established
        with self.lock:
            connections = self.connections.get(peer_name)

            return connections is not None and all(connections.values())

    def close_connection(self, peer_name, connection_type, conn):
        with self.lock:
            connections = self.connections.get(peer_name)

            if not connections:
                return

            if connections[connection_type] is not conn:
                return

            connections[connection_type] = None

            if all(value is None for value in connections.values()):
                self.connections.pop(peer_name, None)

        conn.close()

    def recv_exact(self, conn, size):
        data = bytearray()

        while len(data) < size:
            try:
                chunk = conn.recv(size - len(data))
            # Prevent the program from crashing when the other peer goes offline
            except ConnectionResetError:
                return None

            if not chunk:
                return None

            data.extend(chunk)

        return bytes(data)

    def recv_message(self, conn):
        type_data = self.recv_exact(conn, c.HEADER)

        if type_data is None:
            return None

        data_type = type_data.decode(c.FORMAT).strip()

        if data_type != "MSG":
            return None

        header = self.recv_exact(conn, c.HEADER)

        if header is None:
            return None

        length = int(header.decode(c.FORMAT).strip())

        if length < 0 or length > self.max_length:
            return None

        payload = self.recv_exact(conn, length)

        if payload is None:
            return None

        return payload.decode(c.FORMAT)

    def send_message(self, peer_name, message):
        with self.lock:
            connections = self.connections.get(peer_name)
            conn = connections["message"] if connections else None

        if conn is None:
            return False

        data_type = "MSG".ljust(c.HEADER).encode(c.FORMAT)
        payload = message.encode(c.FORMAT)
        header = str(len(payload)).ljust(c.HEADER).encode(c.FORMAT)

        conn.sendall(data_type + header + payload)

        return True

    def message_receive_loop(self, peer_name, conn):
        while not self.stop_event.is_set():
            message = self.recv_message(conn)

            if message is None:
                break

            with self.lock:
                active = self.active_chat == peer_name

            if active:
                print(f"[{peer_name}] {message}")
            else:
                with self.host.unread_lock:
                    unread = self.host.unread.setdefault(peer_name, [])
                    unread.append(message)
                    count = len(unread)

                print(f"[*] New message from {peer_name} ({count} unread)")

        self.close_connection(peer_name, "message", conn)

    def send_file(self, peer_name, file_path):
        with self.lock:
            connections = self.connections.get(peer_name)
            conn = connections["file"] if connections else None

        if conn is None:
            return False

        filename = os.path.basename(file_path)
        filename_data = filename.encode(c.FORMAT)

        file_size = os.path.getsize(file_path)

        # FILE | filename_length | filename | file_size | file_data

        data_type = "FILE".ljust(c.HEADER).encode(c.FORMAT)

        name_length = str(len(filename_data)).ljust(c.HEADER).encode(c.FORMAT)

        size_header = str(file_size).ljust(c.HEADER).encode(c.FORMAT)

        try:
            with self.file_send_lock:
                conn.sendall(data_type + name_length + filename_data + size_header)

                with open(file_path, "rb") as file:
                    while True:
                        chunk = file.read(self.file_chunk)

                        if not chunk:
                            break

                        conn.sendall(chunk)

        except OSError:
            print(f"[*] Failed to send file to {peer_name}")
            self.close_connection(peer_name, "file", conn)
            return False

        print(f"[*] Sent file {filename} to {peer_name}")

        return True

    def recv_file(self, conn, peer_name):
        type_data = self.recv_exact(conn, c.HEADER)

        if type_data is None:
            return False

        data_type = type_data.decode(c.FORMAT).strip()

        if data_type != "FILE":
            return False

        # Receive file name
        name_header = self.recv_exact(conn, c.HEADER)

        if name_header is None:
            return False

        name_length = int(name_header.decode(c.FORMAT).strip())

        if name_length <= 0 or name_length > 255:
            return False

        filename_data = self.recv_exact(conn, name_length)

        if filename_data is None:
            return False

        filename = os.path.basename(filename_data.decode(c.FORMAT))

        # Receive file size
        size_header = self.recv_exact(conn, c.HEADER)

        if size_header is None:
            return False

        file_size = int(size_header.decode(c.FORMAT).strip())

        if file_size < 0:
            return False

        # Create the downloads directory
        os.makedirs("downloads", exist_ok=True)

        save_path = os.path.join("downloads", filename)

        # If the file with the same name has already existed, add a number to the end of the receiving file
        name, ext = os.path.splitext(filename)
        number = 1

        while os.path.exists(save_path):
            new_filename = f"{name} ({number}){ext}"
            save_path = os.path.join("downloads", new_filename)
            number += 1

        # Receive file data
        with open(save_path, "wb") as file:
            remaining = file_size

            while remaining > 0:
                chunk_size = min(remaining, self.file_chunk)

                chunk = self.recv_exact(conn, chunk_size)

                if chunk is None:
                    return False

                file.write(chunk)
                remaining -= len(chunk)

        print(f"[*] Received {filename} from {peer_name}")

        return True

    def file_receive_loop(self, peer_name, conn):
        while not self.stop_event.is_set():
            try:
                if not self.recv_file(conn, peer_name):
                    break
            except:
                break
        self.close_connection(peer_name, "file", conn)

    def start_chat(self, peer_name):
        if not self.connect_to_peer(peer_name):
            print(f"[*] Cannot connect to {peer_name}")
            return False

        print(f"[*] Connected to {peer_name}")

        with self.lock:
            self.active_chat = peer_name

        with self.host.unread_lock:
            messages = self.host.unread.pop(peer_name, [])

        for message in messages:
            print(f"[{peer_name}] {message}")

        return True

    def leave_chat(self):
        with self.lock:
            self.active_chat = None
