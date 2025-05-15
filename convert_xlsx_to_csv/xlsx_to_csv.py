import pandas as pd


def converts_xlsx_to_csv(file_xlsx, file_csv):
    df = pd.read_excel(file_xlsx)
    df.to_csv(file_csv, index=False)
    print(f"Файл {file_xlsx} успешно преобразован в {file_csv}.")


if __name__ == "__main__":
    input_file = 'contacts_tcsm_.xlsx'
    output_file = 'contacts_tcsm.csv'
    converts_xlsx_to_csv(input_file, output_file)
