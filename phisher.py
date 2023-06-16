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
from os import popen
import click
import json
from typing import List

# Color snippets
black="\033[0;30m"
red="\033[0;31m"
bred="\033[1;31m"
green="\033[0;32m"
bgreen="\033[1;32m"
yellow="\033[0;33m"
byellow="\033[1;33m"
blue="\033[0;34m"
bblue="\033[1;34m"
purple="\033[0;35m"
bpurple="\033[1;35m"
cyan="\033[0;36m"
bcyan="\033[1;36m"
white="\033[0;37m"
nc="\033[00m"

home_dir = popen("echo $HOME").read()
fancy = False

@click.command()
@click.option("--mode","-m","mode", prompt="Enter the mode", help="Choose phishing attack vector", type=click.Choice(['SMS', 'EMAIL'], case_sensitive=False), required=True)
@click.option("--cool", is_flag=True, default=False, help="Toogle fancy UI")

def menu(mode, cool):
    global fancy 
    fancy = cool 
    if mode.lower() == "email":
        email_menu()
    elif mode.lower() == "sms":
        sms_menu()
    ping = silent_shell('ping google.com -c 4 | grep "64 bytes" | cut -f 4,5 -d " "')
    ping.wait()
    output, error = ping.communicate()
    print(output.decode())
    

def email_menu():
    if fancy: 
        sprint(text=f'Email! This is path to your home directory: {home_dir}', second=0.1)
    else:
        print(f"Email! This is the path to your home directory: {home_dir}")        

def sms_menu():
    if fancy:
        sprint(text=f'Sms! This is path to your home directory: {home_dir}', second=0.1)
    else:
        print("Sms! This is path to your home directory: {home_dir}")


# Helper functions

def shell(command):
    try:
        return run(command, shell=True)
    except Exception as e:
        append(e, error_file)

def silent_shell(command, stdout=PIPE, stderr=DEVNULL, cwd="./"):
    try:
        return Popen(command, shell=True, stdout=stdout, stderr=stderr, cwd=cwd)
    except Exception as e:
        append(e, error_file)


def append(file_name, text):
    with open(filename, "a") as file:
        file.write(str(text) + "\n")


def sprint(text, second=0.05):
    for letter in text + '\n':
        stdout.write(letter)
        stdout.flush()
        sleep(second)

# Install packages
def installer(package, package_name=None):
    if package_name is None:
        package_name = package
    for pacman in ["pkg", "apt", "apt-get", "apk", "yum", "dnf", "brew", "pacman", "yay"]:
        # Check if package manager is present but php isn't present
        if is_installed(pacman):
            if not is_installed(package):
                sprint(f"\n{info}Installing {package}{nc}")
                if pacman=="pacman":
                    shell(f"sudo {pacman} -S {package_name} --noconfirm")
                elif pacman=="apk":
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

if __name__ == "__main__":
    menu()    
    print('wtf')
