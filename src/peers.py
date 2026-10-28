import threading as thd

FORMAT = "utf-8"
HEADER = 1024

PORT = 9191
TIMEOUT = 10


def print_help_message():
    print("[*] Available commands: ")
    print(
        "    /list                     Show online users with number, name, IP and status"
    )
    print(
        "    /chat <name|number>       Open a chat with the selected user (TCP connection)"
    )
    print("    <any text>                Send a message to the current chat partner")
    print("    /send <file>              Send a file to the current chat partner")
    print("    /leave                    Close the current chat")
    print("    /status <online|away>     Change your status (sent via UDP)")
    print("    /help                     Show all commands")
    print("    /quit                     Exit the program")


# This is the global variable that other process used to store data
state = "online"
peers = {}
stop_flag = thd.Event()
