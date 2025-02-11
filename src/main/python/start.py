from src.main.python.CLI.server import Server
from modules.functions.os.check_architecrure import check_system_bitness as check

if __name__ == "__main__":
    bitness = check()
    print(bitness)
    server = Server("../../../config/config.json")
    server.start()