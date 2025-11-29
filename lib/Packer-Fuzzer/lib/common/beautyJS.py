# !/usr/bin/env python3
# -*- encoding: utf-8 -*-

import re,os,re
from urllib.parse import urlparse
from lib.common import readConfig
from lib.common.utils import Utils
from lib.Database import DatabaseType
from lib.common.cmdline import CommandLines


class BeautyJs():
    """
    JavaScript代码美化类

    用于格式化JavaScript文件，使其具有更好的可读性
    """

    def __init__(self,projectTag):
        """
        初始化BeautyJs对象

        Args:
            projectTag (str): 项目标识标签
        """
        self.projectTag = projectTag

    def beauty_js(self,filePath):
        """
        美化单个JavaScript文件

        通过添加适当的缩进和换行来格式化JavaScript代码

        Args:
            filePath (str): 要美化的JavaScript文件路径

        Returns:
            None
        """
        # 读取文件内容并按分号分割成行
        lines = open(filePath, encoding="utf-8",errors="ignore").read().split(";")
        indent = 0
        formatted = []

        # 遍历每一行进行格式化处理
        for line in lines:
            newline = []
            for char in line:
                newline.append(char)
                # 遇到左花括号增加缩进并换行
                if char == '{':
                    indent += 1
                    newline.append("\n")
                    newline.append("\t" * indent)
                # 遇到右花括号减少缩进并换行
                if char == "}":
                    indent -= 1
                    newline.append("\n")
                    newline.append("\t" * indent)
            formatted.append("\t" * indent + "".join(newline))

        # 将格式化后的内容写回原文件
        open(filePath, "w", encoding="utf-8",errors="ignore").writelines(";\n".join(formatted))

    def rewrite_js(self):
        """
        重写项目中的所有JavaScript文件

        遍历项目目录下的所有文件，对非数据库文件进行JavaScript代码美化处理

        Returns:
            None
        """
        # 获取项目路径
        projectPath = DatabaseType(self.projectTag).getPathfromDB()

        # 遍历项目目录下的所有文件
        for parent, dirnames, filenames in os.walk(projectPath, followlinks=True):
            for filename in filenames:
                # 排除数据库文件
                if filename != self.projectTag + ".db":
                    filePath = os.path.join(parent, filename)
                    # 对文件进行美化处理
                    BeautyJs(self.projectTag).beauty_js(filePath)

