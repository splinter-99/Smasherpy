#! venv/bin/python3.11
#  I want this module to generate urls, and perform api functions with tinyurl. The main script will   be checking if tunnel service is down  and will change the redirect if needed
"""
create_redirect_url() - connects to tinyurl api and creates new tinyurl redirect to your target url
update_redirect() - updates your redirect url in case of host failure

"""

import random
import time
from multiprocessing import Process, Queue
import click
import sys

import requests
import logging

import json
import string
import os

import settings

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

    def create_redirect_url(self, target_url):
        request_url = f"{BASE_URL}/create"
        unique_alias = self.generate_unique_string()
        data = {'url': target_url,
                'alias': unique_alias
                }

        response = requests.post(url=request_url, headers=self.headers, data=json.dumps(data))
        if response.status_code == 200:
            data = response.json()['data']
            self.domain = data['domain']
            self.alias = data['alias']
            self.tiny_url = f'https://{self.domain}/{self.alias}'
            self.redirect_url = target_url
            return 0

        elif response.status_code == 401:
            return -1
        print(response.status_code)
        return -2

    def update_redirect(self, url):
        request_url = f"{BASE_URL}/change"

        data = {
            'domain': self.domain,
            'alias': self.alias,
            'url': url
        }

        response = requests.patch(url=request_url, headers=self.headers, data=json.dumps(data))

        if response.status_code == 200:
            data = response.json()['data']
            self.redirect_url = data['url']
            return 0

        if response.status_code == 401:  # Token is faulty
            return -1

        print(response.text)
        print(response.headers)
        return -2  # Peculiar error

    def generate_unique_string(self, length=8):
        random_string = ''.join(random.sample(string.ascii_letters, length))
        while random_string in self.existing_strings:
            random_string = ''.join(random.sample(string.ascii_letters, length))

        self.existing_strings.add(random_string)
        return random_string

    def check_status(self):
        try:
            response = requests.head(self.tiny_url, allow_redirects=True)
            if response.url[8:12] == 'tiny':
                logging.critical('Preview feature...')
                exit(-1)

            return 'Final url: ' + response.url + ' Response status code: ' + str(response.status_code)
        except requests.TooManyRedirects:
            return 'Too many redirects!'


    def rebuild_headers(self):
        self.headers = {'Authorization': f'Bearer {self.auth_token}', 'Content-Type': 'application/json',
                        'User-Agent': 'Google Chrome'}

    def __str__(self):
        return f'token: {self.auth_token}\n----------------------------------------------------\n'\
            + f'tiny_url: {self.tiny_url}\n-----------------------------------------------------\n' +\
            f'redirect: {self.redirect_url}'


def run_service(tiny_url):
    while True:
        status = tiny_url.check_status()
        logging.info('Status: ' + status)
        time.sleep(5)

@click.command()
@click.option('--redirect', '-r', prompt='Enter redirect url', help='Enter redirect url for your tinyurl',
              required=True)
def main(redirect):
    initialize_loggers()
    tiny_url = TinyUrl(redirect)
    service_process = Process(target=run_service, args=(tiny_url,))
    service_process.daemon = True
    service_process.start()

    while True:
        user_input = input('Enter command [update <url> - Update redirect url, client - display tinyurl client info] \n\n')
        command = user_input.split()
        if command[0] == 'update':
            if len(command) > 1:
                url = command[1]
                tiny_url.update_redirect(url)
            else:
                logging.error('e.g command: update <url>')
        elif command[0] == 'client':
            logging.info(str(tiny_url))

        if not service_process.is_alive():
            break

        time.sleep(0.1)

    service_process.join()


def initialize_loggers():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    file_handler = logging.FileHandler(f'{home_dir}/.logs/logfile.log')
    file_handler.setLevel(logging.INFO)
    logging.getLogger('').addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    logging.getLogger('').addHandler(console_handler)


if __name__ == '__main__':
    main()
