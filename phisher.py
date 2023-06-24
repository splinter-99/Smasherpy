from signal import SIGINT

import requests
import multiprocessing
from pathlib import Path
from time import (
    ctime,
    sleep,
    time
)
from smtplib import SMTP_SSL
from sys import (
    argv,
    stdout,
    version_info
)
from subprocess import (
    DEVNULL,
    PIPE,
    Popen,
    STDOUT,
    call,
    run
)
from os import popen, kill
import click
import json
from typing import List

# Color snippets
black = "\033[0;30m"
red = "\033[0;31m"
bred = "\033[1;31m"
green = "\033[0;32m"
bgreen = "\033[1;32m"
yellow = "\033[0;33m"
byellow = "\033[1;33m"
blue = "\033[0;34m"
bblue = "\033[1;34m"
purple = "\033[0;35m"
bpurple = "\033[1;35m"
cyan = "\033[0;36m"
bcyan = "\033[1;36m"
white = "\033[0;37m"
nc = "\033[00m"

ask = f"{green}[{white}?{green}] {byellow}"
success = f"{yellow}[{white}√{yellow}] {green}"
error = f"{blue}[{white}√{yellow}] {green}"
info  =   f"{yellow}[{white}+{yellow}] {cyan}"
info2  =   f"{green}[{white}•{green}] {purple}"

packages = [ "php", "ssh" ]
modules = [ "requests", "bs4", "rich" ]
tunnelers = [ "cloudflared", "loclx" ]
processes = [ "php", "ssh", "cloudflared", "loclx", "localxpose" ]


home_dir = popen("echo $HOME").read()
stdout_speed = 0

error_log = None

@click.command()
@click.option("--mode", "-m", "mode", prompt="Enter the mode", help="Choose phishing attack vector",
              type=click.Choice(['SMS', 'EMAIL'], case_sensitive=False), required=True)
@click.option("--speed","-s", "speed", prompt="Enter the speed of output 1-5", type=click.INT, default=0, help="output speed 1-5, default is 0")
def main_menu(mode, speed) :
    global stdout_speed
    stdout_speed = speed * 15
    if mode.lower() == "email":
        email_menu()
    elif mode.lower() == "sms":
        sms_menu()
    ping = silent_shell('ping google.com -c 4 | grep "64 bytes" | cut -f 4,5 -d " "')
    ping.wait()
    output, error = ping.communicate()
    print(output.decode())


def email_menu():
    sprint(f'{success}Email! This is path to your home directory: {home_dir}')

def sms_menu():
    sprint(f'{success}Sms! This is path to your home directory: {home_dir}')


def server():
    while True:
        pass


# Helper functions

def shell(command, capture_output=False):
    try:
        return run(command, shell=True, captur_output=capture_output)
    except Exception as e:
        append(e, error_log)


# Run task in background supressing output by setting stdout and stderr to devnull
def silent_shell(command, stdout=PIPE, stderr=DEVNULL, cwd="./"):
    try:
        return Popen(command, shell=True, stdout=stdout, stderr=stderr, cwd=cwd)
    except Exception as e:
        append(e, error_log)


def append(file_name, text):
    with open(file_name, "a") as file:
        file.write(str(text) + "\n")


def sprint(text):
    global stdout_speed
    for letter in text + '\n':
        stdout.write(letter)
        stdout.flush()
        if stdout_speed == 0:
            continue
        sleep(1/stdout_speed)


#Install packages
def installer(package, package_name=None):
    if package_name is None:
        package_name = package
    for pacman in ["pkg", "apt", "apt-get", "apk", "yum", "dnf", "brew", "pacman", "yay"]:
        # Check if package manager is present but php isn't present
        if is_installed(pacman):
            if not is_installed(package):
                sprint(f"\n{info}Installing {package}{nc}")
                if pacman == "pacman":
                    shell(f"sudo {pacman} -S {package_name} --noconfirm")
                elif pacman == "apk":
                    if is_installed("sudo"):
                        shell(f"sudo {pacman} add {package_name}")
                    else:
                        shell(f"{pacman} add -y {package_name}")
                elif is_installed("sudo"):
                    shell(f"sudo {pacman} install -y {package_name}")
                else:
                    shell(f"{pacman} install -y {package_name}")
                break
    if is_installed("brew"):
        if not is_installed("cloudflare"):
            shell("brew install cloudflare/cloudflare/cloudflared")
        if not is_installed("localxpose"):
            shell("brew install localxpose")


def requirements():
    if is_installed("apt") and not is_installed("pkg"):
        installer("ssh", "openssh-client")
    else:
        installer("ssh", "openssh")
    for package in packages:
        if not is_installed(package):
            sprint(f"{error}{package} cannot be installed. Install it manually!{nc}", stdout_speed)
            exit(1)



def is_running(process):
    return silent_shell(f"pidof {process}").wait() == 0


def is_installed(package):
    return silent_shell(f'command -v {package}').wait() == 0
   


def killer():
    # Previous instances of these should be stopped
    for process in processes:
        if is_running(process):
            # system(f"killall {process}")
            output = shell(f"pidof {process}", True).stdout.decode("utf-8").strip()
            if " " in output:
                for pid in output.split(" "):
                    kill(int(pid), SIGINT)
            elif output != "":
                kill(int(output), SIGINT)
            else:
                print()



def setup_log_file():
    global error_log
    logs_dir = Path(".logs")
    logs_file = logs_dir / "logs"

    # Check if the directory and file exist
    if not logs_dir.exists() or not logs_file.exists():
        # Create the directory and file
        logs_dir.mkdir(parents=True, exist_ok=True)
        logs_file.touch()
    error_log = logs_file

if __name__ == "__main__":
    main_menu()

