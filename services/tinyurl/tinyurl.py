import requests
from requests.exceptions import TooManyRedirects
from requests.exceptions import RequestException
from requests.exceptions import ConnectionError

import logging
import random
import json
import sys
import os
import re
import time
from subprocess import Popen, PIPE
from multiprocessing import Process

from tenacity import retry, stop_after_attempt, wait_random

from consts import TinyUrlPreviewException
from colory.ColoredFormatter import ColoredFormatter
import settings
import utility
import tunneling

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
bwhite = "\033[1;37m"
bmagenta = "\u001b[45;1m"
nc = "\033[00m"
reset = "\u001b[0m"

success = f"{yellow}[{white}√{yellow}] {green}"
error = f"{blue}[{white}√{yellow}] {green}"

home_dir = os.getenv('HOME')
BASE_URL = "https://api.tinyurl.com"

tunneling_service_handler = tunneling.TunnelServiceHandler(settings.TUNNELING_SERVICES_URLS)


class TinyUrl:

    def __init__(self, token):
        self.existing_strings = set()
        self.id = None
        self.alias = None
        self.tiny_url = None
        self.redirect_url = None
        self.auth_token = settings.TINY_URL_AUTH_TOKENS[token - 1]
        self.tunneling_service = tunneling_service_handler.set_tunneling_service()
        self.rebuild_headers()

    def create_redirect_url(self, redirect_url):
        alias = utility.generator.generate_unique_string(self.existing_strings)
        self.existing_strings.add(alias)

        request_url = f"{BASE_URL}/create"
        data = {'url': redirect_url,
                'alias': alias
                }
        logging.info(f'Creating tinyurl for redirect to {redirect_url}...')
        response = requests.post(url=request_url, headers=self.headers, data=json.dumps(data))
        if utility.handle_tiny_url_response(self, response) == 0:
            data = response.json()['data']
            tiny_domain = data['domain']
            self.alias = data['alias']
            self.redirect_url = redirect_url
            self.tiny_url = f'https://{tiny_domain}/{self.alias}'
            logging.info(f'{bgreen}Tinyurl redirect url is created successfully: {self.tiny_url}')
        else:
            logging.error(f'{bred}Tiny url is not created! Response: {response.text}')

    @retry(stop=stop_after_attempt(3), wait=wait_random(min=2, max=4), reraise=True)
    def update_redirect(self, url):
        request_url = f"{BASE_URL}/change"

        data = {
            'domain': 'tinyurl.com',
            'alias': self.alias,
            'url': url
        }

        response = requests.patch(url=request_url, headers=self.headers, data=json.dumps(data))
        error_code = utility.handle_tiny_url_response(self, response)
        if error_code == 0:
            data = response.json()['data']
            self.redirect_url = data['url']
        elif error_code == -2:
            logging.warning(
                f'Updating redirect to {url} failed! Error: {response.text} Status code: {response.status_code}')
        else:
            raise Exception

    def check_status(self):
        try:
            response = requests.head(self.tiny_url, allow_redirects=True)
            if 'tiny' in response.url:
                raise TinyUrlPreviewException()
            if response.url[:8] in response.url:
                logging.info(f'Tinyurl #{self.id} redirected to the correct domain!')
            else:
                logging.info(f'..{response.text} {response.status_code}')
        except TooManyRedirects as e:
            raise e
        except RequestException as e:
            raise e
        except ConnectionError as e:
            raise e
        except Exception as e:
            raise e

    @retry(stop=stop_after_attempt(3), wait=wait_random(min=5, max=10), reraise=True)
    def status_service(self):
        while True:
            failures = 0
            try:
                self.check_status()
                failures = 0
            except TinyUrlPreviewException:
                logging.warning(f'Preview feature blocking the site for Tinyurl #{self.id}...')
                logging.warning(f'Preview feature is blocking the user to see the site for Tinyurl #{self.id}...')
                self.tunneling_service = tunneling_service_handler.cycle_next()
                logging.info(f'Changing redirect url to: {self.tunneling_service}')
                try:
                    self.update_redirect(self.tunneling_service)
                except Exception as e:
                    continue
            except ConnectionError as e:
                error_message = str(e)
                if "Max retries exceeded" in error_message:
                    # Handle the specific error message
                    logging.warning(f'{self.tiny_url} is an incorrect URL!...{e}')
                elif "Failed to establish a new connection" in error_message:
                    # Handle the specific error message
                    logging.warning(f'Failed to establish a new connection for Tinyurl #{self.id}...{e}')
                    break
                else:
                    pass
            except RequestException as e:
                logging.warning(f'Error for Tinyurl #{self.id}: {e}')
            except Exception as e:
                logging.warning(f'Connection error for Tinyurl #{self.id}...{e} Please check!')
            finally:
                failures += 1
                if failures > 3:
                    break
                time.sleep(random.uniform(30, 60))

    def rebuild_headers(self):
        self.headers = {'Authorization': f'Bearer {self.auth_token}', 'Content-Type': 'application/json',
                        'User-Agent': 'Google Chrome'}

    def __str__(self):
        return f'\033[0;33m\nID: {self.id}\n________\n\nToken: {self.auth_token}\nURL: {self.tiny_url}\nRedirect URL: {self.redirect_url}\033[1;36m'


def main_cli():
    Popen(['gnome-terminal', '--', 'tail', '-f', f'{home_dir}/.logs/logfile.log'], stdout=PIPE)
    helper = f'\n{bwhite}SYNOPSIS: \n' \
             f'{byellow}new <url> <token_index> - {yellow}Create new instance of tinyurl\n' \
             f'{byellow}select <id> - {yellow}Select tinyurl instance by their id(use list to see all)\n' \
             f'{byellow}update <url> - {yellow}Update redirect url for selected tinyurl\n' \
             f'{byellow}current - {yellow}Display currently selected tinyurl instance\n' \
             f'{byellow}list - {yellow}List all tinyurl instances\n' \
             f'{byellow}exit - {yellow}Very fancy exit to a program\n\n'

    utility.slow_print(helper, 0.01)

    id_tinyurls_mapping = {}

    processes = []
    tinyurl_processes = {}

    selected_by_id = None

    try:
        while True:
            tinyurls = [tinyurl for tinyurl in id_tinyurls_mapping.values()]
            if tinyurls is not None:
                curr_tinyurl = id_tinyurls_mapping.get(selected_by_id)
            else:
                curr_tinyurl = None

            user_input = input(f'{bgreen}> ').strip()
            commands = re.split(r"\s+", user_input)

            if commands[0] == 'update' and curr_tinyurl is not None:
                if len(commands) > 1:
                    url = commands[1]
                    utility.slow_print(f'{bgreen}Sent request to update {curr_tinyurl.tiny_url} to https://{url}', 0.01)
                    curr_tinyurl.update_redirect(f'https://{url}')
                else:
                    utility.slow_print(f'{error}{bred}Wrong command format! Use help command', 0.01)
            elif commands[0] == 'current':
                print(curr_tinyurl.__str__())
            elif commands[0] == 'new':
                try:
                    url = commands[1]
                    if len(commands) > 2:
                        token_index = int(commands[2])
                    else:
                        token_index = 1
                    new_turl = TinyUrl(token_index)
                    if url[:8] != 'https://':
                        new_turl.create_redirect_url(f'https://{url}')
                    else:
                        new_turl.create_redirect_url(url)
                    if new_turl.redirect_url is None:
                        utility.slow_print('Tinyurl instance not created!', 0.01)
                        continue
                    if tinyurls:
                        last_id = max(id_tinyurls_mapping.keys())
                        next_id = last_id + 1
                    else:
                        next_id = 1
                        selected_by_id = 1

                    id_tinyurls_mapping.update({next_id: new_turl})
                    new_turl.id = next_id

                    new_process = Process(target=new_turl.status_service)  # Update new_process value
                    new_process.daemon = True
                    new_process.start()
                    processes.append(new_process)

                    tinyurl_processes[new_turl] = new_process

                except IndexError:
                    utility.slow_print(f'{bred}Wrong command format or token index! Use help command', 0.01)

            elif commands[0] == 'del':
                if len(commands) > 1:
                    id_to_delete = int(commands[1])
                else:
                    id_to_delete = selected_by_id   # delete selected if not specified
                    if selected_by_id = 1:
                        selected_by_id += 1
                    else:
                        selected_by_id -= 1
                list_keys = [key for key in id_tinyurls_mapping.keys()]
                if id_to_delete not in list_keys:
                    utility.slow_print(f'{bred}Invalid selection!', 0.01)
                    continue

                utility.slow_print(f'{byellow}Tinyurl #{id_to_delete} deleted!', 0.01)
                utility.slow_print(f'{byellow}Tinyurl #{selected_by_id} is now selected!', 0.01)

                id_tinyurls_mapping.pop(id_to_delete)

                for key in id_tinyurls_mapping.keys():
                    if id_to_delete == key:
                        process_to_terminate = tinyurl_processes.get(id_tinyurls_mapping[key])
                        if process_to_terminate:
                            process_to_terminate.terminate()
                            process_to_terminate.join()
                            tinyurl_processes.pop(id_tinyurls_mapping[key])
                        utility.slow_print(f'{bgreen}Tinyurl #{commands[1]} deleted!', 0.01)
                        logging.info(f'{byellow}Deleting Tinyurl #{commands[1]}...')
                        logging.info(f'{byellow}Shutting down linked daemon process...')

            elif commands[0] == 'list':
                for turl in tinyurls:
                    print(turl)

            elif commands[0] == 'select':
                if len(commands) < 2:
                    utility.slow_print(f'{bred}You need to input tinyurl instance id!', 0.01)
                    continue

                num = re.search(r'\d+', commands[1])
\
                if not num:
                    utility.slow_print(f'{bred}You need to input tinyurl instance id!', 0.01)
                    continue

                num = int(num.group())   # Extract the number
                
                if num not in id_tinyurls_mapping.keys():
                    utility.slow_print(f'{bred}No tinyurl instance with id {num}!', 0.01)
                    continue

                selected_by_id = int(commands[1])
                utility.slow_print(f'{byellow}Selected Tinyurl #{selected_by_id} with current redirect to {id_tinyurls_mapping[selected_by_id].redirect_url}\n', 0.01)

            elif 'exit' in commands:
                utility.slow_print(f'{bred}Shutting down running processes...', 0.05)
                for processes in processes:
                    processes.terminate()
                utility.slow_print(f'{bwhite}Thank you for using Murloc tool \u2665', 0.05)
                exit(0)
            elif 'help' in commands:
                print(helper)
            else:
                utility.slow_print(f'{bred}e.g Wrong command format!', 0.01)
            time.sleep(0.1)

    except KeyboardInterrupt:
        for process_to_terminate in processes:
            process_to_terminate.terminate()
            process_to_terminate.join()


def check_and_create_directory(directory_name):
    home_dir = os.path.expanduser('~')
    directory_path = os.path.join(home_dir,'.logs')

    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        print(f'Directory {directory_name} created in {directory_path}')


#  Initialize console, file, queue handlers
def initialize_loggers():
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    formatter = ColoredFormatter(log_format)
    logger = logging.getLogger('')
    logger.setLevel(logging.INFO)


    # File Handler
    check_and_create_directory('.logs')
    file_handler = logging.FileHandler(f'{home_dir}/.logs/logfile.log')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger, file_handler


if __name__ == '__main__':
    logger, file_handler = initialize_loggers()
    try:
        main_cli()
    finally:
        file_handler.close()
