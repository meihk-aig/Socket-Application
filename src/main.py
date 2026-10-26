from broadcast import *
from peers import *

import threading as thd
import time as tm
import socket as sk
import argparse as ap

FORMAT = "utf-8"
HEADER = 1024

PORT = 9191
TIMEOUT = 10

if __name__ == "__main__":
    try:
        # These are parser from the argparse module
        # Eg: Run "python .\src\main.py --name Mathhew" to start the program and set your name Matthew

        parser = ap.ArgumentParser()
        parser.add_argument("--name", required=True)
        parser.add_argument("--bcast", default="255.255.255.255")
        parser.add_argument("--tcp-port", type=int, default=5050)

        lst = parser.parse_args()

        # Create one thread to broadcast your online status
        broadcast_thread = thd.Thread(
            target=send_broadcast_message,
            args=(
                lst.name,
                lst.bcast,
                lst.tcp_port,
            ),
        )
        # Create another thread to get online status of others in your LAN
        recieve_thread = thd.Thread(target=get_broadcast_message, args=(lst.name,))

        # Start the two threads
        broadcast_thread.start()
        recieve_thread.start()

        while True:
            command = input("> ")

            if command == "/quit":
                stop_flag.set()
                break
            elif command == "/list":
                current_time = tm.time()

                index = 1
                for name, info in peers.items():
                    state = "online"

                    if current_time - info["last_seen"] > TIMEOUT:
                        state = "away"

                    print(f"    {index}. {name} ({info['ip']}) {state}")

                    index += 1

    except KeyboardInterrupt:
        print("\nBYE\n")
    finally:
        print("\nBYE\n")
