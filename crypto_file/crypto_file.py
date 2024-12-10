import time
from cryptography.fernet import Fernet


def write_key(name_key):
    """ Создаем ключ и сохраняем его в файл """
    key_obj = Fernet.generate_key()
    with open(name_key, 'wb') as key_file:
        key_file.write(key_obj)


def load_key(name_key):
    """ Загружаем ключ 'crypto.key' из текущего каталога """
    return open(name_key, 'rb').read()


def encrypt(filename, key):
    # Зашифруем файл и записываем его
    f = Fernet(key)
    with open(filename, 'rb') as file:
        # прочитать все данные файла
        file_data = file.read()
        # Зашифровать данные
    encrypted_data = f.encrypt(file_data)
    # записать зашифрованный файл
    with open(filename, 'wb') as file:
        file.write(encrypted_data)


def decrypt(filename, key):
    # Расшифруем файл и записываем его
    f = Fernet(key)
    with open(filename, 'rb') as file:
        # читать зашифрованные данные
        encrypted_data = file.read()
    # расшифровать данные
    decrypted_data = f.decrypt(encrypted_data)
    # записать оригинальный файл
    with open(filename, 'wb') as file:
        file.write(decrypted_data)


if __name__ == "__main__":
    start_time = time.time()
    name_key = 'crypto.key'
    file = 't.txt'

    create_key = input(f"Если 1, если нужно создать ключ \n")

    if create_key == '1':
        write_key(name_key)
        print('create key')

    else:
        pass

    start_script = input(f"Введите номер команды программы=>.\n"
                         f"Если 1, если нужно зашифровать файл\n"
                         f"Если 2, если нужно расшифровать файл \n"
                         f"==>"
                         )
    key = load_key(name_key)
    if start_script == '1':
        encrypt(file, key)
    elif start_script == '2':
        decrypt(file, key)
    else:
        pass
    print("--- %s seconds ---" % (time.time() - start_time))
