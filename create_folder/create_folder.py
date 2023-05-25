import os
import shutil


def create_folder(*args):
    for item in args:
        os.makedirs(os.path.join(*item))


def delete_folder():
    path = '.'
    dirs = os.listdir(path)
    for item in dirs:
        if os.path.isdir(str(item)):
            shutil.rmtree(os.path.join(item))


def folders_tree():
    for dirPath, dirNames, filenames in os.walk("."):
        # перебрать каталоги
        for dirName in dirNames:
            print("Каталог:", os.path.join(dirPath, dirName))
        # перебрать файлы
        for fileName in filenames:
            print("Файл:", os.path.join(dirPath, fileName))


if __name__ == "__main__":
    """ 
    Тестовые переменные
    """
    dict_dirs = {}
    foldersStructure = [
        ('01_Договор', '02_ДопСоглашение', '03_НаСогласовании', '04_Исходники'),
        ('02_Приказы', 'level_1', 'level_2', 'level_3'),
        ('03_Письма', 'level_1', 'level_2', 'level_3'),
        ('04_Рабочая_документация', 'level_1', 'level_2', 'level_3'),
        ('05_Исполнительная_документация', 'level_1', 'level_2', 'level_3'),
        ('06_КС6_Накопительная_ведомость', 'level_1', 'level_2', 'level_3'),
        ('07_КС2_КС3', 'level_1', 'level_2', 'level_3'),
        ('08_Журналы', 'level_1', 'level_2', 'level_3'),
        ('09_Техника_Безопасности', 'level_1', 'level_2', 'level_3'),
        ('10_Чек_Листы', 'level_1', 'level_2', 'level_3'),
        ('11_Накладные', 'level_1', 'level_2', 'level_3'),
        ('12_Акты', 'level_1', 'level_2', 'level_3'),
    ]
    start = int(input(f"Введите команду:\n "
                      f"создать=1\n "
                      f"удалить=2\n "
                      f"список папок и файлов=3\n"
                      f" >>"))
    if start == 1:
        for i in foldersStructure:
            create_folder(i)
    elif start == 2:
        delete_folder()
    elif start == 3:
        folders_tree()
    else:
        print(f"Завершение программы")


