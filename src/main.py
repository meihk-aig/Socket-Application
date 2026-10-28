from broadcast import *
import peer as p

import threading as thd
import time as tm
import socket as sk
import argparse as ap

if __name__ == "__main__":
    try:
        # These are parser from the argparse module
        # Eg: Run "python .\src\main.py --name Mathhew" to start the program and set your name Matthew

        parser = ap.ArgumentParser()
        parser.add_argument("--name", required=True)
        parser.add_argument("--bcast", default="255.255.255.255")
        parser.add_argument("--tcp-port", type=int, default=5050)

        lst = parser.parse_args()

        host = p.Peer(lst.name)

        # Create one thread to broadcast your online status
        broadcast_thread = thd.Thread(
            target=send_broadcast_message,
            args=(
                host,
                lst.bcast,
                lst.tcp_port,
            ),
        )
        broadcast_thread.daemon = True
        # Create another thread to get online status of others in your LAN
        recieve_thread = thd.Thread(target=get_broadcast_message, args=(host,))
        recieve_thread.daemon = True

        # Start the two threads
        print(f"[*] Listening on TCP port {lst.tcp_port}")
        recieve_thread.start()
        print(f"[*] Broadcasting presence on UDP port {p.PORT}")
        broadcast_thread.start()

        while True:
            command = input("> ").split()

            if len(command) == 0:
                continue

            if command[0] == "/quit":
                p.stop_flag.set()
                break
            elif command[0] == "/help":
                p.print_help_message()
            elif command[0] == "/list":
                current_time = tm.time()

                index = 1
                for name, info in host.peers.items():
                    current_state = info["state"]

                    if current_time - info["last_seen"] > p.TIMEOUT:
                        current_state = "away"

                    print(f"    {index}. {name} ({info['ip']}) {current_state}")

                    index += 1
            elif command[0] == "/status" and len(command) == 2:
                if command[1] == "online":
                    host.state = "online"
                elif command[1] == "away":
                    host.state = "away"

                print(f'[*] Your status set to "{host.state}"')

    except KeyboardInterrupt:
        print("BYE")
    finally:
        print("BYE")
