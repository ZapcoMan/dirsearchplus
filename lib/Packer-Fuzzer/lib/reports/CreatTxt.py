#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import os
from docx2txt import process
from lib.common.CreatLog import creatLog


class CreatTxt():
    """
    创建文本文件的类

    该类用于将docx文件转换为txt文件，并进行文本清理处理

    参数:
        projectTag (str): 项目标识，用于构建文件路径
        nameTxt (str): 目标txt文件的路径和名称
    """

    def __init__(self,projectTag,nameTxt):
        self.new_filepath = "reports" + os.sep + "tmp_" + projectTag + ".docx"
        self.txt_filepath = nameTxt
        self.log = creatLog().get_logger()

    def CreatMe(self):
        """
        执行docx到txt的转换操作

        该方法读取docx文件，提取文本内容，清理多余的换行符，
        并将处理后的文本写入指定的txt文件中

        返回值:
            无返回值
        """
        try:
            text = process(self.new_filepath)
            self.log.debug("正确获取到process模块")
        except Exception as e:
            self.log.error("[Err] %s" % e)

        # 清理文本中的多余换行符，将连续5个换行符替换为单个换行符
        if "\n\n\n\n\n" in text:
            text1 = text.replace("\n\n\n\n\n", "\n")

        # 将处理后的文本写入目标txt文件
        with open(self.txt_filepath, "w", encoding="utf-8",errors="ignore") as f:
            f.write(text1)
            f.close()

