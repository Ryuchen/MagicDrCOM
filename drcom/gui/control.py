#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ==================================================
# Licensed under the GPLv3
# 本项目由@Ryuchen开发维护，使用Python3.7
# ==================================================

import sys
import time
import json

from PyQt5 import QtCore
from PyQt5.QtCore import QDir
from PyQt5.QtCore import QObject
from PyQt5.QtGui import QTextCursor

from drcom.gui.window import MainWindow
from drcom.main.client import MagicDrCOMClient


class MainWindowController:
    def __init__(self):
        self._window = MainWindow(self)
        sys.stdout = OutStream(out_signal=self.print_log)
        self._window.retryCheckBox.stateChanged.connect(self.set_relogin_flag)
        self._window.retryTimesSpinBox.valueChanged.connect(self.set_relogin_times)
        self._window.retryCheckSpinBox.valueChanged.connect(self.set_relogin_check)
        self._window.remPasswdCheckBox.stateChanged.connect(self.save_user_config)

        self._client = MagicDrCOMClient()
        if not self.load_user_config():
            self._window.retryCheckBox.setChecked(self._client.relogin_flag)
            self._window.retryTimesSpinBox.setValue(self._client.relogin_times)
            self._window.retryCheckSpinBox.setValue(self._client.relogin_check)
            self._window.remPasswdCheckBox.setChecked(True)
        self.update()

    @property
    def window(self):
        return self._window

    def set_relogin_flag(self):
        self._client.relogin_flag = self._window.retryCheckBox.isChecked()
        self.save_user_config()

    def set_relogin_times(self):
        self._client.relogin_times = self._window.retryTimesSpinBox.value()
        self.save_user_config()

    def set_relogin_check(self):
        self._client.relogin_check = self._window.retryCheckSpinBox.value()
        self.save_user_config()

    def login(self):
        self._client.reset()
        self._client.username = self._window.usernameLineEdit.text()
        self._client.password = self._window.passwordLineEdit.text()
        self.save_user_config()
        self._client.login()
        self.update()

    def logout(self):
        self._client.logout()
        time.sleep(3)
        self.update()

    def load_user_config(self):
        file_path = QDir.homePath()
        if sys.platform in ["linux", "darwin"]:
            file_path = file_path + "/.MagicDrCOM-gui.cfg"
        else:
            file_path = file_path + "\\.MagicDrCOM-gui.cfg"
        try:
            f = open(file_path, 'r')
            file_data = f.read()
            f.close()
        except FileNotFoundError:
            return False

        cfg_dict = json.loads(file_data)
        self._window.retryCheckBox.setChecked(cfg_dict["relogin_flag"])
        self._window.retryTimesSpinBox.setValue(cfg_dict["relogin_times"])
        self._window.retryCheckSpinBox.setValue(cfg_dict["relogin_check"])
        self._window.remPasswdCheckBox.setChecked(cfg_dict["rem_pwd"])
        if cfg_dict["rem_pwd"]:
            self._window.usernameLineEdit.setText(cfg_dict["usr"])
            self._window.passwordLineEdit.setText(cfg_dict["pwd"])
        return True

    def save_user_config(self):
        file_path = QDir.homePath()
        if sys.platform in ["linux", "darwin"]:
            file_path = file_path + "/.MagicDrCOM-gui.cfg"
        else:
            file_path = file_path + "\\.MagicDrCOM-gui.cfg"
        cfg_dict = {"rem_pwd": self._window.remPasswdCheckBox.isChecked(),
                    "relogin_flag": self._window.retryCheckBox.isChecked(),
                    "relogin_times": self._window.retryTimesSpinBox.value(),
                    "relogin_check": self._window.retryCheckSpinBox.value()}
        if self._window.remPasswdCheckBox.isChecked():
            cfg_dict["usr"] = self._window.usernameLineEdit.text()
            cfg_dict["pwd"] = self._window.passwordLineEdit.text()

        f = open(file_path, 'w')
        f.write(json.dumps(cfg_dict, sort_keys=True, indent=4))
        f.close()

    def update(self):
        if not self._client.status:
            self._window.usernameLineEdit.setEnabled(True)
            self._window.passwordLineEdit.setEnabled(True)
            self._window.remPasswdCheckBox.setEnabled(True)
            self._window.retryCheckBox.setEnabled(True)
            self._window.retryTimesSpinBox.setEnabled(True)
            self._window.retryCheckSpinBox.setEnabled(True)
            self._window.loginButton.setText("登录")
            try:
                self._window.loginButton.clicked.disconnect()
            except Exception:
                pass
            self._window.loginButton.clicked.connect(self.login)
        else:
            self._window.usernameLineEdit.setEnabled(False)
            self._window.passwordLineEdit.setEnabled(False)
            self._window.remPasswdCheckBox.setEnabled(False)
            self._window.retryCheckBox.setEnabled(False)
            self._window.retryTimesSpinBox.setEnabled(False)
            self._window.retryCheckSpinBox.setEnabled(False)
            self._window.loginButton.setText("登出")
            try:
                self._window.loginButton.clicked.disconnect()
            except Exception:
                pass
            self._window.loginButton.clicked.connect(self.logout)

    def print_log(self, string):
        self._window.logTextBrowser.insertPlainText(string)
        self._window.logTextBrowser.moveCursor(QTextCursor.End)
        self._window.logTextBrowser.horizontalScrollBar().setValue(0)


class OutStream(QObject):
    out_signal = QtCore.pyqtSignal(str)

    def write(self, text):
        self.out_signal.emit(str(text))
