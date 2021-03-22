# !/usr/bin/env python
# -*- coding: utf-8 -*-
# ========================================================
# @Author: Ryuchen
# @Time: 2020/09/09-19:34
# @Site: https://ryuchen.github.io
# @Contact: chenhaom1993@hotmail.com
# @Copyright: Copyright (C) 2019-2020 MagicDrCOM.
# ========================================================
"""
...
DocString Here
...
"""
import time
import socket

from PySide2 import QtCore

from drcom.main.excepts import DrCOMException
from drcom.main.excepts import TimeoutException


class ExecSignal(QtCore.QObject):
    """
    Defines the signals available from a running worker thread.

    Supported signals are:

    state
        `` finish the job

    error
        `tuple` (info, pcap, traceback.format_exc())

    result
        `object` data returned from processing, anything
    """
    state = QtCore.Signal()
    error = QtCore.Signal(object)
    result = QtCore.Signal(object)


class ClientCheckThreads(QtCore.QRunnable):
    """
    Execute the Dr.COM network status checking job
    """

    def __init__(self, client, *args, **kwargs):
        super(ClientCheckThreads, self).__init__()

        self.client = client

        # Store constructor arguments
        self.args = args
        self.kwargs = kwargs

        self.signals = ExecSignal()

    @QtCore.Slot()
    def run(self):
        try:
            result = self.client.prepare(*self.args, **self.kwargs)
            self.signals.result.emit(result)  # Return the result of the processing
        except DrCOMException as e:
            self.signals.error.emit(e)


class ClientLoginThreads(QtCore.QRunnable):
    """
    Execute the Dr.COM login job
    """

    def __init__(self, client, *args, **kwargs):
        super(ClientLoginThreads, self).__init__()

        self.client = client

        # Store constructor arguments
        self.args = args
        self.kwargs = kwargs

        self.signals = ExecSignal()

    @QtCore.Slot()
    def run(self):
        try:
            result = self.client.login(*self.args, **self.kwargs)
            self.signals.result.emit(result)  # Return the result of the processing
        except DrCOMException as e:
            self.signals.error.emit(e)


class ClientAliveThreads(QtCore.QRunnable):
    """
    Execute the Dr.COM keep alive job
    """

    def __init__(self, client, *args, **kwargs):
        super(ClientAliveThreads, self).__init__()

        self.client = client

        # Store constructor arguments
        self.args = args
        self.kwargs = kwargs

        self.signals = ExecSignal()

    @QtCore.Slot()
    def run(self):
        try:
            self.client.send_alive_pkg1()
            self.client.key = self.client.send_alive_pkg2(self.client.num, self.client.key, cls=1)
            self.client.key = self.client.send_alive_pkg2(self.client.num, self.client.key, cls=3)
        except (TimeoutException, DrCOMException) as e:
            self.signals.error.emit(e)
            self.client.alive_flag = False
        else:
            self.client.alive_flag = True
            self.client.num = self.client.num + 2
        finally:
            self.signals.state.emit()


class ClientRetryThreads(QtCore.QRunnable):
    """
    Execute the Dr.COM retry login job
    """

    def __init__(self, client, *args, **kwargs):
        super(ClientRetryThreads, self).__init__()

        self.client = client

        # Store constructor arguments
        self.args = args
        self.kwargs = kwargs

        self.signals = ExecSignal()

    @QtCore.Slot()
    def run(self):
        try:
            socket.setdefaulttimeout(1)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("114.114.114.114", 53))
        except (TimeoutException, DrCOMException) as e:
            self.signals.error.emit(e)
            self.client.alive_flag = False
        else:
            self.client.alive_flag = True
            self.client.num = self.client.num + 2
        finally:
            self.signals.state.emit()
