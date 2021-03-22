#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ==================================================
# Licensed under the GPLv3
# 本项目由@Ryuchen开发维护，使用Python3.7
# ==================================================

import sys
import time
import struct
import socket
import random

from drcom.main.utils import mac
from drcom.main.utils import hostname
from drcom.main.utils import ipaddress
from drcom.main.utils import md5
from drcom.main.utils import checksum
from drcom.main.utils import int2hex_str
from drcom.main.utils import clean_socket_buffer
from drcom.main.logger import Log
from drcom.main.excepts import DrCOMException
from drcom.main.excepts import TimeoutException
from drcom.configs.settings import *


class DrCOMResponse(object):

    def __init__(self):
        self._msg = ""

    @property
    def msg(self):
        return self._msg

    @msg.setter
    def msg(self, msg):
        self._msg = msg


class DrCOMClient(object):

    def __init__(self, usr="", pwd=""):
        self._usr = usr
        self._pwd = pwd

        self._num = 0
        self._key = b'\x00' * 4

        self.salt = b""
        self.server_ip = ""
        self.auth_info = b""

        self.alive_flag = True
        self.ready_flag = False
        self.login_flag = False

        self.platform = sys.platform

    @property
    def usr(self):
        return self._usr

    @usr.setter
    def usr(self, value):
        self._usr = value

    @property
    def pwd(self):
        return self._pwd

    @pwd.setter
    def pwd(self, value):
        self._pwd = value

    @property
    def num(self):
        return self._num

    @num.setter
    def num(self, value):
        self._num = value

    @property
    def key(self):
        return self._key

    @key.setter
    def key(self, value):
        self._key = value

    def _setup(self):
        """
        尝试获取当前主机的主机名称、MAC地址、联网IP地址
        :return:
        """
        self.host_name = hostname()

        if LOCAL_MAC:  # 如果没有指定本机MAC，尝试自动获取
            self.mac = bytes().fromhex(LOCAL_MAC)
        else:
            self.mac = bytes().fromhex(mac())

        if LOCAL_IP:  # 如果没有指定本机IP，尝试自动获取
            self.ip = LOCAL_IP
        else:
            self.ip = ipaddress()

        if not self.host_name or not self.mac or not self.ip:
            raise DrCOMException("请确保已经接入有线网")

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.socket.settimeout(3)
        try:
            self.socket.bind(("", 61440))
        except (OSError, socket.error):
            raise DrCOMException("检测到重复启动客户端")

    def _make_login_package(self):
        """
        构造登陆数据包
        :return:
        """
        # (0:3 4) Header = Code + Type + EOF + (UserName Length + 20)
        data = b'\x03\x01\x00' + int2hex_str(len(self.usr) + 20)
        # (4:19 16) MD5_A = MD5(Code + Type + Salt + Password)
        data += md5(b'\x03\x01' + self.salt + self.pwd.encode('ascii'))
        # (20:55 36) 用户名
        data += self.usr.encode('ascii').ljust(36, b'\x00')
        # (56:56 1) 控制检查状态
        data += CONTROL_CHECK_STATUS
        # (57:57 1) 适配器编号？
        data += ADAPTER_NUMBER
        # (58:63 6) (MD5_A xor MAC)
        data += int2hex_str(int.from_bytes(data[4:10], 'big') ^ int.from_bytes(self.mac, 'big')).rjust(6, b'\x00')
        # (64:79 16) MD5_B = MD5(0x01 + Password + Salt + 0x00 *4)
        data += md5(b'\x01' + self.pwd.encode('ascii') + self.salt + b'\x00' * 4)
        # (80:80 1) NIC Count
        data += b'\x01'
        # (81:84 4) 本机IP
        data += socket.inet_aton(self.ip)
        # (85:88 4) ip地址 2
        data += b'\00' * 4
        # (89:92 4) ip地址 3
        data += b'\00' * 4
        # (93:96 4) ip地址 4
        data += b'\00' * 4
        # (97:104 8) 校验和A
        data += md5(data + b'\x14\x00\x07\x0b')[:8]
        # (105:105 1) IP Dog
        data += IP_DOG
        # (106:109 4) 未知
        data += b'\x00' * 4
        # (110:141 32) 主机名
        data += self.host_name.encode('ascii').ljust(32, b'\x00')
        # (142:145 4) 主要dns: 114.114.114.114
        data += b'\x72\x72\x72\x72'
        # (146:149 4) DHCP服务器IP
        data += socket.inet_aton(DHCP_SERVER_IP)
        # (150:153 4) 备用dns:8.8.8.8
        data += b'\x08\x08\x08\x08'
        # (154:161 8) 未知
        data += b'\x00' * 8
        data += b'\x94\x00\x00\x00'  # (162:165 4) 未知
        data += b'\x06\x00\x00\x00'  # (166:169 4) OS major 不同客户端有差异
        data += b'\x01\x00\x00\x00'  # (170:173 4) OS minor 不同客户端有差异
        data += b'\xb1\x1d\x00\x00'  # (174:177 4) OS build 不同客户端有差异
        data += b'\x02\x00\x00\x00'  # (178:181 4) 未知 OS相关
        # (182:213 32) 操作系统名称
        data += "WINDOWS".encode('ascii').ljust(32, b'\x00')
        # (214:309 96) 未知 不同客户端有差异，BISTU版此字段包含一段识别符，但不影响登陆
        data += b'\x00' * 96
        # (310:311 2)
        data += AUTH_VERSION
        # (312:313 2) 未知
        data += b'\x02\x0c'
        # (314:317 4) 校验和
        data += checksum(data + b'\x01\x26\x07\x11\x00\x00' + self.mac)
        # (318:319 2) 未知
        data += b'\x00\x00'
        # (320:325 6) 本机MAC
        data += self.mac
        # (326:326 1) auto logout / default: False
        data += b'\x00'
        # (327:327 1) broadcast mode / default : False
        data += b'\x00'
        # (328:329 2) 未知 不同客户端有差异
        data += b'\x17\x77'
        return data

    def _make_alive_package(self, num, key, cls):
        """
        构造心跳数据包
        :param num:
        :param key:
        :param cls:
        :return:
        """
        # (0:0 1) 未知
        data = b'\x07'
        # (1:1 1) 编号
        data += int2hex_str(num % 256)
        # (2:4 3) 未知
        data += b'\x28\x00\x0b'
        # (5:5 1) 类型
        data += int2hex_str(cls)
        # (6:7 2) BISTU版此字段不会变化
        if num == 0:
            data += b'\xdc\x02'
        else:
            data += KEEP_ALIVE_VERSION
        # (8:9 2) 未知 每个包会有变化
        data += b'\x2f\x79'
        # (10:15 6) 未知
        data += b'\x00' * 6
        # (16:19 4)
        data += key
        # (20:23 4) 未知
        data += b'\x00' * 4
        # data += struct.pack("!H",0xdc02)  # 未验证
        if cls == 1:
            # (24:39 16) 未知
            data += b'\x00' * 16
        if cls == 3:
            # host_ip
            foo = b''.join([int2hex_str(int(i)) for i in self.ip.split('.')])
            # use double keep in main to keep online .Ice
            crc = b'\x00' * 4
            # data += struct.pack("!I",crc) + foo + b'\x00' * 8
            data += crc + foo + b'\x00' * 8
        return data

    def _make_logout_package(self):
        # (0:3 4) Header = Code + Type + EOF + (UserName Length + 20)
        data = b'\x06\x01\x00' + int2hex_str(len(self.usr) + 20)
        # TODO MD5_A字段在BISTU版中的算法未知，但以下算法可以正常使用
        # (4:19 16) MD5_A = MD5(Code + Type + Salt + Password)
        data += md5(b'\x06\x01' + self.salt + self.pwd.encode('ascii'))
        # (20:55 36) 用户名
        data += self.usr.encode('ascii').ljust(36, b'\x00')
        # (56:56 1) 控制检查状态
        data += CONTROL_CHECK_STATUS
        # (57:57 1) 适配器编号？
        data += ADAPTER_NUMBER
        # (58:63 6) (MD5_A xor MAC)
        data += int2hex_str(int.from_bytes(data[4:10], 'big') ^ int.from_bytes(self.mac, 'big')).rjust(6, b'\x00')
        data += self.auth_info
        return data

    def _send_package(self, pkg, server):
        """
        发送数据包, 每次发送都尝试三次，如果发送三次都失败，触发超时异常
        :param pkg:
        :return:
        """
        last_times = ReTryTimes
        while last_times > 0:
            last_times = last_times - 1
            clean_socket_buffer(self.socket)
            self.socket.sendto(pkg, server)
            try:
                data, address = self.socket.recvfrom(1024)
            except socket.timeout:
                Log(logging.WARNING, 0, "[DrCOM._send_package]：Continue to retry times [{}]...".format(last_times))
                continue

            if data and address:
                return data, address

        exception = TimeoutException("[DrCOM._send_package]：Failure on sending package...")
        exception.last_pkg = pkg
        raise exception

    def send_alive_pkg1(self):
        """
        发送类型一的心跳包
        :return:
        """
        pkg = b'\xff'
        pkg += md5(b'\x03\x01' + self.salt + self.pwd.encode('ascii'))  # MD5_A
        pkg += b'\x00' * 3
        pkg += self.auth_info
        pkg += struct.pack('!H', int(time.time()) % 0xFFFF)
        pkg += b'\x00' * 3

        data, address = self._send_package(pkg, (self.server_ip, 61440))

        if data[0] == 0x07:
            Log(logging.DEBUG, 0, "[DrCOM.send_alive_pkg1]：Successful sending heartbeat package type 1...")
        else:
            # 当收到的数据包没法识别的时候
            exception = DrCOMException("[DrCOM.send_alive_pkg1]：Receive unknown packages content...")
            exception.last_pkg = data
            raise exception

    def send_alive_pkg2(self, num, key, cls):
        """
        发送类型二的心跳包
        :return:
        """
        pkg = self._make_alive_package(num=num, key=key, cls=cls)

        data, address = self._send_package(pkg, (self.server_ip, 61440))

        if data[0] == 0x07:
            Log(logging.DEBUG, 0, "[DrCOM.send_alive_pkg2]：Successful sending heartbeat package 2[{}]...".format(cls))
            response = data[16:20]
            return response
        else:
            # 当收到的数据包没法识别的时候
            exception = DrCOMException("[DrCOM.send_alive_pkg2]：Receive unknown packages content...")
            exception.last_pkg = data
            raise exception

    def prepare(self):
        """
        获取服务器IP和Salt
        :return:
        """
        self._setup()
        random_value = struct.pack("<H", int(time.time() + random.randint(0xF, 0xFF)) % 0xFFFF)
        pkg = b'\x01\x02' + random_value + b'\x0a' + b'\x00' * 15

        # 尝试目前已知的学校认证服务器地址
        for _ in [(SERVER_IP, 61440), ("1.1.1.1", 61440), ("202.1.1.1", 61440)]:
            data, address = self._send_package(pkg, _)

            # 未获取合理IP地址则进行下一个服务器地址尝试
            if data[0:4] == b'\x02\x02' + random_value:
                self.server_ip = address[0]
                self.salt = data[4:8]

                self.ready_flag = True
                res = DrCOMResponse()
                res.msg = "已做好接入有线网的准备"
                return res

        if not self.server_ip or not self.salt:
            exception = DrCOMException("无法检测到验证服务器")
            exception.last_pkg = pkg
            raise exception

    def login(self):
        """
        登录到目标服务器方法
        :return:
        """
        pkg = self._make_login_package()

        data, address = self._send_package(pkg, (self.server_ip, 61440))

        if data[0] == 0x04:
            self.auth_info = data[23:39]
            # 在这里设置当前为登录状态
            self.login_flag = True
            res = DrCOMResponse()
            res.msg = "已经连接上校园网络"
            return res

        elif data[0] == 0x05:
            if len(data) > 32:
                if data[32] == 0x31:
                    raise DrCOMException("Failure on login because the wrong username...")
                if data[32] == 0x33:
                    raise DrCOMException("Failure on login because the wrong password...")

        else:
            exception = DrCOMException("Receive unknown packages content...")
            exception.last_pkg = data
            raise exception

    def logout(self):
        """
        登出，仅测试了BISTU版本
        登出过程一共会有6个包，分3组，每组2个
        第一组同alive_pkg1的发送与确认
        第二组似乎是用于告知网关准备登出
        第三组会发送登出的详细信息包括用户名等
        """
        # 与alive_pkg1的最后两个字节相同
        pkg = b'\x01\x03'
        pkg += b'\x00\x00'
        pkg += b'\x0a'
        pkg += b'\x00' * 15

        data, address = self._send_package(pkg, (self.server_ip, 61440))

        if data[0:2] != b'\x02\x03':
            exception = DrCOMException("[DrCOM.logout]：Receive unknown packages content...")
            exception.last_pkg = data
            raise exception

        # 第三组
        pkg = self._make_logout_package()

        data, address = self._send_package(pkg, (self.server_ip, 61440))

        if data[0] != 0x04:
            exception = DrCOMException("[DrCOM.logout]：Receive unknown packages content...")
            exception.last_pkg = data
            raise exception

        self.login_flag = False
