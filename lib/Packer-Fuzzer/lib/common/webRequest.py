#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import urllib3,requests,random,time
from threading import Thread
from lib.common.CreatLog import creatLog
from concurrent.futures import ThreadPoolExecutor,ALL_COMPLETED,wait


class WebRequest(object):
    """
    Web请求处理类，用于发送HTTP请求并获取响应信息

    Attributes:
        log: 日志记录器实例
        UserAgent: 用户代理字符串列表
        texts: 存储响应内容的列表
        responses: 存储响应头信息的列表
        mode: 请求模式（1-仅获取状态码，2-获取响应头，3-获取响应头和内容）
        res: 存储响应头和内容的字典
        codes: 存储URL和状态码映射的字典
        urls: 待请求的URL列表
        options: 配置选项对象
        proxy_data: 代理配置字典
    """

    def __init__(self, mode, urls,options):
        """
        初始化WebRequest对象

        Args:
            mode: 请求模式标识
            urls: URL列表
            options: 配置选项对象
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
        self.texts = []  # 保存返回数据包里面的数据
        self.responses = []  # 保存返回包的响应头
        self.mode = int(mode)  # 模式选择
        self.res = {}
        # self.codes = []
        self.codes = {}
        self.urls = urls
        self.options = options
        self.proxy_data = {'http': self.options.proxy,'https': self.options.proxy}

    def check(self, url, options):
        """
        发送HTTP请求并根据模式获取相应数据

        Args:
            url: 目标URL
            options: 配置选项

        Returns:
            根据不同模式返回不同的数据：
            - 模式2：返回响应头列表
            - 模式3：返回响应头和内容的zip对象
        """
        urllib3.disable_warnings()  # 禁止跳出来对warning
        sslFlag = int(self.options.ssl_flag)

        # 构造请求头，支持自定义cookie和header
        if self.options.cookie != None:
            headers = {
                'User-Agent': random.choice(self.UserAgent),
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Cookie':options.cookie,
                self.options.head.split(':')[0]: self.options.head.split(':')[1]
            }
        else:
            headers = {
                'User-Agent': random.choice(self.UserAgent),
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                self.options.head.split(':')[0]: self.options.head.split(':')[1]

            }

        s = requests.Session()
        s.keep_alive = False

        try:
            # 模式1：仅获取状态码
            if self.mode == 1:
                try:
                    if sslFlag == 1:
                        code = str(s.get(url, headers=headers, timeout=6, proxies=self.proxy_data, verify=False).status_code)  # 正常的返回code是int类型
                    else:
                        code = str(s.get(url, headers=headers, timeout=6, proxies=self.proxy_data).status_code)
                    # self.codes.append(url+": "+code)
                    self.codes[url] = code
                except Exception as e:
                    self.log.error("[Err] %s" % e)

            # 模式2：获取响应头
            if self.mode == 2:
                # 获取响应包
                try:
                    if sslFlag == 1:
                        response = str(s.get(url, headers=headers, timeout=6, proxies=self.proxy_data, verify=False).headers)
                    else:
                        response = str(s.get(url, headers=headers, timeout=6, proxies=self.proxy_data).headers)
                    self.responses.append(url + ": " + response)
                    return self.responses
                except Exception as e:
                    self.log.error("[Err] %s" % e)


            # 模式3：获取响应头和内容
            if self.mode == 3:
                try:
                    if sslFlag == 1:
                        text = str(s.get(url, headers=headers, timeout=6, proxies=self.proxy_data, verify=False).text)
                        response = str(s.get(url, headers=headers, timeout=6, proxies=self.proxy_data, verify=False).headers)
                    else:
                        text = str(s.get(url, headers=headers, timeout=6, proxies=self.proxy_data).text)
                        response = str(s.get(url, headers=headers, timeout=6, proxies=self.proxy_data).headers)
                    self.texts.append(url + ": " + text)
                    self.responses.append(response)
                    self.res = zip(self.responses, self.texts)
                    return self.res
                except Exception as e:
                    self.log.error("[Err] %s" % e)

        except Exception as e:
            self.log.error("[Err] %s" % e)

    def forceBrute(self):
        """
        使用多线程并发执行HTTP请求

        通过线程池并发处理多个URL请求，提高扫描效率
        """
        pool = ThreadPoolExecutor(20)
        all_task = [pool.submit(self.check, domain) for domain in self.urls]
        wait(all_task, return_when=ALL_COMPLETED)
        # for path in self.urls:
        #     print(path)
        #     self.check(path)

        # time.sleep(1

        # threads = []
        # for url in urls:
        #     t = Thread(target=self.check, args=(url,))
        #     threads.append(t)
        #     t.start()
        # for t in threads:
        #     t.join()
        # target = (url for url in urls)
        # pool = ThreadPoolExecutor(20)
        # [pool.submit(self.check,domain) for domain in self.urls]
        # time.sleep(1)

