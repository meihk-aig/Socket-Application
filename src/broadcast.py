import peer as p
import threading as thd
import time as tm
import socket as sk


def make_udp_socket():
    # Create an UDP socket with SOCK_DGRAM parameter
    conn = sk.socket(sk.AF_INET, sk.SOCK_DGRAM)
    # The parameters SO_REUSEADDR and True mean that the address (IP and port) can be used by others
    conn.setsockopt(sk.SOL_SOCKET, sk.SO_REUSEADDR, True)
    # The parameters SO_BROADCAST and True make sure that this socket cannot be denied by the operating system
    conn.setsockopt(sk.SOL_SOCKET, sk.SO_BROADCAST, True)
    # Bind the socket to the address as below ("" means all the machine in the LAN)
    conn.bind(("", p.PORT))

    return conn


def get_broadcast_message(host):
    # Create an UDP socket to listen to the message
    conn = make_udp_socket()

    # Consistently listen to the PORT
    while True:
        # The variable data holds the message in bytes (we have to decode it), and addr holds the sender IP and PORT
        data, addr = conn.recvfrom(p.HEADER)
        # Decode the message
        msg = data.decode(p.FORMAT, errors="replace")
        # Split the message into parts to get the information
        info = msg.split("|")
        # Skip the broadcast of this socket
        if len(info) == 4 and info[0] == "!LOL" and info[1] == host.name:
            continue

        peer_name = info[1]
        tcp_port = int(info[2])
        peer_ip = addr[0]
        peer_state = info[3]

        # Add the information recieved to the peers dictionary which is a global variable
        host.peers[peer_name] = {
            "ip": peer_ip,
            "port": tcp_port,
            "last_seen": tm.time(),
            "state": peer_state,
        }

        # If the stop event happens, these two lines will terminate the process
        if p.stop_flag.is_set():
            break


def send_broadcast_message(host, bcast, tcp_port):
    # Create an UDP socket to send the message to others to tell them that you are online
    conn = make_udp_socket()

    # Send message to the PORT every 3 seconds
    while True:
        # Make the message and encode it to bytes
        msg = f"!LOL|{host.name}|{tcp_port}|{host.state}".encode(p.FORMAT)
        # The variable addr holds IP limits (defalt = 255.255.255.255) and the PORT that the others are listening to
        addr = (bcast, p.PORT)
        # Send the message and the adress
        conn.sendto(msg, addr)
        # If the stop event happens, these two lines will terminate the process
        if p.stop_flag.is_set():
            break

        # Stop 3 second before sending another message
        tm.sleep(3)
