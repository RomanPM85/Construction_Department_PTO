import socket
import threading
import tkinter as tk
from tkinter import simpledialog, scrolledtext, filedialog, messagebox, Label
import os
import shutil
from datetime import datetime
import json


class ChatClient:
    def __init__(self, host='127.0.0.1', port=12345):
        self.setup_storage()
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.file_history = self.load_file_history()
        self.server_files = []  # Список файлов на сервере
        self.setup_connection(host, port)

    def setup_storage(self):
        """Настройка директорий для хранения файлов"""
        self.base_dir = os.path.join(os.path.expanduser('~'), 'ChatFiles')
        self.downloads_dir = os.path.join(self.base_dir, 'Downloads')
        self.sent_files_dir = os.path.join(self.base_dir, 'Sent')
        self.sync_dir = os.path.join(self.base_dir, 'Sync')  # Новая директория для синхронизации
        self.history_file = os.path.join(self.base_dir, 'file_history.json')

        # Создаем необходимые директории
        for directory in [self.downloads_dir, self.sent_files_dir, self.sync_dir]:
            os.makedirs(directory, exist_ok=True)

    def load_file_history(self):
        """Загрузка истории файлов"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Ошибка при загрузке истории файлов: {e}")
        return {'sent': [], 'received': [], 'synced': []}  # Добавляем поле для синхронизированных файлов

    def save_file_history(self):
        """Сохранение истории файлов"""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.file_history, f)
        except Exception as e:
            print(f"Ошибка при сохранении истории файлов: {e}")

    def setup_connection(self, host, port):
        """Настройка подключения и GUI"""
        try:
            self.client_socket.connect((host, port))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось подключиться к серверу: {e}")
            return

        self.client_name = simpledialog.askstring("Имя клиента", "Введите ваше имя:")
        if not self.client_name:
            self.client_name = "Аноним"

        # Отправляем имя на сервер
        self.client_socket.sendall(f"MSG:{self.client_name}".encode())

        self.setup_gui()

    def setup_gui(self):
        """Настройка графического интерфейса"""
        self.window = tk.Tk()
        self.window.title(f"Чат - {self.client_name}")

        # Основной фрейм
        main_frame = tk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Чат и список файлов
        chat_files_frame = tk.Frame(main_frame)
        chat_files_frame.pack(fill=tk.BOTH, expand=True)

        # Область чата
        chat_frame = tk.Frame(chat_files_frame)
        chat_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.chat_area = scrolledtext.ScrolledText(chat_frame, state='disabled')
        self.chat_area.pack(fill=tk.BOTH, expand=True)

        # Фрейм для файлов
        files_frame = tk.Frame(chat_files_frame)
        files_frame.pack(side=tk.RIGHT, fill=tk.Y)

        # Заголовок списка файлов
        files_header = tk.Frame(files_frame)
        files_header.pack(fill=tk.X)
        tk.Label(files_header, text="Файлы на сервере").pack(side=tk.LEFT)
        self.auto_refresh_var = tk.BooleanVar(value=True)
        tk.Checkbutton(files_header, text="Автообновление",
                       variable=self.auto_refresh_var).pack(side=tk.RIGHT)

        # Список файлов с чекбоксами
        files_list_frame = tk.Frame(files_frame)
        files_list_frame.pack(fill=tk.BOTH, expand=True)

        # Скроллбар для списка файлов
        scrollbar = tk.Scrollbar(files_list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.files_listbox = tk.Listbox(files_list_frame,
                                        width=30,
                                        selectmode=tk.MULTIPLE,
                                        yscrollcommand=scrollbar.set)
        self.files_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.files_listbox.yview)

        # Кнопки управления файлами
        files_buttons_frame = tk.Frame(files_frame)
        files_buttons_frame.pack(fill=tk.X, pady=5)

        tk.Button(files_buttons_frame, text="Обновить список",
                  command=self.request_files_list).pack(side=tk.LEFT, padx=2)
        tk.Button(files_buttons_frame, text="Скачать выбранные",
                  command=self.download_selected_files).pack(side=tk.LEFT, padx=2)
        tk.Button(files_buttons_frame, text="Открыть",
                  command=self.open_selected_file).pack(side=tk.LEFT, padx=2)
        tk.Button(files_buttons_frame, text="Удалить локальные",
                  command=self.delete_selected_file).pack(side=tk.LEFT, padx=2)

        # Добавляем кнопку синхронизации
        tk.Button(files_buttons_frame, text="Синхронизировать",
                  command=self.sync_files).pack(side=tk.LEFT, padx=2)

        # Ввод сообщения и кнопки
        input_frame = tk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=(5, 0))

        self.message_entry = tk.Entry(input_frame)
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.message_entry.bind("<Return>", self.send_message)

        buttons_frame = tk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=(5, 0))

        tk.Button(buttons_frame, text="Отправить файл",
                  command=self.send_file).pack(side=tk.LEFT)
        tk.Button(buttons_frame, text="Вставить",
                  command=self.paste_from_clipboard).pack(side=tk.LEFT)
        tk.Button(buttons_frame, text="Копировать",
                  command=self.copy_to_clipboard).pack(side=tk.LEFT)

        # Добавляем чекбокс для автосинхронизации
        self.auto_sync_var = tk.BooleanVar(value=False)
        tk.Checkbutton(buttons_frame, text="Автосинхронизация",
                       variable=self.auto_sync_var).pack(side=tk.LEFT)

        tk.Button(buttons_frame, text="Выход",
                  command=self.on_closing).pack(side=tk.RIGHT)

        # Запускаем автообновление списка файлов
        self.start_auto_refresh()

        # Запускаем поток приема сообщений
        self.receive_thread = threading.Thread(target=self.receive_messages)
        self.receive_thread.daemon = True
        self.receive_thread.start()

        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.mainloop()

    def start_auto_refresh(self):
        """Запуск автообновления списка файлов и синхронизации"""

        def refresh():
            if self.auto_refresh_var.get():
                self.request_files_list()

            # Автоматическая синхронизация файлов, если включена
            if self.auto_sync_var.get():
                self.sync_files(silent=True)

            self.window.after(5000, refresh)  # Обновление каждые 5 секунд

        refresh()

    def request_files_list(self):
        """Запрос списка файлов с сервера"""
        try:
            self.client_socket.sendall("LIST_FILES".encode())
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось запросить список файлов: {e}")

    def update_files_list(self, files_data):
        """Обновление списка файлов"""
        self.files_listbox.delete(0, tk.END)
        try:
            files = json.loads(files_data)
            self.server_files = files  # Сохраняем список файлов с сервера

            for file_info in files:
                # Отмечаем синхронизированные файлы
                file_path = os.path.join(self.sync_dir, file_info['name'])
                is_synced = os.path.exists(file_path)
                status = "✓ " if is_synced else ""

                self.files_listbox.insert(tk.END,
                                          f"{status}{file_info['name']} ({file_info['size']} bytes)")

                # Если включена автосинхронизация и файл не синхронизирован
                if self.auto_sync_var.get() and not is_synced:
                    self.download_file(file_info['name'], self.sync_dir, silent=True)

        except Exception as e:
            messagebox.showerror("Ошибка",
                                 f"Ошибка при обновлении списка файлов: {e}")

    def sync_files(self, silent=False):
        """Синхронизация файлов с сервера"""
        if not self.server_files:
            if not silent:
                messagebox.showinfo("Информация", "Нет файлов для синхронизации")
            return

        try:
            # Создаем список файлов, которые нужно синхронизировать
            files_to_sync = []
            for file_info in self.server_files:
                file_name = file_info['name']
                file_path = os.path.join(self.sync_dir, file_name)

                # Если файл не существует или его размер отличается
                if not os.path.exists(file_path) or os.path.getsize(file_path) != file_info['size']:
                    files_to_sync.append(file_name)

            if not files_to_sync:
                if not silent:
                    messagebox.showinfo("Информация", "Все файлы уже синхронизированы")
                return

            # Скачиваем файлы, которые нужно синхронизировать
            for file_name in files_to_sync:
                self.download_file(file_name, self.sync_dir, silent)

            # Обновляем список файлов после синхронизации
            self.request_files_list()

            if not silent:
                messagebox.showinfo("Информация", f"Синхронизировано {len(files_to_sync)} файлов")

        except Exception as e:
            if not silent:
                messagebox.showerror("Ошибка", f"Ошибка при синхронизации файлов: {e}")

    def download_file(self, file_name, save_dir, silent=False):
        """Скачивание одного файла"""
        try:
            self.client_socket.sendall(f"DOWNLOAD_FILE:{file_name}".encode())
            save_path = os.path.join(save_dir, file_name)

            # Ожидаем ответ сервера
            header = self.client_socket.recv(1024).decode()
            if header.startswith("FILE:"):
                _, file_name, file_size = header.split(":")
                file_size = int(file_size)

                received_data = 0
                with open(save_path, 'wb') as f:
                    while received_data < file_size:
                        data = self.client_socket.recv(
                            min(8192, file_size - received_data))
                        if not data:
                            break
                        f.write(data)
                        received_data += len(data)

                # Добавляем в историю синхронизированных файлов
                self.file_history['synced'].append({
                    'name': file_name,
                    'date': datetime.now().isoformat(),
                    'path': save_path
                })
                self.save_file_history()

                if not silent:
                    self.display_message(f"Файл {file_name} успешно сохранен")
                return True
            else:
                if not silent:
                    messagebox.showerror("Ошибка", "Неверный формат ответа сервера")
                return False

        except Exception as e:
            if not silent:
                messagebox.showerror("Ошибка", f"Ошибка при скачивании файла {file_name}: {e}")
            return False

    def download_selected_files(self):
        """Скачивание выбранных файлов"""
        selected_indices = self.files_listbox.curselection()
        if not selected_indices:
            messagebox.showinfo("Информация", "Выберите файлы для скачивания")
            return

        save_dir = filedialog.askdirectory(title="Выберите папку для сохранения")
        if not save_dir:
            return

        for index in selected_indices:
            file_info = self.files_listbox.get(index)
            # Удаляем статус синхронизации и размер из имени файла
            file_name = file_info.replace("✓ ", "").split(" (")[0]
            self.download_file(file_name, save_dir)

    def send_file(self):
        """Отправка файла"""
        file_path = filedialog.askopenfilename()
        if not file_path:
            return

        file_name = os.path.basename(file_path)
        try:
            # Копируем файл в директорию отправленных
            sent_path = os.path.join(self.sent_files_dir, file_name)
            shutil.copy2(file_path, sent_path)

            # Отправляем файл
            file_size = os.path.getsize(file_path)
            header = f"FILE:{file_name}:{file_size}"
            self.client_socket.sendall(header.encode())

            with open(file_path, 'rb') as f:
                while True:
                    data = f.read(8192)
                    if not data:
                        break
                    self.client_socket.sendall(data)

            # Обновляем историю и GUI
            self.file_history['sent'].append({
                'name': file_name,
                'date': datetime.now().isoformat(),
                'path': sent_path
            })
            self.save_file_history()
            self.request_files_list()
            self.display_message(f"Вы отправили файл: {file_name}")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при отправке файла: {e}")

    def receive_file(self, file_info):
        """Получение файла из чата"""
        try:
            file_name, file_size = file_info.split(":")
            file_size = int(file_size)

            # Путь для сохранения файла
            save_path = os.path.join(self.downloads_dir, file_name)

            received_data = 0
            with open(save_path, 'wb') as f:
                while received_data < file_size:
                    data = self.client_socket.recv(min(8192, file_size - received_data))
                    if not data:
                        break
                    f.write(data)
                    received_data += len(data)

            # Обновляем историю
            self.file_history['received'].append({
                'name': file_name,
                'date': datetime.now().isoformat(),
                'path': save_path
            })
            self.save_file_history()

            # Если включена автосинхронизация, копируем файл в директорию синхронизации
            if self.auto_sync_var.get():
                sync_path = os.path.join(self.sync_dir, file_name)
                shutil.copy2(save_path, sync_path)

            self.display_message(f"Получен файл: {file_name}")
            self.request_files_list()  # Обновляем список файлов

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при получении файла: {e}")

    def open_selected_file(self, event=None):
        """Открытие выбранного файла"""
        try:
            selection = self.files_listbox.curselection()
            if selection:
                file_info = self.files_listbox.get(selection[0])
                file_name = file_info.replace("✓ ", "").split(" (")[0]

                # Проверяем наличие файла в разных директориях
                for directory in [self.sync_dir, self.downloads_dir, self.sent_files_dir]:
                    filepath = os.path.join(directory, file_name)
                    if os.path.exists(filepath):
                        os.startfile(filepath)
                        break
                else:
                    # Если файл не найден, предлагаем скачать его
                    if messagebox.askyesno("Файл не найден",
                                           f"Файл {file_name} не найден локально. Скачать?"):
                        self.download_file(file_name, self.downloads_dir)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть файл: {e}")

    def delete_selected_file(self):
        """Удаление выбранного файла"""
        try:
            selection = self.files_listbox.curselection()
            if selection:
                file_info = self.files_listbox.get(selection[0])
                file_name = file_info.replace("✓ ", "").split(" (")[0]

                deleted = False
                for directory in [self.sync_dir, self.downloads_dir, self.sent_files_dir]:
                    filepath = os.path.join(directory, file_name)
                    if os.path.exists(filepath):
                        os.remove(filepath)
                        deleted = True

                if deleted:
                    self.request_files_list()
                    messagebox.showinfo("Информация", f"Файл {file_name} удален локально")
                else:
                    messagebox.showinfo("Информация", f"Файл {file_name} не найден локально")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить файл: {e}")

    def send_message(self, event=None):
        """Отправка сообщения"""
        message = self.message_entry.get().strip()
        if message:
            try:
                full_message = f"MSG:{self.client_name}: {message}"
                self.client_socket.sendall(full_message.encode())
                self.message_entry.delete(0, tk.END)
            except Exception as e:
                messagebox.showerror("Ошибка",
                                     f"Не удалось отправить сообщение: {e}")

    def receive_messages(self):
        """Получение сообщений"""
        while True:
            try:
                header = self.client_socket.recv(1024).decode()
                if not header:
                    break

                if header.startswith("FILE:"):
                    self.receive_file(header[5:])
                elif header.startswith("MSG:"):
                    self.display_message(header[4:])
                elif header.startswith("FILES_LIST:"):
                    self.update_files_list(header[11:])
                else:
                    self.display_message(header)

            except ConnectionResetError:
                self.display_message("Соединение с сервером было разорвано.")
                break
            except ConnectionAbortedError:
                self.display_message("Соединение с сервером было прервано.")
                break
            except Exception as e:
                print(f"Ошибка при получении данных: {e}")
                break

        self.on_closing()

    def display_message(self, message):
        """Отображение сообщения в чате"""
        self.chat_area.config(state='normal')
        self.chat_area.insert(tk.END, f"{message}\n")
        self.chat_area.see(tk.END)
        self.chat_area.config(state='disabled')

    def paste_from_clipboard(self):
        """Вставка из буфера обмена"""
        try:
            self.message_entry.insert(tk.END, self.window.clipboard_get())
        except tk.TclError:
            pass

    def copy_to_clipboard(self):
        """Копирование в буфер обмена"""
        try:
            selected_text = self.chat_area.selection_get()
            self.window.clipboard_clear()
            self.window.clipboard_append(selected_text)
        except tk.TclError:
            pass

    def on_closing(self):
        """Закрытие приложения"""
        try:
            self.client_socket.close()
        except:
            pass
        try:
            self.window.destroy()
        except:
            pass


if __name__ == "__main__":
    ChatClient()
