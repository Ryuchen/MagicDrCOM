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
import threading

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
from drcom.main.excepts import MagicDrCOMException
from drcom.configs.settings import *


class DrCOMClient(object):

    def __init__(self, usr, pwd):
        self.usr = usr
        self.pwd = pwd

        self.salt = b""
        self.server_ip = ""
        self.auth_info = b""

        self._interrupt = False
        self.login_flag = False
        self.alive_flag = False

        self.platform = sys.platform

        self.__initialise__()

    @property
    def interrupt(self):
        return self._interrupt

    @interrupt.setter
    def interrupt(self, value):
        self._interrupt = value

    def __initialise__(self):
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
            Log(logging.ERROR, 10, "[DrCOM.__init__]：无法获取本机的NIC信息，请直接提交到该项目issues")
            raise DrCOMException("无法获取本机的NIC信息")

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.socket.settimeout(3)
        try:
            self.socket.bind(("", 61440))
        except socket.error:
            Log(logging.ERROR, 10, "[DrCOM.__init__]：无法绑定61440端口，请检查是否有其他进程占据了该端口")
            raise DrCOMException("无法绑定本机61440端口")

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
        while last_times > 0 and not self.interrupt:
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

        if self.interrupt:
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
            # 当收到的数据包没法识别的时候，标记当前状态已经为掉线状态
            Log(logging.ERROR, 40, "[DrCOM.send_alive_pkg1]：Receive unknown packages content: {}".format(data))
            self.alive_flag = False

    def send_alive_pkg2(self, num, key, cls):
        """
        发送类型二的心跳包
        :return:
        """
        response = 0
        pkg = self._make_alive_package(num=num, key=key, cls=cls)

        data, address = self._send_package(pkg, (self.server_ip, 61440))

        if data[0] == 0x07:
            Log(logging.DEBUG, 0, "[DrCOM.send_alive_pkg2]：Successful sending heartbeat package 2[{}]...".format(cls))
            response = data[16:20]
        else:
            # 当收到的数据包没法识别的时候，标记当前状态已经为掉线状态
            Log(logging.ERROR, 50, "[DrCOM.send_alive_pkg2]：Receive unknown packages content: {}".format(data))
            self.alive_flag = False

        return response

    def prepare(self):
        """
        获取服务器IP和Salt
        :return:
        """
        random_value = struct.pack("<H", int(time.time() + random.randint(0xF, 0xFF)) % 0xFFFF)
        pkg = b'\x01\x02' + random_value + b'\x0a' + b'\x00' * 15

        # 尝试目前已知的学校认证服务器地址
        for _ in [(SERVER_IP, 61440), ("1.1.1.1", 61440), ("202.1.1.1", 61440)]:
            data, address = self._send_package(pkg, _)

            # 未获取合理IP地址则进行下一个服务器地址尝试
            Log(logging.DEBUG, 0, "[DrCOM.prepare]：Receive PKG content: {}".format(data))
            if data[0:4] == b'\x02\x02' + random_value:
                self.server_ip = address[0]
                self.salt = data[4:8]
                Log(logging.DEBUG, 0, "[DrCOM.prepare]：Server IP: {}, Salt: {}".format(self.server_ip, self.salt))
                return
            else:
                Log(logging.ERROR, 20, "[DrCOM.prepare]：Receive unknown packages content: {}".format(data))

        if not self.server_ip or not self.salt:
            exception = DrCOMException("No Available Server...")
            exception.last_pkg = pkg
            raise exception

    def reset(self):
        """
        重置所有参数
        :return:
        """
        self.interrupt = False
        self.login_flag = False
        self.alive_flag = False

    def login(self):
        """
        登录到目标服务器方法
        :return:
        """
        pkg = self._make_login_package()

        data, address = self._send_package(pkg, (self.server_ip, 61440))

        Log(logging.DEBUG, 0, "[DrCOM.login]：Receive PKG content: {}".format(data))
        if data[0] == 0x04:
            self.auth_info = data[23:39]
            # 在这里设置当前为登录状态并且也处于在线状态
            self.login_flag = True
            self.alive_flag = True
            Log(logging.INFO, 0, "[DrCOM.login]：Successfully login to DrCOM Server...")
        elif data[0] == 0x05:
            if len(data) > 32:
                if data[32] == 0x31:
                    Log(logging.ERROR, 31, "[DrCOM.login]：Failure on login because the wrong username...")
                if data[32] == 0x33:
                    Log(logging.ERROR, 32, "[DrCOM.login]：Failure on login because the wrong password...")
        else:
            Log(logging.ERROR, 30, "[DrCOM.login]：Receive unknown packages content: {}".format(data))

        if not self.login_flag:
            exception = DrCOMException("Failure on login to DrCOM...")
            exception.last_pkg = pkg
            raise exception

    def keep_alive(self):
        num = 0
        key = b'\x00' * 4
        while self.alive_flag:
            try:
                self.send_alive_pkg1()
                key = self.send_alive_pkg2(num, key, cls=1)
                key = self.send_alive_pkg2(num, key, cls=3)
            except TimeoutException as exc:
                Log(logging.ERROR, 60, "[DrCOM.keep_alive]：" + exc.info)
                self.alive_flag = False
                break
            num = num + 2
            time.sleep(10)

    def logout(self):
        """
        登出，仅测试了BISTU版本
        登出过程一共会有6个包，分3组，每组2个
        第一组同alive_pkg1的发送与确认
        第二组似乎是用于告知网关准备登出
        第三组会发送登出的详细信息包括用户名等
        """
        # 第一组 初步判断是为了判断当前网络是否联通
        # 发送的数据包的最后两个字节可能有验证功能
        self.send_alive_pkg1()

        # 第二组 登出准备
        # 与alive_pkg1的最后两个字节相同
        pkg = b'\x01\x03'
        pkg += b'\x00\x00'
        pkg += b'\x0a'
        pkg += b'\x00' * 15

        data, address = self._send_package(pkg, (self.server_ip, 61440))

        if data[0:2] != b'\x02\x03':
            Log(logging.ERROR, 70, "[DrCOM.login]：Receive unknown packages content: {}".format(data))

        # 第三组
        pkg = self._make_logout_package()

        data, address = self._send_package(pkg, (self.server_ip, 61440))

        if data[0] == 0x04:
            self.login_flag = False
        else:
            Log(logging.ERROR, 71, "[DrCOM.logout]：Receive unknown packages content: {}".format(data))

        if self.login_flag:
            exception = DrCOMException("Failure on logout to DrCOM...")
            exception.last_pkg = pkg
            raise exception


class MagicDrCOMClient(object):

    def __init__(self):
        print("欢迎使用BISTU专版的第三方Dr.COM客户端")
        print("本项目目前由@Ryuchen进行开发和维护")
        print("如有任何问题欢迎在本项目的github页面提交issue")
        print("[https://github.com/Ryuchen/MagicDrCOM/issues]")

        self._usr = ""
        self._pwd = ""
        # self._login_flag = False
        self._alive_check = False
        self._relogin_flag = ReLoginFlag
        self._relogin_times = ReLoginTimes
        self._relogin_check = ReLoginCheck

        try:
            self._client = DrCOMClient(self._usr, self._pwd)
        except DrCOMException as exc:
            Log(logging.ERROR, 10, "[MagicDrCOMClient.__init__]：无法进行初始化：" + exc.info)
            raise MagicDrCOMException("请检查本机设置之后重试~")

    @property
    def username(self):
        return self._usr

    @username.setter
    def username(self, value):
        if value == "":
            raise MagicDrCOMException("账号未填写")
        self._usr = value
        self._client.usr = value

    @property
    def password(self):
        return self._pwd

    @password.setter
    def password(self, value):
        if value == "":
            raise MagicDrCOMException("密码未填写")
        self._pwd = value
        self._client.pwd = value

    # @property
    # def login_flag(self):
    #     return self._login_flag
    #
    # @login_flag.setter
    # def login_flag(self, value):
    #     self._login_flag = value

    @property
    def relogin_flag(self):
        return self._relogin_flag

    @relogin_flag.setter
    def relogin_flag(self, value):
        self._relogin_flag = value

    @property
    def relogin_times(self):
        return self._relogin_times

    @relogin_times.setter
    def relogin_times(self, value):
        self._relogin_times = value

    @property
    def relogin_check(self):
        return self._relogin_check

    @relogin_check.setter
    def relogin_check(self, value):
        self._relogin_check = value

    @property
    def status(self):
        if self._client.login_flag:
            if self._client.alive_flag:
                return ONLINE
            else:
                return DIEOUT
        else:
            return OFFLINE

    def _interval_loop(self, period, callback, args):
        """
        模拟事件循环，用来循环调用请求网站方法
        :param period: 间隔时间
        :param callback: 回调方法
        :param args: 参数
        :return:
        """
        try:
            while self._client.login_flag:
                time.sleep(period)
                callback(*args)
        except MagicDrCOMException:
            Log(logging.ERROR, 120, "[MagicDrCOM._auto_relogin]：超出最大重试次数！")

    def _set_interval(self, period, callback, *args):
        threading.Thread(target=self._interval_loop, args=(period, callback, args)).start()

    def _daemon(self):
        """
        判断网络连通性的方法
        Host: 114.114.114.114
        OpenPort: 53/tcp
        Service: domain (DNS/TCP)
        """
        try:
            socket.setdefaulttimeout(1)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("114.114.114.114", 53))
            Log(logging.INFO, 0, "[MagicDrCOM.check]：Successful connect to network...")
            return True
        except socket.error:
            if self.status == DIEOUT:
                self.relogin()

    def _login(self):
        if self._client.usr == "" or self._client.pwd == "":
            raise MagicDrCOMException("Please enter your username and password...")

        Log(logging.INFO, 0, "[MagicDrCOM.login]：Starting login...")
        try:
            self._client.prepare()
            self._client.login()
            keep_alive_thread = threading.Thread(target=self._client.keep_alive, args=())
            keep_alive_thread.start()
            Log(logging.INFO, 0, "[MagicDrCOM.login]：Successfully login to server...")
        except (DrCOMException, TimeoutException) as exc:
            raise MagicDrCOMException("Failure on login: " + exc.info)

    def login(self):
        """
        登录方法
        :return:
        """
        self._login()
        if self.relogin_flag:
            self._set_interval(self.relogin_check, self._daemon)
            Log(logging.INFO, 0, "[MagicDrCOM.login]：Starting network check daemon thread...")

    def relogin(self):
        self.relogin_times -= 1
        if self.relogin_times >= 0:
            Log(logging.WARNING, 0, "[MagicDrCOM._auto_relogin]：Starting relogin last %d times..." % self.relogin_times)
            self._client.logout()
            time.sleep(5)
            self._client.prepare()
            self._client.login()
        else:
            raise MagicDrCOMException("Maximum time reties...")

    def logout(self):
        Log(logging.INFO, 0, "[MagicDrCOM.logout]：Sending logout request to DrCOM Server")
        try:
            self._client.logout()
            self._client.interrupt = True
            Log(logging.INFO, 0, "[MagicDrCOM.logout]：Successful logout to DrCOM Server")
        except (DrCOMException, TimeoutException) as exc:
            raise MagicDrCOMException("Failure on logout: " + exc.info)

    def reset(self):
        self._client.reset()


# 用于命令行模式
if __name__ == '__main__':
    try:
        mc = MagicDrCOMClient()
        mc.username = USERNAME
        mc.password = PASSWORD
    except MagicDrCOMException:
        sys.exit(1)
    try:
        mc.login()
        user_input = ""
        while not user_input == "logout":
            print("登出请输入 logout ")
            user_input = input()  # 等待输入进行阻塞
        mc.logout()
        sys.exit(1)
    except KeyboardInterrupt as e:
        mc.logout()
        sys.exit(1)
