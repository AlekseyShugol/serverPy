import socket
import os
import json
import datetime
import shutil


class Saver:
    def __init__(self, config_file_path):
        print("initialization main")
        print("reading config file")
        self._config_file_path = config_file_path
        if not os.path.exists(config_file_path):
            print("Config file not found")
            os.makedirs("config")
            data = {
                "host": None,
                "port_sender": None,
                "port_receiver": None,
                "res_directory": None,
                "html_directory": None,
                "max_size_gigabytes": None
            }
            print(f"create config.json as {data}")
            quit(-1)

        config_file = self._read_config()
        self._host = config_file['host']
        self._port = config_file['port_saver']
        self._html_directory = os.path.abspath(config_file['html_directory'])
        self._res_directory = os.path.abspath(config_file['res_directory'])
        self._max_size_gigabytes = config_file['max_size_gigabytes']
        self.MAX_REQUEST_SIZE = 1024 * 1024 * 1024 * self._max_size_gigabytes
        self.MAX_FILE_SIZE = 1024 * 1024 * 1024 * self._max_size_gigabytes
        self._check_folders(self._res_directory, self._html_directory)

    def _read_config(self):
        with open(self._config_file_path, 'r') as config_file:
            return json.load(config_file)

    def _check_folders(self, res_path, html_path):
        print(f'checking {res_path}')
        if not os.path.exists(res_path):
            print(f'folder {res_path} does not exist')
            os.makedirs(res_path)
            print(f'folder {res_path} created')
        print("OK")

        print(f'checking {html_path}')
        if not os.path.exists(html_path):
            print(f'folder {html_path} does not exist')
            os.makedirs(html_path)
            print(f'folder {html_path} created')
        print("OK")

        print(datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S") + "\n")
        if not os.path.exists("modules/main/saver/buf"):
            os.makedirs("modules/main/saver/buf")

    def start_console(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host = self._host
        port = self._port
        server_socket.bind((host, port))
        server_socket.listen()

        print(f"Server running on http://{self._host}:{self._port} " + datetime.datetime.now().strftime(
            "%d.%m.%Y %H:%M:%S"))

        while True:
            conn, addr = server_socket.accept()
            print(f"Подключен к {addr}")

            with conn:
                # Получаем длину имени файла
                filename_length = int.from_bytes(conn.recv(4), 'big')
                filename = conn.recv(filename_length).decode('utf-8')  # Декодируем имя файла

                if not filename:
                    break

                # Сохраняем файл сначала в папку buf
                buf_path = os.path.join("modules/main/saver/buf", filename)
                with open(buf_path, 'wb') as f:
                    print(f"Получение файла: {filename}")
                    while True:
                        data = conn.recv(1024)
                        if not data:
                            break
                        f.write(data)
                print(f"Файл {filename} сохранен в buf.")

                # Переносим файл из buf в res_directory
                res_path = os.path.join(self._res_directory, filename)
                shutil.move(buf_path, res_path)
                print(f"Файл {filename} перемещен в {self._res_directory}.")


if __name__ == "__main__":
    saver = Saver("config/config.json")
    saver.start_console()