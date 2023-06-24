from sys import stdout
from time import sleep


def slow_print(text, letter_time):
    for letter in text + '\n':
        stdout.write(letter)
        stdout.flush()
        sleep(letter_time)
