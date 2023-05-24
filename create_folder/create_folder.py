import os
import shutil


def create_folder():
    os.makedirs(os.path.join('01_Договор', 'level_1', 'level_2', 'level_3'))
    os.makedirs(os.path.join('02_Приказы', 'level_1', 'level_2', 'level_3'))
    os.makedirs(os.path.join('03_Письма', 'level_1', 'level_2', 'level_3'))
    os.makedirs(os.path.join('04_Рабочая_документация', 'level_1', 'level_2', 'level_3'))
    os.makedirs(os.path.join('05_Исполнительная_документация', 'level_1', 'level_2', 'level_3'))
    os.makedirs(os.path.join('06_КС6_Накопительная_ведомость', 'level_1', 'level_2', 'level_3'))
    os.makedirs(os.path.join('07_КС2_КС3', 'level_1', 'level_2', 'level_3'))
    os.makedirs(os.path.join('08_Журналы', 'level_1', 'level_2', 'level_3'))
    os.makedirs(os.path.join('09_Техника_Безопасности', 'level_1', 'level_2', 'level_3'))
    os.makedirs(os.path.join('10_Чек_Листы', 'level_1', 'level_2', 'level_3'))
    os.makedirs(os.path.join('11_Накладные', 'level_1', 'level_2', 'level_3'))
    os.makedirs(os.path.join('12_Акты', 'level_1', 'level_2', 'level_3'))
    os.makedirs(os.path.join('13_Замечания', 'level_1', 'level_2', 'level_3'))


def new_create_folder(*args):
    for i in args:
        os.makedirs(os.path.join(i))


def delete_folder():
    try:
        shutil.rmtree(os.path.join('01_folder'))
        shutil.rmtree(os.path.join('02_folder'))
    except FileNotFoundError:
        pass


if __name__ == "__main__":
    dict_dirs = {}
    list_dirs = ['01_Договор', 'level_1', 'level_2', 'level_3']
    start = int(input(f"Введите команду:\n создать=1\n удалить=2\n >>"))
    if start == 1:
        create_folder()
    elif start == 2:
        delete_folder()
    else:
        print(f"Завершение программы")
