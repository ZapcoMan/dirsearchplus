#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import sys,os


class loadExtensions():
    """
    扩展加载器类

    用于动态加载并运行指定目录下的Python扩展模块

    参数:
        projectTag: 项目标识符，传递给扩展模块
        options: 配置选项，传递给扩展模块
    """

    def __init__(self, projectTag, options):
        """
        初始化扩展加载器

        参数:
            projectTag: 项目标识符，传递给扩展模块
            options: 配置选项，传递给扩展模块
        """
        self.projectTag = projectTag
        self.options = options

    def runExt(self):
        """
        运行扩展模块

        遍历ext目录下的所有Python文件（排除__init__.py），
        动态导入并执行扩展模块的start方法
        """
        # 将ext目录添加到Python路径中
        path = r"ext"
        sys.path.append(path)

        # 遍历ext目录及其子目录中的所有文件
        for root, dirs, files in os.walk(r"ext"):
            for file in files:
                # 筛选出.py文件且排除__init__.py文件
                if os.path.join(root,file).split(os.sep)[-1].split(".")[-1] == "py" and file != '__init__.py':
                    # 提取模块名
                    module_name = os.path.join(root,file).split(os.sep)[-1].split(".")[0]
                    # 动态导入模块
                    module = __import__(module_name)
                    # 实例化扩展类并启动
                    module.ext(self.projectTag, self.options).start()
