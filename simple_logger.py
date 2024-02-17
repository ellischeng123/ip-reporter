import logging
from logging.handlers import RotatingFileHandler
import sys

LOG_FORMAT = '{asctime} [{levelname:7}] {name} {message}'


def setup_logger() -> None:
    handlers = [
        RotatingFileHandler(filename='ip-reporter.log', encoding='utf-8', maxBytes=64 * 1024, backupCount=1),
        logging.StreamHandler(sys.stdout)
    ]
    logging.basicConfig(
        format=LOG_FORMAT, style='{', handlers=handlers, level=logging.INFO
    )


def get_logger(name: str = None) -> logging.Logger:
    return logging.getLogger(name)


setup_logger()

