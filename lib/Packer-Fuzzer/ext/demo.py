#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

from lib.common.utils import Utils
from lib.Database import DatabaseType

class ext():
    """
    扩展功能类

    该类用于处理项目扩展功能，根据状态决定是否执行特定操作

    参数:
        projectTag: 项目标签标识
        options: 配置选项参数
    """

    def __init__(self, projectTag, options):
        """
        初始化扩展功能类

        参数:
            projectTag: 项目标签标识
            options: 配置选项参数
        """
        self.projectTag = projectTag
        self.options = options
        self.statut = 0   #0 disable  1 enable

    def start(self):
        """
        启动扩展功能

        根据当前状态判断是否执行运行方法，只有当状态为启用时才执行
        """
        if self.statut == 1:
            self.run()

    def run(self):
        """
        执行扩展功能的核心逻辑

        输出包含多种语言问候语的时间戳信息
        """
        print(Utils().tellTime() + "Hello Bonjour Hola 你好 こんにちは")
