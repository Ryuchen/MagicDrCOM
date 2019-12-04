#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ==================================================
# Licensed under the GPLv3
# 本项目由@Ryuchen开发维护，使用Python3.7
# ==================================================

import sys

from PySide2 import QtWidgets, QtGui
from drcom.gui.window import MainWindow

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    app.setWindowIcon(QtGui.QIcon('../resources/app.ico'))
    windows = MainWindow()
    windows.show()

    sys.exit(app.exec_())
