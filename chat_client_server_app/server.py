import socket
import threading
import os
import json
from datetime import datetime
import logging
from typing import Dict, Set, Optional


class ChatServer:
    def __init__(self, host: str = '127.0.0.1', port: int = 12345):
        """Инициализация сервера"""
        self.setup_logging()
        self.setup_storage()

        self.host = host
        self.port = port
        self.clients: Dict[socket.socket, str] = {}  # сокет -> имя клиента
        self.clients_lock = threading.Lock()
        self.files_in_transfer: Set[str] = set()
        self.files_in_transfer_lock = threading.Lock()

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.setup_server()

    def setup_logging(self):
        """Настройка логирования"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('server.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def setup_storage(self):
        """Настройка хранилища файлов"""
        self.storage_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                        'server_storage')
        self.files_dir = os.path.join(self.storage_dir, 'files')
        self.metadata_file = os.path.join(self.storage_dir, 'metadata.json')

        # Создаем необходимые директории
        for directory in [self.storage_dir, self.files_dir]:
            os.makedirs(directory, exist_ok=True)

        # Загружаем или создаем метаданные
        self.load_metadata()

    def load_metadata(self):
        """Загрузка метаданных о файлах"""
        try:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r') as f:
                    self.files_metadata = json.load(f)
            else:
                self.files_metadata = {}
        except Exception as e:
            self.logger.error(f"Ошибка при загрузке метаданных: {e}")
            self.files_metadata = {}

    def save_metadata(self):
        """Сохранение метаданных о файлах"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.files_metadata, f)
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении метаданных: {e}")

    def setup_server(self):
        """Настройка и запуск сервера"""
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.logger.info(f"Сервер запущен на {self.host}:{self.port}")

            while True:
                client_socket, address = self.server_socket.accept()
                self.logger.info(f"Новое подключение с {address}")

                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address)
                )
                client_thread.daemon = True
                client_thread.start()

        except Exception as e:
            self.logger.error(f"Ошибка при запуске сервера: {e}")
        finally:
            self.cleanup()

    def handle_client(self, client_socket: socket.socket, address: tuple):
        """Обработка подключения клиента"""
        try:
            # Ожидаем первое сообщение с именем клиента
            data = client_socket.recv(1024).decode()
            if data.startswith("MSG:"):
                client_name = data.split(":")[1].strip()
                with self.clients_lock:
                    self.clients[client_socket] = client_name
                self.broadcast(f"Пользователь {client_name} присоединился к чату",
                               exclude=client_socket)
                self.logger.info(f"Клиент {client_name} ({address}) подключился")

                # Отправляем текущий список файлов
                self.send_files_list(client_socket)

            while True:
                header = client_socket.recv(1024).decode()
                if not header:
                    break

                if header.startswith("FILE:"):
                    self.handle_file_transfer(client_socket, header[5:])
                elif header.startswith("MSG:"):
                    self.handle_message(client_socket, header[4:])
                elif header.startswith("LIST_FILES"):
                    self.send_files_list(client_socket)
                elif header.startswith("CHECK_FILE:"):
                    self.handle_file_check(client_socket, header[11:])
                elif header.startswith("DOWNLOAD_FILE:"):
                    self.handle_file_download(client_socket, header[14:])

        except Exception as e:
            self.logger.error(f"Ошибка при обработке клиента {address}: {e}")
        finally:
            self.handle_client_disconnect(client_socket)

    def handle_file_transfer(self, client_socket: socket.socket, file_info: str):
        """Обработка передачи файла"""
        try:
            file_name, file_size = file_info.split(':')
            file_size = int(file_size)

            file_path = os.path.join(self.files_dir, file_name)

            # Записываем файл
            received_data = 0
            with open(file_path, 'wb') as f:
                while received_data < file_size:
                    data = client_socket.recv(min(8192, file_size - received_data))
                    if not data:
                        break
                    f.write(data)
                    received_data += len(data)

            # Обновляем метаданные
            self.files_metadata[file_name] = {
                'size': file_size,
                'uploaded_by': self.clients[client_socket],
                'upload_date': datetime.now().isoformat(),
                'path': file_path
            }
            self.save_metadata()

            # Оповещаем всех о новом файле
            self.broadcast(
                f"Пользователь {self.clients[client_socket]} загрузил файл: {file_name}",
                exclude=client_socket
            )
            # Обновляем список файлов у всех клиентов
            self.broadcast_files_list()

            self.logger.info(
                f"Файл {file_name} успешно получен от {self.clients[client_socket]}")

        except Exception as e:
            self.logger.error(f"Ошибка при получении файла: {e}")
            client_socket.sendall("ERROR: Ошибка при получении файла".encode())

    def handle_file_check(self, client_socket: socket.socket, file_name: str):
        """Проверка наличия файла"""
        try:
            file_path = os.path.join(self.files_dir, file_name)
            if os.path.exists(file_path):
                client_socket.sendall("FILE_EXISTS".encode())
            else:
                client_socket.sendall("FILE_NOT_FOUND".encode())
        except Exception as e:
            self.logger.error(f"Ошибка при проверке файла: {e}")
            client_socket.sendall("ERROR".encode())

    def handle_file_download(self, client_socket: socket.socket, file_name: str):
        """Обработка запроса на скачивание файла"""
        try:
            file_path = os.path.join(self.files_dir, file_name)
            if not os.path.exists(file_path):
                client_socket.sendall("FILE_NOT_FOUND".encode())
                return

            file_size = os.path.getsize(file_path)
            client_socket.sendall(f"FILE:{file_name}:{file_size}".encode())

            with open(file_path, 'rb') as f:
                while True:
                    data = f.read(8192)
                    if not data:
                        break
                    client_socket.sendall(data)

            self.logger.info(
                f"Файл {file_name} успешно отправлен клиенту {self.clients[client_socket]}")

        except Exception as e:
            self.logger.error(f"Ошибка при отправке файла: {e}")
            client_socket.sendall("ERROR: Ошибка при отправке файла".encode())

    def handle_message(self, client_socket: socket.socket, message: str):
        """Обработка текстового сообщения"""
        try:
            self.broadcast(message, exclude=None)
            self.logger.info(f"Сообщение от {self.clients[client_socket]}: {message}")
        except Exception as e:
            self.logger.error(f"Ошибка при обработке сообщения: {e}")

    def send_files_list(self, client_socket: socket.socket):
        """Отправка списка файлов клиенту"""
        try:
            files_list = []
            for file_name in os.listdir(self.files_dir):
                file_path = os.path.join(self.files_dir, file_name)
                if os.path.isfile(file_path):
                    metadata = self.files_metadata.get(file_name, {})
                    file_info = {
                        'name': file_name,
                        'size': os.path.getsize(file_path),
                        'upload_date': metadata.get('upload_date', ''),
                        'uploaded_by': metadata.get('uploaded_by', 'Unknown')
                    }
                    files_list.append(file_info)

            response = f"FILES_LIST:{json.dumps(files_list)}"
            client_socket.sendall(response.encode())
        except Exception as e:
            self.logger.error(f"Ошибка при отправке списка файлов: {e}")
            try:
                client_socket.sendall("ERROR: Не удалось получить список файлов".encode())
            except:
                pass

    def broadcast_files_list(self):
        """Отправка списка файлов всем клиентам"""
        with self.clients_lock:
            for client_socket in self.clients:
                self.send_files_list(client_socket)

    def handle_client_disconnect(self, client_socket: socket.socket):
        """Обработка отключения клиента"""
        with self.clients_lock:
            if client_socket in self.clients:
                client_name = self.clients[client_socket]
                del self.clients[client_socket]
                self.broadcast(f"Пользователь {client_name} покинул чат")
                self.logger.info(f"Клиент {client_name} отключился")
        try:
            client_socket.close()
        except:
            pass

    def broadcast(self, message: str, exclude: Optional[socket.socket] = None):
        """Отправка сообщения всем клиентам"""
        with self.clients_lock:
            for client in self.clients:
                if client != exclude:
                    try:
                        client.sendall(f"MSG:{message}".encode())
                    except Exception as e:
                        self.logger.error(f"Ошибка при отправке сообщения клиенту: {e}")

    def cleanup(self):
        """Очистка ресурсов при завершении работы сервера"""
        self.logger.info("Завершение работы сервера...")
        with self.clients_lock:
            for client in self.clients:
                try:
                    client.close()
                except:
                    pass
        try:
            self.server_socket.close()
        except:
            pass
        self.save_metadata()


if __name__ == "__main__":
    server = ChatServer()
