MagicDrCOM （基于python3的第三方Dr.COM登录器）
=====================================================================

:Author: Ryuchen
:Version: v1.0.0
:Copyright: GNU General Public License v3.0

.. contents::

本项目之前由[@EverybodyLies]进行开发和维护(目前该项目已经停止维护)
现阶段，因本人[@Ryuchen]进入北信科进行研究生学习，由于使用Mac电脑进行开发，为了方便登录校园网，所以发现和承接了该项目进行后续开发和维护

.. Note:: 本登陆器有图形界面和命令行两种运行模式，图形界面基于PyQt5实现，可跨平台运行，在路由器上可以以命令行模式运行


How to Install
---------------------------------------------

使用pip安装

- pip install MagicDrCOM

或从GitHub获取

- git clone https://github.com/Ryuchen/MagicDrCOM.git


How to Use
---------------------------------------------

- 图形界面模式

- Windows 下

  安装构建好的 MagicDrCOM.exe 程序即可

- Linux 下

  pip install MagicDrCOM 安装完成之后，运行 python3 -m drcom 即可

- MacOS 下

  将构建好的 MagicDrCOM.zip 解压后得到 MagicDrCOM.app 拖入应用程序文件夹下即可

- 命令行模式

  所有平台下面执行下述命令：

  git clone https://github.com/Ryuchen/MagicDrCOM.git

  cd MagicDrCOM

  修改 drcom/configs/settings.py 文件中 PASSWORD 和 USERNAME 字段

  python3 drcom/client.py


Usage Description
---------------------------------------------

- 重试次数：该客户端检测到网络断开后会自动重连，最大尝试重连次数

- 检查时间：该客户端会根据设定时间间隔自动尝试访问DNS服务器，检测网络连通性

- 构建脚本说明

  - 需要在不同的平台下面进行构建;

  - MacOS 下面 icon 图标使用 app.icns;

  - Windos和Linux 使用 app.ico;

- MacOS 或者 Linux 下

  pyinstaller -F --icon=./resources/app.icns --noconsole drcom/MagicDrCOM.py

- Windows PowerShell 下

  pyinstaller -F --icon=.\resources\app.ico --noconsole .\drcom\MagicDrCOM.py


Author Description
---------------------------------------------

Ryuchen (陈 浩)

- Github: https://github.com/Ryuchen
- Email: chenhaom1993@hotmail.com
- QQ: 455480366
- 微信: Chen_laws