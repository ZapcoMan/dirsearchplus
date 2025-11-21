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
    """
    用于扫描和识别通配符响应行为的类。该类通过发送随机路径请求来构建通配符响应模型，并判断后续响应是否属于通配符类型。

    :param requester: 请求对象，负责实际发起HTTP请求
    :param path: 路径模板字符串，其中可能包含通配符测试点标记
    :param tested: 已经测试过的其他Scanner实例字典，用于避免重复测试
    :param context: 当前上下文描述信息，默认为"所有情况"
    """

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
        初始化阶段，生成两个不同随机路径的响应作为基准，建立通配符响应的内容解析器和重定向正则表达式。
        如果已有相同的响应存在，则复用其结果以减少网络请求次数。
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
        """
        查找是否存在与当前响应完全一致的历史测试记录。

        :param response: 待比对的响应对象
        :return: 若找到匹配项则返回对应的Scanner实例，否则返回None
        """
        for category in self.tested:
            for tester in self.tested[category].values():
                if response == tester.response:
                    return tester

        return None

    def is_wildcard(self, response):
        """
        判断给定响应是否符合通配符响应特征。

        :param response: 待判断的响应对象
        :return: 如果响应内容与通配符响应相似则返回True，否则返回False
        """

        # 比较2个二进制响应（如果正文是二进制的，则Response.content为空）
        if not self.response.content and not response.content:
            return self.response.body == response.body

        return self.content_parser.compare_to(response.content)

    def check(self, path, response):
        """
        对指定路径及其响应进行综合分析，确定是否应将其视为有效发现而非通配符响应。

        :param path: 实际访问的路径字符串
        :param response: 响应对象
        :return: 如果不是通配符响应则返回True，表示可能是有效的路径；如果是通配符响应则返回False
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
        根据两次通配符响应的重定向地址生成一个能够匹配所有类似通配符重定向的正则表达式。

        :param first_loc: 第一次响应的重定向地址
        :param first_path: 第一次使用的随机路径
        :param second_loc: 第二次响应的重定向地址
        :param second_path: 第二次使用的随机路径
        :return: 匹配通配符重定向的正则表达式字符串
        """

        if first_path:
            first_loc = unquote(first_loc).replace(first_path, REFLECTED_PATH_MARKER)
        if second_path:
            second_loc = unquote(second_loc).replace(second_path, REFLECTED_PATH_MARKER)

        return generate_matching_regex(first_loc, second_loc)

