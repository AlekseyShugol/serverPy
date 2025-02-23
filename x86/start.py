from check_architecrure import check_system_bitness as check
from serverGUI import ServerGui
from server import Server

passw = str(input("Enter mode(enter to gui, cli to console>> "))

if __name__ == "__main__":
    bitness = check()
    config_path = "config/config.json"
    print(bitness)
    if bitness == "64bit" and passw != "cli":
        app = ServerGui(config_path)
        app.start()
    else:
        server = Server(config_path)
        server.start()

