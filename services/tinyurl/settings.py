import os

home_dir = os.getenv('HOME')


#  File path where your config will be saved
with open('config') as f:
    token_data = f.read()

#  File path where your config will be saved
with open(f'config_tunnel') as f:
    tunnelers_data = f.read()

TINY_URL_AUTH_TOKENS = token_data.split('\n')
TUNNELING_SERVICES_URLS = tunnelers_data.split('\n')

