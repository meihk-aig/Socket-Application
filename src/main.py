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
import argparse as ap

if __name__ == "__main__":
    try:
        with patch_stdout():
            name = input("Enter your name: ")

            bcast = input("Enter your broadcast address (type 0 for default): ")
            if bcast == "0":
                bcast = "255.255.255.255"

            try:
                tcp_port = int(input("Enter your TCP port (between 1024 and 65535): "))
                if tcp_port > 65535 or tcp_port < 1024:
                    raise ValueError
            except ValueError:
                print("Invalid port number, used the default port 5050")
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

                if not args:
                    continue

                if (
                    not args[0].startswith("/")
                    or args[0] == "/leave"
                    or args[0] == "/send"
                ):
                    print("[*] You are not in any chat.")
                    continue

                handler = commands.get(args[0])

                if handler and handler(args) is c.EXIT:
                    break

    except KeyboardInterrupt:
        print("[*] Connection closed")
