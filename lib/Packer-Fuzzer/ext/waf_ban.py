#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import requests,random
from lib.common.utils import Utils
from lib.Database import DatabaseType


class ext():
    """
    扩展模块类，用于检测目标网站是否对当前IP进行了WAF拦截。

    参数:
        projectTag: 项目标识符
        options: 配置选项对象，包含url、cookie、head、proxy、ssl_flag等属性
    """

    def __init__(self, projectTag, options):
        self.projectTag = projectTag
        self.options = options
        self.statut = 1   #0 disable  1 enable
        self.UserAgent = ["Mozilla/5.0 (Windows NT 6.1; WOW64; rv:34.0) Gecko/20100101 Firefox/34.0",
                          "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; en) Opera 9.50",
                          "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.57.2 (KHTML, like Gecko) Version/5.1.7 Safari/534.57.2",
                          "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36",
                          "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; TencentTraveler 4.0)"]
        self.ban_title = ["您的访问请求可能对网站造成安全威胁","您的请求包含恶意行为","已被服务器拒绝拦截时间","Request blocked",
                          "The incident ID is","非法操作！","网站防火墙","已被网站管理员设置拦截","拦截提示","入侵防御系统",
                          "可能托管恶意活动","您正在试图非法攻击","玄武盾","检测到可疑访问","当前访问疑似黑客攻击","创宇盾","安全拦截",
                          "您的访问可能对网站造成威胁","此次访问可能会对网站造成安全威胁","have been blocked","您的访问被阻断",
                          "可能对网站造成安全威胁","您的请求是黑客攻击","WAF拦截"]

    def start(self):
        """
        启动扩展模块的主入口函数。
        当statut为1时调用run方法执行检测逻辑。
        """
        if self.statut == 1:
            self.run()

    def run(self):
        """
        执行WAF拦截检测的核心逻辑。
        根据配置构造HTTP请求头和代理设置，发送GET请求并检查响应内容中是否包含WAF拦截特征字符串。
        如果发现拦截特征则输出警告信息。
        """
        # 构造请求头，根据是否提供cookie决定是否添加Cookie字段
        if self.options.cookie != None:
            header = {
                'User-Agent': random.choice(self.UserAgent),
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Cookie': self.options.cookie,
                self.options.head.split(':')[0]: self.options.head.split(':')[1]
            }
        else:
            header = {
                'User-Agent': random.choice(self.UserAgent),
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                self.options.head.split(':')[0]: self.options.head.split(':')[1]
            }

        # 设置代理配置
        proxy_data = {
            'http': self.options.proxy,
            'https': self.options.proxy,
        }

        # 根据SSL标志决定是否验证证书，并发送GET请求获取网页内容
        sslFlag = int(self.options.ssl_flag)
        if sslFlag == 1:
            testWeb = requests.get(self.options.url, proxies=proxy_data, headers=header,timeout=7,verify=False).text.strip()
        else:
            testWeb = requests.get(self.options.url, proxies=proxy_data, headers=header,timeout=7).text.strip()

        # 检查响应内容中是否包含WAF拦截的特征字符串
        for ban in self.ban_title:
            if ban in testWeb:
                print(Utils().tellTime() + "After a SaoCaoZuo your IP seems to be blocked by GeZhong 666666 de WAF !")
