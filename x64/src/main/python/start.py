from src.main.python.CLI.server import Server
from src.main.python.dev.modules.functions.os.check_architecrure import check_system_bitness as check
from src.main.python.GUI.serverGUI import MyApp
import tkinter as tk

passw = str(input("Enter mode(enter tu gui, cli to console>> "))

if __name__ == "__main__":

    bitness = check()
    print(bitness)
    if bitness == "64bit" and passw != "cli":
        app = MyApp("../../../config/config.json")
        app.start()
    elif passw == "cli":
        server = Server("../../../config/config.json")
        server.start()
    else:
        server = Server("../../../config/config.json")
        server.start()