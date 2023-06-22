#! venv/bin/python3.11
#  I want this module to generate urls, and perform api functions with tinyurl. The main script will   be checking if tunnel service is down  and will change the redirect if needed
"""
create_redirect_url() - connects to tinyurl api and creates new tinyurl redirect to your target url
update_redirect() - updates your redirect url in case of host failure

"""

import requests
import logging
import json
import os
import time
from sys import stdout
from multiprocessing import Process

from retry import retry
import click

import settings
import helper
from tinyurl import ErrorHandler
import beauty

home_dir = os.getenv('HOME')
BASE_URL = "https://api.tinyurl.com"


class TinyUrl:

    def __init__(self, redirect):
        self.existing_strings = set()
        self.domain = None
        self.alias = None
        self.tiny_url = None
        self.redirect_url = None
        self.status_code = None
        self.auth_token = settings.TINY_URL_AUTH_TOKENS[0]
        self.rebuild_headers()
        self.create_redirect_url(redirect)

    @retry(tries=3, delay=3, jitter=(1, 3))
    def create_redirect_url(self, redirect_url):
        alias = helper.generator.generate_unique_string(self.existing_strings)
        self.existing_strings.add(alias)

        request_url = f"{BASE_URL}/create"
        data = {'url': redirect_url,
                'alias': alias
                }
        logging.info(f'Creating redirect url...')
        response = requests.post(url=request_url, headers=self.headers, data=json.dumps(data))
        if ErrorHandler.handle_tiny_url_response(self, response) == 0:
            data = response.json()['data']
            self.domain = data['domain']
            self.alias = data['alias']
            self.redirect_url = redirect_url
            self.tiny_url = f'https://{self.domain}/{self.alias}'
            logging.info(f'Your tinyurl redirect url is created successfully: {self.tiny_url}')
        else:
            raise Exception

    @retry(tries=3, delay=5, jitter=(1, 3))
    def delete_existing_url(self):
        request_url = f"{BASE_URL}/alias/{self.domain}/{self.alias}"
        logging.info(f'Deleting tinyurl with alias: {self.alias}...')
        response = requests.delete(request_url, headers=self.headers)
        if ErrorHandler.handle_tiny_url_response(self, response) == 0:
            self.clear_url_fields()
        else:
            raise Exception

    @retry(tries=3, delay=3, jitter=(1, 3))
    def update_redirect(self, url):
        request_url = f"{BASE_URL}/change"

        data = {
            'domain': self.domain,
            'alias': self.alias,
            'url': url
        }

        response = requests.patch(url=request_url, headers=self.headers, data=json.dumps(data))

        if ErrorHandler.handle_tiny_url_response(self, response) == 0:
            data = response.json()['data']
            self.redirect_url = data['url']
        else:
            raise Exception

    def check_status(self):
        try:
            response = requests.head(self.tiny_url, allow_redirects=True)
            if 'tiny' in response.url:
                logging.error('Preview is blocking the user to see the site immediately...')
                logging.info(f'Saving current alias: {self.alias} for later reinitialization')
                logging.info(f'Redirected to url: {response.url}, response status code: {str(response.status_code)}')
                self.delete_existing_url()
                self.create_redirect_url(self.redirect_url)
            elif response.url == self.redirect_url:
                logging.info('Redirected to the correct redirect url!')
        except requests.TooManyRedirects:
            logging.error('Too many redirects!')

    def rebuild_headers(self):
        self.headers = {'Authorization': f'Bearer {self.auth_token}', 'Content-Type': 'application/json',
                        'User-Agent': 'Google Chrome'}

    def clear_url_fields(self):
        self.alias = None
        self.domain = None
        self.tiny_url = None

    def __str__(self):
        return f'token: {self.auth_token}\n\ntiny_url: {self.tiny_url}\n\nredirect: {self.redirect_url}'


def run_service(tiny_url):
    while True:
        tiny_url.check_status()
        time.sleep(10)


@click.command()
@click.option('--redirect', '-r', prompt='Enter redirect url', help='Enter redirect url for your tinyurl',
              required=True)
def main(redirect):
    initialize_loggers()
    tiny_url = TinyUrl(redirect)
    service_process = Process(target=run_service, args=(tiny_url,))
    service_process.daemon = True
    service_process.start()
    print('Enter command [update <url> - Update redirect url\nclient - Display tinyurl client info]\n')

    while True:
        user_input = input()
        command = user_input.split()
        if command[0] == 'update':
            if len(command) > 1:
                url = command[1]
                tiny_url.update_redirect(url)
            else:
                logging.error('e.g command: update <url>')
        elif command[0] == 'client':
            beauty.slow_print(tiny_url.__str__(), 0.02)

        if not service_process.is_alive():
            break

        time.sleep(0.1)

    service_process.join()


def initialize_loggers():
    logger = logging.getLogger('')
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Console Handler
    console_handler = logging.StreamHandler(stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler
    file_handler = logging.FileHandler(f'{home_dir}/.logs/logfile.log')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


if __name__ == '__main__':
    main()
