import logging


def retry_logger(attempt):
    logger = logging.getLogger(__name__)
    logger.error(f'Request failed, retrying... Retries left: {3-attempt}')





