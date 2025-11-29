#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import urllib3,requests,random
from lib.common.CreatLog import creatLog
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED


class ApiText(object):
    """
    API文本检测类，用于并发检测多个URL的响应内容

    Attributes:
        log: 日志记录器实例
        UserAgent: 用户代理字符串列表，用于模拟不同浏览器请求
        codes: 状态码列表（未使用）
        url: URL列表（未使用）
        urls: 待检测的URL列表
        res: 存储URL检测结果的字典
        options: 配置选项对象
        proxy_data: 代理配置字典
    """

    def __init__(self, urls, options):
        """
        初始化ApiText实例

        Args:
            urls (list): 待检测的URL列表
            options (object): 配置选项对象，包含proxy、contenttype、cookie、head、ssl_flag等属性
        """
        self.log = creatLog().get_logger()
        self.UserAgent = ["Mozilla/5.0 (Windows NT 6.1; WOW64; rv:34.0) Gecko/20100101 Firefox/34.0",
                          "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; en) Opera 9.50",
                          "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.57.2 (KHTML, like Gecko) Version/5.1.7 Safari/534.57.2",
                          "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36",
                          "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11",
                          "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.133 Safari/534.16",
                          "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko",
                          "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.11 TaoBrowser/2.0 Safari/536.11",
                          "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Maxthon/4.4.3.4000 Chrome/30.0.1599.101 Safari/537.36",
                          "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SV1; QQDownload 732; .NET4.0C; .NET4.0E; SE 2.X MetaSr 1.0)",
                          "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E; LBBROWSER)",
                          "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50",
                          "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0",
                          "Opera/9.80 (Windows NT 6.1; U; en) Presto/2.8.131 Version/11.11",
                          "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; TencentTraveler 4.0)"]
        self.codes = []
        self.url = []
        self.urls = urls
        self.res = {}
        self.options = options
        self.proxy_data = {'http': self.options.proxy,'https': self.options.proxy}

    def check(self, url):
        """
        检测单个URL的响应内容

        通过发送HTTP GET请求获取URL的响应文本内容，并将结果存储在实例变量res中。
        支持自定义请求头、Cookie、代理和SSL验证设置。

        Args:
            url (str): 待检测的URL地址

        Note:
            异常处理：网络请求异常会被记录到日志中
        """
        urllib3.disable_warnings()  # 禁止跳出来对warning

        # 设置Content-Type请求头
        if self.options.contenttype != None:
            contenttype = self.options.contenttype
        else:
            contenttype = 'application/x-www-form-urlencoded'

        # 根据是否提供Cookie设置请求头
        if self.options.cookie != None:
            headers = {
                'User-Agent': random.choice(self.UserAgent),
                'Content-Type': contenttype,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Cookie': self.options.cookie,
                self.options.head.split(':')[0]: self.options.head.split(':')[1]
            }
        else:
            headers = {
                'User-Agent': random.choice(self.UserAgent),
                'Content-Type': contenttype,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                self.options.head.split(':')[0]: self.options.head.split(':')[1]
            }

        s = requests.Session()
        s.keep_alive = False
        sslFlag = int(self.options.ssl_flag)

        try:
            # 根据SSL标志决定是否验证SSL证书
            if sslFlag == 1:
                text = str(s.get(url, headers=headers, timeout=6, proxies=self.proxy_data, verify=False).text)
            else:
                text = str(s.get(url, headers=headers, timeout=6, proxies=self.proxy_data).text)
            self.res[url] = text
        except Exception as e:
            self.log.error("[Err] %s" % e)

    def run(self):
        """
        并发执行URL检测任务

        使用线程池并发执行所有URL的检测任务，等待所有任务完成后返回检测结果。

        Returns:
            dict: 包含所有URL检测结果的字典，键为URL，值为响应文本
        """
        # target = (url for url in self.urls)
        pool = ThreadPoolExecutor(20)
        allTask = [pool.submit(self.check, domain) for domain in self.urls]
        wait(allTask, return_when=ALL_COMPLETED)
        # print(self.res)
        return self.res
        # for future in as_completed(allTask):
        #     data = future.result()
        #     print(data)

# if __name__ == '__main__':
#     try:
#         # banner()
#         che = Checkstatus()
#         che.run()
#     except KeyboardInterrupt:
#         print("停止中...")

