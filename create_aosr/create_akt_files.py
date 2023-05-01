import csv
import os
import time
from pathlib import Path
from docxtpl import DocxTemplate

start_time = time.time()


class Akt:
    """
    Класс для создания и удаления актов АОСР по шаблону, используя
    две базы данные в формате csv, данные переменные для акта и данные переменные для сертификатов и паспортов.
    """
    def __init__(self, base_doc, files_csv, certificate_csv, prefix_name_doc='Akt№'):
        self.base_doc=base_doc
        self.files_csv=files_csv
        self.certificate_csv=certificate_csv
        self.prefix_name_doc=prefix_name_doc

    def create_akt(self):
        """ Метод для создания актов по шаблону с данными из БД. """
        doc = DocxTemplate(self.base_doc)
        certificate_list = 'certificate_list'  # ключ к списку сертификатов.
        materials_list = 'materials_list'  # ключ к списку сертификатов.
        with open(self.files_csv, 'r', encoding='utf-8-sig', newline='') as csv_f:
            list_bd = csv.DictReader(csv_f, delimiter=';')
            count = 1
            for row_f in list_bd:
                with open(self.certificate_csv, 'r', encoding='utf-8-sig', newline='') as csv_s:
                    list_certificate = csv.DictReader(csv_s, delimiter=';')

                    # ключи (столбцы) для добавления в список сертификатов в АОСР.
                    certificate_data = ('full_certificate_name',)
                    materials_data = ('full_materials_name',)

                    # создание списков.
                    certificate = []  # список сертификатов для акта.
                    materials = []  # список материалов и сертификатов для акта.

                    for row_s in list_certificate:
                        if row_s[str(count)] == '1':
                            for item in certificate_data:
                                certificate.append(row_s[item])
                            for item in materials_data:
                                materials.append(row_s[item])

                row_f[certificate_list] = certificate
                row_f[materials_list] = materials

                doc.render(row_f)
                extension = '.docx'
                name_doc = str(self.prefix_name_doc) + str(count) + str(extension)
                count = count + 1
                doc.save(name_doc)

    def delete_akt(self):
        """ Метод для удаления созданных актов. """
        path = Path.cwd()
        test = os.listdir(path)
        for item in test:
            if item.startswith(self.prefix_name_doc):
                os.remove(os.path.join(path, item))


if "__main__" == __name__:
    start_script = input(f"Start programme:\n create doc input: 1\n delete doc input: 2\n>>>")
    akt_aosr = Akt('base_aosr.docx', 'value_aosr.csv', 'value_bd.csv', prefix_name_doc='AOSR-№',)

    if start_script == '1':
        akt_aosr.create_akt()
    elif start_script == '2':
        akt_aosr.delete_akt()
    else:
        print(f"не верно введен код")
    print("--- %s seconds ---" % (time.time() - start_time))
