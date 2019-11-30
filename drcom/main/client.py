#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ==================================================
# Licensed under the GPLv3
# 本项目由@Ryuchen开发维护，使用Python3.7
# ==================================================

import sys
import time
import uuid
import struct
import socket
import random
import requests
import threading

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

        self.login_flag = False
        self.keep_alive_flag = False

        self.platform = sys.platform

        self.__initialise__()

    def __initialise__(self):
        """
        尝试绑定当前的主机端口
        :return:
        """
        if LOCAL_MAC == "":  # 如果没有指定本机MAC，尝试自动获取
            self.mac = bytes().fromhex(LOCAL_MAC)
        else:
            self.mac = bytes().fromhex(uuid.UUID(int=uuid.getnode()).hex[-12:])

        self.host_name = socket.getfqdn(socket.gethostname())

        try:
            if LOCAL_IP:  # 如果没有指定本机IP，尝试自动获取
                self.ip = LOCAL_IP
            else:
                self.ip = socket.gethostbyname(self.host_name)
        except socket.gaierror:
            Log(logging.ERROR, 10, "[DrCOM.__init__]：无法获取本机IP地址，请手动填写IP！")
            raise DrCOMException("无法获取本机IP地址")

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.socket.settimeout(3)
        try:
            self.socket.bind(("", 61440))
        except socket.error:
            Log(logging.ERROR, 10, "[DrCOM.__init__]：无法绑定61440端口，请检查您的网络！")
            raise DrCOMException("无法绑定本机61440端口")

    def _make_login_package(self):
        """
        构造登陆包
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
        data += "WINDOWS".encode('ascii').ljust(32, b'\x00')  # (182:213 32) 操作系统名称
        data += b'\x00' * 96  # (214:309 96) 未知 不同客户端有差异，BISTU版此字段包含一段识别符，但不影响登陆
        data += AUTH_VERSION  # (310:311 2)
        data += b'\x02\x0c'  # (312:313 2) 未知
        data += checksum(data + b'\x01\x26\x07\x11\x00\x00' + self.mac)  # (314:317 4) 校验和
        data += b'\x00\x00'  # (318:319 2) 未知
        data += self.mac  # (320:325 6) 本机MAC
        data += b'\x00'  # (326:326 1) auto logout / default: False
        data += b'\x00'  # (327:327 1) broadcast mode / default : False
        data += b'\x17\x77'  # (328:329 2) 未知 不同客户端有差异
        return data

    def _make_alive_package(self, num, key, cls):
        # 构造心跳包
        data = b'\x07'  # (0:0 1) 未知
        data += int2hex_str(num % 256)  # (1:1 1) 编号
        data += b'\x28\x00\x0b'  # (2:4 3) 未知
        data += int2hex_str(cls)  # (5:5 1) 类型
        if num == 0:  # (6:7 2) BISTU版此字段不会变化
            data += b'\xdc\x02'
        else:
            data += KEEP_ALIVE_VERSION
        data += b'\x2f\x79'  # (8:9 2) 未知 每个包会有变化
        data += b'\x00' * 6  # (10:15 6) 未知
        data += key  # (16:19 4)
        data += b'\x00' * 4  # (20:23 4) 未知
        # data += struct.pack("!H",0xdc02)  # 未验证

        if cls == 1:
            data += b'\x00' * 16  # (24:39 16) 未知
        if cls == 3:  # 未验证
            foo = b''.join([int2hex_str(int(i)) for i in self.ip.split('.')])  # host_ip
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
        data += self.usr.encode('ascii').ljust(36, b'\x00')  # (20:55 36) 用户名
        data += CONTROL_CHECK_STATUS  # (56:56 1) 控制检查状态
        data += ADAPTER_NUMBER  # (57:57 1) 适配器编号？
        # (58:63 6) (MD5_A xor MAC)
        data += int2hex_str(int.from_bytes(data[4:10], 'big') ^ int.from_bytes(self.mac, 'big')).rjust(6, b'\x00')
        data += self.auth_info
        return data

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

        pkg_send_flag = False
        last_times = ReTryTimes
        while last_times > 0:
            last_times = last_times - 1
            Log(logging.DEBUG, 0, "[DrCOM.send_alive_pkg1]：Sending heartbeat package type 1...")
            clean_socket_buffer(self.socket)
            self.socket.sendto(pkg, (self.server_ip, 61440))
            try:
                data, address = self.socket.recvfrom(1024)
            except socket.timeout:
                Log(logging.WARNING, 0, "[DrCOM.send_alive_pkg1]：Timeout continue to retry [{}]...".format(last_times))
                continue

            if data[0] == 0x07:
                Log(logging.DEBUG, 0, "[DrCOM.send_alive_pkg1]：Successfully sending heartbeat package type 1...")
                pkg_send_flag = True
                break
            else:
                Log(logging.ERROR, 40, "[DrCOM.send_alive_pkg1]：Receive unknown packages...")

        if not pkg_send_flag:
            exception = TimeoutException("[DrCOM.send_alive_pkg1]：Failure on sending heartbeat package type 1...")
            exception.last_pkg = pkg
            raise exception

    def send_alive_pkg2(self, num, key, cls):
        """
        发送类型二的心跳包
        :return:
        """
        pkg = self._make_alive_package(num=num, key=key, cls=cls)

        response = ""
        pkg_send_flag = False
        last_times = ReTryTimes
        while last_times > 0:
            last_times = last_times - 1
            Log(logging.DEBUG, 0, "[DrCOM.send_alive_pkg2]：Sending heartbeat package type 2 class {}...".format(cls))
            clean_socket_buffer(self.socket)
            self.socket.sendto(pkg, (self.server_ip, 61440))
            try:
                data, address = self.socket.recvfrom(1024)
            except socket.timeout:
                Log(logging.WARNING, 0, "[DrCOM.send_alive_pkg2]：Timeout continue to retry [{}]...".format(last_times))
                continue

            if data[0] == 0x07:
                Log(logging.DEBUG, 0, "[DrCOM.send_alive_pkg2]：Successfully sending heartbeat package type 2 class {}...".format(cls))
                response = data[16:20]
                pkg_send_flag = True
                break
            else:
                Log(logging.ERROR, 50, "[DrCOM.send_alive_pkg2]：Receive unknown packages...")

        if not pkg_send_flag:
            exception = TimeoutException("[DrCOM.send_alive_pkg1]：Failure on sending heartbeat package type 1...")
            exception.last_pkg = pkg
            raise exception

        return response

    def prepare(self):
        """
        获取服务器IP和Salt
        :return:
        """
        random_value = struct.pack("<H", int(time.time() + random.randint(0xF, 0xFF)) % 0xFFFF)
        pkg = b'\x01\x02' + random_value + b'\x0a' + b'\x00' * 15

        # 查看发送包内容
        Log(logging.DEBUG, 0, "[DrCOM.prepare]：Sending PKG content: {}".format(pkg))

        for _ in [(SERVER_IP, 61440), ("1.1.1.1", 61440), ("202.1.1.1", 61440)]:
            last_times = ReTryTimes
            while last_times > 0:
                last_times = last_times - 1
                Log(logging.INFO, 0, "[DrCOM.prepare]：Trying to verify the Server IP and get the Salt...")
                clean_socket_buffer(self.socket)
                self.socket.sendto(pkg, (SERVER_IP, 61440))
                # 尝试获取服务器的IP地址和后续加密的Salt
                # 如果服务器未返回信息则进行重试
                try:
                    data, address = self.socket.recvfrom(1024)
                except socket.timeout:
                    Log(logging.WARNING, 0, "[DrCOM.prepare]：Timeout continue to retry [{}]...".format(last_times))
                    continue
                # 如果服务器返回数据则进行跳出
                # 未获取合理IP地址则进行下一个服务器地址尝试
                Log(logging.DEBUG, 0, "[DrCOM.prepare]：Receive PKG content: {}".format(data))
                if data[0:4] == b'\x02\x02' + random_value:
                    self.server_ip = address[0]
                    self.salt = data[4:8]
                    break
                else:
                    Log(logging.ERROR, 20, "[DrCOM.prepare]：Receive unknown packages...")
                    break
            # 如果已经获取到正常的服务器IP和Salt则跳出服务器列表尝试
            if self.server_ip and self.salt:
                break
            else:
                continue

        if not self.server_ip or not self.salt:
            exception = DrCOMException("Can't connect to Server and fetch Salt...")
            exception.last_pkg = pkg
            raise exception

    def login(self):
        """
        登录
        :return:
        """
        pkg = self._make_login_package()

        # 查看登录包内容
        Log(logging.DEBUG, 0, "[DrCOM.login]：Sending PKG content: {}".format(pkg))

        last_times = ReTryTimes
        while last_times > 0:
            last_times = last_times - 1
            Log(logging.INFO, 0, "[DrCOM.login]：Sending Login request to Server...")
            clean_socket_buffer(self.socket)
            self.socket.sendto(pkg, (self.server_ip, 61440))
            try:
                data, address = self.socket.recvfrom(1024)
            except socket.timeout:
                Log(logging.WARNING, 0, "[DrCOM.login]：Timeout continue to retry [{}]...".format(last_times))
                continue

            Log(logging.DEBUG, 0, "[DrCOM.prepare]：Receive PKG content: {}".format(data))
            if data[0] == 0x04:
                self.auth_info = data[23:39]
                self.login_flag = True
                Log(logging.INFO, 0, "[DrCOM.login]：Successfully login to DrCOM Server...")
                break
            elif data[0] == 0x05:
                if len(data) > 32:
                    if data[32] == 0x31:
                        Log(logging.ERROR, 31, "[DrCOM.login]：Failure on login because the wrong username...")
                    if data[32] == 0x33:
                        Log(logging.ERROR, 32, "[DrCOM.login]：Failure on login because the wrong password...")
                break
            else:
                Log(logging.ERROR, 30, "[DrCOM.login]：Receive unknown packages...")

        if not self.auth_info or not self.login_flag:
            exception = DrCOMException("Failure on login to DrCOM...")
            exception.last_pkg = pkg
            raise exception

    def keep_alive(self):
        num = 0
        key = b'\x00' * 4
        while self.login_flag:
            self.keep_alive_flag = True
            try:
                self.send_alive_pkg1()
                key = self.send_alive_pkg2(num, key, cls=1)
                key = self.send_alive_pkg2(num, key, cls=3)
            except TimeoutException as exc:
                Log(logging.ERROR, 60, "[DrCOM.keep_alive]：" + exc.info)
                break
            num = num + 2
            time.sleep(20)
        self.keep_alive_flag = False

    def logout(self):
        """
        登出，仅测试了BISTU版本
        登出过程一共会有6个包，分3组，每组2个
        第一组同alive_pkg1的发送与确认
        第二组似乎是用于告知网关准备登出
        第三组会发送登出的详细信息包括用户名等
        """
        # 第一组 初步判断是为了判断当前网络是否联通
        self.send_alive_pkg1()  # 发送的数据包的最后两个字节可能有验证功能

        # 第二组 登出准备
        pkg = b'\x01\x03'
        pkg += b'\x00\x00'  # 与alive_pkg1的最后两个字节相同
        pkg += b'\x0a'
        pkg += b'\x00' * 15

        # 查看登出包内容
        Log(logging.DEBUG, 0, "[DrCOM.logout]：Sending PKG content: {}".format(pkg))

        last_times = ReTryTimes
        while last_times > 0:
            last_times = last_times - 1
            Log(logging.INFO, 0, "[DrCOM.logout]：Try to logout current account...")
            clean_socket_buffer(self.socket)
            self.socket.sendto(pkg, (self.server_ip, 61440))
            try:
                data, address = self.socket.recvfrom(1024)
            except socket.timeout:
                Log(logging.WARNING, 0, "[DrCOM.logout]：Timeout continue to retry [{}]...".format(last_times))
                continue

            Log(logging.DEBUG, 0, "[DrCOM.prepare]：Receive PKG content: {}".format(data))
            if data[0:2] == b'\x02\x03':
                break
            else:
                Log(logging.ERROR, 70, "[DrCOM.logout]：Receive unknown packages...")

        # 第三组
        pkg = self._make_logout_package()

        # 查看登出包内容
        Log(logging.DEBUG, 0, "[DrCOM.logout]：Sending PKG content: {}".format(pkg))

        last_times = ReTryTimes
        while last_times > 0:
            last_times = last_times - 1
            Log(logging.INFO, 0, "[DrCOM.logout]：Sending Logout request to Server...")
            clean_socket_buffer(self.socket)
            self.socket.sendto(pkg, (self.server_ip, 61440))
            try:
                data, address = self.socket.recvfrom(1024)
            except socket.timeout:
                Log(logging.WARNING, 0, "[DrCOM.logout]：Timeout continue to retry [{}]...".format(last_times))
                continue

            Log(logging.DEBUG, 0, "[DrCOM.prepare]：Receive PKG content: {}".format(data))
            if data[0] == 0x04:
                self.login_flag = False
                break
            else:
                Log(logging.ERROR, 71, "[DrCOM.logout]：Receive unknown packages...")

        if self.login_flag:
            exception = DrCOMException("Failure on logout to DrCOM...")
            exception.last_pkg = pkg
            raise exception


class MagicDrCOMClient(object):

    def __init__(self):
        print("欢迎使用专为北信科开发的MagicDrCOMClient客户端")
        print("本项目由@Ryuchen[https://github.com/ryuchen]开发维护")
        print("目前为测试版，如有任何问题欢迎在本项目的github页面提交issue")

        self._usr = ""
        self._pwd = ""
        self._login_flag = False
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

    @property
    def login_flag(self):
        return self._login_flag

    @login_flag.setter
    def login_flag(self, value):
        self._login_flag = value

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
            if self._client.keep_alive_flag:
                return "online"
            else:
                return "timeout"
        else:
            return "offline"

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

    def set_interval(self, period, callback, *args):
        threading.Thread(target=self._interval_loop, args=(period, callback, args)).start()

    def _login(self):
        if self._client.usr == "" or self._client.pwd == "":
            raise MagicDrCOMException("Please remember enter your username and password...")

        Log(logging.INFO, 0, "[MagicDrCOM.login]：Starting login")
        try:
            self._client.prepare()
            self._client.login()
            keep_alive_thread = threading.Thread(target=self._client.keep_alive, args=())
            keep_alive_thread.start()
            Log(logging.INFO, 0, "[MagicDrCOM.login]：Successfully login to server...")
        except DrCOMException as exc:
            Log(logging.ERROR, 110, "[MagicDrCOM.login]：Failure on login: " + exc.info)

    def login(self):
        """
        登录方法
        :return:
        """
        self._login()
        if self.relogin_flag:
            self.set_interval(self.relogin_check, self.daemon)
            Log(logging.INFO, 0, "[MagicDrCOM.login]：Starting network daemon thread...")

    def daemon(self):
        """
        判断网络连通性的方法
        :return:
        """
        try:
            res = requests.get('https://www.baidu.com/', timeout=1)
            if res.status_code == 200:
                Log(logging.INFO, 0, "[MagicDrCOM.check]：Successfully connect to network...")
        except Exception:
            if self.login_flag:
                self.relogin()

    def relogin(self):
        self.relogin_times -= 1
        if self.relogin_times >= 0:
            Log(logging.WARNING, 0, "[MagicDrCOM._auto_relogin]：Starting relogin last %d times..." % self.relogin_times)
            self._client.login()
        else:
            raise MagicDrCOMException("Maximum reties...")

    def logout(self):
        if self._client.usr == "" or self._client.pwd == "":
            raise MagicDrCOMException("Please remember enter your username and password...")

        if self.status == "offline":
            return

        Log(logging.INFO, 0, "[MagicDrCOM.logout]：Sending logout request to DrCOM Server")
        try:
            self._client.logout()
            Log(logging.INFO, 0, "[MagicDrCOM.logout]：Successfully logout to DrCOM Server")
        except DrCOMException as exc:
            Log(logging.ERROR, 130, "[MagicDrCOM.logout]：" + exc.info)


# 用于命令行模式
if __name__ == '__main__':
    try:
        mc = MagicDrCOMClient()
        mc.username = USERNAME
        mc.password = PASSWORD
        mc.login_flag = True
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
