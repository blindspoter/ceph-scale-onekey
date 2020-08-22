# -*- coding: utf-8 -*-

import logging
from logging.handlers import RotatingFileHandler

import os

from onekey.config import LOGGER_PATH


def get_logger(logname, log_dir=LOGGER_PATH):
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)
    logger = logging.getLogger('ONEKEY')
    logger.setLevel(logging.DEBUG)
    filename = os.path.join(log_dir, logname)
    fh = RotatingFileHandler(filename, 'ab', 2 * 1024 * 1024, 1)
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s ',
                                  datefmt="%Y-%m-%d %H:%M:%S")
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger


log = get_logger(logname='onekey.log')
