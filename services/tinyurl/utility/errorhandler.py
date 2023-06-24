import logging


def handle_tiny_url_response(tiny_url, response):
    if response.status_code == 200:
        logging.info(f'Request successful!')
        return 0
    if response.status_code == 401:
        logging.error(f'You are not authorized to access this resource or token: {tiny_url.auth_token} is blocked!'
                      f'Response: ' + response.text)
        return -1
    if response.status_code == 405:
        logging.error('You do not have the permission to see this resource! Response: ' + response.text)
        return -2
    if response.status_code == 422:
        logging.error('Error with the request! Response: ' + response.text)
        return -2
    if response.status_code > 500:
        logging.error(f'Error status code: {response.status_code}, Response: {response.text}')
        return -2

