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


def create_files(filenames, text_body):
    with open(filenames, 'a', encoding='utf-8') as f:
        f.write(text_body)


if __name__ == "__main__":
    """ 
    Запуск команд для создание начальной структуры папок и файлов для реестра.
    """
    mainFolder = os.getcwd()
    dict_dirs = {}
    foldersStructure = [
        ("01_Договор", "ДопСоглашение"),
        ("02_Приказы", "Заказчик"),
        ("03_ТехникаБезопасности",),
        ("04_Журналы",),
        ("05_Сотрудники",),
        ("06_Письма",),
        ("07_Накладные",),
        ("08_РабочаяДокументация",),
        ("09_ИсполнительнаяДокументация",),
        ("10_КС6_НакопительнаяВедомость",),
        ("11_КС2_КС3",),
        ("12_ЧекЛисты",),
        ("13_Акты",),
    ]
    body_text = "Hello world!"
    start = int(input(f"Введите команду:\n "
                      f"Создать структуру папок=1\n "
                      f"Удалить все папки=2\n "
                      f"Распечатать список папок и файлов=3\n"
                      f"Создать реестры=4\n"
                      f">>"))
    if start == 1:
        for i in foldersStructure:
            create_folder(i)

    elif start == 2:
        delete_folder()

    elif start == 3:
        folders_tree()

    elif start == 4:
        list_folders = os.listdir(path='.')
        for folder in list_folders:
            if os.path.isdir(folder):
                os.chdir(folder)
                create_files('!Reestr'+folder[2:]+'.xlsx', body_text)
                os.chdir(mainFolder)
            else:
                pass
    else:
        print(f"Завершение программы")


