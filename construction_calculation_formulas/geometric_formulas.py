import math


def cylinder_volume(radius, height):
    """Вычисляет объем цилиндра с обработкой ошибок.
    Args:
        radius: Радиус основания цилиндра.
        height: Высота цилиндра.
    Returns:
        Объем цилиндра или сообщение об ошибке.
    """

    if radius <= 0 or height <= 0:
        return "Ошибка: Радиус и высота должны быть положительными числами."
    return math.pi * radius**2 * height


def trapezoid_area(a, b, h):
    """Вычисляет площадь трапеции с проверкой на корректность ввода.
    Args:
        a: Длина первого основания.
        b: Длина второго основания.
        h: Высота трапеции.
    Returns:
    Площадь трапеции или сообщение об ошибке.
    """
    if a <= 0 or b <= 0 or h <= 0:
        return "Ошибка: Длины оснований и высота должны быть положительными числами."
    return (a + b) * h / 2


# Пример использования
if __name__ == "__main__":

    input_radius = 5
    input_height = 10
    volume = cylinder_volume(input_radius, input_height)
    print(f"Объем цилиндра с радиусом {input_radius} и высотой {input_height}: {volume:.2f}")

    a = 5
    b = 10
    h = 4
    area = trapezoid_area(a, b, h)
    print(f"Площадь трапеции: {area}")
