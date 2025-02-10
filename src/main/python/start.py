from src.main.python.CLI.server import Server

if __name__ == "__main__":
    server = Server("../../../config/config.json")
    server.start()