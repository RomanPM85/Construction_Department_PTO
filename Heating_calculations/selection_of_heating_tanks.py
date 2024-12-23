

def calculate_d(pmax, p0):
    """
    Вычисляет значение D по формуле D = (Pmax - P0) / (Pmax + 1)

    Args:
        pmax: Значение Pmax.
        p0: Значение P0.

    Returns:
        Значение D.
    """
    if not isinstance(pmax, (int, float)) or not isinstance(p0, (int, float)):
        raise TypeError("Pmax и P0 должны быть числами (int или float).")

    if pmax < -1:  # Проверка, чтобы избежать деления на ноль.
        raise ValueError("Pmax не может быть меньше -1. Это приведет к делению на ноль или отрицательному знаменателю.")

    try:
        d = (pmax - p0) / (pmax + 1)
    except ZeroDivisionError:
        raise ZeroDivisionError("Pmax не может быть равен -1.")  # Если все же равно -1, выдаем ZeroDivisionError
    return d


def test():
    #  Примеры использования
    try:
        p_max = 10.5
        p_0 = 2.3
        d_value = calculate_d(p_max, p_0)
        print(f"D = {d_value}")  # Вывод: D = 0.7454545454545455

        p_max = 5
        p_0 = 0
        d_value = calculate_d(p_max, p_0)
        print(f"D = {d_value}")  # Вывод: D = 0.8333333333333334

        p_max = -1
        p_0 = 0
        d_value = calculate_d(p_max, p_0)
    except (TypeError, ValueError, ZeroDivisionError) as e:
        print(f"Ошибка: {e}")


if __name__ == "__main__":
    test()


