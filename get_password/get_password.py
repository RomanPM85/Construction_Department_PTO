import random
import string

def generate_password(total_length: int, num_upper: int, num_digits: int, num_special: int) -> str:
    if num_upper + num_digits + num_special > total_length:
        raise ValueError("Сумма всех заданных количеств символов превышает общую длину пароля")

    num_lower = total_length - (num_upper + num_digits + num_special)

    digits = random.choices(string.digits, k=num_digits)
    uppercase = random.choices(string.ascii_uppercase, k=num_upper)
    special_chars = random.choices("!@#$%^&*()-_=+[]{}", k=num_special)
    lowercase = random.choices(string.ascii_lowercase, k=num_lower)

    password_chars = digits + uppercase + special_chars + lowercase
    random.shuffle(password_chars)

    return ''.join(password_chars)

# Пример вызова:
print(generate_password(total_length=16, num_upper=4, num_digits=4, num_special=4))
