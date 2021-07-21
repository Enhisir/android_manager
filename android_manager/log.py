import sys
import logging
from logging.handlers import TimedRotatingFileHandler


LOG_FILE = "android_manager.log"
FORMATTER = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def get_console_handler():
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(FORMATTER)
    return console_handler


def get_file_handler():
    file_handler = TimedRotatingFileHandler(LOG_FILE)
    file_handler.setFormatter(FORMATTER)
    return file_handler


def get_logger(console_handler=True, file_handler=True):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    if console_handler:
        logger.addHandler(get_console_handler())
    if file_handler:
        logger.addHandler(get_file_handler())
    logger.propagate = False
    return logger


logger = get_logger()
