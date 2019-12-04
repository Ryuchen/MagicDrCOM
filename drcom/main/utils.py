#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ==================================================
# Licensed under the GPLv3
# 本项目由@Ryuchen开发维护，使用Python3.7
# ==================================================
import uuid
import socket
import struct
import hashlib


def mac():
    """
    获取本机mac地址
    :return:
    """
    return uuid.UUID(int=uuid.getnode()).hex[-12:]


def hostname():
    """
    获取本机主机名称
    :return:
    """
    return socket.getfqdn(socket.gethostname())


def ipaddress():
    """
    获取当前联网的IP地址
    :return:
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('114.114.114.114', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip


def md5(string):
    m = hashlib.md5()
    m.update(string)
    return m.digest()


def int2hex_str(num):
    s = '%x' % num
    if len(s) & 1:
        s = '0' + s
    return bytes().fromhex(s)


def checksum(b):
    """
    在python2中的循环如下
    for i in re.findall('....', s):
        ret ^= int(i[::-1].encode('hex'), 16)
    校验和以4个字节为一组进行计算，遇到b'\x0a'时，从b'\x0a'之后开始重新分组
    为了能匹配b'\x0a'，不得不加入一个if
    """
    ret = 1234
    i = 0
    while i + 4 < len(b):
        if not(b[i:i + 4].find(b'\x0a') == -1):
            i = i + b[i:i+4].find(b'\x0a') + 1
        ret ^= int.from_bytes(b[i:i+4][::-1], 'big')
        i = i + 4
    ret = (1968 * ret) & 0xffffffff
    return struct.pack('<I', ret)


def clean_socket_buffer(s):
    timeout = s.gettimeout()
    s.settimeout(0.01)
    while True:
        try:
            s.recvfrom(1024)
        except socket.timeout:
            break
    s.settimeout(timeout)


def print_bytes(byte):
    #
    print("========================================================================")
    print("-NO-  00 01 02 03 04 05 06 07  08 09 0a 0b 0c 0d 0e 0f  --ascii-string--")
    for i in range(0, len(byte), 16):
        print("%04x  " % i, end='')
        for j in range(i, i+16):
            if j < len(byte):
                print("%02x " % byte[j], end='')
            else:
                print("  ", end='')
            if (j+1) % 8 == 0:
                print(" ", end='')
        print(byte[i:i+16].decode('ascii', 'replace').replace('\n', '^'))
    print("========================================================================")
