import re
import json

from defusedxml import ElementTree

from lib.core.settings import QUERY_STRING_REGEX


class MimeTypeUtils:
    """
    MIME类型检测工具类，提供各种数据格式的识别方法
    """

    @staticmethod
    def is_json(content):
        """
        检测给定内容是否为有效的JSON格式

        :param content: 待检测的字符串内容
        :return: 如果内容是有效的JSON格式则返回True，否则返回False
        """
        try:
            json.loads(content)
            return True
        except json.decoder.JSONDecodeError:
            return False

    @staticmethod
    def is_xml(content):
        """
        检测给定内容是否为有效的XML格式

        :param content: 待检测的字符串内容
        :return: 如果内容是有效的XML格式则返回True，否则返回False
        """
        try:
            ElementTree.fromstring(content)
            return True
        except ElementTree.ParseError:
            return False
        except Exception:
            return True

    @staticmethod
    def is_query_string(content):
        """
        检测给定内容是否为查询字符串格式（key=value&key2=value2）

        :param content: 待检测的字符串内容
        :return: 如果内容符合查询字符串格式则返回True，否则返回False
        """
        if re.match(QUERY_STRING_REGEX, content):
            return True

        return False


def guess_mimetype(content):
    """
    根据内容自动推测MIME类型

    :param content: 待检测的字符串内容
    :return: 推测出的MIME类型字符串
    """
    # 依次检测JSON、XML和查询字符串格式，返回对应的MIME类型
    if MimeTypeUtils.is_json(content):
        return "application/json"
    elif MimeTypeUtils.is_xml(content):
        return "application/xml"
    elif MimeTypeUtils.is_query_string(content):
        return "application/x-www-form-urlencoded"
    else:
        return "text/plain"

