#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ==================================================
# Licensed under the GPLv3
# 本项目由@Ryuchen开发维护，使用Python3.7
# ==================================================

import sys
import logging

from drcom.configs.settings import LOG_LEVEL


class Log(object):
    def __init__(self, level, err_no, msg):
        logging.basicConfig(stream=sys.stdout, level=LOG_LEVEL, format='%(asctime)s - [%(levelname)s]: %(message)s')
        if level == logging.DEBUG:
            logging.debug(msg)
        if level == logging.INFO:
            logging.info(msg)
        if level == logging.WARNING:
            logging.warning(msg)
        if level == logging.ERROR:
            logging.error("err_no:" + str(err_no) + ", " + msg)
