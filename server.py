import socket
import json
import os
import threading
import datetime
from json import JSONDecodeError

from modules.database import serverDB
from modules.database.serverDB import ServerDB


class Server:
    def __init__(self, config_file_path):
        print("Initializing Server")
        print("Reading config file: ")
        self.config_file_path = config_file_path
        if not os.path.exists(config_file_path):
            print("Config file not found")
            try:
                os.makedirs("config")
            except Exception as e:
                print("Failed to create config file")
            data = {
                "host": "localhost",
                "port_sender": 8000,
                "port_saver": 8001,
                "res_directory": "res",
                "html_directory": "public",
                "log_directory": "logs",
                "database_directory": "data",
                "max_size_gigabytes": 2,
                "secret": "secret",
                "version": "1.0"
            }
            print(f"create config.json as {(json.dumps(data, indent=4))}")
            quit(-1)

        self._config_file_path = config_file_path
        config_file = self._read_config()
        self._host = config_file['host']
        self._port = config_file['port_sender']
        self._html_directory = os.path.abspath(config_file['html_directory'])
        self._res_directory = os.path.abspath(config_file['res_directory'])
        self._max_size_gigabytes = config_file['max_size_gigabytes']
        self._version = config_file['version']
        self._log_directory = os.path.abspath(config_file['log_directory'])
        self._database_directory = os.path.abspath(config_file['database_directory'])
        self._database_name = config_file['database_name']
        self._secret = config_file['secret']
        self.MAX_REQUEST_SIZE = 1024 * 1024 * 1024 * self._max_size_gigabytes
        self.MAX_FILE_SIZE = 1024 * 1024 * 1024 * self._max_size_gigabytes
        self._check_folders(self._res_directory,self._html_directory,self._log_directory,self._database_directory)
        db = ServerDB(self._database_directory,self._database_name)

    def _log(self, content):
        today = datetime.date.today().strftime("%d.%m.%Y")
        filename = os.path.join(self._log_directory,f"{today}.txt")
        with open(filename,"a") as f:
            f.write(content + '\n')

    def _check_folders(self, res_path, html_path,log_directory,database_directory):
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
        print(f'checking {log_directory}')
        if not os.path.exists(log_directory):
            print(f'folder {log_directory} does not exist')
            os.makedirs(log_directory)
            print(f'folder {log_directory} created')
        print("OK")
        print(f'checking {database_directory}')
        if not os.path.exists(database_directory):
            print(f'folder {database_directory} does not exist')
            os.makedirs(database_directory)
            print(f'folder {database_directory} created')
        print("OK")
        print(datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")+"\n")

    def _read_config(self):
        with open(self._config_file_path, 'r') as config_file:
            return json.load(config_file)

    def _print_tree(self, path, prefix=""):
        buffer = []
        try:
            items = os.listdir(path)
        except Exception as e:
            buffer.append(f"Error accessing directory {path}: {e}")
            return buffer

        items.sort()

        for index, item in enumerate(items):
            item_path = os.path.join(path, item)
            is_last = index == len(items) - 1

            connector = "|__ " if is_last else "|-- "
            try:
                item_encoded = item.encode('utf-8').decode('utf-8')
            except UnicodeDecodeError:
                item_encoded = item.encode('utf-8', 'replace').decode('utf-8')

            buffer.append(prefix + connector + item_encoded)

            if os.path.isdir(item_path):
                new_prefix = prefix + ("    " if is_last else "|   ")
                buffer.extend(self._print_tree(item_path, new_prefix))

        return buffer

    def _create_directory_structure(self, path):
        structure = {}
        try:
            items = os.listdir(path)
        except Exception as e:
            return {"error": str(e)}
        for item in items:
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                structure[item] = {
                    "type": "directory",
                    "children": self._create_directory_structure(item_path)
                }
            else:
                structure[item] = {
                    "type": "file"
                }
        return structure

    def _read_full_request(self, conn):
        data = b''
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            data += chunk

            if len(data) > self.MAX_REQUEST_SIZE:
                raise ValueError("Request size exceeds limit")
            if b'\r\n\r\n' in data:
                headers_part, body_part = data.split(b'\r\n\r\n', 1)
                headers = headers_part.decode().split('\r\n')
                content_length = 0

                for header in headers:
                    if header.lower().startswith('content-length:'):
                        content_length = int(header.split(': ')[1])
                        break

                if content_length > self.MAX_REQUEST_SIZE:
                    raise ValueError("Request body too large")

                while len(body_part) < content_length:
                    chunk = conn.recv(4096)
                    if not chunk:
                        break
                    body_part += chunk
                    if len(body_part) > self.MAX_REQUEST_SIZE:
                        raise ValueError("Request body too large")

                return headers_part.decode() + '\r\n\r\n' + body_part.decode()
        return None

    def _handle_client(self, conn):
        try:
            conn.settimeout(45)
            request = self._read_full_request(conn)

            print(request)
            self._log(f"{request}")

            print(datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S"))
            print("\n"
                  ".....................................................")
            print("")
            self._log(f"..............................................")


            if not request:
                return

            if request.startswith('GET'):
                self._handle_get(conn, request)
            elif request.startswith('POST'):
                self._handle_post(conn, request)
            else:
                self._send_response(conn, "Method Not Allowed", 405)
        except ValueError as e:
            self._send_response(conn, str(e), 413)
        except Exception as e:
            self._send_response(conn, f"Internal Server Error: {e}", 500)
        finally:
            conn.close()

    def _handle_post(self, conn, request):
        status_code = 200
        content_type = 'text/plain'
        response_body = "Unknown command."

        try:
            headers, body = request.split('\r\n\r\n', 1)
            content_length = int(
                [h for h in headers.split('\r\n') if h.startswith("Content-Length:")][0].split(': ')[1])

            if "upload" in headers:
                file_name = headers.split('filename="')[1].split('"')[0]
                file_path = os.path.join(self._res_directory, file_name)

                # Save the uploaded file
                with open(file_path, 'wb') as f:
                    f.write(body.encode()[:content_length])  # Write only the content length bytes

                response_body = f"File '{file_name}' uploaded successfully."
                content_type = 'text/plain'
            else:
                command_data = json.loads(body)
                command = command_data.get("command")

                if command == "status":
                    response_body = "Server is running."
                elif command == "list":
                    structure = self._create_directory_structure(self._res_directory)
                    response_body = json.dumps(structure, indent=2)
                    content_type = 'application/json'
                elif command == "tree":
                    tree_lines = self._print_tree(self._res_directory)
                    response_body = "\n".join(tree_lines)
                elif command == "version":
                    response_body = f"Current version is {self._version}"
                elif command == "versionNum":
                    response_body = f"{self._version}"
                elif command == "auth":
                    response_body = "in dev now"
                elif command == "reg":
                    response_body = "in dev now"
                else:
                    response_body = "Unsupported command."
                    status_code = 400
        except JSONDecodeError as e:
            response_body = f" {str(e)}"
            status_code = 400
        except Exception as e:
            response_body = f"Error processing request: {str(e)}"
            status_code = 500

        self._send_response(conn, response_body, status_code, content_type)

    def _handle_get(self, conn, request):
        try:
            request_line = request.split('\r\n')[0]
            method, path, protocol = request_line.split()
            path = path.lstrip('/')

            if path == "":
                full_path = os.path.join(self._html_directory, "index.html")
            elif path == "menu":
                full_path = os.path.join(self._html_directory, "menu.html")
            elif path == "main":
                full_path = os.path.join(self._html_directory, "main.html")
            elif path.endswith('.html'):
                full_path = os.path.join(self._html_directory, path)
            elif path=='icon.png':
                full_path = os.path.join(self._html_directory, path)

            else:
                full_path = os.path.join(self._res_directory, path)

            if os.path.isfile(full_path):
                if full_path.endswith('.html'):
                    self._serve_html_file(conn, full_path)
                else:
                    self._serve_file(conn, full_path)
            else:
                self._serve_404(conn)
        except Exception as e:
            self._send_response(conn, "Bad Request", 400)

    def _serve_file(self, conn, file_path):
        try:
            if not os.path.isfile(file_path):
                self._send_response(conn, "Not Found", 404)
                return
            file_size = os.path.getsize(file_path)

            # Проверка на превышение максимального размера
            if file_size > self.MAX_FILE_SIZE:
                try:
                    self._serve_413(conn)
                except Exception as e:
                    self._send_response(conn, "File size exceeds limit", 413)
                return

            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)

            headers = [
                "HTTP/1.1 200 OK",
                "Content-Type: application/octet-stream",
                f"Content-Length: {file_size}",
                f"Content-Disposition: attachment; filename=\"{file_name}\"",
                "\r\n"
            ]

            conn.sendall("\r\n".join(headers).encode())

            with open(file_path, 'rb') as f:
                while chunk := f.read(4096):
                    try:
                        conn.sendall(chunk)
                    except (ConnectionResetError, BrokenPipeError):
                        print(f"Connection lost while sending file: {file_path}")
                        break
                    except Exception as e:
                        print(e)
                        return
        except Exception as e:
            print(f"Error serving file {file_path}: {e}")
            self._send_response(conn, "Internal Server Error", 500)

    def _serve_html_file(self, conn, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self._send_response(conn, content, content_type='text/html')
        except FileNotFoundError:
            self._serve_404(conn)

    def _send_response(self, conn, content, status_code=200, content_type='text/plain'):
        headers = {
            "Content-Type": content_type,
            "Connection": "close"
        }

        response = [
            f"HTTP/1.1 {status_code} {self._get_status_text(status_code)}",
            f"Content-Length: {len(content)}",
            *[f"{k}: {v}" for k, v in headers.items()],
            "\r\n"
        ]

        header_data = "\r\n".join(response)
        conn.sendall(header_data.encode() + content.encode())

    def _send_response_headers(self, conn, status_code, headers):
        response = [
            f"HTTP/1.1 {status_code} {self._get_status_text(status_code)}",
            *[f"{k}: {v}" for k, v in headers.items()],
            "\r\n"
        ]
        header_data = "\r\n".join(response)
        conn.sendall(header_data.encode())

    def _get_status_text(self, status_code):
        return {
            200: 'OK',
            400: 'Bad Request',
            403: 'Forbidden',
            404: 'Not Found',
            405: 'Method Not Allowed',
            413: 'Payload Too Large',
            500: 'Internal Server Error'
        }.get(status_code, 'Unknown Status')

    def _serve_404(self, conn):
        error_path = os.path.join(self._html_directory, '404.html')
        if os.path.exists(error_path):
            with open(error_path, 'r') as f:
                content = f.read()
            self._send_response(conn, content, 404, "text/html")
        else:
            self._send_response(conn, "Not Found", 404)

    def _serve_413(self, conn):
        error_path = os.path.join(self._html_directory, '413.html')
        if os.path.exists(error_path):
            with open(error_path, 'r') as f:
                content = f.read()
            self._send_response(conn, content, 404, "text/html")
        else:
            self._send_response(conn, "Payload Too Large", 404)

    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self._host, self._port))
        server.listen(50)
        line = f'| Server running on http://{self._host}:{self._port} { datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")} |'
        self._log(line)
        print("+"* len(line))
        print(line)
        print("+" * len(line))
        flag = True
        try:
            while flag:
                conn, addr = server.accept()
                line = f"Connected to IP: {addr[0]}\nPORT: {addr[1]}\nDATE: " + datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")+"\n"

                print("-" * len(line))
                self._log("-" * len(line))
                self._log(line)
                print(line)
                client_thread = threading.Thread(target=self._handle_client, args=(conn,))
                client_thread.start()
        except KeyboardInterrupt:
            print("Остановка сервера...")
        finally:
            server.close()
            print(f"Сервер остановлен.\n{datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
            self._log(f"Сервер остановлен.\n{datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")

    def __del__(self):
        print("+++++++++++++++++++++++++++++")
        print("| The server is shutting up |")
        print("+++++++++++++++++++++++++++++")

if __name__ == "__main__":
    server = Server("config/config.json")
    server.start()