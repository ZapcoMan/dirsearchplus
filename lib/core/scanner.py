# -*- coding: utf-8 -*-
#  本程序是自由软件；您可以重新分发它和/或修改它
#  遵循自由软件基金会发布的GNU通用公共许可证的条款；
#  许可证的版本2，或（根据您的选择）任何更高版本。
#
#  本程序的分发是希望它有用，
#  但没有任何担保；甚至没有适销性或特定用途适用性的暗示保证。
#  有关详细信息，请参阅GNU通用公共许可证。
#
#  您应该已经收到GNU通用公共许可证的副本；
#  如果没有，请写信给自由软件基金会，地址：51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#  作者: Mauro Soria

import re

from urllib.parse import unquote

from lib.core.logger import logger
from lib.core.settings import (
    REFLECTED_PATH_MARKER,
    TEST_PATH_LENGTH,
    WILDCARD_TEST_POINT_MARKER,
)
from lib.parse.url import clean_path
from lib.utils.diff import generate_matching_regex, DynamicContentParser
from lib.utils.random import rand_string


class Scanner:
    def __init__(self, requester, **kwargs):
        self.path = kwargs.get("path", "")
        self.tested = kwargs.get("tested", [])
        self.context = kwargs.get("context", "所有情况")
        self.requester = requester
        self.response = None
        self.wildcard_redirect_regex = None
        self.setup()

    def setup(self):
        """
        生成通配符响应信息容器，这将用于与其他路径响应进行比较
        """

        first_path = self.path.replace(
            WILDCARD_TEST_POINT_MARKER,
            rand_string(TEST_PATH_LENGTH),
        )
        first_response = self.requester.request(first_path)
        self.response = first_response

        duplicate = self.get_duplicate(first_response)
        # 之前已执行另一个测试并且响应与此相同
        if duplicate:
            self.content_parser = duplicate.content_parser
            self.wildcard_redirect_regex = duplicate.wildcard_redirect_regex
            logger.debug(f'跳过"{self.context}"的第二次测试')
            return

        second_path = self.path.replace(
            WILDCARD_TEST_POINT_MARKER,
            rand_string(TEST_PATH_LENGTH, omit=first_path),
        )
        second_response = self.requester.request(second_path)

        if first_response.redirect and second_response.redirect:
            self.wildcard_redirect_regex = self.generate_redirect_regex(
                clean_path(first_response.redirect),
                first_path,
                clean_path(second_response.redirect),
                second_path,
            )
            logger.debug(f'用于检测"{self.context}"通配符重定向的模式（正则表达式）: {self.wildcard_redirect_regex}')

        self.content_parser = DynamicContentParser(
            first_response.content, second_response.content
        )

    def get_duplicate(self, response):
        for category in self.tested:
            for tester in self.tested[category].values():
                if response == tester.response:
                    return tester

        return None

    def is_wildcard(self, response):
        """检查响应是否与通配符响应相似"""

        # 比较2个二进制响应（如果正文是二进制的，则Response.content为空）
        if not self.response.content and not response.content:
            return self.response.body == response.body

        return self.content_parser.compare_to(response.content)

    def check(self, path, response):
        """
        执行分析以查看响应是否为通配符
        """

        if self.response.status != response.status:
            return True

        # 请阅读第129行到第138行以了解此工作流程。
        if self.wildcard_redirect_regex and response.redirect:
            # - unquote(): 有时，响应重定向中的一些路径字符会被编码或解码
            # 但它仍然是通配符重定向，所以取消引用所有内容以防止误报
            # - clean_path(): 去除URL中的查询和DOM，因为它们可能发生奇怪的行为
            # 太混乱了，我放弃了寻找测试它们的方法
            path = unquote(clean_path(path))
            redirect = unquote(clean_path(response.redirect))
            regex_to_compare = self.wildcard_redirect_regex.replace(
                REFLECTED_PATH_MARKER, re.escape(path)
            )
            is_wildcard_redirect = re.match(regex_to_compare, redirect, re.IGNORECASE)

            # 如果重定向不匹配规则，则标记为已找到
            if not is_wildcard_redirect:
                logger.debug(f'"{redirect}"不匹配正则表达式"{regex_to_compare}"，通过')
                return True

        if self.is_wildcard(response):
            return False

        return True

    @staticmethod
    def generate_redirect_regex(first_loc, first_path, second_loc, second_path):
        """
        从2个通配符响应的重定向中，生成一个匹配每个通配符重定向的正则表达式。

        工作原理：
        1. 用标记替换2个重定向URL中的路径（如果它被反射出来）
           （例如 /path1 -> /foo/path1 和 /path2 -> /foo/path2 都会变成 /foo/[mark]）
        2. 比较2个重定向并生成匹配两者的正则表达式
           （例如 /foo/[mark]?a=1 和 /foo/[mark]?a=2 将有正则表达式: ^/foo/[mark]?a=(.*)$）
        3. 下次重定向时，用路径替换正则表达式中的标记并检查是否匹配
           （例如 /path3 -> /foo/path3?a=5，正则表达式变成 ^/foo/path3?a=(.*)$，匹配成功）
        """

        if first_path:
            first_loc = unquote(first_loc).replace(first_path, REFLECTED_PATH_MARKER)
        if second_path:
            second_loc = unquote(second_loc).replace(second_path, REFLECTED_PATH_MARKER)

        return generate_matching_regex(first_loc, second_loc)
