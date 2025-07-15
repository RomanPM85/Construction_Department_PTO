import os
import config
import pandas as pd
from datetime import datetime  # <-- оставляем только этот импорт
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import io
import pytz
import sqlite3


def adapt_date(date_obj):
    return date_obj.isoformat()

def convert_date(bytestring):
    return datetime.date.fromisoformat(bytestring.decode())

sqlite3.register_adapter(datetime.date, adapt_date)
sqlite3.register_converter("DATE", convert_date)



class DatabaseManager:
    def __init__(self, db_path="employees_database.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT,
                object TEXT,
                full_name TEXT NOT NULL,
                birth_date DATE,
                position TEXT,
                phone_number TEXT,
                email TEXT,
                passport_series TEXT,
                passport_number TEXT,
                passport_date DATE,
                passport_issued_by TEXT,
                car_brand TEXT,
                car_plate_number TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def add_employees_from_excel(self, excel_data):
        def safe_str(value):
            if value is None or (isinstance(value, float) and pd.isna(value)):
                return ''
            return str(value).strip()

        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = conn.cursor()
        for _, row in excel_data.iterrows():
            full_name = safe_str(row.get('Фамилия И.О', ''))
            birth_date = pd.to_datetime(row.get('Дата рождения', None), errors='coerce').date() if pd.notna(
                row.get('Дата рождения', None)) else None
            passport_series = safe_str(row.get('ПАСПОРТ Серия', ''))
            passport_number = safe_str(row.get('ПАСПОРТ Номер', ''))
            obj = safe_str(row.get('Объект', ''))

            # Проверяем, существует ли уже такая запись с учётом объекта
            cursor.execute('''
                SELECT 1 FROM employees
                WHERE full_name = ?
                  AND (birth_date = ? OR (birth_date IS NULL AND ? IS NULL))
                  AND passport_series = ?
                  AND passport_number = ?
                  AND object = ?
                LIMIT 1
            ''', (full_name, birth_date, birth_date, passport_series, passport_number, obj))

            exists = cursor.fetchone()
            if exists:
                # Запись уже есть — пропускаем
                continue

            # Если нет — вставляем новую запись
            cursor.execute('''
                INSERT INTO employees (
                    company, object, full_name, birth_date, position, phone_number,
                    email, passport_series, passport_number, passport_date,
                    passport_issued_by, car_brand, car_plate_number
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                safe_str(row.get('Компания', '')),
                obj,
                full_name,
                birth_date,
                safe_str(row.get('Должность', '')),
                safe_str(row.get('№ телефона', '')),
                safe_str(row.get('Электронная почта', '')),
                passport_series,
                passport_number,
                pd.to_datetime(row.get('ПАСПОРТ Дата', None), errors='coerce').date() if pd.notna(
                    row.get('ПАСПОРТ Дата', None)) else None,
                safe_str(row.get('ПАСПОРТ Кем выдан', '')),
                safe_str(row.get('Авто Марка', '')),
                safe_str(row.get('Авто Гос. Номер', ''))
            ))
        conn.commit()
        conn.close()

    def get_employees_by_company(self, company_name):
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        df = pd.read_sql_query('''
            SELECT company as "Компания",
                   object as "Объект",
                   full_name as "Фамилия И.О",
                   birth_date as "Дата рождения",
                   position as "Должность",
                   phone_number as "№ телефона",
                   email as "Электронная почта",
                   passport_series as "ПАСПОРТ Серия",
                   passport_number as "ПАСПОРТ Номер",
                   passport_date as "ПАСПОРТ Дата",
                   passport_issued_by as "ПАСПОРТ Кем выдан",
                   car_brand as "Авто Марка",
                   car_plate_number as "Авто Гос. Номер"
            FROM employees
            WHERE company = ?
            ORDER BY full_name
        ''', conn, params=(company_name,))
        conn.close()
        return df

    def get_all_companies(self):
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT company FROM employees ORDER BY company')
        companies = [row[0] for row in cursor.fetchall()]
        conn.close()
        return companies

    def get_all_objects(self):
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT DISTINCT object FROM employees WHERE object IS NOT NULL AND object != "" ORDER BY object')
        objects = [row[0] for row in cursor.fetchall()]
        conn.close()
        return objects

    def get_all_employees(self):
        """Получение полного списка всех сотрудников"""
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        df = pd.read_sql_query('''
            SELECT company as "Компания",
                   object as "Объект",
                   full_name as "Фамилия И.О",
                   birth_date as "Дата рождения",
                   position as "Должность",
                   phone_number as "№ телефона",
                   email as "Электронная почта",
                   passport_series as "ПАСПОРТ Серия",
                   passport_number as "ПАСПОРТ Номер",
                   passport_date as "ПАСПОРТ Дата",
                   passport_issued_by as "ПАСПОРТ Кем выдан",
                   car_brand as "Авто Марка",
                   car_plate_number as "Авто Гос. Номер"
            FROM employees
            ORDER BY full_name
        ''', conn)
        conn.close()
        return df


class ExcelManager:
    @staticmethod
    def create_blank_template():
        df = pd.DataFrame(columns=[
            'Компания', 'Объект', 'Фамилия И.О', 'Дата рождения', 'Должность', '№ телефона',
            'Электронная почта', 'ПАСПОРТ Серия', 'ПАСПОРТ Номер', 'ПАСПОРТ Дата',
            'ПАСПОРТ Кем выдан', 'Авто Марка', 'Авто Гос. Номер'
        ])
        for i in range(5):
            df.loc[i] = [''] * len(df.columns)
        return df

    @staticmethod
    def dataframe_to_excel_bytes(df):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Список')
        output.seek(0)
        return output.getvalue()


class EmailSender:
    def __init__(self, smtp_server, smtp_port, email_user, email_password):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email_user = email_user
        self.email_password = email_password

    def send_excel_file(self, recipient_email, excel_data, filename):
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_user
            msg['To'] = recipient_email
            msg['Subject'] = f"Список сотрудников - {filename}"

            part = MIMEBase('application', 'octet-stream')
            part.set_payload(excel_data)
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )
            msg.attach(part)

            server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            server.login(self.email_user, self.email_password)
            server.sendmail(self.email_user, recipient_email, msg.as_string())
            server.quit()
            return True
        except Exception as e:
            print(f"Ошибка отправки email: {e}")
            return False


class TelegramBot:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.email_sender = EmailSender(config.SMTP_SERVER, config.SMTP_PORT, config.EMAIL_USER, config.EMAIL_PASSWORD)

    def user_is_allowed(self, update: Update):
        user_id = update.effective_user.id
        return user_id in config.ALLOWED_USERS

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.user_is_allowed(update):
            await update.message.reply_text("❌ У вас нет доступа к этому боту.")
            return
        help_text = """
🤖 Бот для управления списками сотрудников

Доступные команды:
/blank - Получить пустой бланк для заполнения
/list <компания> - Получить список по компании
/companies - Показать все доступные компании
/all - Показать общий список людей
/send_email <email> <компания> - Отправить список на email
/help - Показать эту справку

Также вы можете:
• Отправить заполненный Excel файл для добавления в базу
        """
        await update.message.reply_text(help_text)

    async def get_blank(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.user_is_allowed(update):
            await update.message.reply_text("❌ У вас нет доступа к этому боту.")
            return
        try:
            df = ExcelManager.create_blank_template()
            excel_bytes = ExcelManager.dataframe_to_excel_bytes(df)
            filename = f"blank_template_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"  # <-- здесь используется datetime.now()
            await update.message.reply_document(
                document=io.BytesIO(excel_bytes),
                filename=filename,
                caption="📋 Пустой бланк для заполнения"
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка создания бланка: {e}")

    async def get_list_by_company(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.user_is_allowed(update):
            await update.message.reply_text("❌ У вас нет доступа к этому боту.")
            return
        if not context.args:
            await update.message.reply_text("❌ Укажите название компании. Пример: /list Компания1")
            return
        company_name = ' '.join(context.args)
        try:
            df = self.db_manager.get_employees_by_company(company_name)
            if df.empty:
                await update.message.reply_text(f"❌ Список для компании '{company_name}' пуст")
                return
            excel_bytes = ExcelManager.dataframe_to_excel_bytes(df)
            filename = f"list_{company_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            await update.message.reply_document(
                document=io.BytesIO(excel_bytes),
                filename=filename,
                caption=f"📊 Список сотрудников для компании: {company_name}"
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка получения списка: {e}")

    async def get_companies(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.user_is_allowed(update):
            await update.message.reply_text("❌ У вас нет доступа к этому боту.")
            return
        try:
            companies = self.db_manager.get_all_companies()
            if not companies:
                await update.message.reply_text("❌ В базе данных нет компаний")
                return
            companies_text = "📍 Доступные компании:\n\n" + "\n".join([f"• {comp}" for comp in companies])
            await update.message.reply_text(companies_text)
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка получения компаний: {e}")

    async def send_to_email(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.user_is_allowed(update):
            await update.message.reply_text("❌ У вас нет доступа к этому боту.")
            return
        if len(context.args) < 2:
            await update.message.reply_text("❌ Укажите email и компанию. Пример: /send_email user@example.com Компания1")
            return
        email = context.args[0]
        company_name = ' '.join(context.args[1:])
        try:
            df = self.db_manager.get_employees_by_company(company_name)
            if df.empty:
                await update.message.reply_text(f"❌ Список для компании '{company_name}' пуст")
                return
            excel_bytes = ExcelManager.dataframe_to_excel_bytes(df)
            filename = f"list_{company_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            if self.email_sender.send_excel_file(email, excel_bytes, filename):
                await update.message.reply_text(f"✅ Список отправлен на {email}")
            else:
                await update.message.reply_text("❌ Ошибка отправки email")
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка отправки: {e}")

    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.user_is_allowed(update):
            await update.message.reply_text("❌ У вас нет доступа к этому боту.")
            return
        document = update.message.document
        if not document.file_name.endswith(('.xlsx', '.xls')):
            await update.message.reply_text("❌ Пожалуйста, отправьте Excel файл (.xlsx или .xls)")
            return
        try:
            file = await context.bot.get_file(document.file_id)
            file_bytes = await file.download_as_bytearray()
            df = pd.read_excel(io.BytesIO(file_bytes))
            required_columns = ['Компания', 'Фамилия И.О', 'Дата рождения']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                await update.message.reply_text(f"❌ Отсутствуют обязательные колонки: {', '.join(missing_columns)}")
                return
            self.db_manager.add_employees_from_excel(df)
            await update.message.reply_text(f"✅ Добавлено {len(df)} записей в базу данных")
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка обработки файла: {e}")

    async def send_to_telegram(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.user_is_allowed(update):
            await update.message.reply_text("❌ У вас нет доступа к этому боту.")
            return
        if len(context.args) < 2:
            await update.message.reply_text("❌ Укажите @username и компанию. Пример: /send_tg @username Компания1")
            return
        username = context.args[0]
        company_name = ' '.join(context.args[1:])
        try:
            df = self.db_manager.get_employees_by_company(company_name)
            if df.empty:
                await update.message.reply_text(f"❌ Список для компании '{company_name}' пуст")
                return
            excel_bytes = ExcelManager.dataframe_to_excel_bytes(df)
            filename = f"list_{company_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            await context.bot.send_document(
                chat_id=username,
                document=io.BytesIO(excel_bytes),
                filename=filename,
                caption=f"📊 Список сотрудников для компании: {company_name}"
            )
            await update.message.reply_text(f"✅ Файл отправлен пользователю {username}")
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка отправки: {e}")

    async def get_objects(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.user_is_allowed(update):
            await update.message.reply_text("❌ У вас нет доступа к этому боту.")
            return
        try:
            objects = self.db_manager.get_all_objects()
            if not objects:
                await update.message.reply_text("❌ В базе данных нет объектов")
                return
            objects_text = "📍 Доступные объекты:\n\n" + "\n".join([f"• {obj}" for obj in objects])
            await update.message.reply_text(objects_text)
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка получения объектов: {e}")

    async def get_all(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.user_is_allowed(update):
            await update.message.reply_text("❌ У вас нет доступа к этому боту.")
            return
        try:
            df = self.db_manager.get_all_employees()
            if df.empty:
                await update.message.reply_text("❌ В базе данных нет записей")
                return
            excel_bytes = ExcelManager.dataframe_to_excel_bytes(df)
            filename = f"all_employees_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            await update.message.reply_document(
                document=io.BytesIO(excel_bytes),
                filename=filename,
                caption="📋 Общий список всех сотрудников"
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка получения списка: {e}")


def main():
    bot = TelegramBot()
    timezone = pytz.timezone("Europe/Moscow")

    application = Application.builder().token(config.BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("help", bot.start))
    application.add_handler(CommandHandler("blank", bot.get_blank))
    application.add_handler(CommandHandler("list", bot.get_list_by_company))
    application.add_handler(CommandHandler("companies", bot.get_companies))
    application.add_handler(CommandHandler("send_email", bot.send_to_email))
    application.add_handler(CommandHandler("send_tg", bot.send_to_telegram))
    application.add_handler(CommandHandler("objects", bot.get_objects))
    application.add_handler(CommandHandler("all", bot.get_all))

    application.add_handler(MessageHandler(filters.Document.ALL, bot.handle_document))


    print("🤖 Бот запущен...")
    application.run_polling()


if __name__ == "__main__":
    main()
