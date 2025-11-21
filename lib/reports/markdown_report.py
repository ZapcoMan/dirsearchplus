import time
import sys

from lib.core.settings import NEW_LINE
from lib.reports.base import FileBaseReport


class MarkdownReport(FileBaseReport):
    """
    Markdown格式报告生成器类

    该类继承自FileBaseReport，用于生成Markdown格式的扫描结果报告
    """

    def get_header(self):
        """
        生成Markdown报告的头部信息

        构建包含命令行信息、执行时间和表格标题的报告头部

        Returns:
            str: 包含报告头部信息的Markdown格式字符串
        """
        # 构建报告头部基本信息
        header = "### Information" + NEW_LINE
        header += f"Command: {chr(32).join(sys.argv)}"
        header += NEW_LINE
        header += f"Time: {time.ctime()}"
        header += NEW_LINE * 2

        # 添加表格标题行和分隔行
        header += "URL | Status | Size | Content Type | Redirection" + NEW_LINE
        header += "----|--------|------|--------------|------------" + NEW_LINE
        return header

    def generate(self, entries):
        """
        生成完整的Markdown格式报告

        将扫描结果条目转换为Markdown表格格式的报告内容

        Args:
            entries (list): 扫描结果条目列表，每个条目应包含url、status、length、type、redirect属性

        Returns:
            str: 完整的Markdown格式报告内容
        """
        # 初始化输出内容并添加报告头部
        output = self.get_header()

        # 遍历所有条目，将每个条目的信息添加到输出中
        for entry in entries:
            output += f"{entry.url} | {entry.status} | {entry.length} | {entry.type} | {entry.redirect}" + NEW_LINE

        return output

