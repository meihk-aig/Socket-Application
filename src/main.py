import broadcast as brd
import peer as p
import const_val as c
import chat as cht
import commands as cmds

import prompt_toolkit as ptk
from prompt_toolkit.patch_stdout import patch_stdout

import threading as thd
import time as tm
import socket as sk

if __name__ == "__main__":
    try:
        # These are parser from the argparse module
        # Eg: Run "python .\src\main.py --name Mathhew" to start the program and set your name Matthew
        with patch_stdout():

            name = " "
            while " " in name:
                name = input("Enter your name (No space): ")

            bcast = input("Enter broadcast address (type 0 for default): ")
            if bcast == "0":
                bcast = "255.255.255.255"

            try:
                tcp_port = int(input("Enter TCP port (between 1024 and 65535): "))
                if tcp_port < 1024 or tcp_port > 65535:
                    raise ValueError
            except ValueError:
                print("[*] Invalid TCP port, set to 5050")
                tcp_port = 5050

            host = p.Peer(name)

            broadcaster = brd.Broadcaster(host, bcast, tcp_port)
            broadcaster.start_broadcasting()
            broadcaster.start_listening()

            manager = cht.ChatManager(tcp_port, host)

            session = ptk.PromptSession()

            commands = {
                "/quit": lambda args: cmds.quit_command(args, broadcaster),
                "/status": lambda args: cmds.status_command(args, host),
                "/list": lambda args: cmds.list_command(args, host),
                "/chat": lambda args: cmds.chat_command(args, manager, session),
                "/help": lambda args: cmds.help_command(args),
            }

            print("[*] Type /help for instructions.")
            while True:
                args = session.prompt("> ").split()

                if len(args) == 0:
                    continue

                handler = commands.get(args[0])

                if handler and handler(args) is c.EXIT:
                    break

    except KeyboardInterrupt:
        print("[*] Connection closed")
