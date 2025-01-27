import requests
from bs4 import BeautifulSoup
import os


def download_file_from_google_drive_url(url, path_save):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Проверка на ошибки HTTP

        soup = BeautifulSoup(response.text, 'html.parser')
        download_link_element = soup.find('a', id='uc-download-link')
        if not download_link_element:
            print("Ссылка на скачивание не найдена")
            return False

        download_link = download_link_element['href']
        response_download = requests.get(download_link, stream=True)
        response_download.raise_for_status()  # Проверка на ошибки HTTP

        content_disposition = response_download.headers.get('content-disposition')
        if content_disposition:
            file_name = content_disposition.split('filename=')[1].strip('"')
        else:
            file_name = url.split("/")[-2] + '.file'

        file_path = os.path.join(path_save, file_name)

        with open(file_path, 'wb') as f:
            for chunk in response_download.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Файл скачан в {file_path}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Ошибка: {e}")
        return False
    except Exception as e:
        print(f"Ошибка: {e}")
        return False


# Пример использования
google_drive_url = "your_google_drive_url"  # Замените на вашу ссылку на файл
save_path = "./downloaded_files"  # Папка для сохранения файлов
if download_file_from_google_drive_url(google_drive_url, save_path):
    print("Файл скачан")
else:
    print("Не удалось скачать файл")
