#  I want this module to generate urls, and perform api functions with tinyurl. The main script will   be checking if tunnel service is down  and will change the redirect if needed
"""
create_redirect_url() - connects to tinyurl api and creates new tinyurl redirect to your target url
update_redirect() - updates your redirect url in case of host failure

"""

import requests
from requests.exceptions import TooManyRedirects
from requests.exceptions import RequestException

import logging
import json
import os
import time
from subprocess import Popen, PIPE
from multiprocessing import Process

from retry import retry

from consts import TinyUrlPreviewException
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
        self.auth_token = settings.TINY_URL_AUTH_TOKENS[token]
        self.tunneling_service = tunneling_service_handler.set_tunneling_service()
        self.rebuild_headers()

    def create_redirect_url(self, redirect_url):
        alias = utility.generator.generate_unique_string(self.existing_strings)
        self.existing_strings.add(alias)

        request_url = f"{BASE_URL}/create"
        data = {'url': redirect_url,
                'alias': alias
                }
        logging.info(f'Creating redirect url...')
        response = requests.post(url=request_url, headers=self.headers, data=json.dumps(data))
        if utility.handle_tiny_url_response(self, response) == 0:
            data = response.json()['data']
            tiny_domain = data['domain']
            self.alias = data['alias']
            self.redirect_url = redirect_url
            self.tiny_url = f'https://{tiny_domain}/{self.alias}'
            logging.info(f'{green}Your tinyurl redirect url is created successfully: {self.tiny_url}')
        else:
            logging.error(f'Tiny url is not created! Response: {response.text} ')

    @retry(tries=3, delay=3, jitter=(1, 3))
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
            logging.warning(f'Updating redirect to {url} failed!')
        else:
            raise Exception

    @retry(tries=3, delay=10, jitter=(1, 3), logger=logging.getLogger(__name__))
    def check_status(self):
        try:
            response = requests.head(self.tiny_url, allow_redirects=True)
            if 'tiny' in response.url:
                logging.warning(f'Preview is blocking the user to see the site for tinyurl #{self.id} immediately...')
                logging.info(f'Redirected to url: {response.url}, response status code: {str(response.status_code)}')
                logging.info(f'Changing redirect url to: {self.tunneling_service}')
                self.update_redirect(self.tunneling_service)
                self.tunneling_service = tunneling_service_handler.cycle_next()
                raise TinyUrlPreviewException()
            if response.url[:8] in response.url:
                logging.info(f'tinyurl #{self.id} redirected to the correct domain!')
            else:
                logging.info(f'..{response.text} {response.status_code}')
        except TooManyRedirects:
            logging.error('Too many redirects!')
        except RequestException as e:
            logging.error(f'Error: {e}')

    def status_service(self):
        while True:
            try:
                self.check_status()
                time.sleep(30)
            except TinyUrlPreviewException:
                logging.critical(f'Deleting tiny url #{self.id}')
                del self


    def rebuild_headers(self):
        self.headers = {'Authorization': f'Bearer {self.auth_token}', 'Content-Type': 'application/json',
                        'User-Agent': 'Google Chrome'}

    def __str__(self):
        return f'\033[0;33m"\nID: {self.id}\n________\n\nToken: {self.auth_token}\nURL: {self.tiny_url}\nRedirect URL: {self.redirect_url}\033[1;36m\n'


def main_cli():
    Popen(['gnome-terminal', '--', 'tail', '-f', f'{home_dir}/.logs/logfile.log'], stdout=PIPE)
    utility.slow_print(f'{green}SYNOPSIS: \n\n'
                       'new <url> <token_index> - Create new instance of tinyurl\n\n'
                       'select <id> - Select tinyurl instance by id(use list to see all)\n\n'
                       'update <url> - Update redirect url for selected tinyurl\n\n'
                       'client - Display currently selected tinyurl instance\n\n'
                       'list - List all tinyurl instances\n\n', 0.01)
    count = 1
    tinyurls = []
    processes = []
    selected = 1

    while True:
        tiny_url = None
        for tinyurl in tinyurls:
            if tinyurl.id == selected:
                tiny_url = tinyurl
        # Get user input without displaying it
        user_input = input()
        commands = user_input.split(" ")

        if commands[0] == 'update' and tiny_url is not None:
            if len(commands) > 1:
                url = commands[1]
                tiny_url.update_redirect(f'https://{url}')
            else:
                utility.slow_print(f'{nc}e.g command: update <url>', 0.02)
        elif commands[0] == 'client':
            utility.slow_print(tiny_url.__str__(), 0.02)
        elif commands[0] == 'new':
            try:
                url = commands[1]
                token_index = int(commands[2])
                tinyurl = TinyUrl(token_index, str(count))
                if url[:8] != 'https':
                    tinyurl.create_redirect_url(f'https://{url}')
                else:
                    tinyurl.create_redirect_url(url)
                if tinyurl.redirect_url is None:
                    del tinyurl
                    continue

                tinyurls.append(tinyurl)
                new_process = Process(target=tinyurl.status_service)  # Update new_process value
                new_process.daemon = True
                new_process.start()

                processes.append(new_process)
                selected = count
                count += 1

            except IndexError:
                utility.slow_print(f'{red}e.g Wrong command format!', 0.02)
            except Exception as e:
                utility.slow_print(f'{red} Something went wrong!', 0.02)

        elif commands[0] == 'list':
            for tinyurl in tinyurls:
                print(tinyurl)
        elif commands[0] == 'select':
            selected = commands[1]
        else:
            utility.slow_print(f'{red}e.g Wrong command format!', 0.01)

        time.sleep(0.1)


class ColoredFormatter(logging.Formatter):

    # Define color codes
    COOL = "\033[1;33;45m"
    RED = "\033[1;31m"
    YELLOW = "\033[1;33m"
    RESET = "\033[0m"

    def format(self, record):
        # Set the appropriate color based on the log level
        if record.levelno == logging.ERROR:
            color_code = self.RED
        elif record.levelno == logging.INFO:
            color_code = self.COOL
        else:
            color_code = self.YELLOW

        # Add color codes to the log message
        record.msg = f"{color_code}{record.msg}{self.RESET}"
        return super().format(record)


#  Initialize console, file, queue handlers
def initialize_loggers():
    log_format: str = "%(asctime)s - %(levelname)s - %(message)s"
    logger = logging.getLogger('')
    logger.setLevel(logging.INFO)
    formatter = ColoredFormatter(log_format)

    # Create a console handler and set the formatter
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # File Handler
    file_handler = logging.FileHandler(f'{home_dir}/.logs/logfile.log')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


if __name__ == '__main__':
    initialize_loggers()
    main_cli()


