import difflib
import re

from lib.core.settings import MAX_MATCH_RATIO


class DynamicContentParser:
    """
    动态内容解析器，用于比较两个响应内容是否相似。

    该类通过分析两个内容之间的差异来判断后续内容是否与基础内容属于同一结构，
    主要应用于处理动态内容（如时间戳、随机数等）的网页响应匹配场景。

    :param content1: 基准内容字符串
    :param content2: 对比内容字符串
    """

    def __init__(self, content1, content2):
        self._static_patterns = None
        self._differ = difflib.Differ()
        self._is_static = content1 == content2
        self._base_content = content1

        if not self._is_static:
            self._static_patterns = self.get_static_patterns(
                self._differ.compare(content1.split(), content2.split())
            )

    def compare_to(self, content):
        """
        将给定的内容与初始化时提供的基准内容进行对比，判断它们是否足够相似。

        比较流程如下：
          1. 若初始内容完全相同（静态），则直接进行全等比较；
          2. 否则提取当前内容中的稳定模式，并与已知的静态模式做匹配；
          3. 如果静态模式匹配失败，则进一步使用序列相似度算法确认相似性；

        :param content: 待比较的内容字符串
        :return: bool - 表示内容是否足够相似
        """

        if self._is_static:
            return content == self._base_content

        diff = self._differ.compare(self._base_content.split(), content.split())
        static_patterns_are_matched = self._static_patterns == self.get_static_patterns(diff)
        match_ratio = difflib.SequenceMatcher(None, self._base_content, content).ratio()
        return static_patterns_are_matched or match_ratio > MAX_MATCH_RATIO

    @staticmethod
    def get_static_patterns(patterns):
        """
        从 difflib.Differ 的输出中筛选出稳定的文本片段。

        difflib.Differ.compare 返回的结果格式类似：
        ["  str1", "- str2", "+ str3", "  str4"]

        其中以 "  " 开头的部分表示未发生变化的内容。此方法仅保留这些部分。

        :param patterns: Differ 输出的差异列表
        :return: list[str] - 所有不变的文本段组成的列表
        """
        return [pattern for pattern in patterns if pattern.startswith("  ")]


def generate_matching_regex(string1, string2):
    """
    根据两个字符串生成一个能同时匹配两者的正则表达式。

    正则由前缀一致部分 + 中间任意字符 + 后缀一致部分组成。

    :param string1: 第一个字符串
    :param string2: 第二个字符串
    :return: str - 构造出的正则表达式字符串
    """
    start = "^"
    end = "$"

    for char1, char2 in zip(string1, string2):
        if char1 != char2:
            start += ".*"
            break

        start += re.escape(char1)

    if start.endswith(".*"):
        for char1, char2 in zip(string1[::-1], string2[::-1]):
            if char1 != char2:
                break

            end = re.escape(char1) + end

    return start + end

