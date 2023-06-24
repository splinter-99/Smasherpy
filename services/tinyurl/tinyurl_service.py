import time


def run_service(tiny_url):
    while True:
        tiny_url.check_status()
        time.sleep(30)
