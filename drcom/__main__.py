#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ==================================================
# Licensed under the GPLv3
# 本项目由@Ryuchen开发维护，使用Python3.7
# ==================================================

import sys

from PyQt5.QtWidgets import QApplication

from drcom.gui.control import MainWindowController

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window_controller = MainWindowController()
    main_window_controller.window.show()
    sys.exit(app.exec_())

