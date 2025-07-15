import os
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import re


class DocumentTransferActGenerator:
    def __init__(self, template_path='templates/act_template.html'):
        """
        Инициализация генератора актов

        :param template_path: Путь к HTML-шаблону
        """
        self.template_path = Path(template_path)
        self.output_dir = self.template_path.parent / 'generated_acts'

        # Создаем директорию для выходных файлов
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Настройка Jinja2 для работы с HTML
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.template_path.parent),
            autoescape=True
        )

    def generate_act(self, project_details):
        """
        Генерация акта приема-передачи документации

        :param project_details: Словарь с деталями проекта
        :return: Путь к сгенерированному HTML-файлу
        """
        try:
            # Загружаем шаблон
            template = self.jinja_env.get_template(self.template_path.name)

            # Подготавливаем контекст для шаблона
            context = {
                # Общие данные
                'current_date': datetime.now(),
                'city': project_details.get('city', ''),

                # Стороны передачи
                'customer': {
                    'name': project_details.get('customer_name', ''),
                    'representative': {
                        'position': project_details.get('customer_position', ''),
                        'full_name': project_details.get('customer_full_name', '')
                    }
                },
                'contractor': {
                    'name': project_details.get('contractor_name', ''),
                    'representative': {
                        'position': project_details.get('contractor_position', ''),
                        'full_name': project_details.get('contractor_full_name', '')
                    }
                },

                # Детали проекта
                'project': {
                    'name': project_details.get('project_name', ''),
                    'organization': project_details.get('project_organization', ''),
                    'number': project_details.get('project_number', '')
                },

                # Документация
                'documents': project_details.get('documents', [
                    {'code': '', 'name': '', 'copies': '', 'notes': ''}
                ])
            }

            # Рендерим шаблон
            rendered_html = template.render(context)

            # Формируем имя файла
            filename = f"Act_{context['project']['number'] or 'Unknown'}_{datetime.now().strftime('%Y%m%d')}.html"
            output_path = self.output_dir / filename

            # Сохраняем документ
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(rendered_html)

            print(f"Акт сгенерирован: {output_path}")
            return output_path

        except Exception as e:
            print(f"Ошибка генерации акта: {e}")
            return None

    def extract_placeholders(self):
        """
        Извлечение потенциальных плейсхолдеров из шаблона

        :return: Список найденных плейсхолдеров
        """
        placeholders = []

        try:
            with open(self.template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()

            # Поиск плейсхолдеров в стиле Jinja2
            placeholders = re.findall(r'\{\{\s*([^{}]+)\s*\}\}', template_content)

        except Exception as e:
            print(f"Ошибка извлечения плейсхолдеров: {e}")

        return list(set(placeholders))

    def modify_template(self, modifications):
        """
        Модификация HTML-шаблона

        :param modifications: Словарь изменений
        """
        try:
            with open(self.template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()

            # Применяем изменения (простой пример)
            for key, value in modifications.items():
                template_content = template_content.replace(f'{{{{ {key} }}}}', value)

            # Сохраняем модифицированный шаблон
            modified_template_path = self.template_path.parent / f"{self.template_path.stem}_modified{self.template_path.suffix}"

            with open(modified_template_path, 'w', encoding='utf-8') as f:
                f.write(template_content)

            print(f"Шаблон модифицирован: {modified_template_path}")
            return modified_template_path

        except Exception as e:
            print(f"Ошибка модификации шаблона: {e}")
            return None


def main():
    # Путь к HTML-шаблону
    template_path = 'templates/act_template.html'

    # Создание генератора актов
    generator = DocumentTransferActGenerator(template_path)

    # Пример данных для генерации акта
    project_details = {
        'city': 'Москва',
        'customer_name': 'ООО "СтройИнвест"',
        'customer_position': 'Директор по развитию',
        'customer_full_name': 'Иванов Иван Иванович',

        'contractor_name': 'АО "МонтажСтрой"',
        'contractor_position': 'Главный инженер',
        'contractor_full_name': 'Петров Петр Петрович',

        'project_name': 'Реконструкция торгового центра',
        'project_organization': 'ПСК "Архитектура"',
        'project_number': 'АФП-2024-06-23',

        'documents': [
            {
                'code': 'АР-1',
                'name': 'Архитектурные решения',
                'copies': '3',
                'notes': 'Основной комплект'
            },
            {
                'code': 'КЖ-1',
                'name': 'Конструкции железобетонные',
                'copies': '2',
                'notes': 'Рабочий комплект'
            }
        ]
    }

    # Извлечение плейсхолдеров
    placeholders = generator.extract_placeholders()
    print("Найденные плейсхолдеры:", placeholders)

    # Генерация акта
    generated_act_path = generator.generate_act(project_details)

    # Демонстрация модификации шаблона
    modifications = {
        'project.name': 'Новое название проекта',
        'customer.name': 'ООО "Новый Заказчик"'
    }
    generator.modify_template(modifications)


if __name__ == "__main__":
    main()
