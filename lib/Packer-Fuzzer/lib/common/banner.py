# !/usr/bin/env python3
# -*- encoding: utf-8 -*-

import random
# from lib.common.utils import Utils
from .utils import Utils
# from lib.common.cmdline import CommandLines
from .cmdline import CommandLines

Version = 'Packer Fuzzer v1.4.15'
red = '\033[25;31m'
green = '\033[25;32m'
yellow = '\033[25;33m'
blue = '\033[25;34m'
Fuchsia = '\033[25;35m'
cyan = '\033[25;36m'
end = '\033[0m'
colors = [red,green,yellow,blue,Fuchsia,cyan]

# 定义多个Banner样式，用于程序启动时展示不同的彩色Logo图案
Banner1 = """{}
 _______________
< Packer Fuzzer >
 ---------------
        \   ^__^
         \  (oo)\_______
            (__)\       )\/\\
                ||----w |
                ||     ||
           {}
{}
""".format(random.choice(colors),Version,end)

Banner2 = """{}
 _______________
< Packer Fuzzer >
 ---------------
   \\
    \\
        .--.
       |o_o |
       |:_/ |
      //   \ \\
     (|     | )
    /'\_   _/`\\
    \___)=(___/
       {}
 {}
""".format(random.choice(colors),Version,end)

Banner3 = '''{}
 _______________
< Packer Fuzzer >
 ---------------
    \\
     \\
                                   .::!!!!!!!:.
  .!!!!!:.                        .:!!!!!!!!!!!!
  ~~~~!!!!!!.                 .:!!!!!!!!!UWWW$$$
      :$$NWX!!:           .:!!!!!!XUWW$$$$$$$$$P
      $$$$$##WX!:      .<!!!!UW$$$$"  $$$$$$$$#
      $$$$$  $$$UX   :!!UW$$$$$$$$$   4$$$$$*
      ^$$$B  $$$$\     $$$$$$$$$$$$   d$$R"
        "*$bd$$$$      '*$$$$$$$$$$$o+#"
             """"          """""""
             {}
{}
'''.format(Fuchsia,Version,end)

Banner7 = ""

def RandomBanner():
    """
    随机打印一个Banner图标

    该函数根据命令行参数判断是否静默模式，如果不是静默模式则输出默认Banner和一句随机鸡汤文案。
    目前强制使用Banner7（空字符串），实际不会显示任何图案。

    参数:
        无

    返回值:
        无
    """
    # BannerList = [Banner1,Banner2,Banner3,Banner7]
    if CommandLines().cmd().silent is None:
        print(Banner7)
        print(Utils().getMyWord("{xhlj}") + "\n")


# 程序启动时调用，显示Banner信息
RandomBanner()
