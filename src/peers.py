import threading as thd

# This is the global variable that other process used to store data
peers = {}
stop_flag = thd.Event()
