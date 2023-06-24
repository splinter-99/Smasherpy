from environs import Env

env = Env()
env.read_env()

TINY_URL_AUTH_TOKENS = env.str("TINY_URL_AUTH_TOKENS", '').split('\n')
TUNNELING_SERVICES_URLS = env.str("TUNNELING_SERVICES_URLS", '').split('\n')

