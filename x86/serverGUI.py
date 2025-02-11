import json
import os
import socket
import tkinter as tk
from json import JSONDecodeError
from tkinter import messagebox, ttk
import threading
import datetime
from urllib.parse import unquote

from serverDB import ServerDB
from jwtManager import JWTManager

class MyApp:
    def __init__(self, config_file_path):
        self._root = tk.Tk()
        self._root.geometry("800x600")

        # Создаем тулбар
        self._toolbar = ttk.Frame(self._root)
        self._toolbar.pack(side=tk.TOP, fill=tk.X)

        self._clear_button = tk.Button(self._toolbar, text="Clear", command=self.clear_text)
        self._clear_button.pack(side=tk.LEFT, padx=5, pady=5)

        self._tree_button = tk.Button(self._toolbar, text="Tree", command=self._show_tree)
        self._tree_button.pack(side=tk.LEFT, padx=5, pady=5)

        # Создаем текстовое поле
        self._text_area = tk.Text(self._root, height=15, width=150)
        self._text_area.pack(padx=10, pady=(5, 5), fill=tk.BOTH, expand=True)
        self._text_area.insert(tk.END, "The application is running\n")
        self._text_area.configure(state=tk.DISABLED)

        self._config_file_path = config_file_path
        fullPath = os.path.realpath(config_file_path)
        print("Full Path:", fullPath)

        if not os.path.exists(config_file_path):
            messagebox.showerror("Error", f"Config file not found\nMake sure {fullPath} exists")
            self._root.destroy()
            return

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
        self._secrets_file = self._read_secret(config_file["secret_path"])
        self._secret = self._secrets_file['secret']
        self.MAX_REQUEST_SIZE = 1024 * 1024 * 1024 * self._max_size_gigabytes
        self.MAX_FILE_SIZE = 1024 * 1024 * 1024 * self._max_size_gigabytes

        # Запуск проверки папок в отдельном потоке
        threading.Thread(target=self._check_folders, args=(self._res_directory, self._html_directory, self._log_directory, self._database_directory), daemon=True).start()

        self._db = ServerDB(self._database_directory, self._database_name)

        self._root.title(f"Server Manager v{self._version}")

    def start(self):
        """Запуск главного цикла приложения."""
        self._root.mainloop()

    def display_text(self, text):
        """Метод для добавления текста в текстовое поле."""
        self._text_area.configure(state=tk.NORMAL)
        self._text_area.insert(tk.END, f"{text}\n")
        self._text_area.see(tk.END)
        self._text_area.configure(state=tk.DISABLED)

    def clear_text(self):
        """Метод для очистки текстового поля."""
        self._text_area.configure(state=tk.NORMAL)
        self._text_area.delete(1.0, tk.END)
        self._text_area.configure(state=tk.DISABLED)

    def _get_datetime(self, end="\n"):
        return datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S") + end

    def _log(self, content):
        today = self._get_datetime()
        filename = os.path.join(self._log_directory, f"{today}.txt")
        with open(filename, "a") as f:
            f.write(content + '\n')

    def _check_folders(self, res_path, html_path, log_directory, database_directory):
        for path in [res_path, html_path, log_directory, database_directory]:
            self.display_text(f'Checking {path}')
            if not os.path.exists(path):
                self.display_text(f'Folder {path} does not exist')
                os.makedirs(path)
                self.display_text(f'Folder {path} created')
            self.display_text("OK")
        self.display_text(self._get_datetime())

    def _read_config(self):
        with open(self._config_file_path, 'r') as config_file:
            return json.load(config_file)

    def _read_secret(self, file_path):
        try:
            with open(file_path, 'r') as secret_file:
                return json.load(secret_file)
        except FileNotFoundError:
            messagebox.showerror("Error", f"Config file not found\nMake sure {file_path} exists")

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

    def _show_tree(self):
        """Показать дерево директорий в новом окне."""
        tree_window = tk.Toplevel(self._root)
        tree_window.title("Directory Tree")
        tree_window.geometry("600x400")

        tree_text_area = tk.Text(tree_window, wrap="word")
        tree_text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        tree_output = self._print_tree(self._res_directory)
        formatted_tree = "\n".join(tree_output)

        tree_text_area.insert(tk.END, formatted_tree)
        tree_text_area.configure(state=tk.NORMAL)  # Делаем текст редактируемым для возможности копирования
        tree_text_area.configure(state=tk.DISABLED)  # Возвращаем в нередактируемый режим

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

            # Декодируем только после завершения чтения
            try:
                decoded_data = data.decode('utf-8')
            except UnicodeDecodeError:
                print("Ошибка декодирования. Проверьте кодировку.")
                # Можно обработать ошибку или вернуть None
                return None

            if len(decoded_data) > self.MAX_REQUEST_SIZE:
                raise ValueError("Request size exceeds limit")
            if '\r\n\r\n' in decoded_data:
                headers_part, body_part = decoded_data.split('\r\n\r\n', 1)
                headers = headers_part.split('\r\n')
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
                    body_part += chunk.decode('utf-8', errors='ignore')  # Декодируем только тело

                return headers_part + '\r\n\r\n' + body_part

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
            post_data = {}
            command = ""
            # Разделяем заголовки и тело запроса
            if '\r\n\r\n' not in request:
                raise ValueError("Invalid request format: missing headers-body separator.")

            headers, body = request.split('\r\n\r\n', 1)

            # Извлекаем Content-Length (если есть)
            content_length = 0
            for header_line in headers.split('\r\n'):
                if header_line.startswith("Content-Length:"):
                    content_length = int(header_line.split(': ')[1])
                    break

            # Проверяем, что тело запроса не пустое
            if not body and content_length > 0:
                raise ValueError("Empty body in request.")

            # Извлекаем Content-Type (если есть)
            content_type = 'text/plain'  # Значение по умолчанию
            for header_line in headers.split('\r\n'):
                if header_line.startswith("Content-Type:"):
                    content_type = header_line.split(': ')[1]
                    break

            # Обрабатываем multipart/form-data
            if 'multipart/form-data' in content_type:
                boundary = content_type.split('boundary=')[1]
                parts = body.split('--' + boundary)

                for part in parts:
                    if 'filename="' in part:
                        file_name = part.split('filename="')[1].split('"')[0]
                        file_content = part.split('\r\n\r\n')[1].rstrip('\r\n--')
                        file_path = os.path.join(self._res_directory, file_name)

                        with open(file_path, 'wb') as f:
                            f.write(file_content.encode())

                        response_body = f"File '{file_name}' uploaded successfully."
                        break
            # Обрабатываем application/json
            elif 'application/json' in content_type:
                if not body:
                    raise ValueError("Empty JSON body.")

                try:
                    post_data = json.loads(body)  # Декодируем JSON из тела запроса
                    command = post_data.get("command")  # Извлекаем команду
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON: {str(e)}")

            # Обрабатываем обычные form-data
            else:
                for pair in body.split('&'):
                    if '=' in pair:
                        key, value = pair.split('=', 1)
                        post_data[key] = unquote(value)
                try:

                    command = post_data.get("command")  # Извлекаем команду
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON: {str(e)}")



            # Дополнительная логика для обработки команд
            if "upload" in headers:
                file_name = headers.split('filename="')[1].split('"')[0]
                file_path = os.path.join(self._res_directory, file_name)

                with open(file_path, 'wb') as f:
                    f.write(body.encode()[:content_length])

            content_type = 'text/plain'
            if command == "status":
                response_body = "Server is running."
            elif command == "list":
                token = JWTManager(self._secret)
                user_token = post_data.get("token")
                if token.validate_token(user_token):
                    structure = self._create_directory_structure(self._res_directory)
                    response_body = json.dumps(structure, indent=2)
                    content_type = 'application/json'
                else:
                    response_body = {"status": "error", "message": "Invalid token"}
                    response_body = json.dumps(response_body, indent=2)
                    self._send_response(conn, response_body)
            elif command == "tree":
                tree_lines = self._print_tree(self._res_directory)
                response_body = "\n".join(tree_lines)
            elif command == "version":
                response_body = f"Current version is {self._version}"
            elif command == "versionNum":
                response_body = f"{self._version}"
            elif command == "auth":
                login = post_data.get("login")
                password = post_data.get("password")
                response_body = {}
                if not login:
                    response_body = {"status": "Login is required."}
                    response_body = json.dumps(response_body)
                elif not password:
                    response_body = {"status": "Password is required."}
                    response_body = json.dumps(response_body)


                check_result = self._db.check_user(login, password)
                if check_result:
                    token = JWTManager(self._secret)
                    user_id = self._db.get_user_id_by_login(login)
                    encode_token = token.encode(user_id)

                    response_body = {
                        "status": "success",
                        f"token": f"{encode_token}"
                    }
                    response_body = json.dumps(response_body)
                else:
                    response_body = {
                        "status": "auth error"
                    }
                    response_body = json.dumps(response_body)
            elif command == "reg":
                login = post_data.get("login")
                password = post_data.get("password")
                if not login:
                    response_body = {"status": "Login is required."}
                elif not password:
                    response_body = {"status": "Password is required."}
                else:
                    content_type = "application/json"
                    self._db.insert_user(login, password)
                    message1 = f"User {login} registered successfully."
                    message2 = f"Add {login} to db successfully."
                    time = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                    print(message1)
                    print(message2)
                    print(time)
                    self._log(f"{message1}\n{message2}\n{time}")
                    if self._db.check_user(login, password):
                        response_body = {"status":"success"}
                    response_body = json.dumps(response_body)
            else:
                response_body = {"status": "unsupported"}
                response_body = json.dumps(response_body)
                status_code = 400
        except JSONDecodeError as e:
            response_body = {"status": "error", "message": str(e)}
            response_body = json.dumps(response_body)
            status_code = 400
        except ValueError as e:
            response_body = {"status": "error", "message": str(e)}
            response_body = json.dumps(response_body)
            status_code = 400
        except Exception as e:
            response_body = {"status": "error", "message": str(e)}
            response_body = json.dumps(response_body)
            status_code = 500

        self._send_response(conn, response_body, status_code, content_type)

    def _handle_get(self, conn, request):
        try:
            request_line = request.split('\r\n')[0]
            method, path, protocol = request_line.split()
            path = path.lstrip('/')
            path = unquote(path)

            if path == "":
                full_path = os.path.join(self._html_directory, "index.html")
            elif path == "menu":
                full_path = os.path.join(self._html_directory, "menu.html")
            elif path == "main":
                full_path = os.path.join(self._html_directory, "main.html")
            elif path == "reg":
                full_path = os.path.join(self._html_directory, "registration.html")
            elif path == "auth":
                full_path = os.path.join(self._html_directory, "index.html")
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

    def start_server(self):
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



