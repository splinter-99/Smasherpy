from environs import Env

env = Env()
env.read_env()

TINY_URL_AUTH_TOKENS = env.str("TINY_URL_AUTH_TOKENS", '').split(';')

