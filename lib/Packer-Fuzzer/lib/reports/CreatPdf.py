#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import os
from docx2pdf import convert
from lib.common.CreatLog import creatLog


class CreatPdf():
    """
    PDF创建类，用于将Word文档转换为PDF格式

    Attributes:
        new_filepath (str): 源Word文档文件路径
        pdf_filepath (str): 目标PDF文件保存路径
        log: 日志记录器实例
    """

    def __init__(self, projectTag, namePdf):
        """
        初始化PDF创建器

        Args:
            projectTag (str): 项目标识，用于构建源文件路径
            namePdf (str): PDF文件的保存路径和文件名
        """
        self.new_filepath = "reports" + os.sep + "tmp_" + projectTag + ".docx"
        self.pdf_filepath = namePdf
        self.log = creatLog().get_logger()

    def CreatMe(self):
        """
        执行Word到PDF的转换操作

        该方法使用docx2pdf库将指定的Word文档转换为PDF格式，
        并记录转换过程中的日志信息。

        Returns:
            None
        """
        try:
            convert(self.new_filepath, self.pdf_filepath)
            self.log.debug("正确获取到pdf转化模块")
        except Exception as e:
            self.log.error("[Err] %s" % e)
