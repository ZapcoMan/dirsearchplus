# !/usr/bin/env python3
# -*- encoding: utf-8 -*-
import signal
import sys

from lib.Controller import Project
from lib.TestProxy import testProxy
from lib.common.cmdline import CommandLines


# 处理SIGINT信号 (CTRL+C)
def signal_handler(sig, frame):
    """
    信号处理函数，用于捕获SIGINT信号（Ctrl+C）并优雅退出程序

    :param sig: 信号编号
    :param frame: 信号发生时的堆栈帧
    :return: None
    """
    print('\n[!] 检测到中断信号，正在退出程序...')
    sys.exit(0)

# 注册信号处理器，捕获Ctrl+C中断信号
signal.signal(signal.SIGINT, signal_handler)

class Program:
    """
    程序主类，负责初始化配置选项并执行检查逻辑
    """

    def __init__(self, options):
        """
        初始化Program实例

        :param options: 命令行解析后的配置选项对象
        """
        self.options = options

    def check(self):
        """
        执行主要的检查逻辑，创建Project实例并启动解析过程

        :return: None
        """
        url = self.options.url
        t = Project(url, self.options)
        t.parseStart()


if __name__ == '__main__':
    # 解析命令行参数
    cmd = CommandLines().cmd()
    # 测试代理连接
    testProxy(cmd, 1)
    try:
        # 创建程序实例并执行检查
        PackerFuzzer = Program(cmd)
        PackerFuzzer.check()
    except KeyboardInterrupt:
        print('\n[!] 检测到中断信号，正在退出程序...')
    except Exception as e:
        print(f'[!] 程序执行出错: {str(e)}')
