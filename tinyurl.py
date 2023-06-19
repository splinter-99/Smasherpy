#  I want this module to generate urls, and perform api functions with tinyurl. The main script will   be checking if tunnel service is down  and will change the redirect if needed

#  This is a basic python module for interacting with tinyurl api, for free version usage
#  0 returns indicate success, -1  indicates token is dead, -2 indicates peculiarity, do a manual check

import random
import requests

import json
import string
import os

import settings

home_dir = os.getenv('HOME')


class TinyUrl:

    def __init__(self):
        self.auth_token = settings.TINY_URL_AUTH_TOKENS[0]
        self.rebuild_headers()
        self.existing_strings = set()

    def create_redirect_url(self, target_url):
        request_url = "https://api.tinyurl.com/create"
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
            self.target_url = target_url
            return 0

        elif response.status_code == 401:
            return -1
        print(response.status_code)
        return -2

    def update_redirect(self, url):
        request_url = "https://api.tinyurl.com/change"

        data = {
            'domain': self.domain,
            'alias': self.alias,
            'url': url
        }

        response = requests.patch(url=request_url, headers=self.headers, data=json.dumps(data))

        if response.status_code == 200:
            data = response.json()['data']
            self.target_url = data['url']
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

    def check_url_shortener(self):
        retry = 3
        while retry != -1:
            response = requests.head(self.tiny_url, allow_redirects=True)
            print(response.status_code)
            if response.status_code != 200:
                retry -= -1
                continue
            final_url = response.url
            if final_url == self.target_url:
                return 0
            if final_url in self.tiny_url:
                return -2  # Something is wrong with the redirect, maybe user is getting warning message
        return -1  # Something is wrong with the connection, most likely won't be the issue. Use different vpn conn!

    def rebuild_headers(self):
        self.headers = {'Authorization': f'Bearer {self.auth_token}', 'Content-Type': 'application/json'}

    def __str__(self):
        return f'token: {self.auth_token}\n----------------------------------------------------\n' + f'tiny_url: {self.tiny_url}\n-----------------------------------------------------\n' + f'target_url: {self.target_url}'
