<h1 align="center">Magic-Dr.COM （基于 Python3 的第三方 Dr.COM 登录器）</h1>


### 🏠 [个人小栈](https://ryuchen.github.io/)

    > 未来更新的说明会刊登在这里，并且会不定时分享部分内容和心得

### 📎 项目说明:

本项目之前由[@EverybodyLies](https://github.com/Everyb0dyLies)进行开发和维护(目前该项目已经停止维护)

现阶段，因本人[@Ryuchen](https://github.com/Ryuchen)进入北信科进行研究生学习，由于使用Mac电脑进行开发，为了方便登录校园网，所以发现和承接了该项目进行后续开发和维护

本登陆器有图形界面和命令行两种运行模式，图形界面基于PyQt5实现，可跨平台运行，在路由器上可以以命令行模式运行。

### 📖 安装说明

#### 如何安装：

使用pip安装

`pip install MagicDrCOM`

或从GitHub获取

`git clone https://github.com/Ryuchen/MagicDrCOM.git`

#### 如何使用：

+ 图形界面模式

    + Windows 下
        > 安装构建好的 MagicDrCOM.exe 程序即可
    
    + Linux 下
        > `pip install MagicDrCOM` 安装完成之后，运行 `python3 -m drcom` 即可
        
    + MacOS 下
        > 将构建好的 MagicDrCOM.zip 解压后得到 MagicDrCOM.app 拖入应用程序文件夹下即可

+ 命令行模式

    + *所有平台* 下面执行下述命令：
    
        ```BASH
        git clone https://github.com/Ryuchen/MagicDrCOM.git
        
        cd MagicDrCOM
        
        # 修改 drcom/configs/settings.py 文件中 PASSWORD 和 USERNAME 字段
        
        python3 -m drcom
        ```

### 📖 使用说明

重试次数：该客户端检测到网络断开后会自动重连，最大尝试重连次数

检查时间：该客户端会根据设定时间间隔自动尝试访问DNS服务器，检测网络连通性

构建脚本说明

```bash
# 需要在不同的平台下面进行构建
# MacOS 下面 icon 图标使用 app.icns
# Windos和Linux 使用 app.ico

# MacOS 或者 Linux 下
pyinstaller -F --icon=./resources/app.icns --noconsole drcom/MagicDrCOM.py

# Windows PowerShell 下
pyinstaller -F --icon=.\resources\app.ico --noconsole .\drcom\MagicDrCOM.py
```

### ❔ 提交ISSUE

欢迎大家在issue提交bug，我会尽量跟进并尽可能及时修复，如果大神比较着急，自己修改代码，也欢迎发送pull requests。

如果你不能登录，或中途闪退，请发issue的时候详细描述bug出现之前的每一步具体操作和软件崩溃的表现行为，以及操作系统和运行环境，如果可能请附上INFO级日志输出。

**请不要提交无效的issue！**

[提问的智慧](https://github.com/ryanhanwu/How-To-Ask-Questions-The-Smart-Way/blob/master/README-zh_CN.md)，不负责教授基础操作！

### 👤 作者介绍

Ryuchen ( 陈 浩 )

* Github: [https://github.com/Ryuchen](https://github.com/Ryuchen)
* Email: [chenhaom1993@hotmail.com](chenhaom1993@hotmail.com)
* QQ: 455480366
* 微信: Chen_laws

Nameplace ( 虚位以待 )

### ⭐ 渴望支持

如果你想继续观察 MagicDrCOM 接下来的走向，请给我们一个 ⭐ 这是对于我们最大的鼓励。
此外，如果你觉得 MagicDrCOM 对你有帮助，你可以赞助我们一杯咖啡，鼓励我们继续开发维护下去。

| **微信**                         | **支付宝**                           |
| ------------------------------- | ----------------------------------- |
|<p align="center">![扫码赞助](https://github.com/Ryuchen/Panda-Sandbox/raw/master/docs/sponsor/wechat.jpg)</p>|<p align="center">![扫码赞助](https://github.com/Ryuchen/Panda-Sandbox/raw/master/docs/sponsor/alipay.jpg)</p>|

### 🤝 贡献源码

本项目参考了以下项目，顺序不分先后

drcoms/drcom-generic，https://github.com/drcoms/drcom-generic

coverxit/EasyDrcom，https://github.com/coverxit/EasyDrcom/

mchome/dogcom，https://github.com/mchome/dogcom

dantmnf/drcom-client，https://github.com/dantmnf/drcom-client

非常感谢这些前辈，如果没有他们，本项目很难开展

Contributions, issues and feature requests are welcome!

Feel free to check [issues page](https://github.com/Ryuchen/MagicDrCOM/issues).

### 📖 License

MagicDrCOM is licensed under the GNU General Public License v3.0

重申本代码仅用于实验和学习，使用者的一切商业行为及非法行为皆由其本人承担责任

[![PyPI version](https://img.shields.io/pypi/v/MagicDrCOM.svg)](https://pypi.python.org/pypi/MagicDrCOM)
<img src="https://img.shields.io/badge/language-python3-blue.svg?cacheSeconds=2592000" />

