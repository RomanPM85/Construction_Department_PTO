import psutil
import platform
import time
from tabulate import tabulate


def get_cpu_usage():
    return psutil.cpu_percent(interval=1)


def get_memory_usage():
    memory = psutil.virtual_memory()
    return {
        'Всего': f'{memory.total / (1024 ** 3):.2f} ГБ',
        'Используется': f'{memory.used / (1024 ** 3):.2f} ГБ',
        'Свободно': f'{memory.available / (1024 ** 3):.2f} ГБ',
        'Процент использования': f'{memory.percent}%'
    }


def get_system_info():
    system_info = {
        'Имя компьютера': platform.node(),
        'Версия Windows': platform.version(),
        'Процессор': platform.processor(),
        'Релиз': platform.release(),
        'Физические ядра': psutil.cpu_count(logical=False),
        'Логические ядра': psutil.cpu_count(logical=True)
    }
    return system_info


def get_top_processes(n=10):
    processes = []
    for proc in sorted(psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']),
                       key=lambda x: x.info['cpu_percent'],
                       reverse=True)[:n]:
        try:
            processes.append([
                proc.info['pid'],
                proc.info['name'],
                f"{proc.info['cpu_percent']:.2f}%",
                f"{proc.info['memory_percent']:.2f}%"
            ])
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    return processes


def get_suspicious_processes(threshold_cpu=50.0, threshold_memory=10.0):
    suspicious_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            if proc.info['cpu_percent'] > threshold_cpu or proc.info['memory_percent'] > threshold_memory:
                suspicious_processes.append([
                    proc.info['pid'],
                    proc.info['name'],
                    f"{proc.info['cpu_percent']:.2f}%",
                    f"{proc.info['memory_percent']:.2f}%"
                ])
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    return suspicious_processes


def main():
    print("=== Мониторинг системы ===")

    # Вывод информации о системе
    system_info = get_system_info()
    for key, value in system_info.items():
        print(f"{key}: {value}")

    print(f"\nЗагрузка CPU: {get_cpu_usage()}%")

    print("\nИспользование памяти:")
    for key, value in get_memory_usage().items():
        print(f"{key}: {value}")

    print("\nТоп процессов по использованию CPU:")
    top_processes = get_top_processes()
    print(tabulate(top_processes,
                   headers=['PID', 'Название', 'CPU %', 'Память %'],
                   tablefmt='grid'))

    print("\nПодозрительные процессы (CPU > 50% или Память > 10%):")
    suspicious_processes = get_suspicious_processes()
    if suspicious_processes:
        print(tabulate(suspicious_processes,
                       headers=['PID', 'Название', 'CPU %', 'Память %'],
                       tablefmt='grid'))
    else:
        print("Подозрительных процессов не найдено.")


if __name__ == '__main__':
    main()
