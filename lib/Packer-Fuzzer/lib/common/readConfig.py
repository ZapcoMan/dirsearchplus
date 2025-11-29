# !/usr/bin/env python3
# -*- encoding: utf-8 -*-

import os
from configparser import ConfigParser


class ReadConfig(object):
    """
    配置文件读取类

    用于读取系统配置文件和语言配置文件中的配置项
    """

    def __init__(self):
        """
        初始化配置文件读取器

        设置配置文件路径并初始化配置解析器和结果列表
        """
        self.path = os.getcwd() + os.sep + "config.ini"  # 配置文件地址
        self.langPath = os.getcwd() + os.sep + "doc/lang.ini"  # 配置文件地址
        self.config = ConfigParser()
        self.res = []

    def getValue(self, sections, key):
        """
        获取配置文件中指定section和key的值

        Args:
            sections (str): 配置文件中的section名称
            key (str): section下的键名

        Returns:
            list: 包含获取到的配置值的列表
        """
        self.config.read(self.path, encoding="utf-8")
        options = self.config[sections][key]
        self.res.append(options)
        return self.res

    def getLang(self, sections, key):
        """
        获取语言配置文件中指定section和key的值

        Args:
            sections (str): 语言配置文件中的section名称
            key (str): section下的键名

        Returns:
            list: 包含获取到的语言配置值的列表
        """
        self.config.read(self.langPath, encoding="utf-8")
        options = self.config[sections][key]
        self.res.append(options)
        return self.res

