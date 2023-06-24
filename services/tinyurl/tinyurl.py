import requests
from requests.exceptions import TooManyRedirects
from requests.exceptions import RequestException
from requests.exceptions import ConnectionError

import logging
import random
import json
import os
import time
from subprocess import Popen, PIPE
from multiprocessing import Process

from tenacity import retry, stop_after_attempt, wait_random
from urllib3 import HTTPSConnectionPool

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
nc = "\033[00m"

home_dir = os.getenv('HOME')
BASE_URL = "https://api.tinyurl.com"

tunneling_service_handler = tunneling.TunnelServiceHandler(settings.TUNNELING_SERVICES_URLS)


class TinyUrl:

    def __init__(self, token, id):
        self.id = id
        self.existing_strings = set()
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
            logging.info(f'Tinyurl redirect url is created successfully: {self.tiny_url}')
        else:
            logging.error(f'Tiny url is not created! Response: {response.text} ')

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
            logging.warning(f'Updating redirect to {url} failed! Error: {response.text} Status code: {response.status_code}')
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
            try:
                self.check_status()
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
                time.sleep(random.uniform(30, 60))

    def rebuild_headers(self):
        self.headers = {'Authorization': f'Bearer {self.auth_token}', 'Content-Type': 'application/json',
                        'User-Agent': 'Google Chrome'}

    def __str__(self):
        return f'\033[0;33m\nID: {self.id}\n________\n\nToken: {self.auth_token}\nURL: {self.tiny_url}\nRedirect URL: {self.redirect_url}\033[1;36m'


def main_cli():
    Popen(['gnome-terminal', '--', 'tail', '-f', f'{home_dir}/.logs/logfile.log'], stdout=PIPE)
    helper = f'\n{bwhite}SYNOPSIS: \n' \
             f'{bgreen}new <url> <token_index> - {green}Create new instance of tinyurl\n' \
             f'{bgreen}select <id> - {green}Select tinyurl instance by id (use list to see all)\n' \
             f'{bgreen}update <url> - {green}Update redirect url for selected tinyurl\n' \
             f'{bgreen}current - {green}Display currently selected tinyurl instance\n' \
             f'{bgreen}list - {green}List all tinyurl instances\n\n'

    utility.slow_print(helper, 0.01)
    count = 1
    tinyurls = []
    processes = []
    tinyurl_processes = {}
    selected = 0

    try:
        while True:
            if tinyurls is not None:
                try:
                    tiny_url = tinyurls[selected - 1]
                except IndexError:
                    pass
            else:
                tiny_url = None
            user_input = input().strip()
            commands = user_input.split(" ")

            if commands[0] == 'update' and tiny_url is not None:
                if len(commands) > 1:
                    url = commands[1]
                    tiny_url.update_redirect(f'https://{url}')
                else:
                    utility.slow_print(f'{bred}Wrong command format! Look Synopsis!', 0.01)
            elif commands[0] == 'current':
                print(tinyurl.__str__())
            elif commands[0] == 'new':
                try:
                    url = commands[1]
                    if len(commands) == 3:
                        token_index = int(commands[2])
                    else:
                        token_index = 1
                    tinyurl = TinyUrl(token_index, str(count))
                    if url[:8] != 'https://':
                        tinyurl.create_redirect_url(f'https://{url}')
                    else:
                        tinyurl.create_redirect_url(url)
                    if tinyurl.redirect_url is None:
                        utility.slow_print('Tinyurl instance not created!', 0.01)
                        del tinyurl
                        continue

                    tinyurls.append(tinyurl)
                    new_process = Process(target=tinyurl.status_service)  # Update new_process value
                    new_process.daemon = True
                    new_process.start()
                    processes.append(new_process)

                    tinyurl_processes[tinyurl] = new_process
                    selected = count
                    count += 1

                except IndexError:
                    utility.slow_print(f'{bred}e.g Wrong command format! Look Synopsis!', 0.01)
                except Exception as e:
                    utility.slow_print(f'{bred} Something went wrong!', 0.01)

            elif commands[0] == 'del':
                for i, tinyurl in enumerate(tinyurls):
                    if tinyurl.id == commands[1]:
                        tiny_url = tiny_url
                        tinyurls.pop(i)
                        logging.info(f'{byellow}Deleting Tinyurl #{commands[1]}...')
                        logging.info(f'{byellow}Shutting down linked process...')
                        process = tinyurl_processes.get(tiny_url)
                        if process:
                            process.terminate()
                            process.join()
                            del tinyurl_processes[tiny_url]
                        del tiny_url
                        break
            elif commands[0] == 'list':
                for tinyurl in tinyurls:
                    print(tinyurl)

            elif commands[0] == 'select':
                selected = int(commands[1])
            elif 'exit' in commands:
                utility.slow_print(f'{bred}Shutting down running processes...', 0.05)
                for processes in processes:
                    processes.terminate()
                utility.slow_print(f'{bwhite}Thank you for using Murlocs creation!', 0.05)
                exit(0)
            elif 'help' in commands:
                print(helper)
            else:
                utility.slow_print(f'{bred}e.g Wrong command format!', 0.01)

            time.sleep(0.1)
    except KeyboardInterrupt:
        for process in processes:
            process.terminate()
            process.join()


#  Initialize console, file, queue handlers
def initialize_loggers():
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    formatter = ColoredFormatter(log_format)
    logger = logging.getLogger('')
    logger.setLevel(logging.INFO)

    # Create a console handler and set the formatter
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # File Handler
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
