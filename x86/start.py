from server import Server
from check_architecrure import check_system_bitness as check
from serverGUI import MyApp
import tkinter as tk

# passw = str(input("Enter mode(enter tu gui, cli to console>> "))

if __name__ == "__main__":
    passw = input("enter mode: ")
    bitness = check()
    print(bitness)
    if bitness == "64bit" and passw != "cli":
        app = MyApp("config/config.json")
        app.start()
    elif passw == "cli":
        server = Server("config/config.json")
        server.start()
    else:
        server = Server("config/config.json")
        server.start()