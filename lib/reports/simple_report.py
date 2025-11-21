from lib.core.settings import NEW_LINE
from lib.reports.base import FileBaseReport


class SimpleReport(FileBaseReport):
    """
    简单报告生成器类

    继承自FileBaseReport基类，用于生成简单的URL报告
    """

    def generate(self, entries):
        """
        生成简单格式的报告

        将输入的条目列表转换为以换行符分隔的URL字符串报告

        参数:
            entries: 包含条目对象的可迭代对象，每个条目对象需要有url属性

        返回:
            str: 由换行符连接的所有条目URL组成的字符串报告
        """
        # 使用生成器表达式提取所有条目的URL，并用换行符连接成一个字符串
        return NEW_LINE.join(entry.url for entry in entries)

