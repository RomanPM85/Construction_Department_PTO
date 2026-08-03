import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import PyPDF2


class PDFExtractorApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Advanced PDF Extractor")
        self.root.geometry("700x600")

        # Внутреннее хранилище для загруженных файлов
        self.loaded_files = {}
        self.file_counter = 1

        self.setup_ui()
    def setup_ui(self):
        # Вкладки: Рабочая область и Справка (man)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.main_frame = tk.Frame(self.notebook)
        self.man_frame = tk.Frame(self.notebook)

        self.notebook.add(self.main_frame, text="📁 Рабочая область")
        self.notebook.add(self.man_frame, text="📖 Руководство (man)")

        # --- РАБОЧАЯ ОБЛАСТЬ ---
        btn_frame = tk.Frame(self.main_frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        self.btn_load = tk.Button(
            btn_frame,
            text="➕ Загрузить PDF файлы",
            command=self.load_files,
            bg="#e1f5fe",
        )
        self.btn_load.pack(side=tk.LEFT, padx=5)

        self.btn_clear = tk.Button(
            btn_frame,
            text="🗑️ Очистить список",
            command=self.clear_list,
            bg="#ffebee",
        )
        self.btn_clear.pack(side=tk.LEFT, padx=5)

        # Таблица файлов
        table_frame = tk.Frame(self.main_frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        columns = ("cmd", "name", "pages")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        self.tree.heading("cmd", text="Команда (ID)")
        self.tree.heading("name", text="Имя файла")
        self.tree.heading("pages", text="Страниц всего")

        self.tree.column("cmd", width=100, anchor=tk.CENTER)
        self.tree.column("name", width=470, anchor=tk.W)
        self.tree.column("pages", width=100, anchor=tk.CENTER)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Извлечение страниц
        extract_frame = tk.LabelFrame(
            self.main_frame, text=" Комбинированное извлечение страниц ", padx=10, pady=10
        )
        extract_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(
            extract_frame,
            text="Введите сложную команду (Пример: F1L3,4,6;F2L5-8). Наберите 'man' для справки:",
            fg="#444444",
        ).pack(anchor=tk.W, pady=2)

        input_frame = tk.Frame(extract_frame)
        input_frame.pack(fill=tk.X)

        self.entry_cmd = tk.Entry(input_frame, font=("Courier", 11))
        self.entry_cmd.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.entry_cmd.bind("<Return>", lambda event: self.process_command())

        self.btn_extract = tk.Button(
            input_frame,
            text="Собрать PDF",
            command=self.process_command,
            bg="#c8e6c9",
        )
        self.btn_extract.pack(side=tk.RIGHT, padx=5)

        # Отрисовка страницы руководства
        self.setup_man_page()
    def setup_man_page(self):
        man_text = tk.Text(
            self.man_frame,
            bg="#1e1e1e",
            fg="#ffffff",
            insertbackground="white",
            font=("Courier", 10),
            padx=15,
            pady=15,
        )
        man_text.pack(fill=tk.BOTH, expand=True)

        help_content = """PDF-EXTRACTOR(1)             Руководство пользователя            PDF-EXTRACTOR(1)

НАЗВАНИЕ
    pdf-extractor — продвинутая утилита сборки и нарезки PDF.

СИНТАКСИС КОМАНД
    Базовый блок: FnLm1,m2,m3-m4
    Разделитель файлов: Точка с запятой (;)

КОНСТРУКТОР КОМАНД:
    man
        Показать это руководство.

    FnLm1,m2,m3
        Выбор конкретных страниц через запятую.
        Пример: F1L3,5,8 — берет листы 3, 5 и 8 из файла F1.

    FnLm1-m2
        Выбор диапазона страниц через дефис.
        Пример: F1L2-5 — берет листы со 2 по 5 включительно.

    СЛОЖНЫЕ СВЯЗКИ (Мульти-файл):
        Вы можете комбинировать любые файлы и страницы в одну строку с помощью ';'.
        Все указанные листы соберутся в ОДИН выходной PDF в порядке их перечисления.

        Пример: F1L3,4,6;F2L5
        Действие: Взять листы 3, 4, 6 из первого файла, затем прикрепить к ним 
        лист 5 из второго файла и сохранить как новый общий документ.

        Пример: F1L1-3,5;F2L10;F1L8
        Действие: Склеит страницы 1,2,3,5 из F1, затем страницу 10 из F2, 
        и добавит в конец страницу 8 из F1.

ПРАВИЛА:
    * Номера страниц указываются от 1 (человеческий отсчет).
    * Регистр букв игнорируется (f1l3 и F1L3 эквивалентны).
    * Порядок страниц в итоговом файле в точности повторяет вашу команду.
"""
        man_text.insert(tk.END, help_content)
        man_text.config(state=tk.DISABLED)
    def load_files(self):
        file_paths = filedialog.askopenfilenames(
            title="Выберите PDF файлы", filetypes=[("PDF Files", "*.pdf")]
        )
        if not file_paths:
            return

        for path in file_paths:
            if any(f["path"] == path for f in self.loaded_files.values()):
                continue
            try:
                with open(path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    num_pages = len(reader.pages)

                file_name = os.path.basename(path)
                cmd_alias = f"F{self.file_counter}"

                self.loaded_files[cmd_alias] = {
                    "name": file_name,
                    "path": path,
                    "pages": num_pages,
                }
                self.tree.insert(
                    "", tk.END, values=(cmd_alias, file_name, num_pages)
                )
                self.file_counter += 1
            except Exception as e:
                messagebox.showerror(
                    "Ошибка", f"Не удалось прочитать файл {path}\nИсключение: {e}"
                )

    def clear_list(self):
        self.loaded_files.clear()
        self.file_counter = 1
        for item in self.tree.get_children():
            self.tree.delete(item)
    def process_command(self):
        raw_cmd = self.entry_cmd.get().strip().upper()
        if not raw_cmd:
            return

        if raw_cmd == "MAN":
            self.notebook.select(self.man_frame)
            self.entry_cmd.delete(0, tk.END)
            return

        try:
            sub_commands = [cmd.strip() for cmd in raw_cmd.split(";") if cmd.strip()]
            if not sub_commands:
                raise ValueError("Пустая команда.")

            assembly_plan = []

            for sub_cmd in sub_commands:
                if "L" not in sub_cmd:
                    raise ValueError(f"Ошибочный блок '{sub_cmd}'. Отсутствует маркер листа 'L'.")

                file_part, pages_part = sub_cmd.split("L", 1)

                if file_part not in self.loaded_files:
                    raise ValueError(f"Код файла '{file_part}' не найден в таблице загруженных.")

                file_info = self.loaded_files[file_part]
                total_pages = file_info["pages"]

                page_tokens = [t.strip() for t in pages_part.split(",") if t.strip()]
                if not page_tokens:
                    raise ValueError(f"Не указаны страницы для файла {file_part}.")

                for token in page_tokens:
                    if "-" in token:
                        start_str, end_str = token.split("-", 1)
                        start = int(start_str)
                        end = int(end_str)
                        if start < 1 or end > total_pages or start > end:
                            raise ValueError(
                                f"Неверный диапазон '{token}' для {file_part}. В файле всего {total_pages} стр."
                            )
                        for p in range(start - 1, end):
                            assembly_plan.append((file_info["path"], p))
                    else:
                        page_num = int(token)
                        if page_num < 1 or page_num > total_pages:
                            raise ValueError(
                                f"Страница '{token}' не существует в {file_part}. Всего стр: {total_pages}."
                            )
                        assembly_plan.append((file_info["path"], page_num - 1))

            if not assembly_plan:
                raise ValueError("Не выбрано ни одной страницы для экспорта.")

            save_path = filedialog.asksaveasfilename(
                title="Сохранить собранный PDF как...",
                defaultextension=".pdf",
                filetypes=[("PDF Files", "*.pdf")],
                initialfile="combined_output.pdf",
            )

            if not save_path:
                return

            writer = PyPDF2.PdfWriter()
            opened_readers = {}

            for file_path, page_idx in assembly_plan:
                if file_path not in opened_readers:
                    opened_readers[file_path] = PyPDF2.PdfReader(file_path)
                reader = opened_readers[file_path]
                writer.add_page(reader.pages[page_idx])

            with open(save_path, "wb") as f_out:
                writer.write(f_out)

            messagebox.showinfo("Успех", f"Новый PDF успешно собран ({len(assembly_plan)} стр.)\nПуть: {save_path}")
            self.entry_cmd.delete(0, tk.END)

        except ValueError as ve:
            messagebox.showwarning("Ошибка синтаксиса", str(ve))
        except Exception as e:
            messagebox.showerror("Критическая ошибка", f"Не удалось собрать файл:\n{e}")
if __name__ == "__main__":
    root = tk.Tk()
    app = PDFExtractorApp(root)
    root.mainloop()
