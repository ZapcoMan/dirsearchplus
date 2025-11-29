#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import logging,time,os
from lib.common.utils import Utils
from lib.common.cmdline import CommandLines


"""
1.from lib.common.CreatLog import creatLog
2._init_()里加入self.log = creatLog().get_logger()
3.self.log.debug("这里输入日志信息如api接口正常这样的")
4.self.log.info("这里输入print信息")
例如：
try:
    self.log.debug("正常输出信息")
except Exception as e:
    self.log.error("[Err] %s" %e)
需要使用日志记录的地方大致有一下几处：
    输入输出处，无论是从文件输入还是从网络等其他地方输入
    执行命令处
    调用函数处
"""

global log_name,logs #全局变量引用
logs = Utils().creatTag(6)
log_name = "logs" + os.sep + Utils().creatTag(6) + ".log"

class creatLog():
    """
    日志记录类，用于创建和管理日志记录器

    Attributes:
        logger: logging.Logger对象，实际的日志记录器实例
        log_time: str，格式化后的当前时间字符串
        fh: logging.FileHandler，文件日志处理器
        chd: logging.StreamHandler，控制台日志处理器
        formatter: logging.Formatter，日志格式化器
        formatter_info: logging.Formatter，控制台输出格式化器
    """

    def __init__(self , logger=None):
        """
        初始化日志记录器

        Args:
            logger (str, optional): 日志记录器名称，默认为None
        """
        self.logger = logging.getLogger(logger)
        self.logger.setLevel(logging.NOTSET)
        self.log_time = time.strftime("%Y_%m_%d_")

    def info(self, message):
        """
        记录INFO级别的日志信息，并设置特定颜色显示

        Args:
            message (str): 要记录的日志消息内容
        """
        self.fontColor('\033[0;34m%s\033[0m')
        self.logger.info(message)

    def set_logger(self):
        """
        配置日志处理器和格式化器
        如果日志记录器尚未配置处理器，则创建文件处理器和控制台处理器，
        并根据命令行参数设置不同的日志级别
        """
        # 检查是否已存在处理器，避免重复添加
        if not self.logger.handlers:
            # 创建文件日志处理器，将日志写入文件
            self.fh = logging.FileHandler(log_name, "w" ,encoding="utf-8")
            self.fh.setLevel(logging.DEBUG)

            # 创建控制台日志处理器
            self.chd = logging.StreamHandler()

            # 根据命令行参数设置控制台日志级别
            if CommandLines().cmd().silent != None:
                self.chd.setLevel(logging.ERROR)  # 静默模式只显示错误信息
            else: #静默模式不显示INFO
                self.chd.setLevel(logging.INFO)

            # 创建日志格式化器
            self.formatter = logging.Formatter(
                "[%(levelname)s]--%(asctime)s-%(filename)s->%(funcName)s line:%(lineno)d: %(message)s\n")
            self.formatter_info = logging.Formatter()

            # 设置处理器的格式化器
            self.chd.setFormatter(self.formatter_info)
            self.fh.setFormatter(self.formatter)

            # 将处理器添加到日志记录器中
            self.logger.addHandler(self.fh)
            self.logger.addHandler(self.chd)

    def get_logger(self):
        """
        获取配置好的日志记录器实例

        Returns:
            logging.Logger: 配置完成的日志记录器对象
        """
        creatLog.set_logger(self)
        return self.logger

    def remove_log_handler(self):
        """
        移除日志处理器并关闭相关资源
        清理日志记录器中的所有处理器，并关闭文件和控制台处理器
        """
        self.logger.removeHandler(self.fh)
        self.logger.removeHandler(self.chd)
        self.fh.close()
        self.chd.close()

