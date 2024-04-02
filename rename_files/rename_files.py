import time
import re
from pathlib import Path


def rename_file_methods_one(file):
    """ A function that removes the following characters
    from file names " ", ".", "(", ")" and replace it with "_". """
    current_dir = Path.cwd()
    files = current_dir.glob(file)
    for i in files:
        first_name = i.stem
        replacements = {' ': '_', '.': '_', ')': '_', '(': '_'}
        replaced_chars = [replacements.get(char, char) for char in first_name]
        new_file = ''.join(replaced_chars)
        new_file = del_dup(new_file)
        i.rename(new_file + i.suffix)
    print(f"Successfully!")


def file_search():
    find_obj = input(f" Which files should I rename ? \n")
    return str(find_obj)


def rename_file_methods_two(file):
    current_dir = Path.cwd()
    files = current_dir.glob(file)


def del_dup(line):
    stack = []
    for char in line:
        stack.pop() if stack and char == stack[-1] else stack.append(char)
    return ''.join(stack)


if __name__ == "__main__":
    program_start_time = time.time()
    this_programme = ""
    welcome = (f"Hi, my name is Roman, this_programme: {this_programme} \n"
               f"(The GNU General Public License v3.0) Mamchiy Roman https://github.com/RomanPM85")
    print(welcome)
    start_script = input(f"Enter the program command number=>.\n"
                         f"Run the program using method one, press 1 \n"
                         f"==>"
                         )

    if start_script == '1':
        rename_file_methods_one(file_search())
    elif start_script == '2':
        pass

    else:
        print(f"the code is not entered")
print("--- %s seconds ---" % (time.time() - program_start_time))
