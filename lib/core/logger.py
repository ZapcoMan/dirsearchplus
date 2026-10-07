import logging
from logging.handlers import RotatingFileHandler

from lib.core.data import options


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# 默认禁用日志记录器
logger.disabled = True


def enable_logging():
    """
    启用日志记录功能

    该函数将启用预先配置的日志记录器，并设置日志文件的轮转机制。
    日志格式包含时间戳、日志级别和消息内容。
    日志文件的路径和大小限制从options配置中读取。

    参数:
        无

    返回值:
        无
    """
    # 启用日志记录器
    logger.disabled = False
    # 创建日志格式化器
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    # 创建轮转文件处理器，当日志文件达到指定大小时自动轮转
    handler = RotatingFileHandler(options["log_file"], maxBytes=options["log_file_size"])
    # 设置处理器的日志级别
    handler.setLevel(logging.DEBUG)
    # 为处理器设置格式化器
    handler.setFormatter(formatter)
    # 将处理器添加到日志记录器中
    logger.addHandler(handler)


def enable_console_logging(level=logging.DEBUG):
    """
    将日志同时输出到控制台（供 --debug 使用）

    不依赖日志文件配置，直接在 stderr 输出，便于排查问题。
    """
    logger.disabled = False
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

