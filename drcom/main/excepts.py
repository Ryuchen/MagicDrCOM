#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ==================================================
# Licensed under the GPLv3
# 本项目由@Ryuchen开发维护，使用Python3.7
# ==================================================


class DrCOMException(Exception):
    def __init__(self, *args, **kwargs):
        super(DrCOMException, self).__init__(args, kwargs)
        if len(args[0]) > 0:
            self.info = args[0]
        self.last_pkg = None


class TimeoutException(Exception):
    def __init__(self, *args, **kwargs):
        super(TimeoutException, self).__init__(args, kwargs)
        if len(args[0]) > 0:
            self.info = args[0]
        self.last_pkg = None


class MagicDrCOMException(Exception):
    def __init__(self, *args, **kwargs):
        super(MagicDrCOMException, self).__init__(args, kwargs)
        if len(args[0]) > 0:
            self.info = args[0]
