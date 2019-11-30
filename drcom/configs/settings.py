#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ==================================================
# Licensed under the GPLv3
# 本项目由@Ryuchen开发维护，使用Python3.7
# ==================================================

import logging


# local config
USERNAME = ""
PASSWORD = ""
LOCAL_IP = ""  # 选填，默认为空，应填写本机IP，如：192.168.100.123
LOCAL_MAC = ""  # 选填，默认为空，应填写本机网卡MAC，全小写，无连接符，如：001a264a7b0d


# app config
ReTryTimes = 3
ReLoginFlag = True
ReLoginTimes = 3
ReLoginCheck = 30
LOG_LEVEL = logging.INFO


# login config
# 关键参数，BISTU版专属，请勿随意更改
SERVER_IP = '192.168.211.3'
DHCP_SERVER_IP = '211.68.32.204'
CONTROL_CHECK_STATUS = b'\x20'
ADAPTER_NUMBER = b'\x01'
IP_DOG = b'\x01'
AUTH_VERSION = b'\x0a\x00'
KEEP_ALIVE_VERSION = b'\xdc\x02'

# 状态声明参数
DIEOUT = 2
ONLINE = 1
OFFLINE = 0
