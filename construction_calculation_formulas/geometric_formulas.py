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


# Пример использования
if __name__ == "__main__":

    input_radius = 5
    input_height = 10
    volume = cylinder_volume(input_radius, input_height)
    print(f"Объем цилиндра с радиусом {input_radius} и высотой {input_height}: {volume:.2f}")
