#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ==================================================
# Licensed under the GPLv3
# 本项目由@Ryuchen开发维护，使用Python3.7
# ==================================================

import os
import sys
import json
import time
import socket

from drcom.main.client import DrCOMClient
from drcom.main.excepts import DrCOMException
from drcom.main.excepts import TimeoutException
from PySide2 import QtCore, QtGui, QtWidgets


class QHLine(QtWidgets.QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QtWidgets.QFrame.HLine)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.setFixedHeight(3)


class QVLine(QtWidgets.QFrame):
    def __init__(self):
        super(QVLine, self).__init__()
        self.setFrameShape(QtWidgets.QFrame.VLine)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.setFixedWidth(3)


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()
        self._set_window_UI()
        self._load_user_config()

        self.client = None

        self.alive_flag = False
        self.alive_Timer = QtCore.QTimer()
        self.alive_interval = 10 * 1000
        self.retry_Timer = QtCore.QTimer()
        self.retry_interval = 10 * 1000

        try:
            self.client = DrCOMClient()
            self.update()
        except DrCOMException as e:
            self.logger("[Magic-Dr.COM::__init__]: {}".format(e.info))
        else:
            self.logger("[Magic-Dr.COM::__init__]: Successful initialise...")

    def _set_window_UI(self):
        self.setObjectName("MainWindow")
        self.setWindowTitle("Github@Ryuchen")
        self.setWindowFlags(QtGui.Qt.WindowCloseButtonHint)
        self._set_center_position()
        self._set_central_widget()

    def _set_center_position(self):
        availableWidth = QtWidgets.QDesktopWidget().width()
        availableHeight = QtWidgets.QDesktopWidget().height()

        # 计算出窗口左上角的坐标
        x = (availableWidth - 280) / 2
        y = (availableHeight - 360) / 2
        self.setGeometry(QtCore.QRect(x, y, 280, 350))
        self.setFixedSize(280, 350)  # cannot resize window size

    def _set_central_widget(self):
        centralWidget = QtWidgets.QWidget()
        centralWidget.setObjectName("CentralWidget")
        centralWidgetLayout = QtWidgets.QVBoxLayout()
        centralWidgetLayout.addWidget(self._set_description_widget())
        centralWidgetLayout.addWidget(QHLine())
        centralWidgetLayout.addWidget(self._set_loginForm_widget())
        centralWidgetLayout.addWidget(self._set_optionForm_widget())
        centralWidgetLayout.addSpacing(40)
        centralWidgetLayout.setMargin(2)
        centralWidgetLayout.setAlignment(QtGui.Qt.AlignCenter)
        centralWidget.setLayout(centralWidgetLayout)
        self.setCentralWidget(centralWidget)

    @staticmethod
    def _set_description_widget():
        description = QtWidgets.QWidget()
        description.setObjectName("DescriptionWidget")
        description.setFixedSize(280, 50)
        descriptionWidgetLayout = QtWidgets.QVBoxLayout()
        descriptionWidgetLayout.addSpacing(8)
        descriptionWidgetLayout.setMargin(4)
        title = QtWidgets.QLabel("Magic-Dr.COM(锐捷)客户端")
        title.setObjectName("DescriptionTitle")
        title.setStyleSheet("""
            QLabel#DescriptionTitle {
                font: 16px;
            }
        """)
        title.setFixedSize(280, 24)
        title.setAlignment(QtGui.Qt.AlignCenter)

        subTitle = QtWidgets.QLabel("<a href='https://github.com/Ryuchen/MagicDrCOM'>Author@Ryuchen</a>")
        subTitle.setOpenExternalLinks(True)
        subTitle.setObjectName("DescriptionSubTitle")
        subTitle.setStyleSheet("""
            QLabel#DescriptionSubTitle {
                font: 12px;
            }
        """)
        title.setFixedSize(280, 18)
        subTitle.setAlignment(QtGui.Qt.AlignCenter)

        descriptionWidgetLayout.addWidget(title)
        descriptionWidgetLayout.addWidget(subTitle)
        description.setLayout(descriptionWidgetLayout)
        return description

    def _set_loginForm_widget(self):
        loginForm = QtWidgets.QWidget()
        loginForm.setObjectName("LoginFormWidget")
        loginForm.setFixedSize(280, 80)
        loginFormLayout = QtWidgets.QFormLayout()
        loginFormLayout.setMargin(0)
        loginFormLayout.setContentsMargins(50, 20, 50, 0)

        self.usrLineEdit = QtWidgets.QLineEdit()
        self.usrLineEdit.setObjectName("usrLineEdit")
        loginFormLayout.addRow(self.tr("学号: "), self.usrLineEdit)

        self.pwdLineEdit = QtWidgets.QLineEdit()
        self.pwdLineEdit.setObjectName("pwdLineEdit")
        self.pwdLineEdit.setEchoMode(QtWidgets.QLineEdit.Password)
        loginFormLayout.addRow(self.tr("密码: "), self.pwdLineEdit)

        loginFormLayout.setLabelAlignment(QtGui.Qt.AlignCenter)
        loginForm.setLayout(loginFormLayout)
        return loginForm

    def _set_optionForm_widget(self):
        optionForm = QtWidgets.QWidget()
        optionForm.setObjectName("OptionFormWidget")
        optionForm.setFixedSize(280, 140)
        optionFormLayout = QtWidgets.QVBoxLayout()
        optionFormLayout.setMargin(0)
        optionFormLayout.setContentsMargins(0, 0, 0, 0)
        optionFormLayout.setAlignment(QtGui.Qt.AlignCenter)

        checkBoxGroup = QtWidgets.QWidget()
        checkBoxGroup.setObjectName("CheckBoxGroup")
        checkBoxGroupLayout = QtWidgets.QHBoxLayout()
        checkBoxGroupLayout.setMargin(0)
        checkBoxGroupLayout.setAlignment(QtGui.Qt.AlignJustify)
        self.retryCheckBox = QtWidgets.QCheckBox("断线重连")
        self.retryCheckBox.setObjectName("RetryCheckBox")
        checkBoxGroupLayout.addWidget(self.retryCheckBox)
        checkBoxGroupLayout.addSpacing(10)
        self.remPwdCheckBox = QtWidgets.QCheckBox("记住密码")
        self.remPwdCheckBox.setObjectName("RemPwdCheckBox")
        checkBoxGroupLayout.addWidget(self.remPwdCheckBox)
        checkBoxGroup.setLayout(checkBoxGroupLayout)
        optionFormLayout.addWidget(checkBoxGroup)

        retryCheck = QtWidgets.QWidget()
        retryCheck.setObjectName("RetryCheck")
        retryCheckLayout = QtWidgets.QHBoxLayout()
        retryCheckLayout.setMargin(4)
        retryCheckLayout.setContentsMargins(0, 0, 0, 0)
        retryCheckLayout.setAlignment(QtGui.Qt.AlignCenter)
        retryCheckLabel = QtWidgets.QLabel("检查时间")
        retryCheckLabel.setObjectName("RetryCheckLabel")
        retryCheckLayout.addWidget(retryCheckLabel)
        self.retryCheckSpinBox = QtWidgets.QSpinBox()
        self.retryCheckSpinBox.setObjectName("RetryCheckSpinBox")
        self.retryCheckSpinBox.setFixedWidth(80)
        self.retryCheckSpinBox.setMinimum(10)
        self.retryCheckSpinBox.setMaximum(120)
        retryCheckLayout.addWidget(self.retryCheckSpinBox)
        retryCheckLayout.addWidget(QtWidgets.QLabel("秒"))
        retryCheck.setLayout(retryCheckLayout)
        optionFormLayout.addWidget(retryCheck)

        retryTimes = QtWidgets.QWidget()
        retryTimes.setObjectName("RetryTimes")
        retryTimesLayout = QtWidgets.QHBoxLayout()
        retryTimesLayout.setMargin(4)
        retryTimesLayout.setContentsMargins(0, 0, 0, 0)
        retryTimesLayout.setAlignment(QtGui.Qt.AlignCenter)
        retryTimesLabel = QtWidgets.QLabel("重试次数")
        retryTimesLabel.setObjectName("RetryTimesLabel")
        retryTimesLayout.addWidget(retryTimesLabel)
        self.retryTimesSpinBox = QtWidgets.QSpinBox()
        self.retryTimesSpinBox.setObjectName("RetryTimesSpinBox")
        self.retryTimesSpinBox.setFixedWidth(80)
        self.retryTimesSpinBox.setMinimum(3)
        self.retryTimesSpinBox.setMaximum(10)
        retryTimesLayout.addWidget(self.retryTimesSpinBox)
        retryTimesLayout.addWidget(QtWidgets.QLabel("次"))
        retryTimes.setLayout(retryTimesLayout)
        optionFormLayout.addWidget(retryTimes)

        optionFormLayout.addSpacing(10)

        self.loginButton = QtWidgets.QPushButton("登录")
        self.loginButton.setObjectName("LoginButton")
        self.loginButton.clicked.connect(self.login)
        optionFormLayout.addWidget(self.loginButton)

        optionFormLayout.addSpacing(30)

        optionForm.setLayout(optionFormLayout)
        return optionForm

    def _load_user_config(self):
        currentPath = QtCore.QDir.homePath()
        if sys.platform in ["linux", "darwin"]:
            settingPath = os.path.join(currentPath, ".MagicDrCOM-gui.cfg")
        else:
            settingPath = os.path.join(currentPath, ".MagicDrCOM-gui.cfg")

        if not os.path.exists(settingPath):
            return

        with open(settingPath, "r") as userSetting:
            setting = json.loads(userSetting.read())
            self.retryTimesSpinBox.setValue(setting["relogin_times"])
            self.retryCheckSpinBox.setValue(setting["relogin_check"])
            self.retryCheckBox.setChecked(setting["relogin_flag"])
            self.remPwdCheckBox.setChecked(setting["rem_pwd"])
            if setting["rem_pwd"]:
                self.usrLineEdit.setText(setting["usr"])
                self.pwdLineEdit.setText(setting["pwd"])

    def _save_user_config(self):
        currentPath = QtCore.QDir.homePath()
        if sys.platform in ["linux", "darwin"]:
            settingPath = os.path.join(currentPath, ".MagicDrCOM-gui.cfg")
        else:
            settingPath = os.path.join(currentPath, ".MagicDrCOM-gui.cfg")

        setting = {"rem_pwd": self.remPwdCheckBox.isChecked(),
                   "relogin_flag": self.retryCheckBox.isChecked(),
                   "relogin_times": self.retryTimesSpinBox.value(),
                   "relogin_check": self.retryCheckSpinBox.value()}
        if self.remPwdCheckBox.isChecked():
            setting["usr"] = self.usrLineEdit.text()
            setting["pwd"] = self.pwdLineEdit.text()

        with open(settingPath, 'w') as userSetting:
            userSetting.write(json.dumps(setting, sort_keys=True, indent=4))

    def _keep_alive(self):
        self.logger("{}: Sending heartbeat package".format(time.strftime("%m-%d %H:%M:%S", time.localtime())))
        try:
            self.client.send_alive_pkg1()
            self.client.key = self.client.send_alive_pkg2(self.client.num, self.client.key, cls=1)
            self.client.key = self.client.send_alive_pkg2(self.client.num, self.client.key, cls=3)
        except (TimeoutException, DrCOMException) as e:
            self.logger(e.info)
            self.alive_flag = False
        else:
            self.alive_flag = True
        self.client.num = self.client.num + 2

    def _retry_login(self):
        """
        判断网络连通性的方法
        Host: 114.114.114.114
        OpenPort: 53/tcp
        Service: domain (DNS/TCP)
        """
        try:
            socket.setdefaulttimeout(1)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("114.114.114.114", 53))
            return True
        except socket.error:
            self.logger("[Magic-Dr.COM::_retry_login]: Network connection seems broken...")
            self.alive_Timer.stop()
            self.logout()
            self.login()
            self.alive_Timer.start(self.alive_interval)

    def login(self):
        if not self.client:
            self.info("<h4>当前无法进行登录</h4><p>初始化未完成，请重启该程序进行重试~~~</p>")
            return
        self.client.usr = self.usrLineEdit.text()
        self.client.pwd = self.pwdLineEdit.text()
        try:
            self.client.prepare()
            self.client.login()
            self._keep_alive()
            # 启动心跳Timer
            self.alive()
            if self.retryCheckBox.isChecked():
                # 启动守护Timer
                self.retry()
            self._save_user_config()
        except (DrCOMException, TimeoutException) as e:
            self.logger(e.info)
        else:
            self.logger("[Magic-Dr.COM::login]: Successful login to server...")
        self.update()

    def alive(self):
        self.alive_Timer.timeout.connect(self._keep_alive)
        self.alive_Timer.start(self.alive_interval)

    def retry(self):
        self.retry_Timer.timeout.connect(self._retry_login)
        self.retry_Timer.start(self.retryCheckSpinBox.value() * 1000)

    def logout(self):
        if self.alive_Timer.isActive():
            self.alive_Timer.stop()
        if self.retry_Timer.isActive():
            self.retry_Timer.stop()
        try:
            self.client.logout()
        except (DrCOMException, TimeoutException) as e:
            self.logger(e.info)
        else:
            self.logger("[Magic-Dr.COM::login]: Successful logout to server...")
        self.update()

    def update(self):
        if self.client:
            if not self.client.login_flag:
                self.usrLineEdit.setEnabled(True)
                self.pwdLineEdit.setEnabled(True)
                self.remPwdCheckBox.setEnabled(True)
                self.retryCheckBox.setEnabled(True)
                self.retryTimesSpinBox.setEnabled(True)
                self.retryCheckSpinBox.setEnabled(True)
                self.loginButton.setText("登录")
                self.loginButton.clicked.disconnect()
                self.loginButton.clicked.connect(self.login)
            else:
                self.usrLineEdit.setEnabled(False)
                self.pwdLineEdit.setEnabled(False)
                self.remPwdCheckBox.setEnabled(False)
                self.retryCheckBox.setEnabled(False)
                self.retryTimesSpinBox.setEnabled(False)
                self.retryCheckSpinBox.setEnabled(False)
                self.loginButton.setText("注销")
                self.loginButton.clicked.disconnect()
                self.loginButton.clicked.connect(self.logout)
            QtWidgets.QApplication.processEvents()

    def logger(self, msg):
        self.statusBar().clearMessage()
        self.statusBar().showMessage(msg)
        QtWidgets.QApplication.processEvents()

    @staticmethod
    def info(msg):
        message = QtWidgets.QMessageBox()
        message.setIcon(QtWidgets.QMessageBox.Information)
        message.setWindowTitle("提示")
        message.setText(msg)
        message.setDefaultButton(QtWidgets.QMessageBox.Yes)
        message.exec_()

    def closeEvent(self, event: QtGui.QCloseEvent):
        description = "是否退出当前程序?"
        reply = QtWidgets.QMessageBox.warning(self, "警告", description,
                                              QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                              QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
            self.showMinimized()
