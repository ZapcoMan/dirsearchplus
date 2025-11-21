import json
import time
import sys

from lib.reports.base import FileBaseReport


class JSONReport(FileBaseReport):
    """
    JSON格式报告生成器类

    该类继承自FileBaseReport，用于将扫描结果生成JSON格式的报告
    """

    def generate(self, entries):
        """
        生成JSON格式的报告

        Args:
            entries: 扫描结果条目列表，每个条目包含URL、状态码等信息

        Returns:
            str: 格式化后的JSON字符串报告，包含扫描信息和结果详情
        """
        # 初始化报告结构，包含基本信息和结果列表
        report = {
            "info": {"args": " ".join(sys.argv), "time": time.ctime()},
            "results": [],
        }

        # 遍历所有扫描结果条目，提取关键信息并添加到报告中
        for entry in entries:
            result = {
                "url": entry.url,
                "status": entry.status,
                "content-length": entry.length,
                "content-type": entry.type,
                "redirect": entry.redirect,
            }
            report["results"].append(result)

        # 将报告转换为格式化的JSON字符串并返回
        return json.dumps(report, sort_keys=True, indent=4)

