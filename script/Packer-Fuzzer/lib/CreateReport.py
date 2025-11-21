# !/usr/bin/env python3
# -*- encoding: utf-8 -*-

import os,re,sqlite3,time
from docx import Document   #用来建立一个word对象
from docx.shared import Pt  #用来设置字体的大小
from urllib.parse import urlparse
from .common.utils import Utils
from .Database import DatabaseType
from .common.CreatLog import creatLog
from .reports.CreatPdf import CreatPdf
from .reports.CreatTxt import CreatTxt
from .reports import CreatHtml
from .common.cmdline import CommandLines
from .reports.CreatWord import Docx_replace


class CreateReport():
    """
    报告生成类，用于根据项目标签生成多种格式的扫描报告（如 HTML、DOCX、PDF、TXT）。

    Attributes:
        projectTag (str): 项目的唯一标识符，用于数据库查询及文件命名。
        log (Logger): 日志记录器实例，用于输出运行日志。
    """

    def __init__(self,projectTag):
        """
        初始化 CreateReport 类。

        Args:
            projectTag (str): 项目的唯一标识符。
        """
        self.projectTag = projectTag
        self.log = creatLog().get_logger()

    def create_repoter(self):
        """
        根据命令行指定的报告类型生成对应的报告文件。

        支持的报告类型包括：html、doc、pdf、txt。会从数据库获取主 URL，
        并基于该 URL 和 projectTag 构造报告文件名。

        此方法还会处理 silent 模式下的自定义文件名，并复制必要的资源文件。
        """
        # 获取主URL并解析主机地址作为文件名的一部分
        main_url = DatabaseType(self.projectTag).getURLfromDB()
        parse_url = urlparse(main_url)
        host = parse_url.netloc.replace(':', '_') # win系统不能使用冒号作为文件名

        # 解析需要生成的报告类型列表
        reportType = CommandLines().cmd().report
        reportTypes = reportType.split(',')

        # 判断是否需要生成任意一种支持的报告
        if "doc" in reportTypes or "pdf" in reportTypes or "txt" in reportTypes or "html" in reportTypes:
            self.log.info(Utils().tellTime() + Utils().getMyWord("{report_creat}"))

        # 处理 HTML 报告生成逻辑
        if "html" in reportTypes:
            # 确定 HTML 文件名称
            if CommandLines().cmd().silent != None:
                nameHtml = "reports" + os.sep + CommandLines().cmd().silent + ".html"
            else:
                nameHtml = "reports" + os.sep + host + "-" + self.projectTag + ".html"

            # 若不存在 res 目录则拷贝模板中的静态资源
            if os.path.exists("reports" + os.sep + "res"):
                pass
            else:
                Utils().copyPath("doc" + os.sep + "template" + os.sep + "html" + os.sep + "res","reports")

            try:
                CreatHtml(self.projectTag,nameHtml).CreatMe()
                self.log.debug("html模板正常")
                # 输出HTML报告绝对路径，方便在浏览器中打开
                html_abs_path = os.path.abspath(nameHtml)
                self.log.info(Utils().tellTime() + "HTML报告已生成: " + html_abs_path)
                self.log.info("请在浏览器中打开以上路径查看详细扫描结果")
            except Exception as e:
                self.log.error("[Err] %s" % e)

        # 处理 DOC、TXT、PDF 报告生成逻辑
        if "doc" in reportTypes or "pdf" in reportTypes or "txt" in reportTypes:
            # 替换 Word 文档中的占位符内容
            Docx_replace(self.projectTag).mainReplace()

            # 生成 DOCX 报告
            if "doc" in reportTypes:
                if CommandLines().cmd().silent != None:
                    nameDoc = "reports" + os.sep + CommandLines().cmd().silent + ".docx"
                else:
                    nameDoc = "reports" + os.sep + host + "-" + self.projectTag + ".docx"
                Docx_replace(self.projectTag).docMove(nameDoc)

            # 生成 TXT 报告
            if "txt" in reportTypes:
                if CommandLines().cmd().silent != None:
                    nameTxt = "reports" + os.sep + CommandLines().cmd().silent + ".txt"
                else:
                    nameTxt = "reports" + os.sep + host + "-" + self.projectTag + ".txt"
                CreatTxt(self.projectTag,nameTxt).CreatMe()

            # 生成 PDF 报告
            if "pdf" in reportTypes:
                if CommandLines().cmd().silent != None:
                    namePdf =  "reports" + os.sep + CommandLines().cmd().silent + ".pdf"
                else:
                    namePdf = "reports" + os.sep + host + "-" + self.projectTag + ".pdf"
                CreatPdf(self.projectTag,namePdf).CreatMe()

            # 清理临时生成的 DOCX 文件
            Docx_replace(self.projectTag).docDel()

        # 最终提示所有报告已完成生成
        if "doc" in reportTypes or "pdf" in reportTypes or "txt" in reportTypes or "html" in reportTypes:
            time.sleep(2) #waiting
            self.log.info(Utils().tellTime() + Utils().getMyWord("{report_fini}"))
