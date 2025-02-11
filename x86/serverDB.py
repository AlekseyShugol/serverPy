import sqlite3
import bcrypt


class ServerDB:
    def __init__(self, path, name):
        self._conn = sqlite3.connect(f"{path}/{name}.db", check_same_thread=False)
        self._cursor = self._conn.cursor()
        self._cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                login TEXT NOT NULL UNIQUE,
                password BLOB NOT NULL,  -- Изменяем тип на BLOB для хранения байтов
                role TEXT NOT NULL DEFAULT 'user'
            )
        ''')
        self.ensure_admin()  # Проверяем наличие админа при инициализации

    def ensure_admin(self):
        # Проверяем, есть ли администратор
        self._cursor.execute("SELECT * FROM users WHERE login = ?", ("admin",))
        if not self._cursor.fetchone():
            # Хешируем пароль для админа
            password = "admin"
            self.insert_user("admin", password, role='admin')  # Добавляем админа

    def insert_user(self, login, password, role='user'):
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())  # Хешируем пароль
        self._cursor.execute("INSERT INTO users (login, password, role) VALUES (?, ?, ?)",
                             (login, hashed_password, role))
        self._conn.commit()


    def get_user(self, login):
        self._cursor.execute("SELECT id, login, password, role FROM users WHERE login = ?", (login,))
        result = self._cursor.fetchone()
        if result:
            return {
                "id": result[0],
                "login": result[1],
                "password": result[2],  # Это хешированный пароль
                "role": result[3]
            }
        return None  # Если пользователь не найден

    def update_user(self, user_id, login, password, role='user'):
        self._cursor.execute("SELECT role FROM users WHERE id = ?", (user_id,))
        current_role = self._cursor.fetchone()

        if current_role and current_role[0] == 'admin':
            # Если это администратор, не разрешаем менять логин
            self._cursor.execute("UPDATE users SET password = ?, role = ? WHERE id = ?",
                                 (bcrypt.hashpw(password.encode(), bcrypt.gensalt()), role, user_id))
        else:
            self._cursor.execute("UPDATE users SET login = ?, password = ?, role = ? WHERE id = ?",
                                 (login, bcrypt.hashpw(password.encode(), bcrypt.gensalt()), role, user_id))

        self._conn.commit()

    def check_user(self, login, password):
        # Проверяем, существует ли пользователь и совпадают ли пароли
        self._cursor.execute("SELECT password FROM users WHERE login = ?", (login,))
        result = self._cursor.fetchone()

        if result:
            hashed_password = result[0]  # Это должно быть BLOB
            return bcrypt.checkpw(password.encode(), hashed_password)  # Проверяем пароль
        return False  # Пользователь не найден

    def get_users(self):
        self._cursor.execute('SELECT * FROM users')
        return self._cursor.fetchall()

    def delete_user(self, user_id):
        self._cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        self._conn.commit()

    def delete_user_by_login(self, login):
        self._cursor.execute("DELETE FROM users WHERE login = ?", (login,))
        self._conn.commit()

    def get_user_id_by_login(self, login):
        self._cursor.execute("SELECT id FROM users WHERE login = ?", (login,))
        result = self._cursor.fetchone()
        return result[0] if result else None  # Возвращает ID или None, если пользователь не найден

    def __del__(self):
        print("Closing DB")
        self._cursor.close()
        self._conn.close()

# # Пример использования
# db = ServerDB(".", "dbTest")
# a = db.check_user("admin", "admin")  # Используйте правильный пароль
# print(a)  # Ожидается True
# print(db.get_user("admin"))