import random
import string


def generate_unique_string(existing_strings, length=8):
    random_string = ''.join(random.sample(string.ascii_letters, length))
    while random_string in existing_strings:
        random_string = ''.join(random.sample(string.ascii_letters, length))
    return random_string

