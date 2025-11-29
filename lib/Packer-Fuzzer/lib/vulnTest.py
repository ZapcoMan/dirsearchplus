# !/usr/bin/env python3
# -*- encoding: utf-8 -*-

import os, re, sqlite3
from .common import readConfig
from .common.utils import Utils
from .vuln.SqlTest import SqlTest
from .vuln.BacTest import BacTest
from .Database import DatabaseType
from .vuln.InfoTest import InfoTest
from .vuln.CorsTest import CorsTest
from .common.CreatLog import creatLog
from .vuln.UploadTest import UploadTest
from .vuln.UnauthTest import UnAuthTest
from .vuln.PasswordTest import PasswordTest


class vulnTest():
    """
    漏洞测试主类，用于启动各类安全漏洞检测模块。

    :param projectTag: 项目标识符，用于区分不同项目的测试数据
    :param options: 测试选项配置对象，包含运行时的各种参数设置
    """

    def __init__(self, projectTag, options):
        self.projectTag = projectTag
        self.options = options
        self.log = creatLog().get_logger()

    def testStart(self, url):
        """
        启动基础漏洞检测流程，包括未授权访问、信息泄露和CORS配置错误等检测项。

        :param url: 待检测的目标URL地址
        """
        # 执行未授权访问测试
        self.log.info(Utils().tellTime() + Utils().getMyWord("{unauth_test}"))
        try:
            UnAuthTest(self.projectTag).apiUnAuthTest()
            self.log.debug("UnAuthTest模块正常")
        except Exception as e:
            self.log.error("[Err] %s" % e)

        # 执行敏感信息泄露测试
        self.log.info(Utils().tellTime() + Utils().getMyWord("{info_test}"))
        try:
            InfoTest(self.projectTag).startInfoTest()
            self.log.debug("InfoTest模块正常")
        except Exception as e:
            self.log.error("[Err] %s" % e)

        # 执行跨域资源共享（CORS）策略检测
        self.log.info(Utils().tellTime() + Utils().getMyWord("{cors_test}"))
        try:
            cors = CorsTest(url, self.options)
            cors.testStart()
            if cors.flag == 1:
                DatabaseType(self.projectTag).insertCorsInfoIntoDB(cors.header, cors.res)
            self.log.debug("CorsTest模块正常")
        except Exception as e:
            self.log.error("[Err] %s" % e)

    def advtestStart(self, options):
        """
        启动高级漏洞检测流程，包括弱密码、水平越权、文件上传及SQL注入等检测项。

        :param options: 高级测试所需的额外配置参数
        """
        # 弱密码与暴力破解测试
        try:
            self.log.info(Utils().tellTime() + Utils().getMyWord("{password_test}"))
            passwordtest = PasswordTest(self.projectTag)
            passwordtest.passwordTest()
            passwordtest.vulntestStart(options)
            self.log.debug("passwordTest模块正常")
        except Exception as e:
            self.log.error("[Err] %s" % e)

        # 水平权限绕过测试
        try:
            self.log.info(Utils().tellTime() + Utils().getMyWord("{bac_test}"))
            bactest = BacTest(self.projectTag, self.options)
            bactest.bacTest()
            self.log.debug("BacTest模块正常")
        except Exception as e:
            self.log.error("[Err] %s" % e)

        # 文件上传功能模糊测试
        try:
            self.log.info(Utils().tellTime() + Utils().getMyWord("{upload_test}"))
            uploadtest = UploadTest(self.projectTag, self.options)
            uploadtest.uploadTest()
            self.log.debug("UploadTest模块正常")
        except Exception as e:
            self.log.error("[Err] %s" % e)

        # SQL注入漏洞检测
        try:
            self.log.info(Utils().tellTime() + Utils().getMyWord("{sql_test}"))
            sqltest = SqlTest(self.projectTag, self.options)
            sqltest.sqlTest()
            self.log.debug("SqlTest模块正常")
        except Exception as e:
            self.log.error("[Err] %s" % e)
